"""Command handlers for 'expml init' and 'expml quickrun' (USAB-01)."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from experimental_ml.core.findings import ConfigurationError, ExperimentalMLError
from experimental_ml.core.storage import write_json_atomic


def _starter_csv(task: str) -> str:
    if task == "regression":
        rows = ["x1,x2,alvo"] + [
            f"{i * 0.1:.2f},{i * 0.5:.2f},{2.0 * (i * 0.1) + 0.5 * (i * 0.5) + 1.0:.3f}"
            for i in range(1, 31)
        ]
        return "\n".join(rows) + "\n"
    if task == "multiclass_classification":
        rows = ["x1,x2,alvo"] + [
            f"{i * 0.1:.2f},{i * 0.4:.2f},{i % 3}"
            for i in range(1, 31)
        ]
        return "\n".join(rows) + "\n"
    # binary_classification
    rows = ["x1,x2,alvo"] + [
        f"{i * 0.1:.2f},{i * 0.4:.2f},{0 if i <= 15 else 1}"
        for i in range(1, 31)
    ]
    return "\n".join(rows) + "\n"


def handle_init(args: argparse.Namespace) -> int:
    """Create a starter experiment directory with example CSV and valid JSON templates."""
    out_dir = Path(args.output_dir).resolve()
    task = str(getattr(args, "task", "regression")).lower()
    force = bool(getattr(args, "force", False))

    task_upper = task.upper()
    if task_upper not in {"REGRESSION", "BINARY_CLASSIFICATION", "MULTICLASS_CLASSIFICATION"}:
        raise ConfigurationError(
            f"Unsupported task '{task}'. Choose from: regression, binary_classification, multiclass_classification."
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "dados_exemplo.csv"
    if csv_path.exists() and not force:
        raise ConfigurationError(
            f"Starter files already exist at '{out_dir}'. Pass --force to overwrite."
        )
    csv_path.write_text(_starter_csv(task), encoding="utf-8")

    write_json_atomic(
        out_dir / "schema.json",
        {"target_col": "alvo", "task_type": task_upper},
        overwrite=force,
    )
    write_json_atomic(out_dir / "rules.json", [], overwrite=force)
    write_json_atomic(
        out_dir / "scenarios.json",
        [
            {
                "scenario_id": "todas_features",
                "name": "Todas as Features",
                "description": "Conjunto completo de variáveis preditoras",
                "scientific_justification": "Cenário inicial de referência",
                "mode": "FIXED",
                "selected_features": ["x1", "x2"],
            }
        ],
        overwrite=force,
    )

    if task_upper == "REGRESSION":
        models_payload = [
            {
                "model_id": "baseline_media",
                "display_name": "Baseline Média",
                "family": "BASELINE",
                "estimator_factory": "DUMMY_BASELINE_MEAN",
                "parameters": {"strategy": "mean"},
                "capabilities": {"requires_fit": True},
                "description": "Preditor constante pela média do treino",
                "scientific_justification": "Referência mínima de regressão",
            },
            {
                "model_id": "baseline_mediana",
                "display_name": "Baseline Mediana",
                "family": "BASELINE",
                "estimator_factory": "DUMMY_BASELINE_MEDIAN",
                "parameters": {"strategy": "median"},
                "capabilities": {"requires_fit": True},
                "description": "Preditor constante pela mediana do treino",
                "scientific_justification": "Referência robusta a outliers",
            },
        ]
        part_strategy = "KFOLD"
        primary_metric = "rmse"
        metric_dir = "MINIMIZE"
    else:
        models_payload = [
            {
                "model_id": "baseline_majoritario",
                "display_name": "Baseline Majoritário",
                "family": "BASELINE",
                "estimator_factory": "DUMMY_BASELINE_MOST_FREQUENT",
                "parameters": {"strategy": "most_frequent"},
                "capabilities": {"requires_fit": True, "supports_predict_proba": True},
                "description": "Preditor pela classe mais frequente",
                "scientific_justification": "Referência mínima de classificação",
            }
        ]
        part_strategy = "STRATIFIED_KFOLD"
        primary_metric = "accuracy"
        metric_dir = "MAXIMIZE"

    write_json_atomic(out_dir / "models.json", models_payload, overwrite=force)
    write_json_atomic(
        out_dir / "partition.json",
        {
            "strategy": part_strategy,
            "regime": "CV_ONLY",
            "n_splits": 5,
            "master_seed": 42,
        },
        overwrite=force,
    )
    write_json_atomic(
        out_dir / "stats_config.json",
        {
            "metrics_of_interest": [primary_metric],
            "metric_directions": {primary_metric: metric_dir},
            "comparison_scope": "ALL_PAIRWISE",
            "alpha": 0.05,
        },
        overwrite=force,
    )

    sys.stdout.write(
        f"Projeto experimental inicializado em: {out_dir}\n"
        f"Arquivos criados: dados_exemplo.csv, schema.json, rules.json, scenarios.json, models.json, partition.json, stats_config.json\n\n"
        f"Próximo passo (execução rápida completa):\n"
        f"  expml quickrun --experiment-dir {out_dir}\n"
    )
    return 0


def handle_quickrun(args: argparse.Namespace) -> int:
    """Execute Stages 1-6 sequentially from an initialized experiment directory."""
    from experimental_ml.cli.cmd_data import handle_data_profile, handle_data_sanitize
    from experimental_ml.cli.cmd_features import (
        handle_features_explore,
        handle_features_scenarios,
    )
    from experimental_ml.cli.cmd_models import handle_models_validate
    from experimental_ml.cli.cmd_partition import handle_partition_build
    from experimental_ml.cli.cmd_report import handle_report_generate
    from experimental_ml.cli.cmd_run import handle_run_start
    from experimental_ml.cli.cmd_stats import handle_stats_run

    exp_dir = Path(args.experiment_dir).resolve()
    if not exp_dir.is_dir():
        raise ConfigurationError(f"Experiment directory not found at '{exp_dir}'")

    data_path = Path(args.data).resolve() if getattr(args, "data", None) else (exp_dir / "dados_exemplo.csv")
    schema_path = exp_dir / "schema.json"
    rules_path = exp_dir / "rules.json"
    scenarios_path = exp_dir / "scenarios.json"
    models_path = exp_dir / "models.json"
    part_path = exp_dir / "partition.json"
    stats_path = exp_dir / "stats_config.json"

    for req in (data_path, schema_path, scenarios_path, models_path, part_path):
        if not req.exists():
            raise ConfigurationError(
                f"Required file '{req.name}' not found in '{exp_dir}'. Run 'expml init --output-dir {exp_dir}' first."
            )

    force = bool(getattr(args, "force", True))
    sys.stdout.write(f"[1/6] Preparando e diagnosticando dados ({data_path.name})...\n")
    rc = handle_data_profile(
        argparse.Namespace(data=str(data_path), schema=str(schema_path), output_dir=str(exp_dir), force=force)
    )
    if rc != 0:
        return rc
    rc = handle_data_sanitize(
        argparse.Namespace(
            experiment_dir=str(exp_dir),
            rules=str(rules_path) if rules_path.exists() else None,
            force=force,
        )
    )
    if rc != 0:
        return rc

    sys.stdout.write("[2/6] Explorando e validando cenários de features...\n")
    rc = handle_features_explore(argparse.Namespace(experiment_dir=str(exp_dir), force=force))
    if rc != 0:
        return rc
    rc = handle_features_scenarios(
        argparse.Namespace(experiment_dir=str(exp_dir), scenarios=str(scenarios_path), force=force)
    )
    if rc != 0:
        return rc

    sys.stdout.write("[3/6] Validando catálogo de modelos...\n")
    rc = handle_models_validate(
        argparse.Namespace(experiment_dir=str(exp_dir), models=str(models_path), force=force)
    )
    if rc != 0:
        return rc

    sys.stdout.write("[4/6] Construindo partições e executando matriz experimental...\n")
    rc = handle_partition_build(
        argparse.Namespace(experiment_dir=str(exp_dir), config=str(part_path), seed=None, force=force)
    )
    if rc != 0:
        return rc
    rc = handle_run_start(
        argparse.Namespace(
            experiment_dir=str(exp_dir),
            run_dir=None,
            parallel=1,
            error_policy="fault_tolerant",
            no_oof=False,
            metrics=getattr(args, "metrics", None),
            force=force,
        )
    )
    if rc != 0:
        return rc

    sys.stdout.write("[5/6] Consolidando estatísticas e comparações...\n")
    rc = handle_stats_run(
        argparse.Namespace(
            experiment_dir=str(exp_dir),
            config=str(stats_path) if stats_path.exists() else None,
            force=force,
        )
    )
    if rc != 0:
        return rc

    sys.stdout.write("[6/6] Gerando relatórios científicos...\n")
    rc = handle_report_generate(
        argparse.Namespace(
            experiment_dir=str(exp_dir),
            output_dir=None,
            format="both",
            audience="FULL_LAB",
            families=None,
            objective=None,
            force=force,
        )
    )
    return rc
