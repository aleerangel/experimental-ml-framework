"""Unit tests for 7-family TableModel builders and CSV/Markdown/LaTeX renderers (REP-03, CA-E6-01, CA-E6-02)."""

from pathlib import Path
import math

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.storage import write_json_atomic
from experimental_ml.core.types import ObservationId
from experimental_ml.metrics.types import MetricDirection, MetricEvaluationScope, MetricValue
from experimental_ml.reporting.loader import load_experiment_artifacts_readonly
from experimental_ml.reporting.tables import (
    build_table_model,
    render_table_csv,
    render_table_latex,
    render_table_markdown,
)
from experimental_ml.reporting.types import ReportFamily
from experimental_ml.statistics.comparisons import run_statistical_comparisons
from experimental_ml.statistics.multiobjective import compute_pareto_frontier
from experimental_ml.statistics.storage import save_statistics_artifacts
from experimental_ml.statistics.suitability import evaluate_method_suitability
from experimental_ml.statistics.synthesis import synthesize_conclusions
from experimental_ml.statistics.types import (
    AggregatedMetricStats,
    AggregatedTimingStats,
    ComparisonScope,
    ComparisonSpec,
    ConfigurationSummary,
    CoverageStatus,
    DescriptiveConsolidation,
    MultiObjectiveSpec,
    MultiplicityMethod,
    ObjectiveSource,
    ObjectiveSpec,
)
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


def _create_rich_experiment(exp_dir: Path) -> tuple[Path, str]:
    n_folds = 5
    folds = tuple(
        FoldPartition(
            fold_index=i,
            train_ids=tuple(ObservationId(f"tr_{i}_{k}") for k in range(40)),
            val_ids=tuple(ObservationId(f"va_{i}_{k}") for k in range(10)),
        )
        for i in range(n_folds)
    )
    plan = PartitionPlan(
        plan_id="pp_tbl",
        source_dataset_hash="f" * 64,
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=tuple(ObservationId(f"d_{k}") for k in range(50)),
        holdout_ids=(),
        folds=folds,
        config=PartitionConfig(PartitionStrategy.KFOLD, EvaluationRegime.CV_ONLY, n_splits=n_folds),
    )

    # Legitimate 64-char hex-like user model_id to verify NO blanket regex stripping!
    legit_hex_id = "0123456789abcdef" * 4
    timing = AggregatedTimingStats(0.01, 0.05, 0.01, 0.05, 0.0, 0.0, 0.0, 0.0, 0.25, 1.25, 0.01, 0.05, 0.01, 0.05, 0.29, 1.45)

    # m1: constant rmse=1.0 -> t_statistic = -inf; r2 = UNDEFINED_NAN; std=None on single valid fold metric
    sum1 = ConfigurationSummary(
        model_id=legit_hex_id,
        scenario_id="s_base",
        total_folds=5,
        completed_folds=5,
        failed_folds=0,
        cancelled_folds=0,
        coverage=1.0,
        coverage_status=CoverageStatus.VALID,
        completed_fold_ids=tuple(f"fold_{i}" for i in range(5)),
        failed_fold_ids=(),
        cancelled_fold_ids=(),
        fold_metrics={
            f"fold_{i}": {
                "rmse": MetricValue("rmse", 1.0, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 10),
                "r2": MetricValue("r2", float("nan"), MetricStatus.UNDEFINED_NAN, MetricDirection.MAXIMIZE, MetricEvaluationScope.PER_FOLD, 10),
            }
            for i in range(5)
        },
        aggregated_metrics={
            "rmse": AggregatedMetricStats(5, 5, MetricStatus.VALID, 1.0123456789, None, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0),
            "r2": AggregatedMetricStats(0, 5, MetricStatus.UNDEFINED_NAN, None, None, None, None, None, None, None, None),
        },
        pooled_oof_metrics={},
        aggregated_timing=timing,
        feature_stability=None,
    )
    sum2 = ConfigurationSummary(
        model_id="m_alt",
        scenario_id="s_base",
        total_folds=5,
        completed_folds=5,
        failed_folds=0,
        cancelled_folds=0,
        coverage=1.0,
        coverage_status=CoverageStatus.VALID,
        completed_fold_ids=tuple(f"fold_{i}" for i in range(5)),
        failed_fold_ids=(),
        cancelled_fold_ids=(),
        fold_metrics={
            f"fold_{i}": {
                "rmse": MetricValue("rmse", 1.5, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 10),
                "r2": MetricValue("r2", 0.8, MetricStatus.VALID, MetricDirection.MAXIMIZE, MetricEvaluationScope.PER_FOLD, 10),
            }
            for i in range(5)
        },
        aggregated_metrics={
            "rmse": AggregatedMetricStats(5, 5, MetricStatus.VALID, 1.5, 0.0, 1.5, 0.0, 1.5, 1.5, 1.5, 1.5),
            "r2": AggregatedMetricStats(5, 5, MetricStatus.VALID, 0.8, 0.0, 0.8, 0.0, 0.8, 0.8, 0.8, 0.8),
        },
        pooled_oof_metrics={},
        aggregated_timing=timing,
        feature_stability=None,
    )

    consol = DescriptiveConsolidation("exp_tbl", plan.plan_id, 2, {(legit_hex_id, "s_base"): sum1, ("m_alt", "s_base"): sum2}, "2026-11-16T00:00:00Z")
    suit = evaluate_method_suitability(plan, consol)
    spec = ComparisonSpec(("rmse",), {"rmse": MetricDirection.MINIMIZE}, ComparisonScope.ALL_PAIRWISE, multiplicity_method=MultiplicityMethod.HOLM_BONFERRONI)
    comp = run_statistical_comparisons(consol, plan, spec, suit)
    pareto = compute_pareto_frontier(
        consol,
        MultiObjectiveSpec((
            ObjectiveSpec("rmse", MetricDirection.MINIMIZE),
            ObjectiveSpec("fit_mean_s", MetricDirection.MINIMIZE, ObjectiveSource.TIMING_MEAN, "fit_mean_s"),
        )),
    )
    conc = synthesize_conclusions(consol, suit, comp, "rmse", MetricDirection.MINIMIZE, pareto)
    save_statistics_artifacts(exp_dir / "statistics", consol, suit, comp, conc, pareto=pareto)

    (exp_dir / "data").mkdir(parents=True, exist_ok=True)
    write_json_atomic(
        exp_dir / "data" / "dataset_profile.json",
        {"n_rows": 50, "n_cols": 4, "dataset_hash": "e" * 64, "source_hash": "d" * 64},
        overwrite=True,
    )
    (exp_dir / "configuration").mkdir(parents=True, exist_ok=True)
    write_json_atomic(
        exp_dir / "configuration" / "scenarios.json",
        {"scenarios": [{"scenario_id": "s_base", "mode": "FIXED", "features": ["x1", "x2"]}]},
        overwrite=True,
    )
    write_json_atomic(
        exp_dir / "configuration" / "models.json",
        {
            "models": [
                {"model_id": legit_hex_id, "family": "LINEAR", "task_type": "REGRESSION", "config_hash": "c" * 64},
                {"model_id": "m_alt", "family": "TREE", "task_type": "REGRESSION", "config_hash": "b" * 64},
            ]
        },
        overwrite=True,
    )
    return exp_dir, legit_hex_id


def test_m71_03_all_seven_families_supported(tmp_path: Path) -> None:
    """C6: build_table_model supports all 7 ReportFamily values with relative ArtifactProvenance."""
    exp_dir, _ = _create_rich_experiment(tmp_path)
    loaded = load_experiment_artifacts_readonly(exp_dir)

    for fam in ReportFamily:
        tbl = build_table_model(fam, loaded)
        assert tbl.family == fam
        assert len(tbl.columns) >= 1
        assert all(not Path(p).is_absolute() for p in tbl.provenance.source_relative_paths)


def test_m71_03_numeric_parity_and_missing_distinction(tmp_path: Path) -> None:
    """C7: Preserves exact unrounded numbers from statistics/*.json and distinguishes None, UNDEFINED_NAN, and +/-Inf."""
    exp_dir, legit_hex_id = _create_rich_experiment(tmp_path)
    loaded = load_experiment_artifacts_readonly(exp_dir)

    tbl_d = build_table_model(ReportFamily.D_PREDICTIVE_PERFORMANCE, loaded)
    rmse_row = [r for r in tbl_d.rows if r["model_id"] == legit_hex_id and r["metric"] == "rmse"][0]
    r2_row = [r for r in tbl_d.rows if r["model_id"] == legit_hex_id and r["metric"] == "r2"][0]

    # Exact unrounded numeric parity
    assert rmse_row["mean"] == 1.0123456789
    # None (e.g. std=None) stays None -> rendered as "N/A"
    assert rmse_row["std"] is None
    # UNDEFINED_NAN preserved distinctly from None -> rendered as "UNDEFINED_NAN"
    assert r2_row["status"] == "UNDEFINED_NAN"
    assert r2_row["mean"] is not None and math.isnan(r2_row["mean"])

    md_d = render_table_markdown(tbl_d)
    assert "N/A" in md_d
    assert "UNDEFINED_NAN" in md_d

    # Family E preserves -Inf t_statistic and renders as "-Inf"
    tbl_e = build_table_model(ReportFamily.E_STATISTICAL_COMPARISONS, loaded)
    assert math.isinf(tbl_e.rows[0]["t_statistic"]) and tbl_e.rows[0]["t_statistic"] < 0
    assert "-Inf" in render_table_markdown(tbl_e)


def test_m71_03_structural_hash_exclusion(tmp_path: Path) -> None:
    """C8: Technical *_hash fields are excluded while legitimate 64-char user IDs are preserved."""
    exp_dir, legit_hex_id = _create_rich_experiment(tmp_path)
    loaded = load_experiment_artifacts_readonly(exp_dir)

    tbl_a = build_table_model(ReportFamily.A_DATA_CHARACTERIZATION, loaded)
    tbl_c = build_table_model(ReportFamily.C_MODELS_CONFIG, loaded)

    col_keys_a = {c.key for c in tbl_a.columns}
    col_keys_c = {c.key for c in tbl_c.columns}
    assert not any(k.endswith("_hash") for k in col_keys_a | col_keys_c)
    assert "e" * 64 not in render_table_csv(tbl_a)
    assert "c" * 64 not in render_table_csv(tbl_c)
    # Legitimate 64-char hex user model_id is NOT stripped!
    assert legit_hex_id in render_table_csv(tbl_c)


def test_m71_03_renderers_csv_markdown_latex_booktabs(tmp_path: Path) -> None:
    """C9: CSV preserves full precision, Markdown aligns columns, LaTeX uses booktabs and escapes special chars."""
    exp_dir, _ = _create_rich_experiment(tmp_path)
    loaded = load_experiment_artifacts_readonly(exp_dir)

    tbl_d = build_table_model(ReportFamily.D_PREDICTIVE_PERFORMANCE, loaded)
    csv_out = render_table_csv(tbl_d)
    md_out = render_table_markdown(tbl_d)
    tex_out = render_table_latex(tbl_d)

    assert "1.0123456789" in csv_out
    assert "1.0123" in md_out
    assert "---:" in md_out
    assert "\\toprule" in tex_out
    assert "\\midrule" in tex_out
    assert "\\bottomrule" in tex_out
    assert "s\\_base" in tex_out  # underscore escaped for LaTeX


def test_family_a_and_g_populated_from_real_artifacts(tmp_path: Path) -> None:
    """C1 (M8-01, M8-02): Family A reads real dataset_profile.json (nested/summary/fields) and Family G reads cell diagnostics."""
    exp_dir, legit_hex_id = _create_rich_experiment(tmp_path)

    # Replace flat dataset_profile.json with real dataset_profile_to_dict-style structure + optional summary
    write_json_atomic(
        exp_dir / "data" / "dataset_profile.json",
        {
            "source_dataset_hash": "e" * 64,
            "n_rows": 120,
            "n_cols": 6,
            "memory_bytes": 5760,
            "columns": {
                "x1": {"name": "x1", "semantic_type": "continuous"},
                "x2": {"name": "x2", "semantic_type": "continuous"},
                "y": {"name": "y", "semantic_type": "continuous"},
            },
            "duplicate_rows": {"n_duplicate_rows": 2},
            "target": {"column_name": "y", "task_type": "regression"},
            "findings": [{"code": "E1_HIGH_CORRELATION", "severity": "warning"}],
            "summary": {"cleanliness_note": "ok"},
        },
        overwrite=True,
    )

    # Write real cell diagnostics in runs/cells/
    cells_dir = exp_dir / "runs" / "cells"
    cells_dir.mkdir(parents=True, exist_ok=True)
    write_json_atomic(
        cells_dir / f"cell_{legit_hex_id}__s_base__fold_0.json",
        {
            "cell_id": f"cell_{legit_hex_id}__s_base__fold_0",
            "model_id": legit_hex_id,
            "scenario_id": "s_base",
            "fold_id": "fold_0",
            "diagnostics": {
                "model_family": "LINEAR",
                "coefficients": [0.5, -0.25],
                "oob_score": 0.91,
                "extra_metadata": {"n_iter": 12},
            },
        },
        overwrite=True,
    )

    loaded = load_experiment_artifacts_readonly(exp_dir)
    tbl_a = build_table_model(ReportFamily.A_DATA_CHARACTERIZATION, loaded)
    attrs_a = {r["attribute"]: r["value"] for r in tbl_a.rows}
    assert len(tbl_a.rows) >= 5
    assert attrs_a["n_rows"] == 120
    assert attrs_a["n_cols"] == 6
    assert attrs_a["n_columns_profiled"] == 3
    assert attrs_a["n_duplicate_rows"] == 2
    assert attrs_a["n_findings"] == 1
    assert attrs_a["target_column"] == "y"
    assert attrs_a["cleanliness_note"] == "ok"
    assert "e" * 64 not in render_table_csv(tbl_a)

    tbl_g = build_table_model(ReportFamily.G_MODEL_SPECIFIC_ARTIFACTS, loaded)
    assert len(tbl_g.rows) >= 2
    assert any(r["model_id"] == legit_hex_id and r["artifact_key"] == "coefficients" for r in tbl_g.rows)
    assert any(r["model_id"] == legit_hex_id and r["artifact_key"] == "oob_score" for r in tbl_g.rows)
    assert tbl_g.notes == ()


def test_m10_tables_pandas_prep_and_enriched_metadata(tmp_path: Path) -> None:
    """C4 (M10): Pandas prepares tables A-G internally, returns immutable TableModel, enriches B/C/E/G, and supports table_to_dataframe."""
    from types import MappingProxyType
    import pandas as pd
    from experimental_ml.reporting.tables import table_to_dataframe
    from experimental_ml.reporting.types import ReportAudience, ReportContentSelection

    exp_dir, legit_hex_id = _create_rich_experiment(tmp_path)
    loaded = load_experiment_artifacts_readonly(exp_dir)
    real_sc_id = next(iter(loaded.statistics.consolidation.configurations.keys()))[1]
    # Enrich loaded catalogs and cell_diagnostics
    enriched = type(loaded)(
        experiment_id=loaded.experiment_id,
        partition_plan_id=loaded.partition_plan_id,
        statistics=loaded.statistics,
        dataset_profile=loaded.dataset_profile,
        preparation_plan=loaded.preparation_plan,
        partition_plan=loaded.partition_plan,
        scenarios_catalog={
            "scenarios": (
                {
                    "scenario_id": real_sc_id,
                    "mode": "DYNAMIC",
                    "dynamic_method": "TOP_K_RELEVANCE",
                    "top_k": 5,
                    "candidate_features": ("f1", "f2", "f3", "f4", "f5"),
                    "scientific_justification": "Seleção por relevância univariada.",
                },
            ),
        },
        models_catalog={
            "models": (
                {
                    "model_id": legit_hex_id,
                    "display_name": "Ridge Regressor",
                    "family": "LINEAR",
                    "capabilities": {"supported_task_types": ("REGRESSION",)},
                    "preprocessing": {"layer2_steps": ({"name": "STANDARD_SCALER"},)},
                    "default_hyperparameters": {"alpha": 1.0},
                },
                {
                    "model_id": "m2",
                    "display_name": "RF Regressor",
                    "family": "TREE_ENSEMBLE",
                    "task_type": "REGRESSION",
                },
            ),
        },
        execution_state=loaded.execution_state,
        cell_diagnostics=(
            {"model_id": legit_hex_id, "scenario_id": real_sc_id, "diagnostics": {"feature_importances": {"f1": 0.6, "f2": 0.4}}},
            {"model_id": legit_hex_id, "scenario_id": real_sc_id, "diagnostics": {"feature_importances": {"f1": 0.8, "f2": 0.2}}},
        ),
    )

    tbl_b = build_table_model(ReportFamily.B_FEATURE_SCENARIOS, enriched)
    assert isinstance(tbl_b.rows[0], MappingProxyType)
    assert tbl_b.rows[0]["n_features"] == 5
    assert "TOP_K_RELEVANCE" in tbl_b.rows[0]["strategy"]
    assert "Seleção" in tbl_b.rows[0]["scientific_justification"]

    tbl_c = build_table_model(ReportFamily.C_MODELS_CONFIG, enriched)
    row_m1 = next(r for r in tbl_c.rows if r["model_id"] == legit_hex_id)
    assert row_m1["display_name"] == "Ridge Regressor"
    assert row_m1["task_type"] == "REGRESSION"
    assert "STANDARD_SCALER" in row_m1["preprocessing"]
    assert "alpha=1.0" in row_m1["hyperparameters"]

    # Table E filtering by model_ids
    sel_only_m1 = ReportContentSelection(
        audience=ReportAudience.CUSTOM,
        families=(ReportFamily.E_STATISTICAL_COMPARISONS,),
        model_ids=(legit_hex_id,),
        scenario_ids=(real_sc_id,),
        metric_ids=("rmse",),
    )
    tbl_e_filtered = build_table_model(ReportFamily.E_STATISTICAL_COMPARISONS, enriched, sel_only_m1)
    assert len(tbl_e_filtered.rows) == 0

    # Table G numeric dict aggregation across folds
    tbl_g = build_table_model(ReportFamily.G_MODEL_SPECIFIC_ARTIFACTS, enriched)
    assert "f1=0.7000" in tbl_g.rows[0]["summary"]

    # Boundary conversion
    df_c = table_to_dataframe(tbl_c)
    assert isinstance(df_c, pd.DataFrame)
    assert len(df_c) == 1
