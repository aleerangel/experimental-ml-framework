"""Read-only experiment loader and deterministic content selection (REP-02, CA-E6-01)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from experimental_ml.core.storage import read_json
from experimental_ml.reporting.types import (
    LoadedExperimentData,
    ReportAudience,
    ReportContentSelection,
    ReportFamily,
)
from experimental_ml.stages.stage_gates import (
    EXECUTION_STATE_REL_PATH,
    MODELS_CATALOG_REL_PATH,
    PARTITION_PLAN_REL_PATH,
    PREPARATION_PLAN_REL_PATH,
    SCENARIOS_CATALOG_REL_PATH,
    verify_statistics_gate,
)
from experimental_ml.statistics.storage import load_statistics_artifacts


_ARTICLE_COMPACT_FAMILIES = (
    ReportFamily.D_PREDICTIVE_PERFORMANCE,
    ReportFamily.E_STATISTICAL_COMPARISONS,
    ReportFamily.F_STABILITY_COST_PARETO,
)


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    if path.is_file():
        return read_json(path)
    return None


def load_experiment_artifacts_readonly(experiment_dir: Path | str) -> LoadedExperimentData:
    """Verify Stage 5 gate and load Stage 1-5 persisted artifacts strictly read-only (CA-E6-01)."""
    exp_dir = Path(experiment_dir).resolve()
    verify_statistics_gate(exp_dir)
    stats = load_statistics_artifacts(exp_dir / "statistics")

    profile = _read_optional_json(exp_dir / "data" / "dataset_profile.json")
    prep = _read_optional_json(exp_dir / PREPARATION_PLAN_REL_PATH)
    part = _read_optional_json(exp_dir / PARTITION_PLAN_REL_PATH)
    scenarios = _read_optional_json(exp_dir / SCENARIOS_CATALOG_REL_PATH)
    models = _read_optional_json(exp_dir / MODELS_CATALOG_REL_PATH)
    exec_state = _read_optional_json(exp_dir / EXECUTION_STATE_REL_PATH)
    ks_drift = _read_optional_json(exp_dir / "statistics" / "ks_drift_report.json")
    oof_res_diag = _read_optional_json(exp_dir / "statistics" / "oof_residuals_diagnostics.json")
    meta_features = _read_optional_json(exp_dir / "dataset_meta_features.json")

    cell_diags: list[dict[str, Any]] = []
    cells_dir = exp_dir / "runs" / "cells"
    if cells_dir.is_dir():
        for cell_path in sorted(cells_dir.glob("cell_*.json")):
            cell_raw = _read_optional_json(cell_path)
            if isinstance(cell_raw, dict) and isinstance(cell_raw.get("diagnostics"), dict) and cell_raw["diagnostics"]:
                cell_diags.append(
                    {
                        "cell_id": str(cell_raw.get("cell_id", cell_path.stem)),
                        "model_id": str(cell_raw.get("model_id", "")),
                        "scenario_id": str(cell_raw.get("scenario_id", "")),
                        "fold_id": str(cell_raw.get("fold_id", "")),
                        "diagnostics": cell_raw["diagnostics"],
                    }
                )

    return LoadedExperimentData(
        experiment_id=stats.consolidation.experiment_id,
        partition_plan_id=stats.consolidation.partition_plan_id,
        statistics=stats,
        dataset_profile=profile,
        preparation_plan=prep,
        partition_plan=part,
        scenarios_catalog=scenarios,
        models_catalog=models,
        execution_state=exec_state,
        cell_diagnostics=tuple(cell_diags),
        ks_drift_report=ks_drift,
        oof_residuals_diagnostics=oof_res_diag,
        dataset_meta_features=meta_features,
    )


def select_report_content(
    loaded_data: LoadedExperimentData,
    selection: ReportContentSelection | None = None,
) -> ReportContentSelection:
    """Resolve deterministic ReportContentSelection for FULL_LAB, ARTICLE_COMPACT, or CUSTOM (RF6.1)."""
    sel = selection or ReportContentSelection(audience=ReportAudience.FULL_LAB)

    consol = loaded_data.statistics.consolidation
    all_models = sorted({m for m, _ in consol.configurations.keys()})
    all_scenarios = sorted({s for _, s in consol.configurations.keys()})
    all_metrics = sorted(
        {
            metric_name
            for summary in consol.configurations.values()
            for metric_name in summary.aggregated_metrics.keys()
        }
    )

    if sel.audience == ReportAudience.FULL_LAB:
        return ReportContentSelection(
            audience=ReportAudience.FULL_LAB,
            families=tuple(ReportFamily),
            model_ids=tuple(all_models),
            scenario_ids=tuple(all_scenarios),
            metric_ids=tuple(all_metrics),
        )

    if sel.audience == ReportAudience.ARTICLE_COMPACT:
        fams = sel.families if sel.families else _ARTICLE_COMPACT_FAMILIES
        m_ids = tuple(m for m in all_models if m in sel.model_ids) if sel.model_ids else tuple(all_models)
        s_ids = tuple(s for s in all_scenarios if s in sel.scenario_ids) if sel.scenario_ids else tuple(all_scenarios)
        met_ids = tuple(mt for mt in all_metrics if mt in sel.metric_ids) if sel.metric_ids else tuple(all_metrics)
        return ReportContentSelection(
            audience=ReportAudience.ARTICLE_COMPACT,
            families=fams,
            model_ids=m_ids,
            scenario_ids=s_ids,
            metric_ids=met_ids,
        )

    # CUSTOM
    m_ids = tuple(m for m in all_models if m in sel.model_ids) if sel.model_ids else tuple(all_models)
    s_ids = tuple(s for s in all_scenarios if s in sel.scenario_ids) if sel.scenario_ids else tuple(all_scenarios)
    met_ids = tuple(mt for mt in all_metrics if mt in sel.metric_ids) if sel.metric_ids else tuple(all_metrics)
    return ReportContentSelection(
        audience=ReportAudience.CUSTOM,
        families=sel.families,
        model_ids=m_ids,
        scenario_ids=s_ids,
        metric_ids=met_ids,
    )
