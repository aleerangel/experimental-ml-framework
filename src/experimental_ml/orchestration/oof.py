"""Out-of-fold (OOF) prediction consolidation, committee statistics, and storage.

Complies with ORCH-15, ORCH-16, ORCH-17, ORCH-18, ORCH-19, ORCH-20, RF4.7, STORE-01, and ADR-008.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from experimental_ml.core.enums import (
    AggregationScope,
    ExecutionStatus,
    MetricDirection,
    MetricStatus,
    TaskType,
)
from experimental_ml.core.findings import (
    ConfigurationError,
    ContractViolationError,
    DataIntegrityError,
    Finding,
    make_warning,
)
from experimental_ml.core.storage import read_json, write_json_atomic
from experimental_ml.core.types import ModelId, ObservationId, ScenarioId
from experimental_ml.metrics.aggregation import aggregate_fold_metrics
from experimental_ml.metrics.catalog import compute_metric, get_metric_spec
from experimental_ml.metrics.types import (
    AggregatedMetricValue,
    MetricEvaluationScope,
    MetricValue,
)
from experimental_ml.orchestration.types import CellResultRecord, PredictionRecord
import numpy as np


@dataclass(frozen=True, slots=True)
class ConsolidatedOofPredictions:
    """Immutable record consolidating out-of-fold predictions for a (model, scenario) configuration."""

    model_id: ModelId
    scenario_id: ScenarioId
    task_type: TaskType
    observation_ids: tuple[ObservationId, ...]
    y_true: tuple[float, ...]
    y_pred: tuple[float, ...]
    y_std: tuple[float | None, ...] | None = None
    y_proba: tuple[tuple[float, ...], ...] | None = None
    residuals: tuple[float, ...] | None = None
    pooled_metrics: Mapping[str, MetricValue] = field(default_factory=dict)
    aggregated_metrics: Mapping[str, AggregatedMetricValue] = field(default_factory=dict)
    fold_ids: tuple[str, ...] = field(default_factory=tuple)
    coverage: float = 1.0
    status: MetricStatus = MetricStatus.VALID
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.model_id, ModelId):
            object.__setattr__(self, "model_id", ModelId(str(self.model_id)))
        if not isinstance(self.scenario_id, ScenarioId):
            object.__setattr__(self, "scenario_id", ScenarioId(str(self.scenario_id)))
        if not isinstance(self.task_type, TaskType):
            object.__setattr__(self, "task_type", TaskType(self.task_type))

        obs = tuple(ObservationId(str(o)) for o in self.observation_ids)
        y_t = tuple(float(y) for y in self.y_true)
        y_p = tuple(float(y) for y in self.y_pred)

        n = len(obs)
        if n == 0:
            raise ContractViolationError("ConsolidatedOofPredictions cannot be empty (n_samples > 0)")
        if len(y_t) != n:
            raise ContractViolationError(
                f"y_true length ({len(y_t)}) does not match observation_ids ({n})"
            )
        if len(y_p) != n:
            raise ContractViolationError(
                f"y_pred length ({len(y_p)}) does not match observation_ids ({n})"
            )

        # Enforce canonical sorting by observation_id
        if list(obs) != sorted(obs):
            raise ContractViolationError("observation_ids must be canonically sorted in ascending order")

        # Check unique observation_ids
        if len(set(obs)) != n:
            raise ContractViolationError("observation_ids in ConsolidatedOofPredictions must be unique")

        object.__setattr__(self, "observation_ids", obs)
        object.__setattr__(self, "y_true", y_t)
        object.__setattr__(self, "y_pred", y_p)

        if self.y_std is not None:
            y_s = tuple(float(s) if s is not None else None for s in self.y_std)
            if len(y_s) != n:
                raise ContractViolationError(
                    f"y_std length ({len(y_s)}) does not match observation_ids ({n})"
                )
            object.__setattr__(self, "y_std", y_s)

        if self.y_proba is not None:
            proba_tuples = tuple(tuple(float(p) for p in row) for row in self.y_proba)
            if len(proba_tuples) != n:
                raise ContractViolationError(
                    f"y_proba length ({len(proba_tuples)}) does not match observation_ids ({n})"
                )
            object.__setattr__(self, "y_proba", proba_tuples)

        if self.residuals is not None:
            res = tuple(float(r) for r in self.residuals)
            if len(res) != n:
                raise ContractViolationError(
                    f"residuals length ({len(res)}) does not match observation_ids ({n})"
                )
            object.__setattr__(self, "residuals", res)

        if not isinstance(self.pooled_metrics, MappingProxyType):
            object.__setattr__(self, "pooled_metrics", MappingProxyType(dict(self.pooled_metrics)))

        if not isinstance(self.aggregated_metrics, MappingProxyType):
            object.__setattr__(
                self, "aggregated_metrics", MappingProxyType(dict(self.aggregated_metrics))
            )

        if not isinstance(self.fold_ids, tuple):
            object.__setattr__(self, "fold_ids", tuple(str(f) for f in self.fold_ids))

        cov = float(self.coverage)
        if cov < 0.0 or cov > 1.0:
            raise ContractViolationError(f"coverage must be in [0.0, 1.0], got {cov}")
        object.__setattr__(self, "coverage", cov)

        if not isinstance(self.status, MetricStatus):
            object.__setattr__(self, "status", MetricStatus(self.status))

        if not isinstance(self.warnings, tuple):
            object.__setattr__(self, "warnings", tuple(str(w) for w in self.warnings))


def save_oof_predictions(
    oof_record: ConsolidatedOofPredictions,
    run_dir: Path | str,
    *,
    overwrite: bool = False,
) -> Path:
    """Atomically save ConsolidatedOofPredictions to {run_dir}/oof/oof_{model}__{scenario}.json.

    Args:
        oof_record: The consolidated out-of-fold record.
        run_dir: Experiment execution directory.
        overwrite: If False, raises ConfigurationError if destination exists.

    Returns:
        Path to the saved JSON file.

    Raises:
        ConfigurationError: If destination file exists and overwrite is False.
    """
    from experimental_ml.orchestration.codecs import oof_predictions_to_dict

    run_path = Path(run_dir).resolve()
    oof_dir = run_path / "oof"
    oof_dir.mkdir(parents=True, exist_ok=True)

    filename = f"oof_{oof_record.model_id}__{oof_record.scenario_id}.json"
    oof_file = oof_dir / filename

    if not overwrite and oof_file.exists():
        raise ConfigurationError(
            f"Target OOF artifact already exists and overwrite is False: '{oof_file}'"
        )

    d = oof_predictions_to_dict(oof_record)
    write_json_atomic(oof_file, d, overwrite=overwrite)
    return oof_file


def load_oof_predictions(
    model_id: ModelId | str,
    scenario_id: ScenarioId | str,
    run_dir: Path | str,
) -> ConsolidatedOofPredictions:
    """Load ConsolidatedOofPredictions from {run_dir}/oof/oof_{model}__{scenario}.json.

    Args:
        model_id: Model identifier.
        scenario_id: Scenario identifier.
        run_dir: Experiment execution directory.

    Returns:
        Reconstructed ConsolidatedOofPredictions instance.

    Raises:
        ConfigurationError: If OOF artifact file does not exist or is malformed.
    """
    from experimental_ml.orchestration.codecs import oof_predictions_from_dict

    run_path = Path(run_dir).resolve()
    oof_file = run_path / "oof" / f"oof_{model_id}__{scenario_id}.json"

    if not oof_file.exists():
        raise ConfigurationError(f"OOF prediction artifact not found at '{oof_file}'")

    raw = read_json(oof_file)
    if not isinstance(raw, dict):
        raise ConfigurationError(
            f"Malformed OOF artifact at '{oof_file}': expected JSON object, got {type(raw).__name__}"
        )

    return oof_predictions_from_dict(raw)


def consolidate_oof_predictions(
    model_id: ModelId | str,
    scenario_id: ScenarioId | str,
    task_type: TaskType | str,
    prediction_records: Sequence[PredictionRecord],
    *,
    cell_results: Sequence[CellResultRecord] = (),
    metrics: Sequence[str] | None = None,
    target_observation_ids: Sequence[ObservationId | str] | None = None,
) -> ConsolidatedOofPredictions:
    """Consolidate out-of-fold prediction records into a canonical ConsolidatedOofPredictions.

    Args:
        model_id: Unique model identifier.
        scenario_id: Unique scenario identifier.
        task_type: ML task type (REGRESSION, BINARY_CLASSIFICATION, etc.).
        prediction_records: Non-empty sequence of PredictionRecord instances from development folds.
        cell_results: Optional sequence of CellResultRecord instances for fold metrics aggregation.
        target_observation_ids: Optional full expected sequence of observation IDs.

    Returns:
        Canonical ConsolidatedOofPredictions instance.

    Raises:
        DataIntegrityError: If prediction_records is empty, or if conflicting true labels exist.
        ContractViolationError: If inputs violate contracts.
    """
    m_id = ModelId(str(model_id))
    sc_id = ScenarioId(str(scenario_id))
    t_type = TaskType(task_type)

    if not prediction_records:
        raise DataIntegrityError("Cannot consolidate OOF predictions with zero prediction records")

    if cell_results and all(cr.status != ExecutionStatus.COMPLETED for cr in cell_results):
        raise DataIntegrityError(
            f"All folds failed for configuration ({m_id}, {sc_id}). Cannot consolidate OOF predictions."
        )

    # Data collection per observation_id
    obs_y_true: dict[ObservationId, float] = {}
    obs_y_preds: dict[ObservationId, list[float]] = {}
    obs_y_stds: dict[ObservationId, list[float]] = {}
    obs_y_probas: dict[ObservationId, list[tuple[float, ...]]] = {}
    fold_ids_set: set[str] = set()

    for rec in prediction_records:
        # Extract fold_id from cell_id if possible
        cid_str = str(rec.cell_id)
        if "__" in cid_str:
            fold_ids_set.add(cid_str.split("__")[-1])
        else:
            fold_ids_set.add(cid_str)

        has_std = rec.y_std is not None
        has_proba = rec.y_proba is not None

        for idx, obs_id in enumerate(rec.observation_ids):
            yt = float(rec.y_true[idx])
            yp = float(rec.y_pred[idx])

            if obs_id in obs_y_true:
                existing_yt = obs_y_true[obs_id]
                if abs(existing_yt - yt) > 1e-6:
                    raise DataIntegrityError(
                        f"Conflicting true labels for observation '{obs_id}': {existing_yt} vs {yt}"
                    )
            else:
                obs_y_true[obs_id] = yt
                obs_y_preds[obs_id] = []
                obs_y_stds[obs_id] = []
                obs_y_probas[obs_id] = []

            obs_y_preds[obs_id].append(yp)

            if has_std and rec.y_std is not None:
                obs_y_stds[obs_id].append(float(rec.y_std[idx]))

            if has_proba and rec.y_proba is not None:
                obs_y_probas[obs_id].append(rec.y_proba[idx])

    # Canonical sorting by observation_id
    sorted_obs_ids = sorted(obs_y_true.keys())

    y_true_list: list[float] = []
    y_pred_list: list[float] = []
    y_std_list: list[float] = []
    y_proba_list: list[tuple[float, ...]] = []
    has_any_std = any(len(obs_y_stds[o]) > 0 for o in sorted_obs_ids)
    is_multi_fold_eval = any(len(obs_y_preds[o]) > 1 for o in sorted_obs_ids)
    include_stds = has_any_std or is_multi_fold_eval

    has_any_proba = any(len(obs_y_probas[o]) > 0 for o in sorted_obs_ids)

    for o in sorted_obs_ids:
        y_true_list.append(obs_y_true[o])
        preds = obs_y_preds[o]
        k = len(preds)

        if k == 1:
            mu_i = preds[0]
            if include_stds:
                if obs_y_stds[o]:
                    sigma_i = obs_y_stds[o][0]
                else:
                    sigma_i = None
                y_std_list.append(sigma_i)
        else:
            mu_i = float(np.mean(preds))
            if include_stds:
                sigma_i = float(np.std(preds, ddof=1))
                y_std_list.append(sigma_i)

        y_pred_list.append(mu_i)

        if has_any_proba:
            probas = obs_y_probas[o]
            if probas:
                avg_p = tuple(float(p) for p in np.mean(probas, axis=0))
                y_proba_list.append(avg_p)
            else:
                y_proba_list.append(())

    # Residuals
    residuals_tuple = tuple(float(yt - yp) for yt, yp in zip(y_true_list, y_pred_list))

    final_stds: tuple[float | None, ...] | None = None
    if include_stds:
        # If all None or NaN, set to None
        if all(s is None or (isinstance(s, float) and math.isnan(s)) for s in y_std_list):
            final_stds = None
        else:
            final_stds = tuple(y_std_list)

    final_probas: tuple[tuple[float, ...], ...] | None = None
    if has_any_proba and all(len(p) > 0 for p in y_proba_list):
        final_probas = tuple(y_proba_list)

    # Fold IDs
    all_folds = sorted(fold_ids_set)
    if cell_results:
        cr_folds = {cr.fold_id for cr in cell_results}
        all_folds = sorted(fold_ids_set.union(cr_folds))

    # Determine which metrics to evaluate
    if metrics is not None:
        target_metrics = tuple(metrics)
    elif cell_results and any(cr.metrics for cr in cell_results):
        metric_keys_set = set()
        for cr in cell_results:
            if cr.status == ExecutionStatus.COMPLETED and cr.metrics:
                metric_keys_set.update(cr.metrics.keys())
        target_metrics = tuple(sorted(metric_keys_set))
    else:
        if t_type == TaskType.REGRESSION:
            target_metrics = ("rmse", "mae", "r2")
        elif t_type in (TaskType.BINARY_CLASSIFICATION, TaskType.MULTICLASS_CLASSIFICATION):
            target_metrics = ("accuracy", "f1")
        else:
            target_metrics = ()

    # 1. Evaluate POOLED_OOF metrics
    pooled_metrics_dict: dict[str, MetricValue] = {}
    y_true_arr = np.asarray(y_true_list)
    y_pred_arr = np.asarray(y_pred_list)

    for m_name in target_metrics:
        if m_name in ("log_loss", "roc_auc") and final_probas is not None:
            pred_input = np.asarray(final_probas)
        else:
            pred_input = y_pred_arr

        try:
            mv = compute_metric(
                m_name,
                y_true_arr,
                pred_input,
                scope=MetricEvaluationScope.POOLED_OOF,
            )
            pooled_metrics_dict[m_name] = mv
        except Exception as exc:
            try:
                spec = get_metric_spec(m_name)
                m_dir = spec.direction
            except Exception:
                m_dir = MetricDirection.MINIMIZE

            mv_nan = MetricValue(
                metric_id=m_name,
                value=float("nan"),
                status=MetricStatus.UNDEFINED_NAN,
                direction=m_dir,
                scope=MetricEvaluationScope.POOLED_OOF,
                n_samples=len(y_true_arr),
                warnings=(
                    make_warning(
                        "W_UNDEFINED_NAN",
                        f"Evaluation failed for pooled metric '{m_name}': {exc}",
                    ),
                ),
            )
            pooled_metrics_dict[m_name] = mv_nan

    # 2. Compute FOLD_AGGREGATION metrics
    aggregated_metrics_dict: dict[str, AggregatedMetricValue] = {}
    if cell_results:
        fold_metrics_by_id: dict[str, list[MetricValue]] = {}
        for cr in cell_results:
            if cr.status == ExecutionStatus.COMPLETED and cr.metrics:
                for mid, mval in cr.metrics.items():
                    fold_metrics_by_id.setdefault(mid, []).append(mval)

        for mid, m_list in fold_metrics_by_id.items():
            try:
                amv = aggregate_fold_metrics(
                    m_list,
                    scope=AggregationScope.FOLD_AGGREGATION,
                )
                aggregated_metrics_dict[mid] = amv
            except Exception as exc:
                try:
                    spec = get_metric_spec(mid)
                    m_dir = spec.direction
                except Exception:
                    m_dir = MetricDirection.MINIMIZE

                amv_nan = AggregatedMetricValue(
                    metric_id=mid,
                    mean=float("nan"),
                    std=float("nan"),
                    median=float("nan"),
                    iqr=float("nan"),
                    status=MetricStatus.UNDEFINED_NAN,
                    direction=m_dir,
                    scope=AggregationScope.FOLD_AGGREGATION,
                    valid_folds=0,
                    total_folds=len(m_list),
                    coverage=0.0,
                    fold_values=tuple(m_list),
                    warnings=(
                        make_warning(
                            "W_UNDEFINED_NAN",
                            f"Aggregation failed for metric '{mid}': {exc}",
                        ),
                    ),
                )
                aggregated_metrics_dict[mid] = amv_nan

    # 3. Partial coverage and warnings handling
    coverage = 1.0
    overall_status = MetricStatus.VALID
    warnings_list: list[str] = []

    if target_observation_ids is not None:
        expected_set = set(str(o) for o in target_observation_ids)
        obtained_set = set(str(o) for o in sorted_obs_ids)
        missing_obs = sorted(expected_set - obtained_set)
        if missing_obs:
            coverage = len(obtained_set & expected_set) / max(len(expected_set), 1)
            overall_status = MetricStatus.PARTIAL_COVERAGE
            warnings_list.append(
                f"Missing {len(missing_obs)} observation(s) from target: {missing_obs}"
            )
    elif cell_results:
        failed_cells = [cr for cr in cell_results if cr.status != ExecutionStatus.COMPLETED]
        if failed_cells:
            total_c = len(cell_results)
            comp_c = total_c - len(failed_cells)
            coverage = comp_c / max(total_c, 1)
            overall_status = MetricStatus.PARTIAL_COVERAGE
            failed_fold_ids = [cr.fold_id for cr in failed_cells]
            warnings_list.append(
                f"Partial coverage: {len(failed_cells)} fold(s) failed: {failed_fold_ids}"
            )

    if overall_status == MetricStatus.PARTIAL_COVERAGE:
        updated_pooled: dict[str, MetricValue] = {}
        for m_name, mv in pooled_metrics_dict.items():
            if mv.status == MetricStatus.VALID:
                updated_pooled[m_name] = MetricValue(
                    metric_id=mv.metric_id,
                    value=mv.value,
                    status=MetricStatus.PARTIAL_COVERAGE,
                    direction=mv.direction,
                    scope=mv.scope,
                    n_samples=mv.n_samples,
                    warnings=mv.warnings
                    + (
                        make_warning(
                            "W_PARTIAL_COVERAGE",
                            f"Evaluated on partial coverage ({coverage:.1%})",
                        ),
                    ),
                )
            else:
                updated_pooled[m_name] = mv
        pooled_metrics_dict = updated_pooled

    return ConsolidatedOofPredictions(
        model_id=m_id,
        scenario_id=sc_id,
        task_type=t_type,
        observation_ids=tuple(sorted_obs_ids),
        y_true=tuple(y_true_list),
        y_pred=tuple(y_pred_list),
        y_std=final_stds,
        y_proba=final_probas,
        residuals=residuals_tuple,
        pooled_metrics=pooled_metrics_dict,
        aggregated_metrics=aggregated_metrics_dict,
        fold_ids=tuple(all_folds),
        coverage=coverage,
        status=overall_status,
        warnings=tuple(warnings_list),
    )


def consolidate_matrix_oof(
    run_dir: Path | str,
    *,
    task_type: TaskType | str | None = None,
    target_observation_ids: Sequence[ObservationId | str] | None = None,
    overwrite: bool = True,
) -> dict[str, ConsolidatedOofPredictions]:
    """Consolidate out-of-fold predictions for all completed configurations in an experiment matrix.

    Args:
        run_dir: Experiment execution directory containing execution_state.json.
        task_type: Optional task type (defaults to TaskType.REGRESSION).
        target_observation_ids: Optional full expected sequence of observation IDs.
        overwrite: Whether to overwrite existing OOF files.

    Returns:
        Dict mapping configuration key "model__scenario" to ConsolidatedOofPredictions.
    """
    from experimental_ml.orchestration.state import load_execution_state
    from experimental_ml.orchestration.storage import load_cell_artifacts

    run_path = Path(run_dir).resolve()
    exec_state = load_execution_state(run_path)

    config_preds: dict[tuple[str, str], list[PredictionRecord]] = {}
    config_cells: dict[tuple[str, str], list[CellResultRecord]] = {}

    for cid in exec_state.cell_statuses.keys():
        cid_str = str(cid)
        parts = cid_str.replace("cell_", "").split("__")
        if len(parts) >= 3:
            m_id, sc_id = parts[0], parts[1]
        else:
            continue

        config_key = (m_id, sc_id)
        try:
            cell_res, pred_rec = load_cell_artifacts(cid, run_path)
            config_cells.setdefault(config_key, []).append(cell_res)
            if pred_rec is not None:
                config_preds.setdefault(config_key, []).append(pred_rec)
        except Exception:
            continue

    resolved_task_type = TaskType(task_type) if task_type is not None else TaskType.REGRESSION

    results: dict[str, ConsolidatedOofPredictions] = {}
    for (m_id, sc_id), preds in config_preds.items():
        if not preds:
            continue
        cells = config_cells.get((m_id, sc_id), [])
        oof_record = consolidate_oof_predictions(
            model_id=m_id,
            scenario_id=sc_id,
            task_type=resolved_task_type,
            prediction_records=preds,
            cell_results=cells,
            target_observation_ids=target_observation_ids,
        )
        save_oof_predictions(oof_record, run_path, overwrite=overwrite)
        results[f"{m_id}__{sc_id}"] = oof_record

    return results

