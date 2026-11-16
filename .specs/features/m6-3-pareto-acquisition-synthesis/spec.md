# Feature: m6-3-pareto-acquisition-synthesis

**Approved**: 2026-11-16 - user: "aprovado"

## Problem Statement

Com a consolidação descritiva e adequação metodológica (M6.1) e o núcleo de inferência pareada, tamanho de efeito e multiplicidade (M6.2) implementados em `src/experimental_ml/statistics/`, a Etapa 5 do `experimental-ml-framework` necessita agora completar os **Submódulos 5B (Análise Multiobjetivo e Aquisição) e 5C (Síntese de Conclusões Estruturadas)**:

1. **Análise Multiobjetivo e Fronteira de Pareto (`compute_pareto_frontier`, `RF5.5`, `CA-E5-02`)**: Pesquisadores frequentemente precisam equilibrar desempenho preditivo, estabilidade de seleção de atributos e custo computacional (ou múltiplos objetivos configurados). O subsistema precisa identificar exatamente o conjunto de configurações não-dominadas `VALID`, excluindo configurações com cobertura incompleta/nula ou valores indefinidos (`UNDEFINED_NAN`, `ADR-005`) sem coerção para zero.
2. **Critérios de Aquisição Sequencial (`score_candidate_acquisition`, `RF5.5`, `ARQUITETURA §3.5`)**: Quando houver predições com incerteza $(\hat{\mu}_i, \hat{\sigma}_i)$ sobre candidatos, o subsistema deve suportar funções de aquisição configuráveis em NumPy/Python puro (`EXPECTED_IMPROVEMENT`, `UCB`, `LCB`, `EXPLOITATION`, `EXPLORATION`) sem dependência de `scipy` (`XCUT-02`).
3. **Síntese de Conclusões Estruturadas (`synthesize_conclusions`, `StructuredConclusion`, `RF5.6`, `CA-E5-02`)**: Traduzir os resultados tipados de 5A e 5B em conclusões estruturadas e narrativa explicativa auditável, referenciando explicitamente os valores numéricos observados, distinguindo liderança observada, evidência estatística ajustada, magnitude de efeito, relevância prática, compromissos de custo/Pareto e limitações metodológicas — sem declarar equivalência a partir de $p \ge \alpha$ nem declarar vencedores arbitrários.

## Out of Scope

- Persistência em disco de `statistics/` (`save_statistics_bundle`, `load_statistics_bundle`), portão de estágio `verify_statistics_gate` e CLI `expml stats` — escopo do Sub-marco M6.4.
- Inclusão de `scipy` ou qualquer biblioteca externa além de `numpy>=1.24.0` (`XCUT-02`).
- Acoplamento a qualquer domínio aplicado ou dados reais específicos (`RNF02`, `CA02`).

## Assumptions & Open Questions

**Open questions:** none - os contratos de Fronteira de Pareto, funções de aquisição e `StructuredConclusion` estão formalmente definidos em `ARQUITETURA_E_CONTRATOS.md` (Seção 3.5 e ADR-005) e `ESPECIFICACAO_REQUISITOS.md` (RF5.5, RF5.6, CA-E5-02).

| Assumption / Question | Chosen default | Rationale |
| --- | --- | --- |
| Elegibilidade para Fronteira de Pareto (`CA-E5-02`) | Apenas configurações com `coverage_status == CoverageStatus.VALID` e todos os objetivos finitos (`MetricStatus.VALID`) participam da fronteira; demais são registradas em `excluded_configurations` | Impede que configurações falhas ou parciais dominem configurações completas (`ADR-005`, `CA-E5-02`) |
| Definição de dominância de Pareto | A domina B sse A é ao menos tão boa quanto B em todos os objetivos e estritamente melhor em pelo menos um objetivo (respeitando `MINIMIZE`/`MAXIMIZE`) | Definição matemática padrão de otimalidade de Pareto sem pesos arbitrários |
| Cálculo de CDF/PDF normal padrão na aquisição (`EI`) | `math.erf` para $\Phi(z)$ e `math.exp` para $\phi(z)$ em Python/NumPy puro | Atende estritamente a `XCUT-02` com precisão de máquina |
| Tratamento de $\hat{\sigma} = 0$ na aquisição `EI` | Retorna melhoria determinística $\max(0, \hat{\mu} - f^* - \xi)$ (ou $\max(0, f^* - \hat{\mu} - \xi)$ em minimização) | Evita divisão por zero mantendo continuidade limite quando $\hat{\sigma} \to 0^+$ |
| Regra de não-equivalência na síntese (`CA-E5-02`) | Quando $p_{\text{adj}} \ge \alpha$, a narrativa declara ausência de evidência estatística suficiente / resultado inconclusivo, jamais equivalência | Cumpre `CA-E5-02` e evita falácia estatística clássica |

## User Stories

### US-M63-01 (Priority: P1) — Fronteira de Pareto e Análise Multiobjetivo
As an experimental ML researcher,  
I want exact Pareto frontier identification across configurable performance, stability, and computational cost objectives,  
So that multi-objective trade-offs are transparent without arbitrary scalar weighting.

#### Acceptance Criteria
- **AC-M63-01-01**: The system SHALL provide frozen dataclasses `MultiObjectiveSpec`, `ObjectiveSpec` (name, direction, source), `ParetoConfigurationPoint`, and `MultiObjectiveSummary` validating non-empty objectives and immutability (`FrozenInstanceError`).
- **AC-M63-01-02**: WHEN invoking `compute_pareto_frontier` on a `DescriptiveConsolidation` and `MultiObjectiveSpec`, the system SHALL include ONLY configurations with `CoverageStatus.VALID` and finite valid objective values, recording excluded configurations with explicit reasons in `excluded_configurations`.
- **AC-M63-01-03**: The system SHALL identify the exact non-dominated set (`pareto_frontier`) and record each dominated configuration along with the identifiers of configurations that dominate it (`dominated_by`).

---

### US-M63-02 (Priority: P1) — Funções de Aquisição para Candidatos com Incerteza
As an experimental ML researcher,  
I want sequential acquisition scoring (`EXPECTED_IMPROVEMENT`, `UCB`, `LCB`, `EXPLOITATION`, `EXPLORATION`) for candidates with uncertainty $(\hat{\mu}_i, \hat{\sigma}_i)$,  
So that prospective candidate prioritization balances exploitation and exploration in pure NumPy.

#### Acceptance Criteria
- **AC-M63-02-01**: The system SHALL provide enum `AcquisitionCriterion` (`EXPECTED_IMPROVEMENT`, `UCB`, `LCB`, `EXPLOITATION`, `EXPLORATION`) and frozen dataclasses `CandidatePrediction` and `AcquisitionScoreRecord`.
- **AC-M63-02-02**: WHEN invoking `score_candidate_acquisition`, the system SHALL compute exact acquisition scores using pure Python/NumPy (`math.erf` for $\Phi$), handle $\hat{\sigma}_i = 0$ safely without `ZeroDivisionError`, and return scores sorted deterministically in descending preference order with tie-breaking by `candidate_id`.
- **AC-M63-02-03**: IF any candidate has negative $\hat{\sigma}_i$ or non-finite $\hat{\mu}_i$/$\hat{\sigma}_i$, THEN the system SHALL raise `ContractViolationError` or `ConfigurationError`.

---

### US-M63-03 (Priority: P1) — Síntese de Conclusões Estruturadas e Rastreáveis
As an experimental ML researcher,  
I want a pure synthesizer that produces `StructuredConclusion` objects grounded in 5A/5B numerical outputs,  
So that reported conclusions never fabricate numbers, respect methodological caveats, and never equate $p \ge \alpha$ with equivalence.

#### Acceptance Criteria
- **AC-M63-03-01**: The system SHALL provide a frozen dataclass `StructuredConclusion` containing `primary_metric`, `observed_leader`, `statistical_evidence_status`, `effect_magnitude_summary`, `practical_relevance_status`, `cost_tradeoff_summary`, `methodological_caveats`, and `narrative_text`.
- **AC-M63-03-02**: WHEN invoking `synthesize_conclusions` with `DescriptiveConsolidation`, `MethodSuitabilityReport`, `StatisticalComparisonBundle`, and optional `MultiObjectiveSummary`, the system SHALL populate every field strictly from observed 5A/5B numbers and embed exact numeric references inside `narrative_text`.
- **AC-M63-03-03**: WHILE synthesizing conclusions for comparisons with $p_{\text{adj}} \ge \alpha$, the system SHALL state that statistical evidence was insufficient to reject the null hypothesis and SHALL NOT declare equivalence between configurations.
- **AC-M63-03-04**: WHERE `HOLDOUT_ONLY` ($J=1$) or incomplete coverage caveats exist, `synthesize_conclusions` SHALL include all methodological caveats in `methodological_caveats` and in `narrative_text`.

## Requirement Traceability

| Requirement ID | Acceptance Criteria | Target Component | Status |
| --- | --- | --- | --- |
| STAT-09 | AC-M63-01-01, AC-M63-01-02, AC-M63-01-03 | `experimental_ml.statistics.multiobjective` | pending |
| STAT-10 | AC-M63-02-01, AC-M63-02-02, AC-M63-02-03 | `experimental_ml.statistics.acquisition` | pending |
| STAT-11 | AC-M63-03-01, AC-M63-03-02, AC-M63-03-03, AC-M63-03-04 | `experimental_ml.statistics.synthesis` | pending |
