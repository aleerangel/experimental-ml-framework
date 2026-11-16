"""Unit tests for Stage 6 report integrity gate (`verify_report_gate`)."""

import json
from pathlib import Path
import shutil

import pytest

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.findings import DataIntegrityError
from experimental_ml.core.types import ObservationId
from experimental_ml.metrics.types import MetricDirection, MetricEvaluationScope, MetricValue
from experimental_ml.reporting.loader import load_experiment_artifacts_readonly
from experimental_ml.reporting.packaging import build_reproducibility_package
from experimental_ml.reporting.types import PackageMode
from experimental_ml.stages.stage_gates import verify_report_gate
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


def _create_sample_experiment_dir(exp_dir: Path) -> Path:
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
        plan_id="pp_gate_m73",
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
        "exp_gate_m73",
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
    return exp_dir


def test_m73_02_valid_and_portable_after_move(tmp_path: Path) -> None:
    """C5: verify_report_gate passes on valid package and remains valid after moving/renaming root."""
    exp_dir = _create_sample_experiment_dir(tmp_path / "exp")
    loaded = load_experiment_artifacts_readonly(exp_dir)
    pkg_dir = tmp_path / "pkg_original"
    build_reproducibility_package(loaded, output_dir=pkg_dir, mode=PackageMode.REDUCED_NO_RAW_DATA)

    result = verify_report_gate(pkg_dir)
    assert result["status"] == "VERIFIED"
    assert result["experiment_id"] == "exp_gate_m73"
    assert result["partition_plan_id"] == "pp_gate_m73"
    assert result["verified_files_count"] > 0

    moved_dir = tmp_path / "nested" / "pkg_relocated"
    moved_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(pkg_dir), str(moved_dir))

    moved_result = verify_report_gate(moved_dir)
    assert moved_result["status"] == "VERIFIED"
    assert moved_result["verified_files_count"] == result["verified_files_count"]

    # Also verify when package is built directly inside exp_dir alongside statistics/
    build_reproducibility_package(loaded, output_dir=exp_dir, mode=PackageMode.FULL_PACKAGE, source_experiment_dir=exp_dir)
    combined_result = verify_report_gate(exp_dir)
    assert combined_result["status"] == "VERIFIED"


def test_m73_02_tampering_or_missing_raises(tmp_path: Path) -> None:
    """C6: 1-byte tampering, missing file, or uncovered provenance entry raises DataIntegrityError."""
    exp_dir = _create_sample_experiment_dir(tmp_path / "exp")
    loaded = load_experiment_artifacts_readonly(exp_dir)

    # 1. 1-byte modification
    pkg1 = tmp_path / "pkg_tamper"
    build_reproducibility_package(loaded, output_dir=pkg1)
    report_md = pkg1 / "reports" / "report.md"
    raw = bytearray(report_md.read_bytes())
    raw[0] = raw[0] ^ 0x01
    report_md.write_bytes(bytes(raw))
    with pytest.raises(DataIntegrityError):
        verify_report_gate(pkg1)

    # 2. Missing file listed in checksums
    pkg2 = tmp_path / "pkg_missing_file"
    build_reproducibility_package(loaded, output_dir=pkg2)
    (pkg2 / "reports" / "report.html").unlink()
    with pytest.raises(DataIntegrityError):
        verify_report_gate(pkg2)

    # 3. Artifact in artifact_provenance.json missing from checksums.sha256
    pkg3 = tmp_path / "pkg_uncovered"
    build_reproducibility_package(loaded, output_dir=pkg3)
    checksums_path = pkg3 / "reproducibility" / "checksums.sha256"
    filtered = [
        ln for ln in checksums_path.read_text(encoding="utf-8").splitlines()
        if "reports/report.md" not in ln
    ]
    checksums_path.write_text("\n".join(filtered) + "\n", encoding="utf-8")
    with pytest.raises(DataIntegrityError):
        verify_report_gate(pkg3)

    # 4. Missing checksums.sha256
    pkg4 = tmp_path / "pkg_no_checksums"
    build_reproducibility_package(loaded, output_dir=pkg4)
    (pkg4 / "reproducibility" / "checksums.sha256").unlink()
    with pytest.raises(DataIntegrityError):
        verify_report_gate(pkg4)


def test_m73_02_absolute_or_traversal_rejected(tmp_path: Path) -> None:
    """C7: Absolute paths or '..' traversal in checksums.sha256 or artifact_provenance.json raise DataIntegrityError."""
    exp_dir = _create_sample_experiment_dir(tmp_path / "exp")
    loaded = load_experiment_artifacts_readonly(exp_dir)

    # 1. Absolute path in checksums.sha256
    pkg1 = tmp_path / "pkg_abs_checksum"
    build_reproducibility_package(loaded, output_dir=pkg1)
    checksums_path = pkg1 / "reproducibility" / "checksums.sha256"
    checksums_path.write_text(
        checksums_path.read_text(encoding="utf-8") + f"{'0' * 64}  /etc/passwd\n",
        encoding="utf-8",
    )
    with pytest.raises(DataIntegrityError):
        verify_report_gate(pkg1)

    # 2. Traversal '..' in checksums.sha256
    pkg2 = tmp_path / "pkg_trav_checksum"
    build_reproducibility_package(loaded, output_dir=pkg2)
    checksums_path2 = pkg2 / "reproducibility" / "checksums.sha256"
    checksums_path2.write_text(
        checksums_path2.read_text(encoding="utf-8") + f"{'0' * 64}  ../outside.txt\n",
        encoding="utf-8",
    )
    with pytest.raises(DataIntegrityError):
        verify_report_gate(pkg2)

    # 3. Absolute path in artifact_provenance.json
    pkg3 = tmp_path / "pkg_abs_prov"
    build_reproducibility_package(loaded, output_dir=pkg3)
    prov_path = pkg3 / "reproducibility" / "artifact_provenance.json"
    prov_doc = json.loads(prov_path.read_text(encoding="utf-8"))
    prov_doc["artifacts"][0]["output_relative_path"] = "/abs/path/table.csv"
    prov_path.write_text(json.dumps(prov_doc), encoding="utf-8")
    with pytest.raises(DataIntegrityError):
        verify_report_gate(pkg3)
