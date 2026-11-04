# Registro de Validação e Aceite — Marco M1.3

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M1.3 (`m1-3-metrics`)  
> **Data de Validação:** 03 de Novembro de 2026  
> **Commit de Implementação:** [`002fa9a`](https://github.com/alexandrerangel/experimental-ml-framework/commit/002fa9a)  
> **Ambiente Computacional:** Linux 6.17.5-arch1-1 (x86_64), Python 3.12.15, NumPy 2.5.4, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | `pip install -e ".[dev]"` com NumPy | Instalado e validado (`numpy 2.5.4`) | **APROVADO** |
| **Testes Unitários Automatizados** | 22 testes em `tests/unit/test_metrics.py` | 22 testes aprovados (100%) | **APROVADO** |
| **Testes de Regressão Geral** | 52 testes em `pytest tests/` | 52 testes aprovados (100%) | **APROVADO** |
| **Verificação Independente TLC** | `validate_verification.py` e auditoria | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Homologação Manual** | Roteiro `ACCEPTANCE.md` (5 itens + cenário integrado) | Executada e aprovada conforme roteiro | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Suíte Unitária do Módulo Metrics (`tests/unit/test_metrics.py`)

Execução realizada no interpretador do ambiente virtual (`.venv/bin/pytest tests/unit/test_metrics.py -v`):

```text
============================= test session starts ==============================
platform linux -- Python 3.12.15, pytest-9.2.0, pluggy-1.7.0 -- /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework
configfile: pyproject.toml
collecting ... collected 22 items

tests/unit/test_metrics.py::test_direct_scale_errors_accuracy PASSED     [  4%]
tests/unit/test_metrics.py::test_mbe_preserves_signed_value PASSED       [  9%]
tests/unit/test_metrics.py::test_rmse_scale_homoscedasticity PASSED      [ 13%]
tests/unit/test_metrics.py::test_metric_structures_immutable PASSED      [ 18%]
tests/unit/test_metrics.py::test_metric_evaluation_scope_validation PASSED [ 22%]
tests/unit/test_metrics.py::test_array_validation_dimensions PASSED      [ 27%]
tests/unit/test_metrics.py::test_array_validation_non_finites PASSED     [ 31%]
tests/unit/test_metrics.py::test_numerical_stability_and_overflow PASSED [ 36%]
tests/unit/test_metrics.py::test_dimensionless_ratios_accuracy PASSED    [ 40%]
tests/unit/test_metrics.py::test_r2_and_pearson_zero_variance PASSED     [ 45%]
tests/unit/test_metrics.py::test_rmse_rel_pct_and_mape_degenerate PASSED [ 50%]
tests/unit/test_metrics.py::test_kta_centered_and_uncentered PASSED      [ 54%]
tests/unit/test_metrics.py::test_discrete_classification_accuracy PASSED [ 59%]
tests/unit/test_metrics.py::test_precision_division_by_zero_rules PASSED [ 63%]
tests/unit/test_metrics.py::test_recall_and_balanced_accuracy_rules PASSED [ 68%]
tests/unit/test_metrics.py::test_f1_own_denominator_rules PASSED         [ 72%]
tests/unit/test_metrics.py::test_roc_auc_ties_and_ovr PASSED             [ 77%]
tests/unit/test_metrics.py::test_log_loss_validation_and_clipping PASSED [ 81%]
tests/unit/test_metrics.py::test_metrics_catalog_registration PASSED     [ 86%]
tests/unit/test_metrics.py::test_catalog_query_and_dispatch PASSED       [ 90%]
tests/unit/test_metrics.py::test_is_better_adr005_rules PASSED           [ 95%]
tests/unit/test_metrics.py::test_aggregate_and_rank_configurations PASSED [100%]

============================== 22 passed in 0.08s ==============================
```

- **Evidência Mecânica Registrada:** Arquivo [`.specs/features/m1-3-metrics/proofs.md`](./proofs.md).

### 2.2 Relatório do Verificador Independente TLC

- **Arquivo:** [`.specs/features/m1-3-metrics/verification.md`](./verification.md).
- **Veredito:** `PASS` (`author != verifier`).
- **Validação de Portão:** `python3 .agent/skills/tlc-spec-driven/scripts/validate_verification.py m1-3-metrics` finalizado com **0 erros e 0 avisos**.

---

## 3. Verificações Manuais de Aceitação do Consumidor

| Verificação do Roteiro ACCEPTANCE.md | Evidência Existente | Status |
| :--- | :--- | :---: |
| 2.1 Estruturas imutáveis, escopos e catálogo | Coberto por `test_metric_structures_immutable`, `test_metric_evaluation_scope_validation`, `test_metrics_catalog_registration` | **Comprovado por Automação** |
| 2.2 Métricas de regressão e alinhamento | Coberto por `test_direct_scale_errors_accuracy`, `test_mbe_preserves_signed_value`, `test_dimensionless_ratios_accuracy`, `test_kta_centered_and_uncentered` | **Comprovado por Automação** |
| 2.3 Métricas de classificação discreta | Coberto por `test_discrete_classification_accuracy`, `test_precision_division_by_zero_rules`, `test_recall_and_balanced_accuracy_rules`, `test_f1_own_denominator_rules` | **Comprovado por Automação** |
| 2.4 Métricas probabilísticas e ranqueamento | Coberto por `test_roc_auc_ties_and_ovr`, `test_log_loss_validation_and_clipping` | **Comprovado por Automação** |
| 2.5 Comparação, agregação e ranqueamento | Coberto por `test_is_better_adr005_rules`, `test_aggregate_and_rank_configurations` | **Comprovado por Automação** |
| 3. Cenário integrado de ML | Executado com sucesso via script de aceitação | **APROVADO** |
| Homologação manual do roteiro | Executada e confirmada sem divergências | **APROVADO** |

---

## 4. Problemas e Defeitos Encontrados

- **Problemas Detectados:** Nenhum defeito funcional ou quebra de contrato identificada.
- **Conformidade Arquitetural:** 100% de conformidade com ADR-002 (modularidade funcional), ADR-005 (governança de agregação e ranqueamento lexicográfico), ADR-007 (determinismo e hashing canônico) e RNF01/RNF06/RNF07.

---

## 5. Decisão Final de Aceite do Marco M1.3

- **Veredito de Engenharia:** **IMPLEMENTAÇÃO CONCLUÍDA E VERIFICADA**
- **Veredito de Homologação Manual:** **APROVADO** (Homologado formalmente pelo usuário em 03/11/2026: *"O M1.3 — Metrics foi formalmente aprovado na homologação manual."*)
- **Decisão Final:** **APROVADO**
- **Situação Final do Marco:** **CONCLUÍDO E HOMOLOGADO (APROVADO)**
- **Rastreabilidade e Evidências:**
  - Branch: `feat/m1-3-metrics`
  - Sequência de commits atômicos de implementação:
    - `e0a1e08`: `feat(metrics): implementar tipos, escopos e validacao numerica` (T1)
    - `16dbeb8`: `feat(metrics): implementar metricas de regressao mae, rmse e mbe` (T2)
    - `8e64ea9`: `feat(metrics): implementar r2, rmse_rel_pct, mape, pearson e kta` (T3)
    - `f214e5a`: `feat(metrics): implementar metricas discretas de classificacao` (T4)
    - `c3d3eb1`: `feat(metrics): implementar roc_auc e log_loss` (T5)
    - `2e6b687`: `feat(metrics): implementar catalogo de metricas e despacho` (T6)
    - `632a235`: `feat(metrics): implementar agregacao, comparacao e ranqueamento` (T7)
    - `1957b72`: `test(metrics): alinhar nomes de funcoes de teste para checks c21 e c22`
    - `002fa9a`: `test(specs): registrar comprovacoes automatizadas em proofs.md`
    - `7afe8ba`: `docs(specs): concluir verificacao e aceite do marco m1-3-metrics`
    - `c06958b`: `docs(specs): homologar e encerrar marco m1-3-metrics`
  - Veredito da Verificação Independente: `PASS` em `verification.md` auditado por agente independente (`author != verifier`), validado pelo portão mecânico `validate_verification.py` com **0 erros e 0 avisos**.
  - Comprovações automatizadas: 22/22 checks aprovados em `proofs.md`.
  - Suíte de regressão geral: 52/52 testes aprovados (`pytest tests/`).
  - Roteiro de aceitação do consumidor: seções 2.1 a 3 de `ACCEPTANCE.md` executadas com 100% de sucesso.
- **Justificativa:** Todos os 22 checks automatizados (C1 a C22) foram rigorosamente implementados, testados e auditados por agente verificador independente. O roteiro de aceitação do consumidor (`ACCEPTANCE.md`) foi validado integralmente com sucesso, garantindo estabilidade numérica, precisão flutuante float64, preservação de sinais em MBE e cumprimento estrito de regras de agregação e ordenação ADR-005. O marco está apto para transição ao Marco M1.4 (`datasets`).
