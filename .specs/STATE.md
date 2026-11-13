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

### AD-008
- **Decision**: Persistência declarativa de catálogo de modelos (`ModelsCatalog`), resolução dinâmica de fábricas de estimadores (`resolve_estimator_factory`), portão de estágio Stage 3 (`verify_models_gate`) e interface de linha de comando `expml models` (`validate` e `verify`) com pureza de runtime (`CLI-10`) e escrita atômica (`STORE-03`, `STORE-05`).
- **Reason**: Atender aos requisitos `MPC-01` a `MPC-07`, `RF3.1`, `RF3.2`, `RF3.6`, `CA-E3-01` e `ARQUITETURA §2.4`, permitindo que configurações de modelos sejam auditadas, versionadas em formato JSON padronizado (`configuration/models.json`), validadas contra pré-requisitos de preparação (Stage 1 READY) e resolvidas dinamicamente sem permitir a execução de caminhos arbitrários ou strings inválidas.
- **Trade-off**: Requer resolução explícita de nomes canônicos para baselines embutidos (`DUMMY_BASELINE_MEAN`, etc.) e validação de importabilidade para caminhos externos no formato `module:qualname`, além de isolamento estrito de imports pesados na CLI.
- **Scope**: Módulos `models.catalog`, `models.storage`, `stages.stage_gates`, `cli.cmd_models`, `cli.main` e testes associados.
- **Date**: 2026-11-11
- **Status**: active

### AD-009
- **Decision**: Consolidação de predições out-of-fold (`ConsolidatedOofPredictions`) com ordenação lexicográfica canônica obrigatória por `observation_id`, estatísticas de comitê ($\hat{\mu}_i, \hat{\sigma}_i$) para observações com avaliações repetidas, separação estrita de escopos de métricas (`POOLED_OOF` sobre vetores concatenados vs `FOLD_AGGREGATION` para resumos estatísticos inter-folds), tolerância a falhas parciais (`MetricStatus.PARTIAL_COVERAGE`) com alerta de observações ausentes, persistência atômica (`write_json_atomic`) sob `{run_dir}/oof/oof_{model_id}__{scenario_id}.json` e portão de estágio Stage 4 (`verify_runs_gate`).
- **Reason**: Atender aos requisitos `ORCH-15` a `ORCH-21`, `RF4.7`, `CA-E4B-01`, `STORE-01`, `STORE-03`, `STORE-05`, `ADR-005` e `ADR-008`, garantindo que predições out-of-fold de desenvolvimento sejam unificadas de forma reprodutível e determinística, permitindo o cálculo rigoroso de métricas globais sem viés de dobra, fornecendo incerteza de comitê em esquemas repetidos, registrando com precisão falhas de cobertura sob políticas tolerantes a falhas e impedindo o avanço para a etapa de consolidação analítica (Stage 5) sem a validação estrutural e integridade física de todos os artefatos de células e OOF em disco.
- **Trade-off**: Requer cálculo em dois passos para observações com múltiplas dobras (média pontual e desvio com ddof=1), serialização dedicada em JSON com suporte a NaN (`MetricStatus.UNDEFINED_NAN`) e verificação cruzada de integridade de hashes de dataset e partições no portão Stage 4.
- **Scope**: Módulos `experimental_ml.orchestration` e `experimental_ml.stages.stage_gates`.
- **Date**: 2026-11-12
- **Status**: active

### AD-010
- **Decision**: Interface de Linha de Comando `expml run` (subcomandos `start`, `resume`, `status`, `verify`) operando como ponto de entrada da Etapa 4B com reconstituição automatizada dos insumos das etapas anteriores (`SanitizedDatasetView`, `PartitionPlan`, `ScenariosCatalog`, `ModelsCatalog`), verificação estrita de portões upstream, supressão de hashes criptográficos na saída padrão (`CLI-11`), padronização de códigos de saída (0 para sucesso, 2 para erros de domínio sem traceback, 1 para falhas sistêmicas inesperadas via `CLI-06`) e isolamento de importações pesadas no nível de módulo (`CLI-10`).
- **Reason**: Atender aos requisitos `ORCH-22` a `ORCH-28`, `ARQUITETURA §2.4`, `CLI-06` a `CLI-11` e `XCUT-02`, permitindo que pesquisadores e pipelines automatizados disparem matrizes de experimentos em larga escala pelo terminal, monitorem o progresso de forma puramente não-destrutiva, recuperem execuções interrompidas via checkpointing incremental e auditem formalmente a integridade física dos artefatos em disco através de `verify_runs_gate`.
- **Trade-off**: Requer inferência inteligente do diretório de experimento em comandos de retomada e validação de precondições upstream antes de qualquer mutação de disco.
- **Scope**: Módulos `experimental_ml.cli.main` e `experimental_ml.cli.cmd_run`.
- **Date**: 2026-11-12
- **Status**: active

### AD-011
- **Decision**: Saneamento pós-auditoria técnica independente do Marco M5 (resolução dos achados P1: ACH-M5-01 com comitês k=1 sem desvio padrão empírico artificialmente zerado, ACH-M5-02 com validação rigorosa de integridade de hashes do dataset e partition_plan na retomada, e ACH-M5-03 distinguindo formalmente execuções completas de execuções parciais tolerantes a falhas no `verify_runs_gate`).
- **Reason**: Garantir a estrita correção científica, prevenir leakage ou mistura de resultados entre configurações incompatíveis na retomada e assegurar que o portão Stage 4 não mascare execuções incompletas ao liberar a passagem para a Etapa 5.
- **Trade-off**: Requer representação explícita de ausência de dispersão (`None`/`UNDEFINED_NAN`), inclusão de `source_dataset_hash` e `partition_plan_id` no estado persistido e checagem de completude total versus parcial no portão de estágio.
- **Scope**: Módulos `experimental_ml.orchestration.oof`, `state`, `engine` e `stages.stage_gates`.
- **Date**: 2026-11-12
- **Status**: active

### AD-012
- **Decision**: Desacoplamento estrito e absoluto do framework de qualquer domínio aplicado e isolamento formal do critério `CA02` como validação externa a ser conduzida exclusivamente pelo pesquisador.
- **Reason**: Cumprir rigorosamente o princípio RNF02 (Independência de Domínio), assegurando que o repositório, suíte de testes e documentação interna não contenham dependências, termos, dados ou acoplamentos a problemas específicos (como prognose florestal), garantindo a pureza metodológica da biblioteca.
- **Trade-off**: Testes automatizados do repositório operam exclusivamente com fixtures sintéticas autocontidas em memória ou disco temporário; a validação empírica em bases reais é exercida externamente pelo usuário consumidor.
- **Scope**: Todo o repositório `experimental-ml-framework`.
- **Date**: 2026-11-12
- **Status**: active

## Handoff

- **Feature**: m5-matrix-execution-and-orchestration (Marco M5 Concluído, Auditado e Integrado na Main)
- **Phase / Task**: Marco M5 concluído e aceito; preparação e planejamento para o Marco M6 (Consolidação Descritiva e Comparação Estatística Rigorosa).
- **Completed**:
  - Implementação e homologação integral de todos os 4 sub-marcos de M5:
    - M5.1 (`m5-1-cell-execution-contracts`): Contratos funcionais, máquina de estados de célula e tempos desagregados.
    - M5.2 (`m5-2-matrix-executor-checkpointing`): Grade cartesiana, motor de execução com paralelismo configurável e checkpoint/resume.
    - M5.3 (`m5-3-oof-consolidation-stage-gate`): Consolidação OOF, comitê, métricas pooled vs inter-folds e portão `verify_runs_gate`.
    - M5.4 (`m5-4-cli-run-end-to-end`): Interface de terminal `expml run`, ergonomia CLI e integração ponta a ponta.
  - Auditoria técnica independente de M5 realizada com identificação e resolução de 3 achados P1 (`ACH-M5-01`, `ACH-M5-02`, `ACH-M5-03`).
  - Desacoplamento irrestrito de qualquer domínio aplicado (RNF02) e isolamento formal de `CA02` como validação externa.
  - Integração e merge da branch `feat/m5-4-cli-run-end-to-end` na branch `main`.
  - Suíte completa de testes automatizados expandida para **471 testes**, 100% aprovados via `pytest`.
- **In-progress**: Planejamento e especificação dos requisitos do Marco M6 (`statistics` e CLI `stats`).
- **Next step**: Especificação e decomposição de tarefas de M6 (Etapa 5 — Consolidação Descritiva, Adequação Metodológica, Nadeau-Bengio, Wilcoxon, Holm-Bonferroni, Benjamini-Hochberg, Tamanho de Efeito, Fronteira de Pareto e CLI `stats`).
- **Blockers**: none
- **Branch**: main
