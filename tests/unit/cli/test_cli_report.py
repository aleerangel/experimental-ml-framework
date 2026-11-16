"""Unit tests for CLI `expml report` subcommands (`generate`, `export`, `verify`)."""

import json
from pathlib import Path
import shutil

import pytest

from experimental_ml.cli.main import main
from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.types import ObservationId
from experimental_ml.metrics.types import MetricDirection, MetricEvaluationScope, MetricValue
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


def _create_cli_experiment(exp_dir: Path) -> Path:
    n_folds = 5
    folds = tuple(
        FoldPartition(
            fold_index=i,
            train_ids=tuple(ObservationId(f"tr_{i}_{k}") for k in range(20)),
            val_ids=tuple(ObservationId(f"va_{i}_{k}") for k in range(5)),
        )
        for i in range(n_folds)
    )
    plan = PartitionPlan(
        plan_id="pp_cli_m74",
        source_dataset_hash="a" * 64,
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=tuple(ObservationId(f"d_{k}") for k in range(25)),
        holdout_ids=(),
        folds=folds,
        config=PartitionConfig(PartitionStrategy.KFOLD, EvaluationRegime.CV_ONLY, n_splits=n_folds),
    )
    sum1 = ConfigurationSummary(
        model_id="m1",
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
                "rmse": MetricValue("rmse", 1.0 + 0.01 * i, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 5)
            }
            for i in range(5)
        },
        aggregated_metrics={
            "rmse": AggregatedMetricStats(5, 5, MetricStatus.VALID, 1.02, 0.0158, 1.02, 0.02, 1.01, 1.03, 1.00, 1.04)
        },
        pooled_oof_metrics={},
        aggregated_timing=None,
        feature_stability=None,
    )
    sum2 = ConfigurationSummary(
        model_id="m2",
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
                "rmse": MetricValue("rmse", 1.5 + 0.01 * i, MetricStatus.VALID, MetricDirection.MINIMIZE, MetricEvaluationScope.PER_FOLD, 5)
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
    desc = DescriptiveConsolidation(
        "exp_cli_m74",
        plan.plan_id,
        2,
        {("m1", "s1"): sum1, ("m2", "s1"): sum2},
        "2026-11-16T00:00:00Z",
    )
    suit = evaluate_method_suitability(plan, desc)
    spec = ComparisonSpec(("rmse",), {"rmse": MetricDirection.MINIMIZE}, ComparisonScope.ALL_PAIRWISE, multiplicity_method=MultiplicityMethod.HOLM_BONFERRONI)
    comp = run_statistical_comparisons(desc, plan, spec, suit)
    mo = compute_pareto_frontier(desc, MultiObjectiveSpec((ObjectiveSpec("rmse", MetricDirection.MINIMIZE),)))
    synth = synthesize_conclusions(desc, suit, comp, "rmse", MetricDirection.MINIMIZE, mo)
    save_statistics_artifacts(exp_dir / "statistics", desc, suit, comp, synth, pareto=mo)
    data_dir = exp_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "raw.csv").write_text("x,y\n1,2\n", encoding="utf-8")
    return exp_dir


def test_m74_01_cli_report_generate(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """C1: expml report generate writes report.md and/or report.html read-only with exit 0."""
    exp_dir = _create_cli_experiment(tmp_path / "exp")
    rc = main(["report", "generate", "--exp-dir", str(exp_dir), "--format", "both", "--audience", "FULL_LAB"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["experiment_id"] == "exp_cli_m74"
    assert (exp_dir / "reports" / "report.md").is_file()
    assert (exp_dir / "reports" / "report.html").is_file()


def test_m74_01_cli_report_export_modes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """C2: expml report export supports full_package and reduced_no_raw_data with exit 0."""
    exp_dir = _create_cli_experiment(tmp_path / "exp")
    pkg_reduced = tmp_path / "pkg_reduced"
    rc = main([
        "report", "export",
        "--experiment-dir", str(exp_dir),
        "--output-dir", str(pkg_reduced),
        "--mode", "reduced_no_raw_data",
    ])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["package_mode"] == "reduced_no_raw_data"
    assert not (pkg_reduced / "data").exists()
    assert (pkg_reduced / "reproducibility" / "checksums.sha256").is_file()


def test_m74_01_cli_force_protection(tmp_path: Path) -> None:
    """C3: expml report generate and export without --force return code 2 without overwriting."""
    exp_dir = _create_cli_experiment(tmp_path / "exp")
    assert main(["report", "generate", "--experiment-dir", str(exp_dir)]) == 0
    sentinel = (exp_dir / "reports" / "report.md").read_text(encoding="utf-8")
    assert main(["report", "generate", "--experiment-dir", str(exp_dir)]) == 2
    assert (exp_dir / "reports" / "report.md").read_text(encoding="utf-8") == sentinel
    assert main(["report", "generate", "--experiment-dir", str(exp_dir), "--force"]) == 0

    pkg_dir = tmp_path / "pkg"
    assert main(["report", "export", "--experiment-dir", str(exp_dir), "--output-dir", str(pkg_dir)]) == 0
    assert main(["report", "export", "--experiment-dir", str(exp_dir), "--output-dir", str(pkg_dir)]) == 2
    assert main(["report", "export", "--experiment-dir", str(exp_dir), "--output-dir", str(pkg_dir), "--force"]) == 0


def test_m74_02_cli_report_verify_portable(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """C4: expml report verify returns 0 and VERIFIED even after moving the package directory."""
    exp_dir = _create_cli_experiment(tmp_path / "exp")
    pkg_dir = tmp_path / "pkg_orig"
    assert main(["report", "export", "--experiment-dir", str(exp_dir), "--output-dir", str(pkg_dir)]) == 0
    capsys.readouterr()

    assert main(["report", "verify", "--experiment-dir", str(pkg_dir)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "VERIFIED"

    moved_dir = tmp_path / "moved" / "pkg_relocated"
    moved_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(pkg_dir), str(moved_dir))

    assert main(["report", "verify", "--experiment-dir", str(moved_dir)]) == 0
    out_moved = json.loads(capsys.readouterr().out)
    assert out_moved["status"] == "VERIFIED"


def test_m74_02_cli_report_verify_tamper_fails(tmp_path: Path) -> None:
    """C5: expml report verify returns 2 on 1-byte tampering."""
    exp_dir = _create_cli_experiment(tmp_path / "exp")
    pkg_dir = tmp_path / "pkg_tamper"
    assert main(["report", "export", "--experiment-dir", str(exp_dir), "--output-dir", str(pkg_dir)]) == 0

    report_md = pkg_dir / "reports" / "report.md"
    raw = bytearray(report_md.read_bytes())
    raw[0] = raw[0] ^ 0x01
    report_md.write_bytes(bytes(raw))

    assert main(["report", "verify", "--experiment-dir", str(pkg_dir)]) == 2
