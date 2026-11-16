"""Unit tests for M7.3 reproducibility packaging (`PackageMode`, `build_reproducibility_package`)."""

from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path

import pytest

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.findings import ContractViolationError
from experimental_ml.core.types import ObservationId
from experimental_ml.metrics.types import MetricDirection, MetricEvaluationScope, MetricValue
from experimental_ml.reporting.loader import load_experiment_artifacts_readonly
from experimental_ml.reporting.packaging import build_reproducibility_package
from experimental_ml.reporting.types import (
    PackageMode,
    ReproducibilityPackageManifest,
    ResearcherDeclarations,
)
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


def _create_sample_experiment(exp_dir: Path) -> Path:
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
        plan_id="pp_pkg_m73",
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
        "exp_pkg_m73",
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
    (data_dir / "raw_dataset.csv").write_text("x,y\n1,2\n", encoding="utf-8")
    return exp_dir


def test_m73_01_manifest_and_mode() -> None:
    """C1: PackageMode enum and frozen ReproducibilityPackageManifest."""
    assert PackageMode.FULL_PACKAGE == "full_package"
    assert PackageMode.REDUCED_NO_RAW_DATA == "reduced_no_raw_data"

    manifest = ReproducibilityPackageManifest(
        experiment_id="exp_1",
        partition_plan_id="pp_1",
        package_mode=PackageMode.FULL_PACKAGE,
        reproduction_level="FULL",
        exported_files=("tables/table_d_descriptive_performance.csv",),
        checksums_file="reproducibility/checksums.sha256",
        provenance_file="reproducibility/artifact_provenance.json",
    )
    assert manifest.package_mode == PackageMode.FULL_PACKAGE
    with pytest.raises(FrozenInstanceError):
        manifest.experiment_id = "other"  # type: ignore[misc]


def test_m73_01_relative_paths_and_structure(tmp_path: Path) -> None:
    """C2: Exports tables/, figures/, reports/, reproducibility/ with 100% relative POSIX paths and sorted sha256."""
    exp_dir = _create_sample_experiment(tmp_path / "exp")
    loaded = load_experiment_artifacts_readonly(exp_dir)
    pkg_dir = tmp_path / "pkg_out"

    manifest = build_reproducibility_package(
        loaded,
        output_dir=pkg_dir,
        mode=PackageMode.FULL_PACKAGE,
        declarations=ResearcherDeclarations(scientific_objective="Benchmark RMSE"),
        source_experiment_dir=exp_dir,
    )

    assert (pkg_dir / "tables").is_dir()
    assert (pkg_dir / "figures").is_dir()
    assert (pkg_dir / "reports" / "report.md").is_file()
    assert (pkg_dir / "reports" / "report.html").is_file()

    repro_dir = pkg_dir / "reproducibility"
    for fname in ("artifact_provenance.json", "checksums.sha256", "environment.json", "seeds.json", "REPRODUCE.md"):
        assert (repro_dir / fname).is_file()

    prov = json.loads((repro_dir / "artifact_provenance.json").read_text(encoding="utf-8"))
    assert len(prov["artifacts"]) > 0
    for item in prov["artifacts"]:
        rel = item["output_relative_path"]
        assert not rel.startswith("/")
        assert ".." not in rel.split("/")
        assert "\\" not in rel
        assert (pkg_dir / rel).is_file()

    lines = [
        ln for ln in (repro_dir / "checksums.sha256").read_text(encoding="utf-8").splitlines() if ln.strip()
    ]
    paths_in_checksums = []
    for ln in lines:
        digest, rel_path = ln.split("  ", 1)
        assert len(digest) == 64
        assert not rel_path.startswith("/")
        assert ".." not in rel_path.split("/")
        assert "\\" not in rel_path
        actual_digest = hashlib.sha256((pkg_dir / rel_path).read_bytes()).hexdigest()
        assert digest == actual_digest
        paths_in_checksums.append(rel_path)

    assert paths_in_checksums == sorted(paths_in_checksums)
    assert manifest.checksums_file == "reproducibility/checksums.sha256"
    assert manifest.provenance_file == "reproducibility/artifact_provenance.json"


def test_m73_01_reduced_mode_excludes_raw_data(tmp_path: Path) -> None:
    """C3: REDUCED_NO_RAW_DATA excludes raw data files and documents reproduction level in REPRODUCE.md."""
    exp_dir = _create_sample_experiment(tmp_path / "exp")
    loaded = load_experiment_artifacts_readonly(exp_dir)
    pkg_dir = tmp_path / "pkg_reduced"

    manifest = build_reproducibility_package(
        loaded,
        output_dir=pkg_dir,
        mode=PackageMode.REDUCED_NO_RAW_DATA,
        source_experiment_dir=exp_dir,
    )

    assert manifest.package_mode == PackageMode.REDUCED_NO_RAW_DATA
    assert "REDUCED" in manifest.reproduction_level.upper()
    assert not (pkg_dir / "data").exists()
    reproduce_md = (pkg_dir / "reproducibility" / "REPRODUCE.md").read_text(encoding="utf-8")
    assert "REDUCED_NO_RAW_DATA" in reproduce_md or "REDUCED" in reproduce_md


def test_m73_01_force_false_protects_overwrite(tmp_path: Path) -> None:
    """C4: Existing output files with force=False raise ContractViolationError without overwriting."""
    exp_dir = _create_sample_experiment(tmp_path / "exp")
    loaded = load_experiment_artifacts_readonly(exp_dir)
    pkg_dir = tmp_path / "pkg_force"

    build_reproducibility_package(loaded, output_dir=pkg_dir, mode=PackageMode.FULL_PACKAGE)
    sentinel = (pkg_dir / "reports" / "report.md").read_text(encoding="utf-8")

    with pytest.raises(ContractViolationError):
        build_reproducibility_package(loaded, output_dir=pkg_dir, mode=PackageMode.FULL_PACKAGE, force=False)

    assert (pkg_dir / "reports" / "report.md").read_text(encoding="utf-8") == sentinel

    manifest2 = build_reproducibility_package(loaded, output_dir=pkg_dir, mode=PackageMode.FULL_PACKAGE, force=True)
    assert manifest2.experiment_id == "exp_pkg_m73"
