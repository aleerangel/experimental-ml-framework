"""Out-of-fold (OOF) prediction consolidation, committee statistics, and storage.

Complies with ORCH-15, ORCH-16, ORCH-17, ORCH-18, ORCH-19, ORCH-20, RF4.7, STORE-01, and ADR-008.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from experimental_ml.core.enums import AggregationScope, MetricStatus, TaskType
from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.core.storage import read_json, write_json_atomic
from experimental_ml.core.types import ModelId, ObservationId, ScenarioId
from experimental_ml.metrics.types import AggregatedMetricValue, MetricValue


@dataclass(frozen=True, slots=True)
class ConsolidatedOofPredictions:
    """Immutable record consolidating out-of-fold predictions for a (model, scenario) configuration."""

    model_id: ModelId
    scenario_id: ScenarioId
    task_type: TaskType
    observation_ids: tuple[ObservationId, ...]
    y_true: tuple[float, ...]
    y_pred: tuple[float, ...]
    y_std: tuple[float, ...] | None = None
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
            y_s = tuple(float(s) for s in self.y_std)
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
