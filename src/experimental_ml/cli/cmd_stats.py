"""CLI handlers for Stage 5 statistical consolidation and inference (expml stats).

Conforms to CLI-06, CLI-10 (lazy imports), CLI-11 (no raw hashes on stdout), and STAT-14.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


def handle_stats_run(args: argparse.Namespace) -> int:
    """Handle `expml stats run`."""
    from experimental_ml.core.storage import read_json
    from experimental_ml.metrics.types import MetricDirection
    from experimental_ml.orchestration.oof import load_oof_predictions
    from experimental_ml.orchestration.state import load_execution_state
    from experimental_ml.orchestration.storage import load_cell_artifacts
    from experimental_ml.stages.stage_gates import PARTITION_PLAN_REL_PATH, verify_runs_gate
    from experimental_ml.statistics.comparisons import run_statistical_comparisons
    from experimental_ml.statistics.consolidation import (
        consolidate_descriptive,
        validate_stage5_entry,
    )
    from experimental_ml.statistics.multiobjective import compute_pareto_frontier
    from experimental_ml.statistics.storage import save_statistics_artifacts
    from experimental_ml.statistics.suitability import evaluate_method_suitability
    from experimental_ml.statistics.synthesis import synthesize_conclusions
    from experimental_ml.statistics.types import (
        ComparisonScope,
        ComparisonSpec,
        IncompleteComparisonPolicy,
        MultiObjectiveSpec,
        MultiplicityMethod,
        ObjectiveSpec,
    )
    from experimental_ml.validation.codecs import partition_plan_from_dict

    exp_dir = Path(args.experiment_dir).resolve()
    run_dir = exp_dir / "runs"

    # 1. Verify Stage 4 gate & Stage 5 entry
    verify_runs_gate(exp_dir)
    exec_state = load_execution_state(run_dir)
    validate_stage5_entry(exec_state)

    # 2. Load PartitionPlan and Stage 4 artifacts
    part_dict = read_json(exp_dir / PARTITION_PLAN_REL_PATH)
    partition_plan = partition_plan_from_dict(part_dict)

    cell_results = []
    configs: set[tuple[str, str]] = set()
    for cid in sorted(exec_state.cell_statuses.keys()):
        cell, _ = load_cell_artifacts(cid, run_dir)
        cell_results.append(cell)
        configs.add((cell.model_id, cell.scenario_id))

    oof_records = []
    oof_dir = run_dir / "oof"
    if oof_dir.is_dir():
        for m_id, sc_id in sorted(configs):
            if (oof_dir / f"oof_{m_id}__{sc_id}.json").is_file():
                oof_records.append(load_oof_predictions(m_id, sc_id, run_dir))

    n_folds = max(1, len(partition_plan.folds))
    consol = consolidate_descriptive(
        cell_results,
        total_folds_per_config=n_folds,
        oof_predictions=oof_records or None,
        experiment_id=str(exec_state.experiment_id),
        partition_plan_id=partition_plan.plan_id,
    )
    suit = evaluate_method_suitability(partition_plan, consol)

    # 3. Determine comparison spec (optional --config JSON or sensible default)
    all_metrics: set[str] = set()
    metric_dirs: dict[str, MetricDirection] = {}
    for cell in cell_results:
        for m_id, mv in cell.metrics.items():
            all_metrics.add(m_id)
            metric_dirs[m_id] = mv.direction

    if getattr(args, "config", None):
        cfg = read_json(Path(args.config))
        metrics = tuple(cfg.get("metrics_of_interest", sorted(all_metrics)))
        dirs = {
            m: MetricDirection(cfg.get("metric_directions", {}).get(m, metric_dirs[m].value))
            for m in metrics
        }
        scope = ComparisonScope(cfg.get("comparison_scope", ComparisonScope.ALL_PAIRWISE.value))
        mult = MultiplicityMethod(cfg.get("multiplicity_method", MultiplicityMethod.HOLM_BONFERRONI.value))
        alpha = float(cfg.get("alpha", 0.05))
        baseline = tuple(cfg["baseline_config"]) if cfg.get("baseline_config") else None
        planned = tuple(
            ((a[0], a[1]), (b[0], b[1])) for a, b in cfg.get("planned_pairs", ())
        )
        thresholds = cfg.get("practical_relevance_thresholds")
        policy = IncompleteComparisonPolicy(
            cfg.get("incompleteness_policy", IncompleteComparisonPolicy.STRICT_COMPLETE_ONLY.value)
        )
    else:
        metrics = tuple(sorted(all_metrics))
        dirs = {m: metric_dirs[m] for m in metrics}
        scope = ComparisonScope.ALL_PAIRWISE
        mult = MultiplicityMethod.HOLM_BONFERRONI
        alpha = 0.05
        baseline = None
        planned = ()
        thresholds = None
        policy = IncompleteComparisonPolicy.STRICT_COMPLETE_ONLY

    comp_spec = ComparisonSpec(
        metrics_of_interest=metrics,
        metric_directions=dirs,
        comparison_scope=scope,
        baseline_config=baseline,  # type: ignore[arg-type]
        planned_pairs=planned,
        alpha=alpha,
        multiplicity_method=mult,
        practical_relevance_thresholds=thresholds,
    )
    comp_bundle = run_statistical_comparisons(
        consol, partition_plan, comp_spec, suit, policy=policy
    )

    primary_metric = metrics[0]
    primary_dir = dirs[primary_metric]
    pareto = compute_pareto_frontier(
        consol,
        MultiObjectiveSpec(objectives=(ObjectiveSpec(primary_metric, primary_dir),)),
    )
    conclusion = synthesize_conclusions(
        consol, suit, comp_bundle, primary_metric, primary_dir, multi_objective_summary=pareto
    )

    stats_dir = exp_dir / "statistics"
    save_statistics_artifacts(
        stats_dir,
        consol,
        suit,
        comp_bundle,
        conclusion,
        pareto=pareto,
        force=bool(getattr(args, "force", False)),
    )

    leader_str = (
        f"{conclusion.observed_leader[0]}/{conclusion.observed_leader[1]}"
        if conclusion.observed_leader is not None
        else "none"
    )
    sys.stdout.write(
        f"Stage 5 statistics completed for '{consol.experiment_id}': "
        f"{consol.total_configurations} configuration(s), "
        f"{len(comp_bundle.comparisons)} comparison(s), "
        f"observed leader: {leader_str}.\n"
    )
    return 0


def handle_stats_status(args: argparse.Namespace) -> int:
    """Handle `expml stats status`."""
    from experimental_ml.statistics.storage import load_statistics_artifacts

    exp_dir = Path(args.experiment_dir).resolve()
    stats_dir = exp_dir / "statistics"
    loaded = load_statistics_artifacts(stats_dir)

    leader_str = (
        f"{loaded.conclusion.observed_leader[0]}/{loaded.conclusion.observed_leader[1]}"
        if loaded.conclusion.observed_leader is not None
        else "none"
    )
    sys.stdout.write(
        f"Statistics status for '{loaded.consolidation.experiment_id}':\n"
        f"  Configurations: {loaded.consolidation.total_configurations}\n"
        f"  Comparisons executed: {len(loaded.comparisons.comparisons)} "
        f"(skipped: {len(loaded.comparisons.skipped_comparisons)})\n"
        f"  Observed leader ({loaded.conclusion.primary_metric}): {leader_str}\n"
        f"  Evidence: {loaded.conclusion.statistical_evidence_status}\n"
    )
    return 0


def handle_stats_verify(args: argparse.Namespace) -> int:
    """Handle `expml stats verify`."""
    from experimental_ml.stages.stage_gates import verify_statistics_gate

    exp_dir = Path(args.experiment_dir).resolve()
    summary = verify_statistics_gate(exp_dir)
    sys.stdout.write(
        f"Statistics gate VERIFIED for '{summary['experiment_id']}': "
        f"{summary['total_configurations']} configuration(s), "
        f"{summary['total_comparisons']} comparison(s).\n"
    )
    return 0
