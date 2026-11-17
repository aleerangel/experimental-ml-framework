# Feature: pos-2-guia-pesquisador-cookbook

**Approved**: 2026-11-16 - user: "pode avancar entao"

## Problem Statement

Com o encerramento e homologação da Mega Auditoria Técnica Transversal do MVP (`TA-POS.1` / `pos-1-mega-auditoria-mvp`), o framework `experimental-ml` atingiu estabilidade funcional plena e congelamento de código (591 testes passando, 0 achados P0/P1 abertos, pureza runtime `XCUT-02`). 

O plano de engenharia (`ARQUITETURA_E_CONTRATOS.md` Seção 7 `TA-POS.2`, `ETAPA_ATUAL_ENGENHARIA.md`) e a diretriz explícita do usuário estabelecem a entrega do **Guia Definitivo do Pesquisador, Scientific Cookbook, Catálogo de Referência de APIs/CLI e Limpeza Estrutural do README.md (`TA-POS.2`)**.

Atualmente:
1. O repositório não possui um diretório `docs/` estruturado para pesquisadores e cientistas de dados experimentais.
2. O `README.md` principal na raiz encontra-se sobrecarregado com trechos extensos de código de implementação e detalhes profundos de requisitos/engenharia, em vez de atuar como uma landing page executiva equilibrada com comandos concisos e ponteiros diretos para a documentação técnica especializada.
3. Não existem receitas práticas ("Cookbook") demonstrando como executar os casos experimentais mais sensíveis da literatura científica (modelos analíticos sem ajuste, métricas de kernel quântico, validação agrupada longitudinal anti-leakage, fronteira de Pareto multiobjetivo e pacotes herméticos para conferências).

Para solucionar essa lacuna metodológica, `TA-POS.2` deve estruturar uma base pedagógica completa e navegável em subpastas organizadas sob `docs/`, acompanhada de uma versão enxuta e equilibrada do `README.md` e validada por testes automatizados em múltiplos níveis de integridade documental (links relativos, sintaxe Python, imports reais da API pública, validação léxica de comandos CLI e smoke tests executáveis).

## Out of Scope

- Implementação de novas funcionalidades de código de Machine Learning ou Onda 2 (`MULTI_TARGET_REGRESSION`, `TargetTransformSpec`, `unlabeled_pool`, `PCA`, `BootstrapSplit`, `TemporalSplit`).
- Homologação científica empírica externa em dados proprietários do usuário (`TA-POS.3` / `CA02`), que é de condução exclusiva do pesquisador.
- Instalação de geradores pesados de documentação estática externa (Sphinx, MkDocs, Docusaurus) que violem a pureza `XCUT-02` e o ambiente hermético do projeto; a documentação deve ser Markdown padrão GFM puro com KaTeX e diagramas Mermaid nativos.
- Documentação de módulos internos de baixo nível (ex.: codecs de serialização `orchestration.codecs`, parsers auxiliares ou funções privadas iniciadas por `_`) como contratos públicos estáveis.

## Assumptions & Open Questions

**Open questions:** none - todas as decisões de design foram respondidas diretamente pelo usuário na sessão de alinhamento e verificadas tecnicamente contra o MVP:
1. Idioma: Português integralmente, alinhado aos documentos de engenharia e commits do projeto, mantendo termos técnicos consagrados da literatura científica.
2. Estrutura de diretórios: Subpastas temáticas organizadas sob `docs/` (`docs/guia/`, `docs/cookbook/`, `docs/referencia/`) com um índice central unificador `docs/README.md`.
3. Casos práticos do Cookbook: Todos os 5 cenários selecionados (modelos analíticos sem fit vs treinados, métricas quânticas KTA/probabilísticas, validação agrupada GroupKFold anti-leakage, otimização Pareto multiobjetivo, pacotes herméticos de reprodutibilidade para conferências).
4. Estilo do README.md: Equilibrado com breve fluxo de CLI de 1 linha, badges, breve proposta de valor e tabela completa de navegação direta para `docs/`, `engenharia_software/` e `REFERENCIAS_E_FUNDAMENTACAO.md`.

| Assumption / Question | Chosen default | Rationale |
| --- | --- | --- |
| Divisão oficial das etapas metodológicas | Exatamente 6 etapas metodológicas: E1 (Dados), E2 (Features), E3 (Modelos/Tuning), E4 (Particionamento 4A e Execução Matricial 4B), E5 (Estatística), E6 (Relatórios/Reprodutibilidade) | Alinhado estritamente à Seção 3 de `ARQUITETURA_E_CONTRATOS.md` e aos módulos em `src/experimental_ml/` |
| Delimitação da API Python pública | Símbolos e dataclasses exportados nos `__init__.py` de nível superior dos 11 pacotes (`core`, `data`, `metrics`, `features`, `models`, `tuning`, `validation`, `orchestration`, `statistics`, `reporting`, `stages`) | Evita omissão de `validation`/`metrics` e impede que detalhes internos (`codecs`, helpers privados) sejam documentados como contratos |
| Contrato de códigos de saída da CLI `expml` | `0`: Sucesso; `1`: Erro inesperado de sistema/runtime; `2`: Erro semântico, violação de contrato/dados ou reprovação em portão de estágio | Reflete a implementação real em `cli.main` e subcomandos, onde `ExperimentalMLError` e falhas de validação/gate retornam `2` |
| Verificação em níveis de integridade documental | Teste automatizado com 5 níveis: (1) Links relativos e âncoras; (2) Sintaxe AST; (3) Resolução de imports públicos; (4) Validação de subcomandos CLI; (5) Smoke test executável do Quickstart | Garante robustez sem confundir blocos conceituais/pseudocódigo com scripts executáveis de ponta a ponta |
| Cobertura do Scientific Cookbook | 5 receitas científicas completas e auto-contidas suportadas pelo framework | Cobre todos os diferenciais metodológicos selecionados pelo pesquisador |

## User Stories

### US-POS2-01 (Priority: P1) — Estrutura de Documentação e Índice Unificador em docs/
As an experimental ML researcher,  
I want a unified documentation hub under `docs/README.md` organizing guides, cookbooks, and reference catalogs in Portuguese with direct navigation links,  
So that I can quickly orient myself across the framework's pedagogical resources without hunting through scattered files.

#### Acceptance Criteria
- **AC-POS2-01-01**: WHEN navigating `docs/README.md`, the documentation SHALL present a complete pedagogical overview in Portuguese, explaining the learning path (Quickstart -> 6-Stage Tutorial -> Scientific Cookbook -> Reference Catalog) with direct relative Markdown links to all sub-documents in `docs/guia/`, `docs/cookbook/`, and `docs/referencia/`.
- **AC-POS2-01-02**: WHERE any cross-document reference or external link is cited, the documentation SHALL use valid relative file links conforming to repository structure without dead links or missing anchors.

---

### US-POS2-02 (Priority: P1) — Guia do Pesquisador: Início Rápido e Tutorial das 6 Etapas
As a researcher starting an experimental benchmark,  
I want a 5-step quickstart guide and a comprehensive 6-stage methodological tutorial,  
So that I can learn how to execute a sound scientific experiment from data preparation to reproducible reporting with full theoretical grounding.

#### Acceptance Criteria
- **AC-POS2-02-01**: WHEN reading `docs/guia/01_inicio_rapido.md`, the guide SHALL provide an end-to-end quickstart in at most 5 operational steps (instalação, preparação, particionamento, execução e relatório) utilizing minimal 1-line CLI commands and reproducible Python snippets.
- **AC-POS2-02-02**: WHEN consulting `docs/guia/02_tutorial_6_etapas.md`, the guide SHALL explain step-by-step each of the 6 official methodology stages (Etapa 1: Entrada, Triagem e Diagnóstico Estrutural; Etapa 2: Exploração de Relações e Cenários de Features; Etapa 3: Registro de Modelos, Pré-processamento e Nested Tuning; Etapa 4: Particionamento, Validação e Execução Matricial, abrangendo 4A Particionamento Compartilhado e 4B Execução Matricial Tolerante a Falhas; Etapa 5: Consolidação dos Resultados e Comparação Estatística Rigorosa com Nadeau-Bengio e Wilcoxon; Etapa 6: Relatórios Científicos, Visualizações e Pacote de Reprodutibilidade), highlighting anti-leakage guarantees, stage gate validations, and formal mathematical formulations.

---

### US-POS2-03 (Priority: P1) — Scientific Cookbook com Receitas Metodológicas Avançadas
As an experimental researcher facing complex study designs,  
I want self-contained practical recipes for advanced scientific scenarios,  
So that I can apply rigorous protocols to non-trivial models, custom metrics, grouped data, multi-objective trade-offs, and conference submissions.

#### Acceptance Criteria
- **AC-POS2-03-01**: WHEN consulting `docs/cookbook/01_modelos_analiticos_vs_treinados.md`, the cookbook SHALL provide complete code examples and CLI workflows contrasting analytical/biometric models without fitting (`requires_fit=False`) against standard parametric trained models, documenting parameter persistence and fresh instantiation guarantees (`instantiate_fresh_model`).
- **AC-POS2-03-02**: WHEN consulting `docs/cookbook/02_metricas_quanticas_e_probabilisticas.md`, the cookbook SHALL detail how to evaluate quantum or precomputed kernel alignment metrics (KTA with `requires_kernel_matrix=True`) and probabilistic metrics (ROC-AUC, Log-Loss with `requires_probabilities=True`), explaining the passage of kernel matrices via `PrecomputedKernelAdapter` and continuous probability vectors via `y_proba`.
- **AC-POS2-03-03**: WHEN consulting `docs/cookbook/03_validacao_cruzada_agrupada_holdout.md`, the cookbook SHALL demonstrate group-aware cross-validation (`GroupKFold`) with strict holdout set isolation (`CV_AND_HOLDOUT`), demonstrating the mathematical guarantees of disjoint group partitions between folds and between development and holdout sets.
- **AC-POS2-03-04**: WHEN consulting `docs/cookbook/04_otimizacao_pareto_multiobjetivo.md`, the cookbook SHALL demonstrate multi-objective optimization across the Pareto frontier over configurations with `CoverageStatus.VALID`, detailing the supported objective sources (aggregated metrics, inference latency timing, and feature stability Jaccard) and explicit exclusion handling.
- **AC-POS2-03-05**: WHEN consulting `docs/cookbook/05_pacotes_reprodutibilidade_conferencias.md`, the cookbook SHALL provide the protocol for building and validating hermetic reproducibility packages (`FULL_PACKAGE` and `REDUCED_NO_RAW_DATA`) with SHA-256 relative checksum audits (`checksums.sha256`) for paper submission to scientific conferences.

---

### US-POS2-04 (Priority: P1) — Catálogo de Referência Completo de APIs Python e CLI
As a developer or scientific maintainer,  
I want complete and structured reference catalogs for all Python public APIs and CLI commands,  
So that I can accurately look up function signatures, dataclasses, CLI arguments, exit codes, and stage gate invariants.

#### Acceptance Criteria
- **AC-POS2-04-01**: WHEN reading `docs/referencia/api_python.md`, the reference SHALL catalog the public API across all 11 framework packages (`core`, `data`, `metrics`, `features`, `models`, `tuning`, `validation`, `orchestration`, `statistics`, `reporting`, `stages`) as exported in their top-level `__init__.py` and `__all__`, documenting signatures, types, invariants, and exception behavior while explicitly omitting internal implementation modules.
- **AC-POS2-04-02**: WHEN reading `docs/referencia/cli_catalogo.md`, the reference SHALL exhaustively catalog all `expml` commands (`data`, `partition`, `features`, `models`, `run`, `stats`, `report`), listing arguments, options, input contracts, exit codes (0: sucesso, 1: erro inesperado de sistema, 2: erro semântico, violação de contrato/dados ou reprovação em portão de estágio), and produced artifacts.

---

### US-POS2-05 (Priority: P1) — Limpeza e Reestruturação Equilibrada do README.md
As a visitor or new user exploring the repository,  
I want a clean, balanced, and uncluttered `README.md` on the root,  
So that I can understand the framework's purpose, install it quickly, run basic CLI commands, and immediately find direct pointers to specialized documentation without cognitive overload.

#### Acceptance Criteria
- **AC-POS2-05-01**: WHEN inspecting `README.md`, the document SHALL present an executive, balanced overview containing badges, value proposition, a 1-line installation snippet, a concise 1-line CLI workflow summary, and a clear markdown navigation table pointing directly to `docs/README.md`, `engenharia_software/`, and `REFERENCIAS_E_FUNDAMENTACAO.md`.
- **AC-POS2-05-02**: WHEN inspecting `README.md`, the document SHALL NOT contain long code implementation examples, extensive requirements lists, or raw hex hashes, keeping the text concise and focused.

---

### US-POS2-06 (Priority: P1) — Testes Automatizados de Integridade Documental e Governança
As a project maintainer,  
I want automated multi-tiered tests validating documentation integrity, link validity, API import correctness, CLI lexical conformance, and smoke test execution,  
So that the published documentation remains in strict sync with codebase reality and passes all workspace governance rules.

#### Acceptance Criteria
- **AC-POS2-06-01**: WHEN running automated test suites, the test suite SHALL verify documentation integrity across five distinct levels: (1) valid relative markdown links and anchors; (2) syntactic AST validity of all Python code blocks (ignoring blocks explicitly marked as conceptual); (3) static AST resolution confirming that all symbols imported from `experimental_ml.*` exist in the public API; (4) lexical validation of CLI commands in shell blocks against real `expml` subcommands; and (5) end-to-end execution of snippets marked as executable smoke tests.
- **AC-POS2-06-02**: WHEN inspecting repository files and git commit history, the system SHALL adhere strictly to Portuguese commit messages (`docs(...)`, `chore(...)`, `test(...)`), runtime purity `XCUT-02`, and zero citations of `GEMINI.md`.

## Requirement Traceability

| Requirement ID | Acceptance Criteria | Target Component | Status |
| --- | --- | --- | --- |
| DOC-01 | AC-POS2-01-01, AC-POS2-01-02 | `docs/README.md` | verified |
| DOC-02 | AC-POS2-02-01, AC-POS2-02-02 | `docs/guia/01_inicio_rapido.md`, `docs/guia/02_tutorial_6_etapas.md` | verified |
| DOC-03 | AC-POS2-03-01, AC-POS2-03-02, AC-POS2-03-03, AC-POS2-03-04, AC-POS2-03-05 | `docs/cookbook/*.md` | verified |
| DOC-04 | AC-POS2-04-01, AC-POS2-04-02 | `docs/referencia/api_python.md`, `docs/referencia/cli_catalogo.md` | verified |
| DOC-05 | AC-POS2-05-01, AC-POS2-05-02 | `README.md` | verified |
| DOC-06 | AC-POS2-06-01, AC-POS2-06-02 | `tests/unit/test_documentation_integrity.py` | verified |
