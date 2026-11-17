# Feature: pos-2b-notebooks-interativos

**Approved**: 2026-11-16 - user: "Vamos fazer isso agora"

## Problem Statement

Para consolidar a democratização da pesquisa científica para novos pesquisadores e alunos de Iniciação Científica (IC), o repositório necessita de **notebooks interativos (`.ipynb`)** executáveis em Jupyter, VS Code e Google Colab que demonstrem na prática o ciclo das 6 etapas, estudos de ablação, bloqueios anti-vazamento e análise desacoplada pós-experimento — preservando estritamente a pureza de runtime `XCUT-02` (sem adicionar `jupyter` ou `pandas`/`matplotlib` às dependências de runtime do pacote).

## Out of Scope

- Adição de dependências externas (`jupyter`, `nbformat`, `pandas`, `matplotlib`, `scikit-learn`) ao `dependencies` de runtime em `pyproject.toml`.
- Execução sobre bases de dados externas proprietárias (`CA02` / `TA-POS.3`).

## Assumptions & Open Questions

**Open questions:** none - o escopo dos 4 notebooks foi aprovado diretamente pelo usuário.

| Assumption / Question | Chosen default | Rationale |
| --- | --- | --- |
| Formato dos notebooks | JSON `nbformat` 4.5 gerado com stdlib `json`, células em português | Zero dependências extras no ambiente, compatível com JupyterLab, VS Code e Colab |
| Exibição visual inline | Helper `try: from IPython.display import display, SVG, HTML` com fallback `print()` | Funciona visualmente no Jupyter e executa em Python puro no `pytest` |
| Isolamento de diretório | Uso de `tempfile.TemporaryDirectory()` ou `Path.cwd()` isolado | Evita poluir o repositório durante execução interativa ou testes |

## User Stories

### US-NB-01 (Priority: P1) — Suíte de Testes Automatizados de Execução de Notebooks
As a maintainer,  
I want automated tests parsing and executing every code cell of all `.ipynb` notebooks in `notebooks/`,  
So that all interactive tutorials remain 100% functional and synchronized with the MVP codebase.

#### Acceptance Criteria
- **AC-NB-01-01**: WHEN running `tests/unit/test_notebooks_execution.py`, the test suite SHALL validate JSON `nbformat >= 4` schema and execute all code cells sequentially in an isolated `tmp_path` without errors or external runtime dependencies (`XCUT-02`).

---

### US-NB-02 (Priority: P1) — Quatro Notebooks Didáticos e Científicos em `notebooks/`
As a researcher or undergraduate student (IC),  
I want four self-contained interactive notebooks covering the 6 stages, LS-SVM ablation, group leakage prevention, and read-only post-experiment reporting,  
So that I can learn and adapt rigorous experimental workflows interactively.

#### Acceptance Criteria
- **AC-NB-02-01**: WHEN opening `notebooks/01_tour_6_etapas.ipynb`, the notebook SHALL walk interactively through all 6 official stages (`data`, `features`, `models`, `validation`/`orchestration`, `statistics`, `reporting`) on synthetic tabular data.
- **AC-NB-02-02**: WHEN opening `notebooks/02_ablacao_lssvm_prognose_florestal.ipynb`, the notebook SHALL execute an ablation study comparing LS-SVM Classical RBF, Quantum Kernel, and Quantum Solver on forest prognosis data with statistical comparison and Pareto analysis.
- **AC-NB-02-03**: WHEN opening `notebooks/03_validacao_agrupada_e_prevencao_leakage.ipynb`, the notebook SHALL demonstrate `GroupKFold` with `CV_AND_HOLDOUT` isolation and live demonstrations of stage gates blocking methodological errors.
- **AC-NB-02-04**: WHEN opening `notebooks/04_pos_experimento_relatorios_artigo.ipynb`, the notebook SHALL demonstrate read-only post-experiment loading (`load_experiment_artifacts_readonly`), LaTeX `booktabs` table export, SVG figure rendering, and `reduced_no_raw_data` packaging.
- **AC-NB-02-05**: WHEN inspecting `README.md` and `docs/README.md`, the documentation SHALL include direct navigation links to `notebooks/` while preserving `XCUT-02` runtime purity.

## Requirement Traceability

| Requirement ID | Acceptance Criteria | Target Component | Status |
| --- | --- | --- | --- |
| NB-01 | AC-NB-01-01 | `tests/unit/test_notebooks_execution.py` | verified |
| NB-02 | AC-NB-02-01, AC-NB-02-02, AC-NB-02-03, AC-NB-02-04, AC-NB-02-05 | `notebooks/*.ipynb`, `README.md`, `docs/README.md` | verified |
