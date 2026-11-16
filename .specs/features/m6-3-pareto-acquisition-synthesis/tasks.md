# m6-3-pareto-acquisition-synthesis Tasks (M6.3 Fronteira de Pareto, Aquisição e Síntese)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/m6-3-pareto-acquisition-synthesis/design.md`  
**Status**: In Progress  
**Approved**: 2026-11-16 - user: "aprovado"  
**Build**: none - Python interpreted package without ahead-of-time build step; quality verified via pytest gates  
**Run unit**: .venv/bin/pytest tests/unit/statistics/ tests/integration/statistics/ -v  

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: `engenharia_software/ESPECIFICACAO_REQUISITOS.md`, `engenharia_software/ARQUITETURA_E_CONTRATOS.md`, `pyproject.toml`.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| :--- | :--- | :--- | :--- | :--- |
| M6.3 Domain Types (`src/experimental_ml/statistics/types.py`) | unit | ObjectiveSource, AcquisitionCriterion, ObjectiveSpec, MultiObjectiveSpec, ParetoConfigurationPoint, MultiObjectiveSummary, CandidatePrediction, AcquisitionScoreRecord, StructuredConclusion | `tests/unit/statistics/test_m63_types.py` | `.venv/bin/pytest tests/unit/statistics/test_m63_types.py -v` |
| Pareto Frontier (`src/experimental_ml/statistics/multiobjective.py`) | unit | compute_pareto_frontier, filtragem CoverageStatus.VALID e UNDEFINED_NAN, dominância exata, dominated_by | `tests/unit/statistics/test_pareto.py` | `.venv/bin/pytest tests/unit/statistics/test_pareto.py -v` |
| Acquisition Scoring (`src/experimental_ml/statistics/acquisition.py`) | unit | score_candidate_acquisition (EI, UCB, LCB, EXPLOITATION, EXPLORATION), std=0 seguro, ordenação determinística, rejeição NaN/negativo | `tests/unit/statistics/test_acquisition.py` | `.venv/bin/pytest tests/unit/statistics/test_acquisition.py -v` |
| Conclusion Synthesis (`src/experimental_ml/statistics/synthesis.py`) | unit | synthesize_conclusions, rastreabilidade numérica na narrativa, proibição de equivalência por p>=alpha, preservação de ressalvas | `tests/unit/statistics/test_synthesis.py` | `.venv/bin/pytest tests/unit/statistics/test_synthesis.py -v` |
| Integration & Purity (`tests/integration/statistics/test_m63_integration.py`) | integration | Fluxo M6.1 -> M6.2 -> M6.3 ponta a ponta e pureza runtime XCUT-02 (zero scipy) | `tests/integration/statistics/test_m63_integration.py` | `.venv/bin/pytest tests/integration/statistics/test_m63_integration.py -v` |

---

## Gate Check Commands

| Gate Level | When to Use | Command |
| :--- | :--- | :--- |
| Quick | After tasks with unit tests in statistics | `.venv/bin/pytest tests/unit/statistics/ -v` |
| Full | After tasks with integration tests | `.venv/bin/pytest tests/ -v` |
| Build | After phase completion or full feature verification | `.venv/bin/pytest tests/unit/statistics/ -v` |

---

## Execution Plan

### Phase 1: Estruturas Imutáveis de Pareto, Aquisição e Síntese (`P1`)

```
T1
```

### Phase 2: Fronteira de Pareto (`P2`)

```
T1 --> T2
```

### Phase 3: Funções de Aquisição (`P3`)

```
T1 --> T3
```

### Phase 4: Síntese de Conclusões Estruturadas (`P4`)

```
T2 --> T4
```

### Phase 5: API Pública e Integração Ponta a Ponta (`P5`)

```
T3 --> T5
T4 --> T5
```

---

## Task Breakdown

### Phase 1: Estruturas Imutáveis de Pareto, Aquisição e Síntese

#### T1: Definir tipos e enums de multiobjetivo, aquisição e StructuredConclusion [ ]

**What**: Adicionar `ObjectiveSource`, `AcquisitionCriterion`, `ObjectiveSpec`, `MultiObjectiveSpec`, `ParetoConfigurationPoint`, `ExcludedParetoConfiguration`, `MultiObjectiveSummary`, `CandidatePrediction`, `AcquisitionScoreRecord` e `StructuredConclusion` em `src/experimental_ml/statistics/types.py`, com validações estruturais e imutabilidade (`frozen=True`). Adicionar testes em `tests/unit/statistics/test_m63_types.py`.  
**Where**: `src/experimental_ml/statistics/types.py`  
**Depends on**: None  
**Reuses**: `src/experimental_ml/metrics/types.py`, `src/experimental_ml/core/findings.py`  
**Requirement**: STAT-09, STAT-10, STAT-11  
**Tests**: `tests/unit/statistics/test_m63_types.py`  
**Gate**: `.venv/bin/pytest tests/unit/statistics/test_m63_types.py -v`

---

### Phase 2: Fronteira de Pareto

#### T2: Implementar compute_pareto_frontier [ ]

**What**: Criar `src/experimental_ml/statistics/multiobjective.py` com `compute_pareto_frontier(consolidation, spec)` filtrando estritamente configurações `CoverageStatus.VALID` com objetivos `MetricStatus.VALID` e finitos, registrando excluídas em `excluded_configurations` e identificando exatamente `pareto_frontier` e `dominated_configurations` com `dominated_by`. Adicionar testes em `tests/unit/statistics/test_pareto.py`.  
**Where**: `src/experimental_ml/statistics/multiobjective.py`  
**Depends on**: T1  
**Reuses**: `src/experimental_ml/statistics/types.py`  
**Requirement**: STAT-09  
**Tests**: `tests/unit/statistics/test_pareto.py`  
**Gate**: `.venv/bin/pytest tests/unit/statistics/test_pareto.py -v`

---

### Phase 3: Funções de Aquisição

#### T3: Implementar score_candidate_acquisition [ ]

**What**: Criar `src/experimental_ml/statistics/acquisition.py` com `score_candidate_acquisition` suportando `EXPECTED_IMPROVEMENT`, `UCB`, `LCB`, `EXPLOITATION` e `EXPLORATION` usando `math.erf` para $\Phi(z)$ em Python/NumPy puro (`XCUT-02`), tratando $\hat{\sigma}=0$ com segurança e ordenando deterministicamente com desempate por `candidate_id`. Adicionar testes em `tests/unit/statistics/test_acquisition.py`.  
**Where**: `src/experimental_ml/statistics/acquisition.py`  
**Depends on**: T1  
**Reuses**: `src/experimental_ml/statistics/types.py`  
**Requirement**: STAT-10  
**Tests**: `tests/unit/statistics/test_acquisition.py`  
**Gate**: `.venv/bin/pytest tests/unit/statistics/test_acquisition.py -v`

---

### Phase 4: Síntese de Conclusões Estruturadas

#### T4: Implementar synthesize_conclusions [ ]

**What**: Criar `src/experimental_ml/statistics/synthesis.py` com `synthesize_conclusions` consumindo 5A (`DescriptiveConsolidation`), adequação (`MethodSuitabilityReport`), 5B (`StatisticalComparisonBundle`) e `MultiObjectiveSummary` opcional, produzindo `StructuredConclusion` com referências numéricas exatas na narrativa, preservação de ressalvas metodológicas e proibição de declarar equivalência a partir de $p_{\text{adj}} \ge \alpha$. Adicionar testes em `tests/unit/statistics/test_synthesis.py`.  
**Where**: `src/experimental_ml/statistics/synthesis.py`  
**Depends on**: T2  
**Reuses**: `src/experimental_ml/statistics/types.py`  
**Requirement**: STAT-11  
**Tests**: `tests/unit/statistics/test_synthesis.py`  
**Gate**: `.venv/bin/pytest tests/unit/statistics/test_synthesis.py -v`

---

### Phase 5: API Pública e Integração Ponta a Ponta

#### T5: Expor API pública de M6.3 e validar integração e pureza XCUT-02 [ ]

**What**: Atualizar `__all__` e exportações em `src/experimental_ml/statistics/__init__.py` com os símbolos de M6.3. Criar `tests/integration/statistics/test_m63_integration.py` validando o fluxo completo M6.1 -> M6.2 -> M6.3 e pureza de runtime sem `scipy` (`XCUT-02`).  
**Where**: `src/experimental_ml/statistics/__init__.py`  
**Depends on**: T3, T4  
**Reuses**: `src/experimental_ml/statistics/multiobjective.py`, `acquisition.py`, `synthesis.py`  
**Requirement**: STAT-09, STAT-10, STAT-11  
**Tests**: `tests/integration/statistics/test_m63_integration.py`  
**Gate**: `.venv/bin/pytest tests/unit/statistics/ tests/integration/statistics/ -v`

---

## Checks

**C1** - `MultiObjectiveSpec`, `ObjectiveSpec`, `ParetoConfigurationPoint` e `MultiObjectiveSummary` validam entradas e garantem imutabilidade (`FrozenInstanceError`). (STAT-09, AC-M63-01-01)  
Proof: run unit | tests/unit/statistics/test_m63_types.py::test_m63_01_multiobjective_types_and_immutability PASSED

**C2** - `compute_pareto_frontier` aceita apenas configurações `CoverageStatus.VALID` com objetivos finitos e registra excluídas em `excluded_configurations`. (STAT-09, AC-M63-01-02)  
Proof: run unit | tests/unit/statistics/test_pareto.py::test_m63_01_excludes_partial_and_nan_configs PASSED

**C3** - `compute_pareto_frontier` identifica exatamente o conjunto não-dominado e registra `dominated_by` para dominadas. (STAT-09, AC-M63-01-03)  
Proof: run unit | tests/unit/statistics/test_pareto.py::test_m63_01_exact_pareto_frontier_and_dominance PASSED

**C4** - `AcquisitionCriterion`, `CandidatePrediction` e `AcquisitionScoreRecord` são congelados e validam entradas. (STAT-10, AC-M63-02-01)  
Proof: run unit | tests/unit/statistics/test_m63_types.py::test_m63_02_acquisition_types_and_immutability PASSED

**C5** - `score_candidate_acquisition` calcula EI, UCB, LCB, EXPLOITATION e EXPLORATION com precisão em NumPy puro, trata std=0 com segurança e ordena deterministicamente. (STAT-10, AC-M63-02-02)  
Proof: run unit | tests/unit/statistics/test_acquisition.py::test_m63_02_acquisition_criteria_and_zero_std PASSED

**C6** - `score_candidate_acquisition` rejeita std negativo ou valores não finitos. (STAT-10, AC-M63-02-03)  
Proof: run unit | tests/unit/statistics/test_acquisition.py::test_m63_02_invalid_candidates_rejected PASSED

**C7** - `StructuredConclusion` é congelada e contém todos os campos obrigatórios. (STAT-11, AC-M63-03-01)  
Proof: run unit | tests/unit/statistics/test_m63_types.py::test_m63_03_structured_conclusion_immutability PASSED

**C8** - `synthesize_conclusions` referencia diretamente os valores numéricos de 5A e 5B na narrativa sem fabricar métricas. (STAT-11, AC-M63-03-02)  
Proof: run unit | tests/unit/statistics/test_synthesis.py::test_m63_03_numeric_traceability_in_narrative PASSED

**C9** - `synthesize_conclusions` nunca declara equivalência a partir de p_adj >= alpha. (STAT-11, AC-M63-03-03)  
Proof: run unit | tests/unit/statistics/test_synthesis.py::test_m63_03_no_equivalence_from_nonsignificance PASSED

**C10** - `synthesize_conclusions` preserva todas as ressalvas metodológicas (`HOLDOUT_ONLY`, cobertura parcial, amostra pequena). (STAT-11, AC-M63-03-04)  
Proof: run unit | tests/unit/statistics/test_synthesis.py::test_m63_03_preserves_methodological_caveats PASSED

**C11** - Fluxo integrado ponta a ponta M6.1 -> M6.2 -> M6.3 via API pública de `experimental_ml.statistics`. (STAT-09)  
Proof: run unit | tests/integration/statistics/test_m63_integration.py::test_m63_end_to_end_pipeline PASSED

**C12** - Módulos de M6.3 operam 100% em Python/NumPy puro sem importação de `scipy`. (XCUT-02)  
Proof: run unit | tests/integration/statistics/test_m63_integration.py::test_m63_runtime_purity_xcut02 PASSED

---

## Handoff

- **Dispatched:** none
- **Current Task:** T1
- **Next Task:** T2
