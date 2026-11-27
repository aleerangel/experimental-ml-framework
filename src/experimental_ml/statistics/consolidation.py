"""Consolidation and descriptive statistics module (STAT-02, STAT-03, CA-E5-01).

Implements Stage 4B -> Stage 5 gate validation (validate_stage5_entry) and
descriptive consolidation (consolidate_descriptive).
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from experimental_ml.core.enums import ExecutionStatus, MetricStatus
from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.features.stability import SelectionStabilityReport, compute_selection_stability
from experimental_ml.metrics.types import MetricValue
from experimental_ml.orchestration.oof import ConsolidatedOofPredictions
from experimental_ml.orchestration.state import (
    MatrixExecutionState,
    load_execution_state,
    matrix_execution_state_from_dict,
)
from experimental_ml.orchestration.types import CellResultRecord
from experimental_ml.statistics.types import (
    AggregatedMetricStats,
    AggregatedTimingStats,
    ConfigurationSummary,
    CoverageStatus,
    DescriptiveConsolidation,
)


def validate_stage5_entry(
    execution_state_or_target: MatrixExecutionState | Path | str | dict[str, Any],
) -> None:
    """Validate prerequisites before entering Stage 5 (STAT-02, CA-E5-01).

    Args:
        execution_state_or_target: A MatrixExecutionState instance, run directory/file path,
            or dictionary.

    Raises:
        ContractViolationError: If execution_state.json is missing or corrupted,
            if any cell has non-terminal status (PENDING or RUNNING),
            or if completed_cells == 0.
    """
    state: MatrixExecutionState
    if isinstance(execution_state_or_target, MatrixExecutionState):
        state = execution_state_or_target
    elif isinstance(execution_state_or_target, (str, Path)):
        target_path = Path(execution_state_or_target).resolve()
        state_file: Path
        if target_path.is_file() and target_path.name == "execution_state.json":
            state_file = target_path
            run_dir = target_path.parent
        elif (target_path / "execution_state.json").exists():
            state_file = target_path / "execution_state.json"
            run_dir = target_path
        elif (target_path / "runs" / "execution_state.json").exists():
            state_file = target_path / "runs" / "execution_state.json"
            run_dir = target_path / "runs"
        else:
            raise ContractViolationError(
                f"execution_state.json missing or unreadable at '{target_path}'"
            )

        try:
            state = load_execution_state(run_dir)
        except Exception as exc:
            raise ContractViolationError(
                f"Failed to parse execution state from '{state_file}': {exc}"
            ) from exc
    elif isinstance(execution_state_or_target, dict):
        try:
            state = matrix_execution_state_from_dict(execution_state_or_target)
        except Exception as exc:
            raise ContractViolationError(
                f"Failed to parse execution state dictionary: {exc}"
            ) from exc
    else:
        raise ContractViolationError(
            f"Unsupported execution state target type: {type(execution_state_or_target).__name__}"
        )

    # 1. Non-terminal cells check (PENDING or RUNNING)
    non_terminal = [
        cid
        for cid, status in state.cell_statuses.items()
        if status in (ExecutionStatus.PENDING, ExecutionStatus.RUNNING)
    ]
    if non_terminal:
        raise ContractViolationError(
            f"Execution contains {len(non_terminal)} non-terminal cell(s) (PENDING or RUNNING): {non_terminal}. "
            "Execution is in progress and must be completed or resumed before Stage 5."
        )

    # 2. At least one completed cell required
    if state.completed_cells == 0:
        raise ContractViolationError(
            f"Matrix execution contains zero completed cells ({state.completed_cells}/{state.total_cells}). "
            "At least one completed cell is required for Stage 5 consolidation."
        )


def consolidate_descriptive(
    cell_results: Sequence[CellResultRecord],
    *,
    total_folds_per_config: Mapping[tuple[str, str], int] | int,
    oof_predictions: Sequence[ConsolidatedOofPredictions] | None = None,
    n_total_candidates_per_config: Mapping[tuple[str, str], int] | None = None,
    experiment_id: str = "",
    partition_plan_id: str = "",
    timestamp_utc: str | None = None,
) -> DescriptiveConsolidation:
    """Consolidate cell results and OOF predictions descriptively per configuration (STAT-03, CA-E5-01).

    Args:
        cell_results: Sequence of CellResultRecord instances from Stage 4.
        total_folds_per_config: Mapping from (model_id, scenario_id) to total planned folds,
            or a single integer if uniform.
        oof_predictions: Optional sequence of ConsolidatedOofPredictions instances.
        n_total_candidates_per_config: Optional mapping from (model_id, scenario_id) to total
            candidate features in the pool for Kuncheva stability calculation.
        experiment_id: Canonical experiment identifier.
        partition_plan_id: Canonical partition plan identifier.
        timestamp_utc: Optional ISO-8601 UTC timestamp. Defaults to current time.

    Returns:
        Immutable DescriptiveConsolidation instance.
    """
    ts = timestamp_utc or datetime.now(timezone.utc).isoformat()

    # 1. Group cell results by (model_id, scenario_id)
    grouped: dict[tuple[str, str], list[CellResultRecord]] = {}
    for cell in cell_results:
        key = (str(cell.model_id), str(cell.scenario_id))
        grouped.setdefault(key, []).append(cell)

    # Also ensure configurations specified in total_folds_per_config are included even if zero cells
    if isinstance(total_folds_per_config, Mapping):
        for key in total_folds_per_config.keys():
            grouped.setdefault(key, [])

    # Index OOF predictions by (model_id, scenario_id)
    oof_by_config: dict[tuple[str, str], ConsolidatedOofPredictions] = {}
    if oof_predictions:
        for oof in oof_predictions:
            oof_key = (str(oof.model_id), str(oof.scenario_id))
            oof_by_config[oof_key] = oof

    configurations_summary: dict[tuple[str, str], ConfigurationSummary] = {}

    for (m_id, sc_id), cells in grouped.items():
        dev_cells = [c for c in cells if c.phase != "FINAL_HOLDOUT"]
        holdout_cells = [c for c in cells if c.phase == "FINAL_HOLDOUT"]

        # Determine total folds for this configuration (DEV_CV only)
        if isinstance(total_folds_per_config, Mapping):
            k_total = total_folds_per_config.get((m_id, sc_id), len(dev_cells) or 1)
        else:
            k_total = int(total_folds_per_config)

        completed_cells = [c for c in dev_cells if c.status == ExecutionStatus.COMPLETED]
        failed_cells = [c for c in dev_cells if c.status == ExecutionStatus.FAILED]
        cancelled_cells = [c for c in dev_cells if c.status == ExecutionStatus.CANCELLED]

        completed_fold_ids = tuple(c.fold_id for c in completed_cells)
        failed_fold_ids = tuple(c.fold_id for c in failed_cells)
        cancelled_fold_ids = tuple(c.fold_id for c in cancelled_cells)

        k_completed = len(completed_cells)
        k_failed = len(failed_cells)
        k_cancelled = len(cancelled_cells)

        coverage = float(k_completed / k_total) if k_total > 0 else 0.0

        if coverage >= 1.0:
            cov_status = CoverageStatus.VALID
        elif coverage > 0.0:
            cov_status = CoverageStatus.PARTIAL_COVERAGE
        else:
            cov_status = CoverageStatus.NO_COVERAGE

        # Extract fold metrics from completed cells
        fold_metrics: dict[str, dict[str, MetricValue]] = {}
        for c in completed_cells:
            fold_metrics[c.fold_id] = dict(c.metrics)

        # Aggregate metrics across completed folds
        aggregated_metrics: dict[str, AggregatedMetricStats] = {}

        # Collect all metric IDs observed in completed cells
        all_metric_ids: set[str] = set()
        for c in completed_cells:
            all_metric_ids.update(c.metrics.keys())

        for met_id in sorted(all_metric_ids):
            mvs = [c.metrics[met_id] for c in completed_cells if met_id in c.metrics]
            valid_mvs = [
                mv for mv in mvs
                if mv.status == MetricStatus.VALID and math.isfinite(mv.value)
            ]
            n_valid = len(valid_mvs)

            if n_valid == 0:
                agg_stat = AggregatedMetricStats(
                    n_valid=0,
                    n_total=k_total,
                    status=MetricStatus.UNDEFINED_NAN,
                    mean=None,
                    std=None,
                    median=None,
                    iqr=None,
                    q25=None,
                    q75=None,
                    min_value=None,
                    max_value=None,
                )
            elif n_valid == 1:
                val = float(valid_mvs[0].value)
                status = MetricStatus.VALID if n_valid == k_total else MetricStatus.PARTIAL_COVERAGE
                agg_stat = AggregatedMetricStats(
                    n_valid=1,
                    n_total=k_total,
                    status=status,
                    mean=val,
                    std=None,
                    median=val,
                    iqr=0.0,
                    q25=val,
                    q75=val,
                    min_value=val,
                    max_value=val,
                )
            else:
                arr = np.array([float(mv.value) for mv in valid_mvs], dtype=np.float64)
                status = MetricStatus.VALID if n_valid == k_total else MetricStatus.PARTIAL_COVERAGE
                q75, q25 = np.percentile(arr, [75, 25])
                agg_stat = AggregatedMetricStats(
                    n_valid=n_valid,
                    n_total=k_total,
                    status=status,
                    mean=float(np.mean(arr)),
                    std=float(np.std(arr, ddof=1)),
                    median=float(np.median(arr)),
                    iqr=float(q75 - q25),
                    q25=float(q25),
                    q75=float(q75),
                    min_value=float(np.min(arr)),
                    max_value=float(np.max(arr)),
                )
            aggregated_metrics[met_id] = agg_stat

        # Aggregate timing breakdown across completed cells
        aggregated_timing: AggregatedTimingStats | None = None
        if completed_cells:
            n_cells = float(len(completed_cells))
            de_total = sum(c.timing.data_extraction_time_s for c in completed_cells)
            prep_total = sum(c.timing.preprocessing_time_s for c in completed_cells)
            fs_total = sum(c.timing.feature_selection_time_s for c in completed_cells)
            tun_total = sum(c.timing.tuning_time_s for c in completed_cells)
            fit_total = sum(c.timing.fit_time_s for c in completed_cells)
            pred_total = sum(c.timing.predict_time_s for c in completed_cells)
            eval_total = sum(c.timing.evaluation_time_s for c in completed_cells)
            cell_sum = sum(c.timing.total_cell_time_s for c in completed_cells)

            aggregated_timing = AggregatedTimingStats(
                data_extraction_mean_s=float(de_total / n_cells),
                data_extraction_total_s=float(de_total),
                preprocessing_mean_s=float(prep_total / n_cells),
                preprocessing_total_s=float(prep_total),
                feature_selection_mean_s=float(fs_total / n_cells),
                feature_selection_total_s=float(fs_total),
                tuning_mean_s=float(tun_total / n_cells),
                tuning_total_s=float(tun_total),
                fit_mean_s=float(fit_total / n_cells),
                fit_total_s=float(fit_total),
                predict_mean_s=float(pred_total / n_cells),
                predict_total_s=float(pred_total),
                evaluation_mean_s=float(eval_total / n_cells),
                evaluation_total_s=float(eval_total),
                total_cell_mean_s=float(cell_sum / n_cells),
                total_cell_sum_s=float(cell_sum),
            )

        # Feature selection stability across folds
        feature_stability: SelectionStabilityReport | None = None
        if len(completed_cells) >= 2:
            fold_selections = [c.selected_features for c in completed_cells]
            # Determine n_total_candidates
            n_cands: int | None = None
            if n_total_candidates_per_config:
                n_cands = n_total_candidates_per_config.get((m_id, sc_id))
            if n_cands is None:
                all_feats = set().union(*fold_selections)
                n_cands = max(len(all_feats), 1)

            feature_stability = compute_selection_stability(
                fold_selections=fold_selections,
                n_total_candidates=n_cands,
            )

        # Pooled OOF metrics
        pooled_oof: dict[str, MetricValue] = {}
        if (m_id, sc_id) in oof_by_config:
            pooled_oof = dict(oof_by_config[(m_id, sc_id)].pooled_metrics)

        # Final holdout metrics (isolated from DEV_CV aggregation & inferential tests)
        holdout_metrics: dict[str, MetricValue] = {}
        completed_holdouts = [c for c in holdout_cells if c.status == ExecutionStatus.COMPLETED]
        if completed_holdouts:
            holdout_metrics = dict(completed_holdouts[-1].metrics)

        cfg_summary = ConfigurationSummary(
            model_id=m_id,
            scenario_id=sc_id,
            total_folds=k_total,
            completed_folds=k_completed,
            failed_folds=k_failed,
            cancelled_folds=k_cancelled,
            coverage=coverage,
            coverage_status=cov_status,
            completed_fold_ids=completed_fold_ids,
            failed_fold_ids=failed_fold_ids,
            cancelled_fold_ids=cancelled_fold_ids,
            fold_metrics=fold_metrics,
            aggregated_metrics=aggregated_metrics,
            pooled_oof_metrics=pooled_oof,
            holdout_metrics=holdout_metrics,
            aggregated_timing=aggregated_timing,
            feature_stability=feature_stability,
        )
        configurations_summary[(m_id, sc_id)] = cfg_summary

    return DescriptiveConsolidation(
        experiment_id=experiment_id,
        partition_plan_id=partition_plan_id,
        total_configurations=len(configurations_summary),
        configurations=configurations_summary,
        timestamp_utc=ts,
    )
