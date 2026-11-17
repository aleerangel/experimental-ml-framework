# POS-3 Results — `pos-3-usabilidade-acessibilidade-pesquisador`

## Summary

- **CLI Ergonomia (`src/experimental_ml/cli/cmd_init.py`, `main.py`, `cmd_data.py`, `cmd_run.py`, `cmd_report.py`)**:
  - `expml init --output-dir <dir>` cria projeto pronto (`dados_exemplo.csv` e 6 JSONs válidos) e `expml quickrun --experiment-dir <dir>` executa Etapas 1–6 sequencialmente.
  - `--rules` opcional em `expml data sanitize` quando sem achados confirmados; `--metrics` em `expml run start`; `--experiment-dir` em `expml run {status,verify,resume}`; caminhos completos no `expml report generate` e mensagens orientadas à resolução.
- **Fachada Python de Alto Nível (`src/experimental_ml/pipeline.py`, `__init__.py`)**:
  - `experimental_ml.run_experiment(...)` aceita tanto entradas simples de ML (`data`, `target`, `task`, `models={"Nome": estimador}`) quanto especificações formais (`ModelSpec`, `DatasetSchemaSpec`, `FeatureScenario`, `PartitionConfig`), mantendo `CLI-10` via PEP 562 (`__getattr__`) e pureza `XCUT-02`.
- **Documentação por 5 Jornadas (`docs/`)**:
  - Criados `docs/guia/00_comecando_do_zero.md`, `docs/guia/03_interpretando_resultados.md`, `docs/referencia/cli_schemas_json.md`, e reorganizado `docs/README.md` pelas 5 Jornadas.

## Verification

- `check_proofs.py pos-3-usabilidade-acessibilidade-pesquisador`: **3 pass, 0 fail** (`HEAD: c32004c`)
- `.venv/bin/pytest tests/ -q`: **598 passed in 17.75s**
- `verification.md`: **PASS** (`Independent Verifier 7f98d020-9c01-41a2-a550-0e1651d63782`)
