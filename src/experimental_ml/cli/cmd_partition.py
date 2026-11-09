"""Command handlers for 'expml partition' subcommands.

Complies with CLI-04, CLI-05, CLI-07, CLI-08, CLI-10, and CLI-11.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from experimental_ml.cli.cmd_data import _load_schema_spec
from experimental_ml.core.findings import ConfigurationError, DataIntegrityError
from experimental_ml.core.storage import read_json, write_json_atomic
from experimental_ml.data.codecs import (
    dataset_descriptor_from_dict,
    dataset_profile_from_dict,
    preparation_plan_from_dict,
)
from experimental_ml.data.loader import load_dataset
from experimental_ml.data.preparation import sanitize_dataset
from experimental_ml.stages.stage_gates import (
    DATASET_DESCRIPTOR_REL_PATH,
    DATASET_PROFILE_REL_PATH,
    PARTITION_PLAN_REL_PATH,
    PREPARATION_PLAN_REL_PATH,
    SPLITS_CSV_GZ_REL_PATH,
    SPLITS_SCHEMA_REL_PATH,
    reconstruct_sanitized_view,
    verify_partition_gate,
    verify_preparation_gate,
)
from experimental_ml.validation.codecs import (
    partition_plan_from_dict,
    partition_plan_to_dict,
)
from experimental_ml.validation.engine import build_partition_plan
from experimental_ml.validation.storage import (
    write_splits_csv_gz,
    write_splits_schema,
)
from experimental_ml.validation.types import (
    EvaluationRegime,
    PartitionConfig,
    PartitionStrategy,
)
from experimental_ml.validation.validators import validate_partition_plan


def handle_partition_build(args: argparse.Namespace) -> int:
    """Handle 'expml partition build'."""
    exp_dir = Path(args.experiment_dir).resolve()
    config_path = Path(args.config).resolve()

    if not config_path.exists():
        raise ConfigurationError(f"Partition config file not found at '{config_path}'")

    # CLI-07: verify upstream preparation gate
    verify_preparation_gate(exp_dir)

    # Load partition config JSON
    cfg_d = read_json(config_path)
    master_seed = (
        args.seed if args.seed is not None else int(cfg_d.get("master_seed", 42))
    )

    config = PartitionConfig(
        strategy=PartitionStrategy(cfg_d["strategy"]),
        regime=EvaluationRegime(cfg_d.get("regime", "CV_ONLY")),
        n_splits=int(cfg_d.get("n_splits", 5)),
        holdout_fraction=cfg_d.get("holdout_fraction"),
        n_bootstraps=cfg_d.get("n_bootstraps"),
        time_col=cfg_d.get("time_col"),
        group_col=cfg_d.get("group_col"),
        stratify=bool(cfg_d.get("stratify", False)),
        shuffle=bool(cfg_d.get("shuffle", True)),
        master_seed=master_seed,
    )

    # Reconstruct sanitized view using public stages API (REV-M2-08)
    view = reconstruct_sanitized_view(exp_dir)

    # Build deterministic partition plan
    plan = build_partition_plan(view, config)

    # Persist partition artifacts
    plan_file = exp_dir / PARTITION_PLAN_REL_PATH
    splits_file = exp_dir / SPLITS_CSV_GZ_REL_PATH
    schema_file = exp_dir / SPLITS_SCHEMA_REL_PATH

    write_json_atomic(plan_file, partition_plan_to_dict(plan), overwrite=args.force)
    write_splits_csv_gz(splits_file, plan, overwrite=args.force)
    write_splits_schema(schema_file, plan, overwrite=args.force)

    # CLI-04 & CLI-11: print readable summary without raw 64-char hash digests
    n_total = len(plan.development_ids) + len(plan.holdout_ids)
    sys.stdout.write(
        f"Partition plan built successfully: regime={plan.regime.value}, strategy={plan.strategy.value}\n"
    )
    sys.stdout.write(
        f"Observations: total={n_total}, development={len(plan.development_ids)}, holdout={len(plan.holdout_ids)}\n"
    )
    sys.stdout.write(f"Folds ({len(plan.folds)}):\n")
    for f in plan.folds:
        sys.stdout.write(
            f"  Fold {f.fold_index}: train={len(f.train_ids)}, val={len(f.val_ids)}\n"
        )

    return 0


def handle_partition_verify(args: argparse.Namespace) -> int:
    """Handle 'expml partition verify'."""
    exp_dir = Path(args.experiment_dir).resolve()

    # CLI-05 & CLI-07: verify partition gate and consistency
    verify_partition_gate(exp_dir)

    # Mathematical invariant validation
    plan_dict = read_json(exp_dir / PARTITION_PLAN_REL_PATH)
    plan = partition_plan_from_dict(plan_dict)
    view = reconstruct_sanitized_view(exp_dir)

    validate_partition_plan(plan, view)

    # CLI-05 & CLI-11: print confirmation without hash digests
    sys.stdout.write(
        "Partition plan verification PASSED. All stage gates and mathematical invariants satisfied.\n"
    )
    return 0
