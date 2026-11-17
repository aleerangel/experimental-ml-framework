# POS-2B Results — `pos-2b-notebooks-interativos`

## Summary

- **4 Notebooks Interativos (`notebooks/*.ipynb`, `nbformat 4.5`)**:
  - `01_tour_6_etapas.ipynb`: Tour interativo completo pelas 6 etapas oficiais.
  - `02_ablacao_lssvm_prognose_florestal.ipynb`: Estudo de ablação LS-SVM (Clássico RBF, Kernel Quântico e Solver Quântico) em prognose florestal com Fronteira de Pareto.
  - `03_validacao_agrupada_e_prevencao_leakage.ipynb`: `GroupKFold` com `CV_AND_HOLDOUT` e demonstrações ao vivo de bloqueios metodológicos.
  - `04_pos_experimento_relatorios_artigo.ipynb`: Leitura somente-leitura, tabelas LaTeX `booktabs`, figuras SVG inline e pacote `reduced_no_raw_data`.
- **Testes Automatizados (`tests/unit/test_notebooks_execution.py`)**: Validação de esquema, pureza AST `XCUT-02` e execução sequencial de 100% das células em `tmp_path`.

## Verification

- `check_proofs.py pos-2b-notebooks-interativos`: **2 pass, 0 fail** (`HEAD: 03f657f`)
- `.venv/bin/pytest tests/ -q`: **596 passed in 17.68s**
- `verification.md`: **PASS** (`Independent Verifier 6e87c763-608d-414a-b2fc-d5918eab25f1`)
