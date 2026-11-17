# POS-2B — Notebooks Interativos Design

**Spec**: `.specs/features/pos-2b-notebooks-interativos/spec.md`  
**Status**: Approved  
**Approved**: 2026-11-16 - user: "Vamos fazer isso agora"  

---

## 1. Visão Geral

Quatro notebooks `.ipynb` autocontidos em `notebooks/`, acompanhados de `tests/unit/test_notebooks_execution.py` que executa 100% das células de código em `tmp_path` e valida a pureza `XCUT-02`.

- `notebooks/01_tour_6_etapas.ipynb`
- `notebooks/02_ablacao_lssvm_prognose_florestal.ipynb`
- `notebooks/03_validacao_agrupada_e_prevencao_leakage.ipynb`
- `notebooks/04_pos_experimento_relatorios_artigo.ipynb`
