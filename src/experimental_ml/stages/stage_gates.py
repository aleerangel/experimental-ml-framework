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
from experimental_ml.features.scenarios import (
    ScenariosCatalog,
    load_scenarios,
    validate_scenarios,
)
from experimental_ml.validation.codecs import partition_plan_from_dict
from experimental_ml.validation.storage import read_splits_csv_gz

# Canonical experiment layout constants (ARQUITETURA §5, D11)
DATASET_DESCRIPTOR_REL_PATH = "data/dataset_descriptor.json"
DATASET_PROFILE_REL_PATH = "data/dataset_profile.json"
PREPARATION_PLAN_REL_PATH = "configuration/preparation_plan.json"
SCENARIOS_CATALOG_REL_PATH = "configuration/scenarios.json"
MODELS_CATALOG_REL_PATH = "configuration/models.json"
EXPLORATORY_FEATURES_REL_PATH = "reports/exploratory_features.json"
SANITIZED_VIEW_REL_PATH = "data/sanitized_view.json"
PARTITION_PLAN_REL_PATH = "partitions/partition_plan.json"
SPLITS_CSV_GZ_REL_PATH = "partitions/splits.csv.gz"
SPLITS_SCHEMA_REL_PATH = "partitions/splits.schema.json"
EXECUTION_STATE_REL_PATH = "runs/execution_state.json"
CELLS_DIR_REL_PATH = "runs/cells"
PREDICTIONS_DIR_REL_PATH = "runs/predictions"
OOF_DIR_REL_PATH = "runs/oof"


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


def verify_scenarios_gate(
    target: Path | str,
    view: SanitizedDatasetView | None = None,
) -> ScenariosCatalog:
    """Verify that Stage 2 feature scenarios exist, are valid, and hashes match view (SCN-08).

    Args:
        target: Path to scenarios.json file OR experiment directory root containing
            configuration/scenarios.json.
        view: Optional SanitizedDatasetView. If omitted and target is an experiment
            directory, view will be reconstructed via reconstruct_sanitized_view.

    Returns:
        Validated ScenariosCatalog.

    Raises:
        ContractViolationError: If scenarios.json is missing or invalid.
        DataIntegrityError: If dataset_hash does not match the view.
    """
    path = Path(target).resolve()
    if path.is_dir():
        catalog_path = path / SCENARIOS_CATALOG_REL_PATH
        active_view = view if view is not None else reconstruct_sanitized_view(path)
    else:
        catalog_path = path
        active_view = view

    if not catalog_path.exists():
        raise ContractViolationError(
            f"Scenarios configuration file not found: '{catalog_path}' (SCN-08)"
        )

    catalog = load_scenarios(catalog_path)

    if active_view is not None:
        if catalog.dataset_hash != active_view.dataset_hash:
            raise DataIntegrityError(
                f"Scenarios catalog dataset_hash mismatch: expected '{active_view.dataset_hash}', "
                f"got '{catalog.dataset_hash}'"
            )
        # Structural re-validation against active view
        validate_scenarios(catalog.scenarios, active_view)

    return catalog


def verify_models_gate(target: Path | str) -> Any:
    """Verify that Stage 3 models catalog exists, is valid, and preparation gate holds.

    Args:
        target: Path to models.json file OR experiment directory root containing
            configuration/models.json.

    Returns:
        Validated ModelsCatalog instance.

    Raises:
        ContractViolationError: If preparation gate is not READY, or if catalog has 0 models.
        DataIntegrityError: If configuration/models.json is missing or corrupted.
    """
    from experimental_ml.models.spec import validate_models_catalog
    from experimental_ml.models.storage import load_models_catalog

    path = Path(target).resolve()
    if path.is_dir():
        catalog_path = path / MODELS_CATALOG_REL_PATH
        # Precondition: preparation gate must hold (STORE-05)
        verify_preparation_gate(path)
    else:
        catalog_path = path
        exp_dir = path.parent.parent
        if (exp_dir / PREPARATION_PLAN_REL_PATH).exists():
            verify_preparation_gate(exp_dir)

    if not catalog_path.exists():
        raise DataIntegrityError(f"Models catalog missing at '{catalog_path}'")

    try:
        catalog = load_models_catalog(catalog_path)
    except Exception as exc:
        raise DataIntegrityError(f"Failed to load models catalog at '{catalog_path}': {exc}") from exc

    if len(catalog.models) == 0:
        raise ContractViolationError(f"Models catalog at '{catalog_path}' cannot be empty")

    validate_models_catalog(catalog.models)
    return catalog


def verify_runs_gate(target: Path | str) -> dict[str, Any]:
    """Verify that Stage 4 execution artifacts exist, are terminal, and hashes are aligned.

    Args:
        target: Root directory of the experiment, OR runs directory containing execution_state.json.

    Returns:
        Summary dict containing execution metrics and verified configurations.

    Raises:
        ContractViolationError: If non-terminal cells (PENDING/RUNNING) exist.
        DataIntegrityError: If execution_state is missing/corrupted, cell/prediction artifacts
            are missing, OOF records are missing, or cross-hashes diverge.
    """
    from experimental_ml.core.enums import ExecutionStatus
    from experimental_ml.orchestration.oof import load_oof_predictions
    from experimental_ml.orchestration.state import load_execution_state

    target_path = Path(target).resolve()

    if (target_path / "execution_state.json").exists():
        run_dir = target_path
        exp_dir = target_path.parent if target_path.name == "runs" else target_path
    elif (target_path / EXECUTION_STATE_REL_PATH).exists():
        run_dir = target_path / "runs"
        exp_dir = target_path
    else:
        run_dir = target_path / "runs" if (target_path / "runs").exists() else target_path
        exp_dir = target_path
        state_file = run_dir / "execution_state.json"
        if not state_file.exists():
            raise DataIntegrityError(f"Execution state missing at '{state_file}'")

    # 1. Upstream gates verification if upstream artifacts exist in exp_dir
    if (exp_dir / PREPARATION_PLAN_REL_PATH).exists() and (exp_dir / DATASET_DESCRIPTOR_REL_PATH).exists():
        verify_preparation_gate(exp_dir)
    if (exp_dir / PARTITION_PLAN_REL_PATH).exists() and (exp_dir / SPLITS_CSV_GZ_REL_PATH).exists():
        verify_partition_gate(exp_dir)
    if (exp_dir / SCENARIOS_CATALOG_REL_PATH).exists() and (exp_dir / SANITIZED_VIEW_REL_PATH).exists():
        verify_scenarios_gate(exp_dir)
    if (exp_dir / MODELS_CATALOG_REL_PATH).exists() and (exp_dir / PREPARATION_PLAN_REL_PATH).exists():
        verify_models_gate(exp_dir)

    # 2. Load execution state
    state_file = run_dir / "execution_state.json"
    if not state_file.exists():
        raise DataIntegrityError(f"Execution state missing at '{state_file}'")

    try:
        exec_state = load_execution_state(run_dir)
    except Exception as exc:
        raise DataIntegrityError(f"Failed to load execution state at '{state_file}': {exc}") from exc

    # 3. Non-terminal cell statuses check
    non_terminal = [
        cid
        for cid, status in exec_state.cell_statuses.items()
        if status in (ExecutionStatus.PENDING, ExecutionStatus.RUNNING)
    ]
    if non_terminal:
        raise ContractViolationError(
            f"Execution contains {len(non_terminal)} non-terminal cell(s) (PENDING or RUNNING): {non_terminal}"
        )

    # 4. Verify physical disk artifacts for cells
    candidate_cells_dirs = [run_dir / "cells", exp_dir / "runs" / "cells"]
    candidate_preds_dirs = [
        run_dir / "predictions",
        exp_dir / "predictions",
        exp_dir / "runs" / "predictions",
    ]
    candidate_oof_dirs = [run_dir / "oof", exp_dir / "oof", exp_dir / "runs" / "oof"]

    completed_configs: set[tuple[str, str]] = set()

    for cid, status in exec_state.cell_statuses.items():
        cell_file_found = any((d / f"cell_{cid}.json").exists() for d in candidate_cells_dirs)
        if not cell_file_found:
            raise DataIntegrityError(
                f"Missing cell artifact for cell '{cid}' with status {status.value}"
            )

        if status == ExecutionStatus.COMPLETED:
            pred_file_found = any((d / f"pred_{cid}.json").exists() for d in candidate_preds_dirs)
            if not pred_file_found:
                raise DataIntegrityError(
                    f"Missing prediction artifact for completed cell '{cid}'"
                )

            cid_str = str(cid)
            parts = cid_str.replace("cell_", "").split("__")
            if len(parts) >= 3:
                m_id, sc_id = parts[0], parts[1]
                completed_configs.add((m_id, sc_id))

    # 5. Verify OOF records exist for all completed configurations
    for m_id, sc_id in completed_configs:
        oof_filename = f"oof_{m_id}__{sc_id}.json"
        oof_found_dir: Path | None = None
        for d in candidate_oof_dirs:
            if (d / oof_filename).exists():
                oof_found_dir = d.parent
                break

        if oof_found_dir is None:
            raise DataIntegrityError(
                f"Missing consolidated OOF predictions for configuration ({m_id}, {sc_id})"
            )

        try:
            load_oof_predictions(m_id, sc_id, oof_found_dir)
        except Exception as exc:
            raise DataIntegrityError(
                f"Failed to load OOF artifact for configuration ({m_id}, {sc_id}): {exc}"
            ) from exc

    # 6. Cross-hash verification across all cell records (ACH-M5-03)
    if (exp_dir / PARTITION_PLAN_REL_PATH).exists():
        part_dict = read_json(exp_dir / PARTITION_PLAN_REL_PATH)
        expected_plan_id = part_dict.get("plan_id")
        if expected_plan_id:
            for cid in exec_state.cell_statuses.keys():
                for d in candidate_cells_dirs:
                    cfile = d / f"cell_{cid}.json"
                    if cfile.exists():
                        c_dict = read_json(cfile)
                        c_plan_id = c_dict.get("partition_plan_id")
                        if c_plan_id and str(c_plan_id) != str(expected_plan_id):
                            raise DataIntegrityError(
                                f"partition_plan_id mismatch in cell '{cid}': expected '{expected_plan_id}', got '{c_plan_id}'"
                            )
                        break

    if (exp_dir / SANITIZED_VIEW_REL_PATH).exists():
        view_dict = read_json(exp_dir / SANITIZED_VIEW_REL_PATH)
        expected_dataset_hash = view_dict.get("dataset_hash")
        if expected_dataset_hash and exec_state.source_dataset_hash:
            if str(exec_state.source_dataset_hash) != str(expected_dataset_hash):
                raise DataIntegrityError(
                    f"source_dataset_hash mismatch: expected '{expected_dataset_hash}', got '{exec_state.source_dataset_hash}'"
                )

    # 7. Semantic completeness determination (ACH-M5-03)
    is_complete = (
        exec_state.failed_cells == 0
        and exec_state.cancelled_cells == 0
        and exec_state.completed_cells == exec_state.total_cells
        and exec_state.total_cells > 0
    )
    status_str = "READY" if is_complete else "PARTIAL_READY"
    warnings_list: list[str] = []
    if not is_complete:
        warnings_list.append(
            f"Execution is partially complete: {exec_state.completed_cells}/{exec_state.total_cells} completed, "
            f"{exec_state.failed_cells} failed, {exec_state.cancelled_cells} cancelled."
        )

    return {
        "experiment_id": str(exec_state.experiment_id),
        "total_cells": exec_state.total_cells,
        "completed_cells": exec_state.completed_cells,
        "failed_cells": exec_state.failed_cells,
        "cancelled_cells": exec_state.cancelled_cells,
        "execution_complete": is_complete,
        "verified_configurations": [f"{m}__{s}" for m, s in sorted(completed_configs)],
        "status": status_str,
        "warnings": warnings_list,
    }



