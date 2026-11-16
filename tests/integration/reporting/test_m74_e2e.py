"""End-to-end Stage 1 -> Stage 6 integration and XCUT-02 purity tests for M7.4."""

from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from experimental_ml.core.enums import MetricStatus
from experimental_ml.core.storage import read_json
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
from experimental_ml.validation.codecs import partition_plan_from_dict


def _get_expml_cmd() -> list[str]:
    return [sys.executable, "-m", "experimental_ml.cli.main"]


def test_m74_e2e_stage1_to_stage6_cli(tmp_path: Path) -> None:
    """C6: End-to-end Stage 1 -> Stage 6 CLI workflow with move portability, tamper detection, and XCUT-02 purity."""
    cmd = _get_expml_cmd()
    raw_hash_re = re.compile(r"\b[0-9a-f]{64}\b")

    inputs = tmp_path / "inputs"
    inputs.mkdir()
    raw_csv = inputs / "dataset.csv"
    rows = ["id,f1,target"]
    for i in range(1, 21):
        rows.append(f"{i},{10.0 + i},{i % 2}")
    raw_csv.write_text("\n".join(rows) + "\n", encoding="utf-8")

    schema_file = inputs / "schema.json"
    schema_file.write_text(
        json.dumps(
            {
                "target_col": "target",
                "task_type": "BINARY_CLASSIFICATION",
                "column_semantic_types": {"f1": "NUMERIC_CONTINUOUS"},
            }
        ),
        encoding="utf-8",
    )
    rules_file = inputs / "rules.json"
    rules_file.write_text("[]", encoding="utf-8")
    part_cfg_file = inputs / "partition_config.json"
    part_cfg_file.write_text(
        json.dumps({"strategy": "KFOLD", "regime": "CV_ONLY", "n_splits": 5, "master_seed": 42}),
        encoding="utf-8",
    )

    exp_dir = tmp_path / "exp_e2e"

    # Stage 1 & Stage 2 via CLI
    for args in (
        ["data", "profile", "--data", str(raw_csv), "--schema", str(schema_file), "--output-dir", str(exp_dir)],
        ["data", "sanitize", "--experiment-dir", str(exp_dir), "--rules", str(rules_file)],
        ["partition", "build", "--experiment-dir", str(exp_dir), "--config", str(part_cfg_file)],
        ["partition", "verify", "--experiment-dir", str(exp_dir)],
    ):
        proc = subprocess.run([*cmd, *args], capture_output=True, text=True, check=True)
        assert not raw_hash_re.search(proc.stdout)
        assert not raw_hash_re.search(proc.stderr)

    # Persist Stage 5 statistics linked to the Stage 2 PartitionPlan
    part_plan = partition_plan_from_dict(read_json(exp_dir / "partitions" / "partition_plan.json"))
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
                "f1": MetricValue("f1", 0.80 + 0.01 * i, MetricStatus.VALID, MetricDirection.MAXIMIZE, MetricEvaluationScope.PER_FOLD, 4)
            }
            for i in range(5)
        },
        aggregated_metrics={
            "f1": AggregatedMetricStats(5, 5, MetricStatus.VALID, 0.82, 0.0158, 0.82, 0.02, 0.81, 0.83, 0.80, 0.84)
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
                "f1": MetricValue("f1", 0.70 + 0.01 * i, MetricStatus.VALID, MetricDirection.MAXIMIZE, MetricEvaluationScope.PER_FOLD, 4)
            }
            for i in range(5)
        },
        aggregated_metrics={
            "f1": AggregatedMetricStats(5, 5, MetricStatus.VALID, 0.72, 0.0158, 0.72, 0.02, 0.71, 0.73, 0.70, 0.74)
        },
        pooled_oof_metrics={},
        aggregated_timing=None,
        feature_stability=None,
    )
    consol = DescriptiveConsolidation("exp_e2e_m74", part_plan.plan_id, 2, {("m1", "s1"): sum1, ("m2", "s1"): sum2}, "2026-11-16T00:00:00Z")
    suit = evaluate_method_suitability(part_plan, consol)
    spec = ComparisonSpec(("f1",), {"f1": MetricDirection.MAXIMIZE}, ComparisonScope.ALL_PAIRWISE, multiplicity_method=MultiplicityMethod.HOLM_BONFERRONI)
    comp = run_statistical_comparisons(consol, part_plan, spec, suit)
    pareto = compute_pareto_frontier(consol, MultiObjectiveSpec((ObjectiveSpec("f1", MetricDirection.MAXIMIZE),)))
    conc = synthesize_conclusions(consol, suit, comp, "f1", MetricDirection.MAXIMIZE, pareto)
    save_statistics_artifacts(exp_dir / "statistics", consol, suit, comp, conc, pareto=pareto)

    # Stage 6 via CLI: report generate -> report export -> move -> report verify -> 1-byte tamper
    pkg_dir = tmp_path / "exported_pkg"
    for args in (
        ["report", "generate", "--experiment-dir", str(exp_dir), "--format", "both", "--objective", "E2E test"],
        ["report", "export", "--experiment-dir", str(exp_dir), "--output-dir", str(pkg_dir), "--mode", "full_package"],
        ["report", "verify", "--experiment-dir", str(pkg_dir)],
    ):
        proc = subprocess.run([*cmd, *args], capture_output=True, text=True, check=True)
        assert not raw_hash_re.search(proc.stdout)
        assert not raw_hash_re.search(proc.stderr)

    moved_pkg = tmp_path / "relocated" / "pkg_moved"
    moved_pkg.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(pkg_dir), str(moved_pkg))

    proc_moved = subprocess.run(
        [*cmd, "report", "verify", "--experiment-dir", str(moved_pkg)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(proc_moved.stdout)["status"] == "VERIFIED"

    # 1-byte tamper -> non-zero exit code (2)
    report_md = moved_pkg / "reports" / "report.md"
    buf = bytearray(report_md.read_bytes())
    buf[0] ^= 0x01
    report_md.write_bytes(bytes(buf))
    proc_tamper = subprocess.run(
        [*cmd, "report", "verify", "--experiment-dir", str(moved_pkg)],
        capture_output=True,
        text=True,
    )
    assert proc_tamper.returncode == 2
