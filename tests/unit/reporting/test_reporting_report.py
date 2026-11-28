"""Unit tests for full scientific report generation in Markdown and self-contained HTML (REP-05, RNF03)."""

from pathlib import Path
import pytest

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.storage import write_json_atomic
from experimental_ml.core.types import ObservationId
from experimental_ml.metrics.types import MetricDirection, MetricEvaluationScope, MetricValue
from experimental_ml.reporting.loader import load_experiment_artifacts_readonly
from experimental_ml.reporting.report import render_full_report
from experimental_ml.reporting.types import ResearcherDeclarations
from experimental_ml.statistics.comparisons import run_statistical_comparisons
from experimental_ml.statistics.multiobjective import compute_pareto_frontier
from experimental_ml.statistics.storage import save_statistics_artifacts
from experimental_ml.statistics.suitability import evaluate_method_suitability
from experimental_ml.statistics.synthesis import synthesize_conclusions
from experimental_ml.statistics.types import (
    AggregatedMetricStats,
    ComparisonScope,
    ComparisonSpec,
    ConfigurationSummary,
    CoverageStatus,
    DescriptiveConsolidation,
    MultiObjectiveSpec,
    MultiplicityMethod,
    ObjectiveSpec,
)
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)


def _create_report_experiment(exp_dir: Path) -> None:
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
        plan_id="pp_rep_full",
        source_dataset_hash="a" * 64,
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=tuple(ObservationId(f"d_{k}") for k in range(50)),
        holdout_ids=(),
        folds=folds,
        config=PartitionConfig(PartitionStrategy.KFOLD, EvaluationRegime.CV_ONLY, n_splits=n_folds),
    )
    sum1 = ConfigurationSummary(
        model_id="m_alpha",
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
        fold_metrics={
            f"fold_{i}": {
                "rmse": MetricValue("rmse", 1.0 + 0.01 * i, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 10)
            }
            for i in range(5)
        },
        aggregated_metrics={
            "rmse": AggregatedMetricStats(5, 5, MetricStatus.VALID, 1.02345, 0.0158, 1.02, 0.02, 1.01, 1.03, 1.00, 1.04)
        },
        pooled_oof_metrics={},
        aggregated_timing=None,
        feature_stability=None,
    )
    sum2 = ConfigurationSummary(
        model_id="m_beta",
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
        fold_metrics={
            f"fold_{i}": {
                "rmse": MetricValue("rmse", 1.5 + 0.01 * i, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 10)
            }
            for i in range(5)
        },
        aggregated_metrics={
            "rmse": AggregatedMetricStats(5, 5, MetricStatus.VALID, 1.52, 0.0158, 1.52, 0.02, 1.51, 1.53, 1.50, 1.54)
        },
        pooled_oof_metrics={},
        aggregated_timing=None,
        feature_stability=None,
    )
    consol = DescriptiveConsolidation("exp_rep_full", plan.plan_id, 2, {("m_alpha", "s1"): sum1, ("m_beta", "s1"): sum2}, "2026-11-16T00:00:00Z")
    suit = evaluate_method_suitability(plan, consol)
    spec = ComparisonSpec(("rmse",), {"rmse": MetricDirection.MINIMIZE}, ComparisonScope.ALL_PAIRWISE, multiplicity_method=MultiplicityMethod.HOLM_BONFERRONI)
    comp = run_statistical_comparisons(consol, plan, spec, suit)
    pareto = compute_pareto_frontier(consol, MultiObjectiveSpec((ObjectiveSpec("rmse", MetricDirection.MINIMIZE),)))
    conc = synthesize_conclusions(consol, suit, comp, "rmse", MetricDirection.MINIMIZE, pareto)
    save_statistics_artifacts(exp_dir / "statistics", consol, suit, comp, conc, pareto=pareto)

    (exp_dir / "data").mkdir(parents=True, exist_ok=True)
    write_json_atomic(exp_dir / "data" / "dataset_profile.json", {"n_rows": 50, "dataset_hash": "e" * 64}, overwrite=True)


def test_m72_02_three_sections_markdown_and_html(tmp_path: Path) -> None:
    """C4: render_full_report separates Researcher Declarations, Computational Facts, and Derived Interpretations."""
    _create_report_experiment(tmp_path)
    loaded = load_experiment_artifacts_readonly(tmp_path)
    decl = ResearcherDeclarations(
        scientific_objective="Evaluate synthetic tabular generalization.",
        data_origin_note="Synthetic controlled fixture.",
        metric_rationale="RMSE chosen as primary error metric.",
    )

    md = render_full_report(loaded, fmt="markdown", declarations=decl, figure_paths=("figures/fig_d.svg",))
    assert "1. Declarações do Pesquisador" in md
    assert "2. Fatos Computacionais Registrados" in md
    assert "3. Interpretações Derivadas e Condicionadas" in md
    assert "4. Glossário Estatístico" in md
    assert "Evaluate synthetic tabular generalization." in md
    assert "![Figura — figures/fig_d.svg](figures/fig_d.svg)" in md

    html_doc = render_full_report(loaded, fmt="html", declarations=decl, figure_paths=("figures/fig_d.svg",))
    assert "<!DOCTYPE html>" in html_doc
    assert '<html lang="pt-BR">' in html_doc
    assert "1. Declarações do Pesquisador" in html_doc
    assert "2. Fatos Computacionais Registrados" in html_doc
    assert "3. Interpretações Derivadas e Condicionadas" in html_doc
    assert "4. Glossário Estatístico" in html_doc
    assert "@media print" in html_doc
    assert '<img src="figures/fig_d.svg"' in html_doc


def test_m72_02_html_offline_parity_and_no_hashes(tmp_path: Path) -> None:
    """C5: HTML embeds CSS inline with zero external links, preserves numeric parity, and excludes *_hash."""
    _create_report_experiment(tmp_path)
    loaded = load_experiment_artifacts_readonly(tmp_path)

    html_doc = render_full_report(loaded, fmt="html")
    assert "<style>" in html_doc
    assert "http://" not in html_doc and "https://" not in html_doc
    assert "e" * 64 not in html_doc
    assert "1.0234" in html_doc or "1.02345" in html_doc


def test_m72_02_invalid_report_format_raises(tmp_path: Path) -> None:
    """C6: Unsupported report format raises ConfigurationError."""
    _create_report_experiment(tmp_path)
    loaded = load_experiment_artifacts_readonly(tmp_path)

    with pytest.raises(ConfigurationError):
        render_full_report(loaded, fmt="docx")


def test_m11_2_report_includes_ks_drift_and_residuals(tmp_path: Path) -> None:
    """M11.2 (T3): render_full_report renders KS dataset-shift and OOF residuals tables in pt-BR."""
    from dataclasses import replace

    _create_report_experiment(tmp_path)
    loaded = load_experiment_artifacts_readonly(tmp_path)
    enriched = replace(
        loaded,
        ks_drift_report={
            "reference_label": "DEV",
            "comparison_label": "FINAL_HOLDOUT",
            "features": [{"feature_name": "x1", "is_target": False, "ks_statistic": 0.45, "p_value": 0.002, "drift_detected": True}],
        },
        oof_residuals_diagnostics={
            "configurations": [
                {
                    "model_id": "m1",
                    "scenario_id": "s1",
                    "n_samples": 40,
                    "lilliefors_d": 0.09,
                    "lilliefors_p": 0.35,
                    "normal_aic": 120.5,
                    "student_t_aic": 122.1,
                    "preferred_family": "NORMAL",
                }
            ]
        },
    )
    md = render_full_report(enriched, fmt="markdown")
    html_doc = render_full_report(enriched, fmt="html")
    assert "Diagnóstico de Dataset Shift" in md
    assert "Diagnóstico de Resíduos OOF" in md
    assert "Diagnóstico de Dataset Shift" in html_doc
    assert "Diagnóstico de Resíduos OOF" in html_doc


def test_m11_3_report_includes_dataset_meta_features(tmp_path: Path) -> None:
    """M113-03: render_full_report exibe Caracterização Estatística Ampliada quando dataset_meta_features está presente."""
    from dataclasses import replace

    _create_report_experiment(tmp_path)
    loaded = load_experiment_artifacts_readonly(tmp_path)
    enriched = replace(
        loaded,
        dataset_meta_features={
            "samples_to_features_ratio": 12.5,
            "intrinsic_dim_ratio_95": 0.6,
            "max_vif": 8.2,
            "linearity_score": 0.91,
        },
    )
    md = render_full_report(enriched, fmt="markdown")
    html_doc = render_full_report(enriched, fmt="html")
    assert "Caracterização Estatística Ampliada (Meta-Features)" in md
    assert "12.5000" in md
    assert "Caracterização Estatística Ampliada (Meta-Features)" in html_doc
    assert "0.9100" in html_doc

