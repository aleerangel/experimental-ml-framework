"""Stage gates and cross-stage artifact integrity validation.

Complies with STORE-03, STORE-05, STORE-06, and CA-GER-01.
"""

from __future__ import annotations

from pathlib import Path

from experimental_ml.core.findings import ContractViolationError, DataIntegrityError
from experimental_ml.core.storage import read_json
from experimental_ml.data.codecs import (
    dataset_descriptor_from_dict,
    dataset_profile_from_dict,
    preparation_plan_from_dict,
)
from experimental_ml.data.loader import load_dataset
from experimental_ml.data.preparation import SanitizedDatasetView, sanitize_dataset
from experimental_ml.data.schema import load_schema_spec
from experimental_ml.validation.codecs import partition_plan_from_dict
from experimental_ml.validation.storage import read_splits_csv_gz

# Canonical experiment layout constants (ARQUITETURA §5, D11)
DATASET_DESCRIPTOR_REL_PATH = "data/dataset_descriptor.json"
DATASET_PROFILE_REL_PATH = "data/dataset_profile.json"
PREPARATION_PLAN_REL_PATH = "configuration/preparation_plan.json"
SANITIZED_VIEW_REL_PATH = "data/sanitized_view.json"
PARTITION_PLAN_REL_PATH = "partitions/partition_plan.json"
SPLITS_CSV_GZ_REL_PATH = "partitions/splits.csv.gz"
SPLITS_SCHEMA_REL_PATH = "partitions/splits.schema.json"


def verify_preparation_gate(experiment_dir: Path | str) -> None:
    """Verify that Stage 1 preparation artifacts exist, are READY, and hashes are aligned.

    Args:
        experiment_dir: Root directory of the experiment.

    Raises:
        ContractViolationError: If preparation_plan.json is missing or not 'READY' (STORE-05).
        DataIntegrityError: If descriptor or profile is missing or dataset hashes diverge.
    """
    exp_dir = Path(experiment_dir).resolve()

    desc_path = exp_dir / DATASET_DESCRIPTOR_REL_PATH
    prof_path = exp_dir / DATASET_PROFILE_REL_PATH
    plan_path = exp_dir / PREPARATION_PLAN_REL_PATH

    if not desc_path.exists():
        raise DataIntegrityError(f"Dataset descriptor missing at '{desc_path}'")
    if not prof_path.exists():
        raise DataIntegrityError(f"Dataset profile missing at '{prof_path}'")
    if not plan_path.exists():
        raise ContractViolationError(f"Preparation plan missing at '{plan_path}'")

    desc_dict = read_json(desc_path)
    prof_dict = read_json(prof_path)
    plan_dict = read_json(plan_path)

    # 1. Preparation status must be READY
    status = plan_dict.get("status")
    if status != "READY":
        raise ContractViolationError(
            f"Preparation plan at '{plan_path}' is not READY (status: '{status}')"
        )

    # 2. Hash alignment across descriptor, profile, and plan
    desc_hash = desc_dict.get("dataset_hash")
    prof_hash = prof_dict.get("source_dataset_hash")
    plan_source_hash = plan_dict.get("source_dataset_hash")

    if not (desc_hash and prof_hash and plan_source_hash):
        raise DataIntegrityError("One or more upstream artifacts lack valid dataset hashes")

    if not (desc_hash == prof_hash == plan_source_hash):
        raise DataIntegrityError(
            f"Dataset hash divergence between descriptor ({desc_hash}), "
            f"profile ({prof_hash}), and preparation plan ({plan_source_hash})"
        )


def verify_partition_gate(experiment_dir: Path | str) -> None:
    """Verify that Stage 4A partition artifacts are consistent with sanitized view and splits.

    Args:
        experiment_dir: Root directory of the experiment.

    Raises:
        ContractViolationError: If upstream preparation gate fails.
        DataIntegrityError: If partition artifacts are missing, hashes diverge, or splits mismatch.
    """
    exp_dir = Path(experiment_dir).resolve()

    # Precondition: upstream preparation gate must hold
    verify_preparation_gate(exp_dir)

    view_path = exp_dir / SANITIZED_VIEW_REL_PATH
    part_path = exp_dir / PARTITION_PLAN_REL_PATH
    splits_path = exp_dir / SPLITS_CSV_GZ_REL_PATH
    schema_path = exp_dir / SPLITS_SCHEMA_REL_PATH

    if not view_path.exists():
        raise DataIntegrityError(f"Sanitized view descriptor missing at '{view_path}'")
    if not part_path.exists():
        raise DataIntegrityError(f"Partition plan missing at '{part_path}'")
    if not splits_path.exists():
        raise DataIntegrityError(f"Splits matrix missing at '{splits_path}'")
    if not schema_path.exists():
        raise DataIntegrityError(f"Splits schema missing at '{schema_path}'")

    view_dict = read_json(view_path)
    part_dict = read_json(part_path)
    plan = partition_plan_from_dict(part_dict)
    splits_rows = read_splits_csv_gz(splits_path)

    # 1. Hash linkage: PartitionPlan source_dataset_hash == sanitized_view dataset_hash
    view_hash = view_dict.get("dataset_hash")
    if plan.source_dataset_hash != view_hash:
        raise DataIntegrityError(
            f"PartitionPlan source_dataset_hash '{plan.source_dataset_hash}' "
            f"diverges from sanitized_view dataset_hash '{view_hash}'"
        )

    # Check plan digest correspondence between sanitized_view and active preparation_plan (REV-M2-05)
    prep_plan_path = exp_dir / PREPARATION_PLAN_REL_PATH
    prep_dict = read_json(prep_plan_path)
    prep_digest = prep_dict.get("plan_digest")
    view_plan_digest = view_dict.get("source_plan_digest")
    if prep_digest and view_plan_digest and prep_digest != view_plan_digest:
        raise DataIntegrityError(
            f"sanitized_view source_plan_digest '{view_plan_digest}' "
            f"diverges from active preparation_plan plan_digest '{prep_digest}'"
        )

    # 2. Strict consistency between splits.csv.gz and partition_plan.json (STORE-06)
    expected_total = len(plan.development_ids) + len(plan.holdout_ids)
    if len(splits_rows) != expected_total:
        raise DataIntegrityError(
            f"splits.csv.gz row count ({len(splits_rows)}) does not match "
            f"PartitionPlan total observations ({expected_total})"
        )

    holdout_set = set(str(oid) for oid in plan.holdout_ids)
    dev_set = set(str(oid) for oid in plan.development_ids)

    n_folds = len(plan.folds)
    fold_train_sets = [{str(oid) for oid in f.train_ids} for f in plan.folds]
    fold_val_sets = [{str(oid) for oid in f.val_ids} for f in plan.folds]

    for row in splits_rows:
        oid = row["observation_id"]
        role = row["holdout_role"]

        if role == "HOLDOUT":
            if oid not in holdout_set:
                raise DataIntegrityError(
                    f"Observation '{oid}' marked as HOLDOUT in splits.csv.gz but absent from plan.holdout_ids"
                )
            for k in range(n_folds):
                if row.get(f"fold_{k}") != "EXCLUDED":
                    raise DataIntegrityError(
                        f"Holdout observation '{oid}' not marked as EXCLUDED in fold_{k}"
                    )
        elif role == "DEVELOPMENT":
            if oid not in dev_set:
                raise DataIntegrityError(
                    f"Observation '{oid}' marked as DEVELOPMENT in splits.csv.gz but absent from plan.development_ids"
                )
            for k in range(n_folds):
                col_val = row.get(f"fold_{k}")
                in_train = oid in fold_train_sets[k]
                in_val = oid in fold_val_sets[k]
                expected_role = "TRAIN" if in_train else ("VAL" if in_val else "EXCLUDED")
                if col_val != expected_role:
                    raise DataIntegrityError(
                        f"Observation '{oid}' in fold_{k} expected to be '{expected_role}' "
                        f"but marked as '{col_val}' in splits.csv.gz"
                    )
        else:
            raise DataIntegrityError(f"Invalid holdout_role '{role}' for observation '{oid}'")


def reconstruct_sanitized_view(experiment_dir: Path | str) -> SanitizedDatasetView:
    """Reconstruct in-memory SanitizedDatasetView from upstream Stage 1 artifacts (REV-M2-08).

    Verifies the preparation gate preconditions and executes deterministic
    sanitization from persisted dataset descriptor, profile, and preparation plan.

    Args:
        experiment_dir: Path to the experiment directory.

    Returns:
        Deterministic, immutable SanitizedDatasetView.

    Raises:
        ContractViolationError: If preparation gate fails.
        DataIntegrityError: If artifacts are missing or corrupted.
    """
    exp_dir = Path(experiment_dir).resolve()
    verify_preparation_gate(exp_dir)

    desc_path = exp_dir / DATASET_DESCRIPTOR_REL_PATH
    prof_path = exp_dir / DATASET_PROFILE_REL_PATH
    prep_plan_path = exp_dir / PREPARATION_PLAN_REL_PATH

    desc = dataset_descriptor_from_dict(read_json(desc_path))
    if not desc.raw_source_path or not desc.schema_path:
        raise DataIntegrityError(
            "Dataset descriptor lacks raw source path or schema path for reloading"
        )

    schema = load_schema_spec(desc.schema_path)
    bundle = load_dataset(desc.raw_source_path, schema=schema)
    prof = dataset_profile_from_dict(read_json(prof_path))
    plan = preparation_plan_from_dict(read_json(prep_plan_path))

    return sanitize_dataset(bundle, prof, plan)
