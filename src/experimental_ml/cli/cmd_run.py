"""Command handlers for 'expml run' subcommands.

Complies with CLI-06, CLI-07, CLI-08, CLI-09, CLI-10, CLI-11, ORCH-22 to ORCH-28, and ARQUITETURA §2.4.
"""

from __future__ import annotations

import argparse


def handle_run_start(args: argparse.Namespace) -> int:
    """Execute an experiment matrix and optionally consolidate OOF predictions.

    Args:
        args: Parsed CLI arguments.

    Returns:
        0 on success, non-zero on error.
    """
    from pathlib import Path
    import sys

    from experimental_ml.core.enums import ErrorPolicy
    from experimental_ml.core.findings import ConfigurationError, ExperimentalMLError
    from experimental_ml.core.storage import read_json
    from experimental_ml.features.scenarios import load_scenarios
    from experimental_ml.models.storage import load_models_catalog
    from experimental_ml.orchestration import run_experiment_matrix
    from experimental_ml.stages.stage_gates import (
        MODELS_CATALOG_REL_PATH,
        PARTITION_PLAN_REL_PATH,
        SCENARIOS_CATALOG_REL_PATH,
        reconstruct_sanitized_view,
        verify_models_gate,
        verify_partition_gate,
        verify_preparation_gate,
        verify_scenarios_gate,
    )
    from experimental_ml.validation.codecs import partition_plan_from_dict

    try:
        experiment_dir = Path(args.experiment_dir).resolve()
        if not experiment_dir.exists():
            raise ConfigurationError(f"Experiment directory not found at '{experiment_dir}'")

        run_dir = Path(args.run_dir).resolve() if getattr(args, "run_dir", None) else experiment_dir / "runs"
        force = bool(getattr(args, "force", False))

        # Overwrite protection against pre-existing execution state (CLI-08)
        if (run_dir / "execution_state.json").exists() and not force:
            raise ConfigurationError(
                f"Run directory '{run_dir}' already contains execution_state.json. Use --force to overwrite."
            )

        # 1. Verify upstream gates
        verify_preparation_gate(experiment_dir)
        verify_partition_gate(experiment_dir)
        verify_scenarios_gate(experiment_dir)
        verify_models_gate(experiment_dir)

        # 2. Reconstitute inputs
        sanitized_view = reconstruct_sanitized_view(experiment_dir)
        part_dict = read_json(experiment_dir / PARTITION_PLAN_REL_PATH)
        partition_plan = partition_plan_from_dict(part_dict)
        scenarios_catalog = load_scenarios(experiment_dir / SCENARIOS_CATALOG_REL_PATH)
        models_catalog = load_models_catalog(experiment_dir / MODELS_CATALOG_REL_PATH)

        # 3. Configure execution parameters
        n_workers = int(getattr(args, "parallel", 1))
        if n_workers < 1:
            raise ConfigurationError(f"Parallel workers must be >= 1, got {n_workers}")

        error_policy_val = str(getattr(args, "error_policy", "fault_tolerant")).upper()
        try:
            error_policy = ErrorPolicy[error_policy_val]
        except KeyError:
            raise ConfigurationError(f"Invalid error-policy: '{error_policy_val}'")

        auto_consolidate = not bool(getattr(args, "no_oof", False))
        master_seed = getattr(partition_plan.config, "master_seed", 42)

        # 4. Dispatch matrix execution
        try:
            state = run_experiment_matrix(
                model_specs=models_catalog.models,
                scenarios=scenarios_catalog.scenarios,
                partition_plan=partition_plan,
                sanitized_view=sanitized_view,
                run_dir=run_dir,
                master_seed=master_seed,
                error_policy=error_policy,
                outer_n_jobs=n_workers,
                overwrite=force,
                auto_consolidate_oof=auto_consolidate,
            )
        except Exception as exc:
            if error_policy == ErrorPolicy.FAIL_FAST:
                sys.stderr.write(f"Execution halted under fail_fast policy: {exc}\n")
                return 1
            raise exc

        # 5. Output summary (CLI-11: zero hashes printed)
        sys.stdout.write(
            f"Experiment matrix execution completed:\n"
            f"  - Total cells: {state.total_cells}\n"
            f"  - Completed cells: {state.completed_cells}\n"
            f"  - Failed cells: {state.failed_cells}\n"
            f"  - Cancelled cells: {state.cancelled_cells}\n"
            f"  - Destination: {run_dir}\n"
        )
        return 0
    except ExperimentalMLError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    except ValueError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2


def handle_run_resume(args: argparse.Namespace) -> int:
    """Resume an interrupted experiment matrix execution.

    Args:
        args: Parsed CLI arguments.

    Returns:
        0 on success, non-zero on error.
    """
    from pathlib import Path
    import sys

    from experimental_ml.core.findings import ConfigurationError, ExperimentalMLError
    from experimental_ml.core.storage import read_json
    from experimental_ml.features.scenarios import load_scenarios
    from experimental_ml.models.storage import load_models_catalog
    from experimental_ml.orchestration import resume_experiment_matrix
    from experimental_ml.stages.stage_gates import (
        MODELS_CATALOG_REL_PATH,
        PARTITION_PLAN_REL_PATH,
        PREPARATION_PLAN_REL_PATH,
        SCENARIOS_CATALOG_REL_PATH,
        reconstruct_sanitized_view,
        verify_models_gate,
        verify_partition_gate,
        verify_preparation_gate,
        verify_scenarios_gate,
    )
    from experimental_ml.validation.codecs import partition_plan_from_dict

    try:
        run_dir = Path(args.run_dir).resolve()
        if not run_dir.exists() or not (run_dir / "execution_state.json").exists():
            raise ConfigurationError(
                f"Run directory '{run_dir}' does not exist or lacks execution_state.json"
            )

        # Infer experiment_dir if not explicitly provided
        if getattr(args, "experiment_dir", None):
            experiment_dir = Path(args.experiment_dir).resolve()
        elif (run_dir.parent / PREPARATION_PLAN_REL_PATH).exists():
            experiment_dir = run_dir.parent
        elif (run_dir.parent.parent / PREPARATION_PLAN_REL_PATH).exists():
            experiment_dir = run_dir.parent.parent
        else:
            experiment_dir = run_dir.parent

        if not experiment_dir.exists():
            raise ConfigurationError(f"Experiment directory not found at '{experiment_dir}'")

        # 1. Verify upstream gates
        verify_preparation_gate(experiment_dir)
        verify_partition_gate(experiment_dir)
        verify_scenarios_gate(experiment_dir)
        verify_models_gate(experiment_dir)

        # 2. Reconstitute inputs
        sanitized_view = reconstruct_sanitized_view(experiment_dir)
        part_dict = read_json(experiment_dir / PARTITION_PLAN_REL_PATH)
        partition_plan = partition_plan_from_dict(part_dict)
        scenarios_catalog = load_scenarios(experiment_dir / SCENARIOS_CATALOG_REL_PATH)
        models_catalog = load_models_catalog(experiment_dir / MODELS_CATALOG_REL_PATH)

        # 3. Configure parameters
        n_workers = int(getattr(args, "parallel", 1))
        if n_workers < 1:
            raise ConfigurationError(f"Parallel workers must be >= 1, got {n_workers}")

        retry_failed = bool(getattr(args, "retry_failed", False))
        auto_consolidate = not bool(getattr(args, "no_oof", False))

        # 4. Resume matrix execution
        state = resume_experiment_matrix(
            run_dir=run_dir,
            model_specs=models_catalog.models,
            scenarios=scenarios_catalog.scenarios,
            partition_plan=partition_plan,
            sanitized_view=sanitized_view,
            outer_n_jobs=n_workers,
            retry_failed=retry_failed,
            auto_consolidate_oof=auto_consolidate,
        )

        # 5. Output summary (CLI-11: zero hashes printed)
        sys.stdout.write(
            f"Experiment matrix execution resumed and completed:\n"
            f"  - Total cells: {state.total_cells}\n"
            f"  - Completed cells: {state.completed_cells}\n"
            f"  - Failed cells: {state.failed_cells}\n"
            f"  - Cancelled cells: {state.cancelled_cells}\n"
            f"  - Destination: {run_dir}\n"
        )
        return 0
    except ExperimentalMLError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    except ValueError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2


def handle_run_status(args: argparse.Namespace) -> int:
    """Inspect progress of an experiment matrix execution.

    Args:
        args: Parsed CLI arguments.

    Returns:
        0 on success, non-zero on error.
    """
    from pathlib import Path
    import sys

    from experimental_ml.core.enums import ExecutionStatus
    from experimental_ml.core.findings import ConfigurationError, ExperimentalMLError
    from experimental_ml.orchestration import load_execution_state

    try:
        run_dir = Path(args.run_dir).resolve()
        if not run_dir.exists() or not (run_dir / "execution_state.json").exists():
            raise ConfigurationError(
                f"Run directory '{run_dir}' does not exist or lacks execution_state.json"
            )

        state = load_execution_state(run_dir)

        total = state.total_cells
        completed = state.completed_cells
        failed = state.failed_cells
        cancelled = state.cancelled_cells
        pending = sum(1 for s in state.cell_statuses.values() if s == ExecutionStatus.PENDING)
        running = sum(1 for s in state.cell_statuses.values() if s == ExecutionStatus.RUNNING)
        pct = (completed / total * 100.0) if total > 0 else 0.0

        # CLI-11: Only semantic counts and status, zero cryptographic hashes
        sys.stdout.write(
            f"Experiment execution status:\n"
            f"  - Total cells: {total}\n"
            f"  - Completed: {completed} ({pct:.1f}%)\n"
            f"  - Failed: {failed}\n"
            f"  - Cancelled: {cancelled}\n"
            f"  - Pending: {pending}\n"
            f"  - Running: {running}\n"
            f"  - State updated at: {state.updated_at}\n"
        )
        return 0
    except ExperimentalMLError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    except ValueError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2


def handle_run_verify(args: argparse.Namespace) -> int:
    """Verify stage 4 execution and OOF gates.

    Args:
        args: Parsed CLI arguments.

    Returns:
        0 on success, non-zero on error.
    """
    from pathlib import Path
    import sys

    from experimental_ml.core.findings import ConfigurationError, ExperimentalMLError
    from experimental_ml.stages.stage_gates import verify_runs_gate

    try:
        run_dir = Path(args.run_dir).resolve()
        if not run_dir.exists():
            raise ConfigurationError(f"Run directory not found at '{run_dir}'")

        summary = verify_runs_gate(run_dir)

        # CLI-11: Suppress cryptographic hashes, report semantic counts and status
        sys.stdout.write(
            f"Stage 4 execution gate verified successfully:\n"
            f"  - Status: {summary.get('status', 'READY')}\n"
            f"  - Total cells: {summary.get('total_cells', 0)}\n"
            f"  - Completed cells: {summary.get('completed_cells', 0)}\n"
            f"  - Failed cells: {summary.get('failed_cells', 0)}\n"
            f"  - Cancelled cells: {summary.get('cancelled_cells', 0)}\n"
            f"  - Verified configurations: {len(summary.get('verified_configurations', []))}\n"
        )
        return 0
    except ExperimentalMLError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    except ValueError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
