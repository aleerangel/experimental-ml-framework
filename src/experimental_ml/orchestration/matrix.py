"""Cartesian experimental cell matrix formulation and deterministic seed derivation.

Complies with ORCH-09, CA-E4B-01, and XCUT-02.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Sequence

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.features.scenarios import FeatureScenario
from experimental_ml.models.spec import ModelSpec
from experimental_ml.orchestration.types import CellId
from experimental_ml.validation.types import FoldPartition, PartitionPlan


@dataclass(frozen=True, slots=True)
class CellDescriptor:
    """Immutable descriptor of an individual experimental cell within the Cartesian grid."""

    cell_id: CellId
    model_spec: ModelSpec
    scenario: FeatureScenario
    fold: FoldPartition
    cell_seed: int

    def __post_init__(self) -> None:
        if not isinstance(self.cell_id, CellId):
            object.__setattr__(self, "cell_id", CellId(str(self.cell_id)))
        if not isinstance(self.model_spec, ModelSpec):
            raise ConfigurationError(
                f"model_spec must be an instance of ModelSpec, got {type(self.model_spec).__name__}"
            )
        if not isinstance(self.scenario, FeatureScenario):
            raise ConfigurationError(
                f"scenario must be an instance of FeatureScenario, got {type(self.scenario).__name__}"
            )
        if not isinstance(self.fold, FoldPartition):
            raise ConfigurationError(
                f"fold must be an instance of FoldPartition, got {type(self.fold).__name__}"
            )
        if not isinstance(self.cell_seed, int) or isinstance(self.cell_seed, bool):
            raise ConfigurationError(
                f"cell_seed must be an integer, got {self.cell_seed!r}"
            )


def derive_cell_seed(
    master_seed: int,
    model_id: str,
    scenario_id: str,
    fold_id: str,
) -> int:
    """Deterministically derive an isolated 31-bit seed for a specific cell via SHA-256.

    Args:
        master_seed: Experiment-wide master random seed.
        model_id: Unique model identifier.
        scenario_id: Unique feature scenario identifier.
        fold_id: Target fold partition identifier.

    Returns:
        Deterministic non-negative 31-bit integer in range [0, 2^31 - 2].
    """
    raw = f"{master_seed}:{model_id}:{scenario_id}:{fold_id}".encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    seed = int.from_bytes(digest[:4], byteorder="big", signed=False) % 2147483647
    return seed


def build_cell_matrix(
    model_specs: Sequence[ModelSpec],
    scenarios: Sequence[FeatureScenario],
    partition_plan: PartitionPlan,
    master_seed: int = 42,
) -> tuple[CellDescriptor, ...]:
    """Formulate the Cartesian product of models x scenarios x folds into ordered descriptors.

    The sequence is deterministically ordered by (model_id, scenario_id, fold_id).

    Args:
        model_specs: Sequence of model specifications to evaluate.
        scenarios: Sequence of feature scenarios to evaluate.
        partition_plan: Partition plan defining validation folds.
        master_seed: Master seed for cell-level random seed derivation.

    Returns:
        Tuple of CellDescriptor instances ordered canonically.

    Raises:
        ConfigurationError: If any of the collections is empty or invalid.
    """
    if not model_specs:
        raise ConfigurationError("model_specs cannot be empty when building cell matrix")
    if not scenarios:
        raise ConfigurationError("scenarios cannot be empty when building cell matrix")
    if not partition_plan.folds:
        raise ConfigurationError("partition_plan contains no folds")

    sorted_models = sorted(model_specs, key=lambda m: str(m.model_id))
    sorted_scenarios = sorted(scenarios, key=lambda s: str(s.scenario_id))
    sorted_folds = sorted(partition_plan.folds, key=lambda f: f.fold_index)

    descriptors: list[CellDescriptor] = []
    for model in sorted_models:
        for scenario in sorted_scenarios:
            for fold in sorted_folds:
                fold_id = f"fold_{fold.fold_index}"
                cell_id_str = f"cell_{model.model_id}__{scenario.scenario_id}__{fold_id}"
                cell_id = CellId(cell_id_str)
                cell_seed = derive_cell_seed(
                    master_seed,
                    str(model.model_id),
                    str(scenario.scenario_id),
                    fold_id,
                )
                descriptors.append(
                    CellDescriptor(
                        cell_id=cell_id,
                        model_spec=model,
                        scenario=scenario,
                        fold=fold,
                        cell_seed=cell_seed,
                    )
                )

    return tuple(descriptors)
