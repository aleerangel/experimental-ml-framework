# POS-3 — Usabilidade e Acessibilidade Científica Design

**Spec**: `.specs/features/pos-3-usabilidade-acessibilidade-pesquisador/spec.md`  
**Status**: Pending Approval  

---

## 1. Visão Geral

O marco `pos-3-usabilidade-acessibilidade-pesquisador` adiciona uma camada ergonômica sobre os contratos M1–M7 sem alterar ou remover nenhuma função pura existente, preservando integralmente a pureza `XCUT-02` e o carregamento *lazy* da CLI (`CLI-10`).

---

## 2. Arquitetura das Intervenções

### 2.1 CLI Ergonomia (`src/experimental_ml/cli/`)
- **`cli/cmd_init.py` (`expml init`)**:
  - Opções: `--output-dir` (obrigatório), `--task {regression,binary_classification,multiclass_classification}` (padrão `regression`), `--force`.
  - Gera `<output-dir>/dados_exemplo.csv` e 6 templates JSON válidos (`schema.json`, `rules.json`, `scenarios.json`, `models.json`, `partition.json`, `stats_config.json`), imprimindo o roteiro dos próximos comandos.
- **`cli/cmd_data.py` (`data sanitize`)**:
  - `--rules` passa a ser opcional; se omitido e `profile` não tiver `CONFIRMED_ISSUE`, prossegue com `rules=[]`. Se houver `CONFIRMED_ISSUE` não tratado, falha com `ConfigurationError` orientando o formato de `rules.json`.
- **`cli/cmd_run.py` (`run start/status/verify/resume`)**:
  - `run start`: adiciona `--metrics METRICS [METRICS ...]` opcional (validando contra `METRICS_CATALOG` e usando defaults seguros apenas se omitido).
  - `run {status,verify,resume}`: aceitam `--experiment-dir` / `--exp-dir` (inferindo `<exp>/runs`) além de `--run-dir`.
- **`cli/cmd_report.py` (`report generate`)**:
  - Imprime os caminhos completos dos relatórios gerados e informa `expml report export` para gerar `tables/` e `figures/`.
- **Mensagens de erro orientadas à resolução**:
  - `cmd_data.py`, `cmd_models.py` e `cmd_features.py` exibem exemplo JSON mínimo esperado em erros de schema/campo ausente.

### 2.2 Fachada Python de Alto Nível (`src/experimental_ml/pipeline.py`)
- **`ExperimentRunSummary`** (`frozen=True, slots=True`) e **`run_experiment(...)`**:
  - Orquestra Etapas 1–6 (ingestão, saneamento, cenários, validação de modelos, particionamento, execução matricial, consolidação, comparação estatística, síntese, salvamento de artefatos estatísticos e relatório `MD`/`HTML`).
  - Exportada em `src/experimental_ml/__init__.py` via PEP 562 (`__getattr__`) para não impactar o tempo de importação da CLI (`CLI-10`).

### 2.3 Documentação por Jornadas (`docs/`)
- `docs/referencia/cli_schemas_json.md`: Schemas JSON completos da CLI e aliases de `resolve_estimator_factory`.
- `docs/guia/03_interpretando_resultados.md`: Guia prático de leitura de métricas, testes pareados, tamanho de efeito, Pareto e não-equivalência ($p \ge \alpha$).
- `docs/README.md`: Reorganizado pelas **5 Jornadas** (separando uso científico de engenharia interna).
