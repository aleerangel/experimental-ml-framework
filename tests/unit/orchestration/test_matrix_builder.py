"""Unit tests for matrix formulation and deterministic seed derivation (M5.2).

Covers C1 to C5 (ORCH-09).
"""

from __future__ import annotations

import pytest

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.types import ModelId, ObservationId, PartitionPlanId, ScenarioId
from experimental_ml.features.scenarios import FeatureScenario, ScenarioMode
from experimental_ml.models import (
    ModelCapabilities,
    ModelFamily,
    ModelSpec,
    resolve_estimator_factory,
)
from experimental_ml.orchestration.matrix import (
    CellDescriptor,
    build_cell_matrix,
    derive_cell_seed,
)
from experimental_ml.orchestration.types import CellId
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


def _create_test_entities():
    # 2 Models
    m1 = ModelSpec(
        model_id=ModelId("model_b"),
        display_name="Model B",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=resolve_estimator_factory("DUMMY_BASELINE_MEAN"),
        description="Model B",
        scientific_justification="Test",
    )
    m2 = ModelSpec(
        model_id=ModelId("model_a"),
        display_name="Model A",
        family=ModelFamily.BASELINE,
        capabilities=ModelCapabilities(requires_fit=True, supports_predict=True),
        estimator_factory=resolve_estimator_factory("DUMMY_BASELINE_MEDIAN"),
        description="Model A",
        scientific_justification="Test",
    )

    # 2 Scenarios
    s1 = FeatureScenario(
        scenario_id=ScenarioId("sc_y"),
        name="Scenario Y",
        description="Scenario Y",
        scientific_justification="Test",
        mode=ScenarioMode.FIXED,
        selected_features=("f1",),
    )
    s2 = FeatureScenario(
        scenario_id=ScenarioId("sc_x"),
        name="Scenario X",
        description="Scenario X",
        scientific_justification="Test",
        mode=ScenarioMode.FIXED,
        selected_features=("f1", "f2"),
    )

    # 3 Folds
    f0 = FoldPartition(fold_index=0, train_ids=(ObservationId("o1"),), val_ids=(ObservationId("o2"),))
    f1 = FoldPartition(fold_index=1, train_ids=(ObservationId("o2"),), val_ids=(ObservationId("o1"),))
    f2 = FoldPartition(fold_index=2, train_ids=(ObservationId("o1"),), val_ids=(ObservationId("o2"),))

    plan = PartitionPlan(
        plan_id=PartitionPlanId("plan_test"),
        source_dataset_hash="hash_01",
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=(ObservationId("o1"), ObservationId("o2")),
        holdout_ids=(),
        folds=(f2, f0, f1),  # Unsorted order to test sorting
        config=PartitionConfig(
            strategy=PartitionStrategy.KFOLD,
            regime=EvaluationRegime.CV_ONLY,
            n_splits=3,
            master_seed=42,
        ),
    )

    return (m1, m2), (s1, s2), plan


def test_m52_01_01_build_cell_matrix_cartesian():
    """C1: build_cell_matrix produces Cartesian product M x C x F (ORCH-09, AC 1)."""
    models, scenarios, plan = _create_test_entities()
    matrix = build_cell_matrix(models, scenarios, plan, master_seed=42)

    # |M| = 2, |C| = 2, |F| = 3 -> 2 * 2 * 3 = 12 cells
    assert len(matrix) == 12
    assert all(isinstance(c, CellDescriptor) for c in matrix)


def test_m52_01_02_build_cell_matrix_canonical_sorting():
    """C2: build_cell_matrix canonically sorts by model_id, scenario_id, fold_id (ORCH-09, AC 2)."""
    models, scenarios, plan = _create_test_entities()
    # Input has model_b before model_a, sc_y before sc_x, and fold 2, 0, 1
    matrix = build_cell_matrix(models, scenarios, plan, master_seed=42)

    expected_order = [
        ("model_a", "sc_x", "fold_0"),
        ("model_a", "sc_x", "fold_1"),
        ("model_a", "sc_x", "fold_2"),
        ("model_a", "sc_y", "fold_0"),
        ("model_a", "sc_y", "fold_1"),
        ("model_a", "sc_y", "fold_2"),
        ("model_b", "sc_x", "fold_0"),
        ("model_b", "sc_x", "fold_1"),
        ("model_b", "sc_x", "fold_2"),
        ("model_b", "sc_y", "fold_0"),
        ("model_b", "sc_y", "fold_1"),
        ("model_b", "sc_y", "fold_2"),
    ]

    actual_order = [
        (str(c.model_spec.model_id), str(c.scenario.scenario_id), f"fold_{c.fold.fold_index}")
        for c in matrix
    ]
    assert actual_order == expected_order


def test_m52_01_03_cell_descriptor_canonical_id():
    """C3: CellDescriptor contains canonical cell_id structure (ORCH-09, AC 3)."""
    models, scenarios, plan = _create_test_entities()
    matrix = build_cell_matrix(models, scenarios, plan, master_seed=100)

    first_cell = matrix[0]
    assert first_cell.cell_id == CellId("cell_model_a__sc_x__fold_0")
    assert isinstance(first_cell.cell_seed, int)
    assert 0 <= first_cell.cell_seed < 2147483647


def test_m52_01_04_derive_cell_seed_determinism():
    """C4: derive_cell_seed produces deterministic 31-bit integer (ORCH-09, AC 4)."""
    s1 = derive_cell_seed(42, "ridge", "sc_baseline", "fold_0")
    s2 = derive_cell_seed(42, "ridge", "sc_baseline", "fold_0")
    assert s1 == s2
    assert isinstance(s1, int)
    assert 0 <= s1 < 2147483647


def test_m52_01_05_derive_cell_seed_dispersion():
    """C5: derive_cell_seed produces distinct seeds for differing inputs (ORCH-09, AC 4)."""
    s1 = derive_cell_seed(42, "ridge", "sc_baseline", "fold_0")
    s2 = derive_cell_seed(42, "ridge", "sc_baseline", "fold_1")
    s3 = derive_cell_seed(42, "lasso", "sc_baseline", "fold_0")
    s4 = derive_cell_seed(43, "ridge", "sc_baseline", "fold_0")

    seeds = {s1, s2, s3, s4}
    assert len(seeds) == 4
