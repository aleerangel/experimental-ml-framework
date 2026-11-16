"""Regression tests for all P0 and P1 code findings uncovered in TA-POS.1."""

from __future__ import annotations

import math

import numpy as np

from experimental_ml.core.enums import MetricStatus, TaskType
from experimental_ml.core.findings import make_warning
from experimental_ml.core.types import ObservationId, ScenarioId
from experimental_ml.data.loader import load_dataset
from experimental_ml.data.schema import DatasetSchemaSpec
from experimental_ml.data.types import ColumnSemanticType
from experimental_ml.features.scenarios import FeatureScenario, ScenarioMode
from experimental_ml.features.selection import select_features_in_fold
from experimental_ml.metrics.aggregation import AggregatedMetricValue
from experimental_ml.metrics.catalog import get_metric_spec
from experimental_ml.metrics.types import MetricDirection, MetricEvaluationScope, MetricValue
from experimental_ml.models.execution import instantiate_fresh_model
from experimental_ml.models.spec import ModelCapabilities, ModelFamily, ModelSpec
from experimental_ml.orchestration.codecs import (
    aggregated_metric_value_from_dict,
    aggregated_metric_value_to_dict,
    metric_value_from_dict,
    metric_value_to_dict,
)
from experimental_ml.statistics.synthesis import synthesize_conclusions
from experimental_ml.statistics.types import (
    AggregatedMetricStats,
    ComparisonScope,
    ComparisonSpec,
    ConfigurationSummary,
    CoverageStatus,
    DescriptiveConsolidation,
    MethodSuitabilityReport,
    StatisticalComparisonBundle,
)
from experimental_ml.tuning.candidates import generate_candidates
from experimental_ml.tuning.types import HyperparameterSearchSpec, SearchStrategy
from experimental_ml.validation.engine import build_partition_plan
from experimental_ml.validation.types import (
    EvaluationRegime,
    PartitionConfig,
    PartitionStrategy,
)
from experimental_ml.validation.validators import validate_partition_plan


def test_p0_01_group_and_temporal_holdout_isolation() -> None:
    """ACH-POS1-P0-01: CV_AND_HOLDOUT must keep groups disjoint and temporal order monotonic across dev/holdout."""
    n = 20
    data_dict = {
        "obs_id": [f"obs_{i}" for i in range(n)],
        "f1": np.arange(n, dtype=np.float64),
        "g": [f"g_{i // 4}" for i in range(n)],
        "t": np.arange(n, dtype=np.float64),
        "target": [i % 2 for i in range(n)],
    }
    schema = DatasetSchemaSpec(
        target_col="target",
        task_type=TaskType.BINARY_CLASSIFICATION,
        column_semantic_types={
            "f1": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "g": ColumnSemanticType.CATEGORICAL,
            "t": ColumnSemanticType.NUMERIC_CONTINUOUS,
        },
        observation_id_col="obs_id",
        group_col="g",
        time_col="t",
    )
    bundle = load_dataset(data_dict, schema)

    cfg_group = PartitionConfig(
        strategy=PartitionStrategy.GROUP_KFOLD,
        regime=EvaluationRegime.CV_AND_HOLDOUT,
        n_splits=3,
        holdout_fraction=0.25,
        group_col="g",
        master_seed=42,
    )
    plan_group = build_partition_plan(bundle, cfg_group)
    g_arr = bundle.columns["g"]
    oid_to_g = {oid: g_arr[i] for i, oid in enumerate(bundle.observation_ids)}
    dev_groups = {oid_to_g[oid] for oid in plan_group.development_ids}
    hold_groups = {oid_to_g[oid] for oid in plan_group.holdout_ids}
    assert dev_groups.isdisjoint(hold_groups)
    validate_partition_plan(plan_group, bundle)

    cfg_temp = PartitionConfig(
        strategy=PartitionStrategy.TEMPORAL,
        regime=EvaluationRegime.CV_AND_HOLDOUT,
        n_splits=3,
        holdout_fraction=0.2,
        time_col="t",
        master_seed=42,
    )
    plan_temp = build_partition_plan(bundle, cfg_temp)
    t_arr = bundle.columns["t"]
    oid_to_t = {oid: t_arr[i] for i, oid in enumerate(bundle.observation_ids)}
    dev_times = [oid_to_t[oid] for oid in plan_temp.development_ids]
    hold_times = [oid_to_t[oid] for oid in plan_temp.holdout_ids]
    assert max(dev_times) <= min(hold_times)
    validate_partition_plan(plan_temp, bundle)


def test_p0_02_instantiate_fresh_model_applies_spec_parameters() -> None:
    """ACH-POS1-P0-02: instantiate_fresh_model must apply model_spec.parameters to the fresh instance."""

    class _DummyWithParams:
        def __init__(self, alpha: float = 1.0) -> None:
            self.alpha = alpha

        def set_params(self, **kwargs: float) -> "_DummyWithParams":
            for k, v in kwargs.items():
                setattr(self, k, v)
            return self

        def fit(self, X: np.ndarray, y: np.ndarray) -> "_DummyWithParams":
            return self

        def predict(self, X: np.ndarray) -> np.ndarray:
            return np.zeros(len(X))

    spec = ModelSpec(
        model_id="m_param",
        display_name="Dummy",
        family=ModelFamily.BASELINE,
        estimator_factory=lambda seed=None: _DummyWithParams(alpha=1.0),
        capabilities=ModelCapabilities(),
        description="Dummy",
        scientific_justification="Regression test",
        parameters={"alpha": 42.5},
    )
    inst = instantiate_fresh_model(spec, seed=7)
    assert inst.alpha == 42.5


def test_p0_03_top_k_relevance_excludes_undefined_nan() -> None:
    """ACH-POS1-P0-03: TOP_K_RELEVANCE must not coerce UNDEFINED_NAN (constant feature) to 0.0."""
    X = {
        "const_feat": np.ones(10, dtype=np.float64),
        "good_feat": np.arange(10, dtype=np.float64),
    }
    y = np.arange(10, dtype=np.float64) * 2.0
    sc = FeatureScenario(
        scenario_id=ScenarioId("sc_dyn"),
        name="Dynamic Top K",
        description="Dynamic Top K test",
        scientific_justification="Exclude NaN features",
        mode=ScenarioMode.DYNAMIC,
        strategy_name="TOP_K_RELEVANCE",
        strategy_params={"k": 2},
    )
    res = select_features_in_fold(X, y, sc)
    assert res.selected_features == ("good_feat",)
    assert math.isnan(res.scores["const_feat"])


def test_p0_04_catalog_requires_probabilities_and_kernel_matrix() -> None:
    """ACH-POS1-P0-04: roc_auc and log_loss require probabilities; kta requires kernel matrix."""
    assert get_metric_spec("roc_auc").requires_probabilities is True
    assert get_metric_spec("log_loss").requires_probabilities is True
    assert get_metric_spec("kta").requires_kernel_matrix is True


def test_p0_05_observed_leader_respects_coverage_precedence_and_mbe_abs() -> None:
    """ACH-POS1-P0-05: VALID coverage outranks PARTIAL_COVERAGE; mbe compares by |mean|."""
    sum_partial = ConfigurationSummary(
        model_id="m_partial",
        scenario_id="s1",
        total_folds=5,
        completed_folds=1,
        failed_folds=4,
        cancelled_folds=0,
        coverage=0.2,
        coverage_status=CoverageStatus.PARTIAL_COVERAGE,
        completed_fold_ids=("fold_0",),
        failed_fold_ids=("fold_1", "fold_2", "fold_3", "fold_4"),
        cancelled_fold_ids=(),
        fold_metrics={},
        aggregated_metrics={
            "mbe": AggregatedMetricStats(1, 5, MetricStatus.PARTIAL_COVERAGE, 0.0, None, 0.0, None, None, None, 0.0, 0.0)
        },
        pooled_oof_metrics={},
    )
    sum_valid_bad_neg = ConfigurationSummary(
        model_id="m_neg_mbe",
        scenario_id="s1",
        total_folds=5,
        completed_folds=5,
        failed_folds=0,
        cancelled_folds=0,
        coverage=1.0,
        coverage_status=CoverageStatus.VALID,
        completed_fold_ids=tuple(f"fold_{i}" for i in range(5)),
        failed_fold_ids=(),
        cancelled_fold_ids=(),
        fold_metrics={},
        aggregated_metrics={
            "mbe": AggregatedMetricStats(5, 5, MetricStatus.VALID, -10.0, 0.1, -10.0, 0.1, -10.0, -10.0, -10.0, -10.0)
        },
        pooled_oof_metrics={},
    )
    sum_valid_best = ConfigurationSummary(
        model_id="m_best",
        scenario_id="s1",
        total_folds=5,
        completed_folds=5,
        failed_folds=0,
        cancelled_folds=0,
        coverage=1.0,
        coverage_status=CoverageStatus.VALID,
        completed_fold_ids=tuple(f"fold_{i}" for i in range(5)),
        failed_fold_ids=(),
        cancelled_fold_ids=(),
        fold_metrics={},
        aggregated_metrics={
            "mbe": AggregatedMetricStats(5, 5, MetricStatus.VALID, 0.05, 0.01, 0.05, 0.01, 0.04, 0.06, 0.03, 0.07)
        },
        pooled_oof_metrics={},
    )
    consol = DescriptiveConsolidation(
        "exp_p05",
        "pp_p05",
        3,
        {("m_partial", "s1"): sum_partial, ("m_neg_mbe", "s1"): sum_valid_bad_neg, ("m_best", "s1"): sum_valid_best},
        "2026-11-16T00:00:00Z",
    )
    suit = MethodSuitabilityReport(EvaluationRegime.CV_ONLY, 5, (0.2,) * 5, 0.75, True, {}, ())
    cspec = ComparisonSpec(("mbe",), {"mbe": MetricDirection.MINIMIZE}, ComparisonScope.ALL_PAIRWISE)
    comp = StatisticalComparisonBundle("exp_p05", "pp_p05", cspec, (), ())
    conc = synthesize_conclusions(consol, suit, comp, "mbe", MetricDirection.MINIMIZE)
    assert conc.observed_leader == ("m_best", "s1")


def test_p0_06_random_search_deterministic_with_override_seed() -> None:
    """ACH-POS1-P0-06: generate_candidates(..., seed=...) overrides None spec.seed deterministically."""
    spec = HyperparameterSearchSpec(
        search_strategy=SearchStrategy.RANDOM_SEARCH,
        param_grid={"x": tuple(range(100)), "y": tuple(range(100))},
        n_iter=5,
        optimization_metric="rmse",
        direction=MetricDirection.MINIMIZE,
        seed=None,
    )
    c1 = generate_candidates(spec, seed=12345)
    c2 = generate_candidates(spec, seed=12345)
    assert c1 == c2


def test_p1_02_finding_roundtrip_in_orchestration_codecs() -> None:
    """ACH-POS1-P1-02: MetricValue and AggregatedMetricValue with Finding warnings round-trip cleanly."""
    warn = make_warning("W_TEST", "degenerate metric", context={"metric": "rmse"})
    mv = MetricValue("rmse", float("nan"), MetricStatus.UNDEFINED_NAN, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 5, warnings=(warn,))
    mv2 = metric_value_from_dict(metric_value_to_dict(mv))
    assert mv2.warnings[0].code == "W_TEST"

    amv = AggregatedMetricValue("rmse", None, None, None, None, None, None, 0, 5, MetricStatus.UNDEFINED_NAN, warnings=(warn,))
    amv2 = aggregated_metric_value_from_dict(aggregated_metric_value_to_dict(amv))
    assert amv2.warnings[0].code == "W_TEST"
