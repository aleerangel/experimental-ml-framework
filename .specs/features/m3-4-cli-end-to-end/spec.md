# M3.4 — CLI de Features e Homologação Ponta a Ponta (m3-4-cli-end-to-end) Specification

**Approved**: 2026-11-10 - user: "aprovado"

## Problem Statement

Na arquitetura do `experimental-ml-framework`, a interface de linha de comando (`expml`) atua como camada de orquestração externa e interface de usuário sem acoplamento a regras de negócio (`ARQUITETURA §2.4`, `CLI-06` a `CLI-11`). 

Após a implementação dos motores de exploração (`explore_features`), validação e persistência de cenários (`FeatureScenario`, `validate_scenarios`, `save_scenarios`, `verify_scenarios_gate`) e seleção intra-fold com estabilidade (`select_features_in_fold`, `compute_selection_stability`) nos Sub-marcos M3.1, M3.2 e M3.3, é necessário disponibilizar os subcomandos oficiais da **Etapa 2 (Feature Engineering & Scenarios)**:
1. `expml features explore`: executa a análise exploratória de relações e redundâncias sobre a visão saneada da base (`SanitizedDatasetView`), salvando o relatório em `reports/exploratory_features.json` com rotulagem explícita `EXPLORATORY_FULL_DATA`.
2. `expml features scenarios`: valida um arquivo declarativo de cenários contra a visão saneada da base, garantindo conformidade com os papéis do esquema e ausência de vazamento de dados, persistindo `configuration/scenarios.json`.
3. `expml features verify`: executa a verificação formal do portão de validação de cenários (`verify_scenarios_gate`) para garantir que etapas subsequentes (como particionamento e ajuste de modelos) só iniciem sobre cenários válidos e consistentes com a base.

Adicionalmente, o Sub-marco M3.4 consolida a homologação integrada da Etapa 2:
- Cumprimento irrestrito da pureza arquitetural da CLI (`CLI-10`): ausência de importações transitivas de bibliotecas pesadas (`numpy`, `hashlib`) durante a carga inicial da CLI.
- Padronização rigorosa de códigos de saída (`0` para sucesso, `2` para argumentos inválidos ou erros de domínio/contrato, `1` para erros inesperados).
- Higiene e clareza da saída de terminal (`CLI-11`), evitando tracebacks não tratados e sem despejar hashes SHA-256 brutos de 64 caracteres em resumos de terminal.
- Homologação fim a fim por subprocesso integrando Etapa 1 e Etapa 2 em ambiente isolado.

## Out of Scope

Explicitamente excluído para manter isolamento e controle de escopo:

| Feature | Reason |
| --- | --- |
| Execução matricial de modelos em folds cruzados (`expml run`) | Pertence ao Marco M5 (`orchestration`) |
| Subcomando de modelos e buscas de hiperparâmetros (`expml models`) | Pertence ao Marco M4 (`models` / `tuning`) |
| Comparações estatísticas e testes pareados (`expml stats`) | Pertence ao Marco M6 (`statistics`) |
| Renderização de relatórios completos em HTML/PDF (`expml report`) | Pertence ao Marco M7 (`reporting`) |

---

## Assumptions & Open Questions

As premissas baseiam-se nos requisitos RF2.1, RF2.2, RF2.3, RF2.6, RNF07, RNF08, nas decisões de arquitetura (ADR-002, ADR-007, ADR-008) e nos contratos de CLI (`CLI-06` a `CLI-11`):

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Ponto de Entrada da CLI | O subcomando `features` é adicionado aos subparsers de `src/experimental_ml/cli/main.py`, despachando para `src/experimental_ml/cli/cmd_features.py`. | Mantém o padrão modular hierárquico estabelecido no M2.5 com `cmd_data.py` e `cmd_partition.py`. | y |
| Layout Canônico de Diretórios | `explore` lê `sanitized_view.json` e grava `reports/exploratory_features.json`; `scenarios` lê `sanitized_view.json` e grava `configuration/scenarios.json`. | Em conformidade estrita com o layout canônico de experimentos de `ARQUITETURA_E_CONTRATOS.md §4`. | y |
| Proteção contra Sobrescrita | Caso o artefato de destino já exista, os comandos recusam a sobrescrita a menos que o argumento `--force` seja explicitamente passado. | Previne perda acidental de relatórios ou configurações em experimentos em andamento (`CA-GER-01`). | y |
| Pureza de Runtime (CLI-10) | O módulo `cmd_features.py` é importado somente quando o comando `features` é ativado no despachante de `main.py`. | Garante que `expml --help` ou `expml --version` permaneça leve e sem importar `numpy` ou `hashlib`. | y |
| Tratamento de Erros e Saída | Exceções de domínio (`ExperimentalMLError`) são capturadas, exibindo mensagem amigável no `stderr` e retornando código `2`. | Cumpre a diretriz de usabilidade da CLI sem expor stack traces assustadores ao usuário. | y |

**Open questions:** none - os padrões e contratos da CLI já foram consolidados no Marco M2.5 e na revisão de integridade.

---

## User Stories

### P1: M3.4 — CLI de Features e Homologação Ponta a Ponta ⭐ MVP

**User Story**: Como pesquisador, quero explorar relações estatísticas da base e configurar catálogos de cenários de features através de subcomandos padronizados da CLI (`expml features explore`, `expml features scenarios`, `expml features verify`), com mensagens claras, ausência de tracebacks e validação rigorosa de portões de etapa, para operacionalizar a Etapa 2 de forma determinística e reproduzível.

**Why P1**: Conclui e homologa a Etapa 2 no nível de interface de usuário e automação, tornando acessíveis todas as capacidades construídas nos sub-marcos M3.1, M3.2 e M3.3.

**Acceptance Criteria**:

1. WHEN `expml features --help` is executed THEN the system SHALL display help for `explore`, `scenarios`, and `verify` subcommands and exit with code 0 (FEAT-01).

2. WHEN `expml features explore --experiment-dir <dir>` is executed on a valid experiment directory THEN the system SHALL reconstruct the sanitized dataset view, execute exploratory feature analysis, atomically save `reports/exploratory_features.json` with `scope = "EXPLORATORY_FULL_DATA"`, display summary metrics in stdout, and exit with code 0 (FEAT-02).

3. WHEN `expml features explore` is executed without `--force` and `reports/exploratory_features.json` already exists THEN the system SHALL exit with code 2 and a clear error message without overwriting the existing report (FEAT-03).

4. WHEN `expml features scenarios --experiment-dir <dir> --scenarios <file>` is executed with a valid scenario specification file THEN the system SHALL validate the scenarios against the sanitized dataset schema, atomically save `configuration/scenarios.json`, display confirmation in stdout, and exit with code 0 (FEAT-04).

5. WHEN `expml features scenarios` encounters invalid scenarios (such as nonexistent columns, target column leakage, or empty fixed features) THEN the system SHALL reject the configuration, display the validation error message on stderr without Python traceback, and exit with code 2 (FEAT-05).

6. WHEN `expml features verify --experiment-dir <dir>` is executed THEN the system SHALL verify the stage gate via `verify_scenarios_gate`, checking file existence, hash integrity, and scenario validity, exiting with code 0 on success or code 2 on gate violation (FEAT-06).

7. WHEN `expml` or `expml --help` or `expml --version` is invoked in a clean Python process THEN neither `numpy` nor `hashlib` SHALL be present in `sys.modules` (FEAT-07).

8. WHEN an end-to-end pipeline execution from data ingestion through feature scenarios is run via subprocess in an isolated directory THEN all stage gates SHALL pass with exit code 0 and generate exact, deterministic artifact structures (FEAT-08).

---

## Requirement Traceability

| Requirement ID | Description | Source / Rationale | Status |
| :--- | :--- | :--- | :--- |
| FEAT-01 | Ponto de entrada e comando de ajuda com subcomandos `explore`, `scenarios` e `verify` | CLI-06, CLI-07, RNF07 | in design |
| FEAT-02 | Execução de exploração de features e persistência atômica de `reports/exploratory_features.json` | RF2.1, CA-E2-01, CLI-08 | in design |
| FEAT-03 | Proteção contra sobreescrita acidental com exigência do argumento `--force` | CA-GER-01, CLI-09 | in design |
| FEAT-04 | Validação e gravação de catálogo de cenários via `expml features scenarios` | RF2.2, RF2.3, CA-E2-02 | in design |
| FEAT-05 | Rejeição sem traceback e código 2 para cenários inválidos ou vazamento de dados | RNF05, CLI-08, CLI-11 | in design |
| FEAT-06 | Subcomando `features verify` executando verificação de portão de etapa `verify_scenarios_gate` | CA-GER-01, ADR-002 | in design |
| FEAT-07 | Pureza de runtime sem importações transitivas de `numpy` ou `hashlib` em `sys.modules` | CLI-10, ADR-008 | in design |
| FEAT-08 | Homologação fim a fim por subprocesso em diretório isolado integrando Etapas 1 e 2 | CA02, RNF08 | in design |
