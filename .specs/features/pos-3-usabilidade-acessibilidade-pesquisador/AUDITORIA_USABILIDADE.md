# Auditoria de Usabilidade e Acessibilidade Científica (`TA-POS.3` — Diagnóstico)

**Data:** 2026-11-16  
**Escopo:** Fases 1, 2 e 3 da Auditoria Transversal de Usabilidade do `experimental-ml` (MVP M1–M7)  
**Princípio Avaliado:** *O pesquisador não deve precisar compreender a arquitetura interna do framework para conseguir conduzir um experimento.*

---

## 1. Resumo Executivo e Veredito do Diagnóstico

O framework `experimental-ml` entrega rigor científico e pureza arquitetural elevados, mas **atualmente exige conhecimento avançado da arquitetura interna e de contratos de serialização para ser operado do início ao fim**, especialmente pela interface de linha de comando (`expml`) e pela API Python modularizada.

O teste real de utilização (Fase 2) demonstrou que **é possível concluir um experimento completo de regressão ponta a ponta pelos meios públicos**, porém **não sem antes consultar o código-fonte interno** (`cmd_*.py`, `catalog.py`, `codecs.py`, `types.py`) para descobrir o formato dos 5–6 arquivos JSON exigidos pela CLI ou as mais de 25 importações de 8 subpacotes na API Python.

---

## 2. Fase 1 — Matriz de Dificuldades no Fluxo de 10 Passos

| # | Passo Investigado | Componente / Arquivo | Conhecimento Prévio Exigido | Motivo da Dificuldade | Consequência para o Pesquisador | Sev. | Tipo | Solução Proposta |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| 1 | Instalar e preparar ambiente | `README.md`, `pyproject.toml` | `venv`, `pip install -e .` | Fluxo funcional e enxuto; exige apenas Python >= 3.10 e NumPy. | Baixa barreira inicial de instalação. | `P2` | Doc | Manter e destacar passo único para `venv` + `pip`. |
| 2 | Identificar ponto de entrada | `expml --help`, `README.md` | Diferença entre 7 subcomandos CLI e 11 pacotes Python | Não há comando orientador nem escolha guiada entre CLI (config JSON) vs. Python (experimento programático). | Hesitação inicial sobre qual interface usar. | `P1` | CLI / Doc | Criar `expml init` / guia de decisão CLI vs. Python. |
| 3 | Iniciar projeto experimental | `cli/main.py` | Estrutura de pastas do experimento | Inexistência de `expml init` para gerar estrutura inicial e templates JSON válidos. | Usuário precisa criar diretórios e JSONs manualmente do zero. | `P0` | Ausência de func. | Implementar `expml init` gerando templates comentados/prontos. |
| 4 | Fornecer conjunto de dados e alvo | `cli/cmd_data.py` | Estrutura JSON de `DatasetSchemaSpec` (`target_col`, `task_type` em MAIÚSCULAS) | `--help` diz apenas `Path to schema JSON file.`; sem `rules.json` (mesmo `[]`), `data sanitize` bloqueia o pipeline mesmo com 0 achados no `profile`. | Erro imediato na primeira etapa; etapa extra redundante quando não há problemas. | `P0` | CLI / Config | Documentar schema JSON, aceitar flags diretas opcionais (`--target`, `--task`) ou auto-sanitizar sem achados. |
| 5 | Selecionar modelos e features | `cli/cmd_models.py`, `models/catalog.py`, `cli/cmd_features.py` | Chaves exatas de `models.json` (`estimator_factory`, `family`, `capabilities`), identificadores `DUMMY_BASELINE_MEAN` ou `"mod:Cls"` | O erro `Missing required field 'estimator_factory'` não mostra exemplo válido; `scenarios.json` exige 6 campos obrigatórios (`scientific_justification`, `description`, etc.) mesmo em testes rápidos. | Pesquisador trava ao registrar modelos ou cenários pela CLI sem ler `catalog.py`. | `P0` | CLI / Erro / Doc | Melhorar mensagens de erro com exemplo JSON mínimo e fornecer templates em `expml init`. |
| 6 | Configurar particionamento | `cli/cmd_partition.py` | Chaves de `PartitionConfig` (`strategy`, `regime`, `n_splits`) | `--config` exige JSON separado; valores de enum em caixa alta (`KFOLD`, `CV_ONLY`) não aparecem no `--help`. | Tentativa e erro repetida até acertar nomes exatos das enums. | `P1` | CLI / Doc | Exibir opções válidas no `--help` e incluir `partition.json` no `expml init`. |
| 7 | Executar experimentos e escolher métricas | `cli/cmd_run.py` | Nenhuma opção CLI para métricas | `cmd_run.py` fixa `default_metrics = ("rmse", "mae", "r2")` (regressão) ou `("accuracy", "balanced_accuracy", "f1")` sem permitir `--metrics` na CLI. | Impossível avaliar `rmse_rel_pct`, `mbe`, `roc_auc` ou `log_loss` pela CLI; força migração para Python. | `P0` | CLI / Ausência de func. | Adicionar `--metrics` opcional em `expml run start` (preservando defaults seguros). |
| 8 | Acompanhar execução e falhas | `cli/main.py`, `cli/cmd_run.py` | Diferença entre `--experiment-dir` e `--run-dir` | `data`, `features`, `models`, `partition`, `stats`, `report` usam `--experiment-dir` (ou `--output-dir`), enquanto `run status/verify/resume` exigem `--run-dir`. | Erro de argumento ao tentar inspecionar `run status --experiment-dir exp`. | `P1` | CLI / Nomenclatura | Aceitar `--experiment-dir` em `run status/verify/resume` (inferindo `<exp>/runs`). |
| 9 | Orquestrar em Python (API) | `experimental_ml.*` | 8 subpacotes diferentes (`data`, `features`, `models`, `validation`, `orchestration`, `statistics`, `reporting`, `core`) | Pesquisador precisa montar manualmente cola entre etapas (`[load_cell_artifacts(cid, ...) for cid in ...]`, `save_statistics_artifacts(...)`). | Código verboso (~70 linhas de cola) antes de rodar um benchmark simples. | `P0` | Arquitetura de uso | Criar fachada opcional de alto nível (ex.: `run_experiment(...)`) sem remover as funções puras. |
| 10 | Localizar e interpretar resultados | `cli/cmd_report.py`, `reporting/report.py` | Diferença entre `report generate` e `report export` | `report generate` não imprime o caminho completo gerado e não gera `tables/`/`figures/`; `report.md` traz `Task Type: N/A` e não explica `SD`, `IQR`, `Coverage` ou valor-$p$ ajustado. | Pesquisador não encontra tabelas LaTeX/figuras SVG após `report generate` e tem dificuldade para interpretar métricas estatísticas. | `P1` | CLI / Resultados | Exibir caminhos completos gerados, explicar `report generate` vs `export` e adicionar glossário interpretativo ao relatório. |

---

## 3. Fase 2 — Relatório do Teste de Utilização Real (Ponta a Ponta)

**Cenário testado:** Regressão tabular sintética (`30 amostras`, `x1, x2 -> y`), 2 modelos comparáveis (`DummyBaselineModel(strategy="mean")` e `DummyBaselineModel(strategy="median")`), validação `KFOLD` ($K=5$), execução via CLI `expml`, estatística e relatório.

### Evidências Observadas Durante o Experimento Real
1. **`expml data profile`**: Executou (`exit 0`) apenas após criação manual de `schema.json` com `{"target_col": "y", "task_type": "REGRESSION"}`.
2. **`expml data sanitize`**: Mesmo com `No diagnostic findings identified`, exigiu criação manual de `rules.json` (`[]`) para desbloquear o portão da Etapa 1.
3. **`expml features explore` e `scenarios`**: Executaram (`exit 0`) com `scenarios.json` contendo todos os campos obrigatórios de `FeatureScenario`.
4. **`expml models validate`**: Falhou na primeira tentativa (`exit 2`: `Error: Missing required field 'estimator_factory' in model spec`) porque o usuário não tem documentação indicando que a chave JSON é `"estimator_factory"` (e não `"estimator_factory_ref"`) nem os aliases embutidos (`DUMMY_BASELINE_MEAN`, etc.) descobertos apenas lendo `src/experimental_ml/models/catalog.py:72-88`. Com a chave correta, concluiu (`exit 0`).
5. **`expml partition build` e `expml run start`**: Executaram (`exit 0`, `10/10` células). Porém, `cmd_run.py:83-87` impôs `("rmse", "mae", "r2")` sem oferecer forma de selecionar métricas via CLI.
6. **`expml stats run` e `expml report generate`**: Executaram (`exit 0`). `report generate` imprimiu JSON `{"files": ["report.md", "report.html"]}` sem informar o diretório completo e sem gerar `tables/` ou `figures/`. Em `exp/reports/report.md`, a seção `1. Researcher Declarations` veio vazia, `Task Type` apareceu como `N/A` na tabela de modelos e não houve explicação textual das siglas estatísticas (`SD`, `IQR`, `Coverage`).

---

## 4. Fase 3 — Avaliação Qualitativa da Experiência de Utilização

| Dimensão | Avaliação Atual | Justificativa Baseada em Evidências |
| :--- | :---: | :--- |
| **Entrada e orientação** | **Insuficiente** | Falta `expml init`, não há indicação de próximo passo ao final de cada comando CLI e a escolha entre CLI vs. API Python não é guiada na entrada. |
| **Configuração** | **Fragmentada** | Exige 5–6 arquivos JSON distintos na CLI sem documentação de seus schemas; mensagens de erro de validação não mostram exemplos de correção. |
| **Execução** | **Funcional, mas assimétrica** | Checkpoint/resume e `FAULT_TOLERANT` são sólidos, mas `expml run` usa `--run-dir` enquanto o resto da CLI usa `--experiment-dir`, e faltam opções de métricas na CLI. |
| **Resultados** | **Parcialmente interpretável** | `report.md` lista tabelas limpas, mas omite glossário de métricas/estatísticas, `report generate` não gera tabelas/figuras separadas e `Task Type` exibe `N/A`. |
| **Documentação** | **Rica em referência, carente em jornada** | Os guias recém-criados em `docs/` e `notebooks/` cobrem bem o Python, mas não cobrem os **schemas JSON exatos da CLI** nem guiam por jornadas progressivas de pesquisador. |
