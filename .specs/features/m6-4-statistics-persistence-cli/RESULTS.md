# Registro de Validação e Aceite — Marco M6.4 (Persistência, Portão de Estágio e CLI `expml stats`)

> **Registro de Resultados Efetivos (RESULTS.md)**  
> **Identificador do Marco:** M6.4 (`m6-4-statistics-persistence-cli`)  
> **Data de Validação:** 16 de Novembro de 2026  
> **Commit de Implementação / Prova:** [`7460578`](https://github.com/aleerangel/experimental-ml-framework/commit/7460578)  
> **Ambiente Computacional:** Linux (x86_64), Python 3.12.16, NumPy 2.5.4, Pytest 9.2.0.

---

## 1. Resumo Executivo da Validação

| Categoria | Planejado no Roteiro | Executado Efetivamente | Status |
| :--- | :---: | :---: | :---: |
| **Instalação e Dependências** | Python >= 3.10 com dependência única de runtime (`numpy>=1.24.0`, zero `scipy`) | Validado via subprocesso isolado (`XCUT-02`) | **APROVADO** |
| **Testes Unitários de Persistência, Portão e CLI** | 10 testes cobrindo C1 a C10 | 10 testes específicos de M6.4 aprovados | **APROVADO** |
| **Testes de Integração e Pureza** | 2 testes em `tests/integration/statistics/test_m64_integration.py` (C11, C12) | 2 testes de integração CLI e pureza aprovados | **APROVADO** |
| **Testes de Regressão Global** | Suíte completa em `pytest tests/` | **548 testes aprovados** (100% de sucesso) | **APROVADO** |
| **Verificação Independente TLC** | Auditoria por subagente independente (`author != verifier`) | Aprovado com veredito `PASS` (0 findings) | **APROVADO** |
| **Sondagem Adversarial Independente** | 3 sondagens (roundtrip `NaN`/`±Inf`/Stability, bloqueio de portão, CLI `--config` e exit 2) | Todas as 3 sondagens adversariais aprovadas | **APROVADO** |

---

## 2. Evidências de Testes Automatizados

### 2.1 Suíte do Marco M6.4

```text
.venv/bin/pytest tests/unit/statistics/test_statistics_storage.py tests/unit/stages/test_stage_statistics_gate.py tests/unit/cli/test_cli_stats.py tests/integration/statistics/test_m64_integration.py -v
12 passed in 0.68s
```

### 2.2 Provas TLC (`check_proofs.py`)

```text
**HEAD**: 7460578
**Tree**: clean
**Shell**: /bin/sh
**Result**: 12 pass, 0 fail
```

### 2.3 Suíte de Regressão Global

```text
.venv/bin/pytest tests/ -q
548 passed in 13.47s
```

---

## 3. Registro do Verificador Independente

- **Veredito:** `PASS`
- **Sondagens Realizadas:**
  1. Roundtrip de persistência preservando `NaN`, `+Inf`, `-Inf`, `AggregatedTimingStats` e `SelectionStabilityReport`; rejeição com `ContractViolationError` quando `force=False`.
  2. `verify_statistics_gate` lançando `DataIntegrityError` em arquivos ausentes, JSON corrompido e divergência de `partition_plan_id` entre manifesto e consolidação.
  3. `expml stats run --config` com `ComparisonSpec` customizado (`AGAINST_BASELINE`, `BENJAMINI_HOCHBERG`, `alpha=0.01`) sem hashes no stdout, e `expml stats verify` retornando código `2` sem traceback.
- **Apontamentos:** Nenhum (`None`). Todos os 12 critérios C1 a C12 sustentam suas garantias formais.

---

## 4. Decisão Formal de Aceite

O Marco M6.4 cumpre integralmente `STAT-12`, `STAT-13`, `STAT-14`, `STORE-03`, `STORE-05`, `CA-GER-01`, `CLI-06`–`CLI-11` e `XCUT-02`, encerrando integralmente o **Marco M6 (Etapa 5 — Consolidação Descritiva e Comparação Estatística Rigorosa)**.

**Decisão:** `APROVADO`
