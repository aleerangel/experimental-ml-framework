"""Command handlers for 'expml data' subcommands.

Complies with CLI-01, CLI-02, CLI-03, CLI-08, CLI-10, and CLI-11.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from experimental_ml.core.enums import TaskType
from experimental_ml.core.findings import ConfigurationError, DataIntegrityError
from experimental_ml.core.storage import read_json, write_json_atomic
from experimental_ml.data.codecs import (
    dataset_descriptor_from_dict,
    dataset_descriptor_to_dict,
    dataset_profile_from_dict,
    dataset_profile_to_dict,
    preparation_plan_to_dict,
    sanitized_view_descriptor_to_dict,
)
from experimental_ml.data.descriptors import DatasetDescriptor, SanitizedViewDescriptor
from experimental_ml.data.loader import load_dataset
from experimental_ml.data.preparation import (
    PreparationRule,
    create_preparation_plan,
    sanitize_dataset,
)
from experimental_ml.data.profiling import profile_dataset
from experimental_ml.data.schema import ColumnSemanticType, DatasetSchemaSpec
from experimental_ml.stages.stage_gates import (
    DATASET_DESCRIPTOR_REL_PATH,
    DATASET_PROFILE_REL_PATH,
    PREPARATION_PLAN_REL_PATH,
    SANITIZED_VIEW_REL_PATH,
)


def _load_schema_spec(schema_path: Path | str) -> DatasetSchemaSpec:
    """Load and parse DatasetSchemaSpec from JSON file."""
    p = Path(schema_path).resolve()
    if not p.exists():
        raise ConfigurationError(f"Schema file not found at '{p}'")
    d = read_json(p)

    task_type = None
    if d.get("task_type"):
        task_type = TaskType(d["task_type"])

    semantic_types = None
    if d.get("column_semantic_types"):
        semantic_types = {
            col: ColumnSemanticType(st) for col, st in d["column_semantic_types"].items()
        }

    return DatasetSchemaSpec(
        target_col=d.get("target_col"),
        task_type=task_type,
        column_semantic_types=semantic_types,
        group_col=d.get("group_col"),
        time_col=d.get("time_col"),
        observation_id_col=d.get("observation_id_col"),
        ignore_cols=tuple(d.get("ignore_cols", ())),
    )


def handle_data_profile(args: argparse.Namespace) -> int:
    """Handle 'expml data profile'."""
    data_path = Path(args.data).resolve()
    schema_path = Path(args.schema).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not data_path.exists():
        raise ConfigurationError(f"Data file not found at '{data_path}'")

    schema = _load_schema_spec(schema_path)
    bundle = load_dataset(str(data_path), schema=schema)
    profile = profile_dataset(bundle)

    desc = DatasetDescriptor(
        dataset_hash=bundle.dataset_hash,
        raw_source_hash=getattr(bundle, "raw_source_hash", None),
        raw_source_path=str(data_path),
        n_observations=len(bundle.observation_ids),
        n_columns=len(bundle.columns),
        column_names=tuple(bundle.columns.keys()),
        column_types={col: str(bundle.columns[col].dtype) for col in bundle.columns},
        target_col=schema.target_col,
        task_type=schema.task_type.value if schema.task_type else None,
        group_col=schema.group_col,
        time_col=schema.time_col,
        schema_path=str(schema_path),
    )

    desc_file = output_dir / DATASET_DESCRIPTOR_REL_PATH
    prof_file = output_dir / DATASET_PROFILE_REL_PATH

    write_json_atomic(desc_file, dataset_descriptor_to_dict(desc), overwrite=args.force)
    write_json_atomic(prof_file, dataset_profile_to_dict(profile), overwrite=args.force)

    # CLI-01 & CLI-11: print dimensions and findings without raw hash digests
    sys.stdout.write(f"Dataset profiled: {profile.n_rows} rows x {profile.n_cols} columns\n")
    if profile.findings:
        sys.stdout.write(f"Findings identified ({len(profile.findings)}):\n")
        for f in profile.findings:
            col = f.context.get("column") if f.context else None
            col_info = f"column '{col}'" if col else "dataset-level"
            sys.stdout.write(f"  [{f.severity.value}] {f.code} ({col_info}): {f.message}\n")
    else:
        sys.stdout.write("No diagnostic findings identified.\n")

    return 0


def handle_data_sanitize(args: argparse.Namespace) -> int:
    """Handle 'expml data sanitize'."""
    exp_dir = Path(args.experiment_dir).resolve()
    rules_path = Path(args.rules).resolve()

    if not rules_path.exists():
        raise ConfigurationError(f"Rules file not found at '{rules_path}'")

    desc_file = exp_dir / DATASET_DESCRIPTOR_REL_PATH
    prof_file = exp_dir / DATASET_PROFILE_REL_PATH

    if not desc_file.exists():
        raise DataIntegrityError(f"Dataset descriptor missing at '{desc_file}'")
    if not prof_file.exists():
        raise DataIntegrityError(f"Dataset profile missing at '{prof_file}'")

    desc = dataset_descriptor_from_dict(read_json(desc_file))
    profile = dataset_profile_from_dict(read_json(prof_file))

    rules_raw = read_json(rules_path)
    if not isinstance(rules_raw, list):
        raise ConfigurationError("Rules file must contain a JSON list of rule objects")

    rules = [
        PreparationRule(
            finding_code=r["finding_code"],
            column=r.get("column"),
            kind=r["kind"],
            parameters=r.get("parameters", {}),
        )
        for r in rules_raw
    ]

    plan = create_preparation_plan(profile, rules)

    if plan.status != "READY":
        # CLI-03: do NOT write preparation_plan.json, print unresolved confirmed issues, exit code 2
        sys.stderr.write(
            f"Preparation plan is INCOMPLETE. Unresolved findings ({len(plan.unresolved_findings)}):\n"
        )
        for u in plan.unresolved_findings:
            col_info = f"column '{u.column}'" if u.column else "dataset-level"
            sys.stderr.write(f"  - {u.finding_code} ({col_info}): {u.reason}\n")
        return 2

    # CLI-02: plan is READY, execute sanitization and save artifacts
    if not desc.raw_source_path or not desc.schema_path:
        raise DataIntegrityError("Dataset descriptor lacks source path or schema path for reloading")

    schema = _load_schema_spec(desc.schema_path)
    bundle = load_dataset(desc.raw_source_path, schema=schema)
    view = sanitize_dataset(bundle, profile, plan)

    plan_file = exp_dir / PREPARATION_PLAN_REL_PATH
    view_file = exp_dir / SANITIZED_VIEW_REL_PATH

    view_desc = SanitizedViewDescriptor(
        dataset_hash=view.dataset_hash,
        source_dataset_hash=view.source_dataset_hash,
        source_plan_digest=view.source_plan_digest,
        n_observations=len(view.observation_ids),
        candidate_feature_cols=view.candidate_feature_cols,
        dropped_observation_ids=view.dropped_observation_ids,
        target_label_mapping=view.target_label_mapping,
        deferred_rules=view.deferred_rules,
    )

    write_json_atomic(plan_file, preparation_plan_to_dict(plan), overwrite=args.force)
    write_json_atomic(view_file, sanitized_view_descriptor_to_dict(view_desc), overwrite=args.force)

    sys.stdout.write(
        f"Dataset sanitized successfully.\n"
        f"Surviving observations: {len(view.observation_ids)} (dropped: {len(view.dropped_observation_ids)})\n"
        f"Candidate features: {len(view.candidate_feature_cols)}\n"
        f"Rules applied: {len(plan.rules)}\n"
    )

    return 0
