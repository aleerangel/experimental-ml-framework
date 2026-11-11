# STATE

## Decisions

### AD-001
- **Decision**: Adotar Hatchling (`hatchling.build`) como build-backend padronizado no `pyproject.toml` e layout `src/experimental_ml/`.
- **Reason**: Backend moderno em conformidade com PEP 517/518/621, suporte nativo ao layout `src/` e empacotamento enxuto sem dependências de compilação C/C++.
- **Trade-off**: Exige ferramentas de empacotamento compatíveis com padrões modernos (PEP 621), sem suporte nativo a extensões C legadas de `setuptools`.
- **Scope**: Todo o framework `experimental-ml-framework`.
- **Date**: 2026-10-31
- **Status**: active

### AD-002
- **Decision**: Adotar o processo de aceite de marcos (*Milestone Acceptance*) baseado em três registros (`SPEC.md`, `ACCEPTANCE.md`, `RESULTS.md`), integrado ao fluxo TLC Spec-Driven.
- **Reason**: Diferenciar a aprovação em testes automatizados do aceite formal da entrega, prevendo validação prática por interfaces públicas sob a perspectiva do consumidor e registro explícito de pendências.
- **Trade-off**: Requer a elaboração e manutenção de três documentos por marco (`SPEC.md`, `ACCEPTANCE.md`, `RESULTS.md`), mantendo pendências manuais registradas explicitamente como PENDENTE.
- **Scope**: Todos os marcos do framework (retroativo a M1.1 e M1.2; mandatório de M1.3 a M7).
- **Date**: 2026-11-02
- **Status**: active

### AD-003
- **Decision**: Decomposição modular do Marco M2 em 5 sub-marcos controláveis (M2.1 a M2.5) e catálogo canônico fechado de 15 achados diagnósticos com severidade imutável e ordenação lexicográfica determinística.
- **Reason**: Garantir isolamento conceitual e controle granular de escopo entre triagem/diagnóstico (`m2-1`), saneamento determinístico (`m2-2`), particionamento compartilhado (`m2-3`), CLI modularizada (`m2-4`) e integração transversal (`m2-5`), evitando acoplamento indevido entre camadas.
- **Trade-off**: Requer manutenção de contratos explícitos entre as sub-etapas (ex.: `SanitizedDatasetView` recebida por `validation` sem expor lógica interna de sanitização).
- **Scope**: Marco M2 e módulos `experimental_ml.data` e `experimental_ml.validation`.
- **Date**: 2026-11-06
- **Status**: active

### AD-004
- **Decision**: Hardening de integridade pós-auditoria da etapa M2 com salvaguardas matemáticas contra folds vazios, tipagem estruturada em JSON codecs, APIs públicas de view slicing/reconstrução e exportações dinâmicas via PEP 562 para pureza de runtime na CLI.
- **Reason**: Sanar as divergências identificadas na auditoria transversal do Marco M2 (`REV-M2-01` a `REV-M2-11`), eliminando fragilidades em partições temporais com NaN, preservando fidelidade estrita de tipos primitivos em mapeamentos de rótulos e evitando que a CLI ou consumidores externos dependam de código privado.
- **Trade-off**: Requer manutenção de estruturas tipadas explícitas em codecs JSON (`key`, `key_type`, `value`) e recálculo canônico de hash de subconjuntos no fatiamento de views.
- **Scope**: Módulos `core`, `data`, `validation`, `stages` e `cli`.
- **Date**: 2026-11-09
- **Status**: active

### AD-005
- **Decision**: Saneamento das estratégias supervisionadas de features na Onda 1 e formalização desacoplada do contrato funcional de modelos heterogêneos (`ModelSpec`, `ModelCapabilities`).
- **Reason**: Eliminar aliases não documentados (`MUTUAL_INFO_TOP_K`, `ACH-M3-01`) restringindo a seleção supervisionada da Onda 1 à estratégia formal `TOP_K_RELEVANCE` e `VARIANCE_THRESHOLD`, e padronizar o ciclo de modelos em funções puras (`instantiate_fresh_model`, `fit_model`, `predict_model`, `extract_model_diagnostics`) com suporte a modelos analíticos sem treino (`requires_fit=False`) e retorno padronizado tripartite (`y_pred`, `y_std`, `y_proba`).
- **Trade-off**: Redução de dimensionalidade via PCA e estimadores contínuos avançados de informação mútua são formalmente alocados para a Onda 2.
- **Scope**: Módulos `features` e `models`.
- **Date**: 2026-11-10
- **Status**: active

### AD-006
- **Decision**: Pipeline funcional de pré-processamento em 2 camadas (Camada 1: Cenário/Domínio; Camada 2: Modelo/Tecnologia) com prevenção de duplicação acidental, ajuste estrito intra-fold, escalonadores puros em NumPy e adaptador de kernel pré-computado sem vazamento.
- **Reason**: Atender aos requisitos `RF3.4`, `CA-E3-02`, `CA-E4B-01` e `XCUT-02`, prevenindo vazamento de dados de avaliação no pré-processamento intra-fold, impedindo reescalonamento redundante ou contraditório entre camadas, garantindo estabilidade numérica com variância zero sem dependência de scikit-learn, e fornecendo Gram matrices $(\mathbf{X}_{\text{train}}, \mathbf{X}_{\text{train}})$ no ajuste e $(\mathbf{X}_{\text{eval}}, \mathbf{X}_{\text{train}})$ na inferência.
- **Trade-off**: Requer manutenção de tipos congelados (`TwoLayerPreprocessingSpec`, `TwoLayerPreprocessingState`), implementação própria em NumPy de escalonadores comuns (`StandardScaler`, `MinMaxScaler`, `MaxAbsScaler`, `RobustScaler`, `AngularScaler`) e projeção intermediária explícita $X_{\text{inter}}$ durante o ajuste da Camada 2.
- **Scope**: Módulo `models.preprocessing` e integração com `models`.
- **Date**: 2026-11-11
- **Status**: active

### AD-007
- **Decision**: Subsistema de otimização aninhada de hiperparâmetros (`experimental_ml.tuning`) confinado estritamente ao treino externo (`CA-E4B-01`), com validação cruzada aninhada ($K_{\text{inner}} \ge 2$), desqualificação mandatória de candidatos com `UNDEFINED_NAN` (ADR-005) e pureza de runtime sem frameworks externos de busca (`XCUT-02`).
- **Reason**: Atender aos requisitos `RF3.5`, `ADR-003`, `ADR-005` e `CA-E4B-01`, garantindo que a seleção de hiperparâmetros reflita o desempenho de generalização interno sem vazamento de dados de avaliação ou holdout externo, que falhas numéricas ou métricas degeneradas jamais vençam candidatos válidos ou sejam coagidas para zero, e que Grid e Random Search operem com reproducibilidade exata sob semente.
- **Trade-off**: Requer geradores próprios de produto cartesiano e amostragem aleatória em NumPy puro, particionamento de índices de dobras internas desacoplado de bibliotecas externas e instanciação compulsória de instâncias desacopladas via `instantiate_fresh_model`.
- **Scope**: Pacote `experimental_ml.tuning` e integração transversal com `models` e `metrics`.
- **Date**: 2026-11-11
- **Status**: active

## Handoff

- **Feature**: m4-3-nested-tuning (Sub-marco M4.3 — Otimização de Hiperparâmetros Aninhada Intra-Fold)
- **Phase / Task**: Conclusão formal do Sub-marco M4.3 (Etapa 3 / Marco M4)
- **Completed**:
  - Conclusão e homologação formal de 100% dos Marcos M1 (`m1-1` a `m1-5`), M2 (`m2-1` a `m2-5`), M3 (`m3-1` a `m3-4`), M4.1 (`m4-1-model-registry-contracts`) e M4.2 (`m4-2-two-layer-preprocessing`).
  - Especificação, Design e Execução do Sub-marco M4.3 (`m4-3-nested-tuning`) com 7 tarefas granulares concluídas e 24 critérios de aceitação formalmente comprovados (`check_proofs.py`: 24 pass, 0 fail).
  - Implementação de `src/experimental_ml/tuning/`:
    - `types.py`: `SearchStrategy` (enum de 4 membros: `FIXED`, `GRID_SEARCH`, `RANDOM_SEARCH`, `CUSTOM_TUNER`), frozen dataclasses com slots (`HyperparameterSearchSpec`, `TuningTrialRecord`, `TuningResult`) e exceção especializada `TuningOptimizationError` (herdando de `ContractViolationError`).
    - `validation.py`: `validate_search_spec` validando compatibilidade contra `METRICS_CATALOG`, consistência de direção (`MAXIMIZE` / `MINIMIZE`), $K_{\text{inner}} \ge 2$ e orçamentos de busca (`ConfigurationError`).
    - `candidates.py`: `generate_candidates` gerando produto cartesiano ordenado e determinístico no Grid Search e amostragem controlada por semente no Random Search.
    - `partitioning.py`: `split_inner_folds` gerando particionamento K-Fold interno puro em NumPy estritamente no intervalo $[0, N_{\text{train}}-1]$ com arrays read-only e disjunção matemática $(\text{Train}_{\text{inner}} \cap \text{Val}_{\text{inner}} = \emptyset)$.
    - `engine.py`: `run_nested_tuning` executando nested CV com alocação limpa de estimadores por dobra (`instantiate_fresh_model`), avaliação via `experimental_ml.metrics`, desqualificação estrita de candidatos com `UNDEFINED_NAN` (ADR-005), disparo de `TuningOptimizationError` sob falha total e seleção determinística de $\theta^*$.
    - `__init__.py`: Exportação limpa da API pública em `__all__`.
  - Pureza estrita de runtime (`XCUT-02`): dependência única de `numpy>=1.24.0`, subprocesso comprovando zero importações de frameworks externos de tuning ou ML (`optuna`, `ray`, `sklearn`, `scipy`).
  - Verificação independente realizada com veredito `PASS` (0 findings) e portão `validate_verification.py --strict` aprovado com 0 erros e 0 avisos.
  - Artefatos de homologação gerados: `verification.md`, `ACCEPTANCE.md` e `RESULTS.md`.
  - Suíte total do framework expandida de 297 para 321 testes automatizados (24 novos testes: 21 unitários em `tests/unit/tuning/` e 3 de integração em `tests/integration/tuning/`), 100% aprovados.
- **In-progress**: Transição para o Sub-marco M4.4 (`m4-4-model-persistence-cli` — Persistência em Disco de `models.json`, Portão de Validação e Subcomandos da CLI `expml models`).
- **Next step**: Homologação / merge da branch `feat/m4-3-nested-tuning` e inicialização da especificação de M4.4.
- **Blockers**: none
- **Branch**: feat/m4-3-nested-tuning
