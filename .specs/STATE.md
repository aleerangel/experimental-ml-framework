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
- **Decision**: Adotar o processo de aceite de marcos (*Milestone Acceptance*) baseado em registros por funcionalidade (`spec.md`, `ACCEPTANCE.md`, `RESULTS.md`, acompanhados de `proofs.md` e `verification.md` no fluxo TLC Spec-Driven; os arquivos `SPEC.md` legados de M1 permanecem como registro histórico).
- **Reason**: Diferenciar a aprovação em testes automatizados do aceite formal da entrega, prevendo validação prática por interfaces públicas sob a perspectiva do consumidor e registro explícito de pendências.
- **Trade-off**: Requer a elaboração e manutenção dos documentos de especificação, aceite e verificação por marco, mantendo pendências manuais registradas explicitamente como PENDENTE.
- **Scope**: Todos os marcos do framework (M1 a M7 e Pós-MVP).
- **Date**: 2026-11-02 (emendada em 2026-11-17)
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
- **Decision**: Desacoplamento estrito do núcleo (`src/experimental_ml/` e `tests/`) de qualquer repositório externo ou domínio aplicado, mantendo a validação externa `CA02` (`TA-POS.4`) fora do repositório.
- **Reason**: Cumprir o princípio RNF02 (Independência de Domínio), assegurando que o código, a suíte de testes e a arquitetura não possuam referências ou acoplamentos a repositórios externos de aplicações específicas. Tutoriais e notebooks ilustrativos autocontidos (como estudos temáticos em `notebooks/` sem referência a repositórios externos) são permitidos.
- **Trade-off**: Testes automatizados operam exclusivamente com fixtures sintéticas autocontidas em memória ou disco temporário; a validação empírica em bases reais é conduzida externamente pelo usuário consumidor.
- **Scope**: `src/experimental_ml/`, `tests/` e documentos normativos de `docs/engenharia_software/`.
- **Date**: 2026-11-12 (emendada em 2026-11-17)
- **Status**: active

### AD-013
- **Decision**: Consolidação descritiva e adequação metodológica da Etapa 5 (Sub-marco M6.1) com:
  1. Portão de entrada Stage 4B $\rightarrow$ 5 (`validate_stage5_entry`) que reconhece `CANCELLED` como estado terminal de processo sem resultados utilizáveis (distinguindo-o de execuções ativas `PENDING`/`RUNNING`), exigindo conclusão ou cancelamento para prosseguir.
  2. Rastreamento tripartite de cobertura por configuração (`VALID` com $C=1.0$, `PARTIAL_COVERAGE` com $0 < C < 1.0$, e `NO_COVERAGE` com $C=0.0$) registrando separadamente `completed_fold_ids`, `failed_fold_ids` e `cancelled_fold_ids`.
  3. Estatísticas descritivas amostrais sem coerção artificial para zero: quando $n_{\text{valid}} = 0$, todos os campos numéricos são `None` e o status é `UNDEFINED_NAN`; quando $n_{\text{valid}} = 1$, `std = None` (sem variância amostral artificialmente zerada); e quando $n_{\text{valid}} \ge 2$, calcula desvio padrão amostral com `ddof=1`.
  4. Preservação de estabilidade por Jaccard $J(S_a, S_b)$ onde $S_a = S_b = \emptyset \implies 1.0$, e interseção vazia com pelo menos um não vazio $\implies 0.0$.
  5. Avaliação de adequação metodológica (`evaluate_method_suitability`) distinguindo estritamente $J = \text{len}(\text{folds})$ como número de partições de desenvolvimento (isolando completamente holdout final sob `CV_AND_HOLDOUT`), calculando razão de sobreposição de treino per-fold $r_j = n_{\text{val}, j} / n_{\text{train}, j}$ e média $\bar{r}$, diagnosticando $J < 6$ para Wilcoxon sem prometer poder estatístico para $J \ge 6$, e avaliando elegibilidade pareada sob políticas configuráveis (`REQUIRE_COMPLETE_PAIRS` vs `USE_COMMON_FOLDS`).
- **Reason**: Atender aos requisitos `RF5.1`, `RF5.2`, `RF5.3`, `CA-E5-01`, `CA-E5-02`, `STAT-01` a `STAT-07`, `RNF02` e `XCUT-02`, estabelecendo a base analítica descritiva e diagnóstica rigorosa antes da inferência estatística (M6.2), impedindo que falhas parciais ou cancelamentos corrompam inferências estatísticas e garantindo fidelidade metodológica estrita.
- **Trade-off**: Requer representação explícita de ausência de dispersão (`None`), controle detalhado de folds comuns entre pares de modelos e nulabilidade controlada em `AggregatedMetricStats`.
- **Scope**: Módulos `experimental_ml.statistics.types`, `consolidation`, `suitability` e portões de estágio.
- **Date**: 2026-11-16
- **Status**: active

### AD-014
- **Decision**: Núcleo de inferência estatística pareada, tamanho de efeito e ajuste de multiplicidade da Etapa 5B (Sub-marco M6.2) 100% em Python/NumPy puro (`XCUT-02`, zero `scipy` em runtime):
  1. Distribuição Student-$t$ exata (`_distributions.py`) via função Beta incompleta regularizada $I_x(a, b)$ por fração continuada modificada de Lentz e bisseção de quantis.
  2. Teste $t$ pareado corrigido de Nadeau-Bengio (`paired_nadeau_bengio_test`) com variância corrigida $(1/J + \bar{r}) S^2_d$, $\nu = J-1$, tratamento seguro para $S^2_d = 0$ ($\bar{d}=0$ vs $\bar{d}\ne 0$) e alerta para coeficiente de variação de tamanho dos *folds* $> 20\%$.
  3. Teste de Wilcoxon pareado (`paired_wilcoxon_test`) com suporte a `"wilcox"` e `"pratt"` (média e variância exatas de Pratt 1959), programação dinâmica exata sobre postos dobrados para $n_{\text{eff}} \le 20$ e $J \le 25$, aproximação normal com continuidade e empates para amostras maiores, e alerta para $J < 6$ ou $n_{\text{eff}} < 6$.
  4. Tamanho de efeito $d_z = \bar{d}/s_d$ (`compute_paired_cohens_d`) com intervalo analítico aproximado ($t_{\alpha/2, J-1}\sqrt{1/J + d_z^2/(2J)}$) e ressalva explícita de não-correção por sobreposição de CV.
  5. Ajustes de multiplicidade (`adjust_pvalues_holm`, `adjust_pvalues_bh`) aplicados independentemente aos $p$-valores de Nadeau-Bengio e Wilcoxon por família de hipóteses, e orquestrador `run_statistical_comparisons` com filtragem de `UNDEFINED_NAN` em células `COMPLETED`, bloqueio estrito em `HOLDOUT_ONLY` ($J=1$) e isolamento de `FINAL_HOLDOUT`.
- **Reason**: Atender aos requisitos `RF5.1`–`RF5.4`, `CA-E5-01`, `CA-E5-02`, `ADR-004`, `ADR-005`, `STAT-05`–`STAT-08` e `XCUT-02` sem introduzir dependências pesadas de runtime.
- **Trade-off**: Requer manutenção própria da função Beta incompleta regularizada e da DP combinatória de Wilcoxon.
- **Scope**: Módulos `experimental_ml.statistics._distributions`, `inference`, `multiplicity`, `comparisons`, `types` e `__init__`.
- **Date**: 2026-11-16
- **Status**: active

### AD-015
- **Decision**: Análise multiobjetivo de Pareto, funções de aquisição sequencial e síntese estruturada de conclusões da Etapa 5B/5C (Sub-marco M6.3) em Python/NumPy puro (`XCUT-02`):
  1. `compute_pareto_frontier` aceita exclusivamente configurações com `CoverageStatus.VALID` e objetivos finitos (`MetricStatus.VALID`), registrando configurações parciais ou indefinidas em `excluded_configurations` sem coerção para zero (`CA-E5-02`, `ADR-005`).
  2. `score_candidate_acquisition` implementa `EXPECTED_IMPROVEMENT`, `UCB`, `LCB`, `EXPLOITATION` e `EXPLORATION` com `math.erf` para $\Phi(z)$, tratamento contínuo de $\hat{\sigma}=0$ e desempate determinístico por `candidate_id`.
  3. `synthesize_conclusions` gera `StructuredConclusion` estritamente vinculada aos valores observados de 5A e 5B, preservando todas as ressalvas metodológicas e proibindo declarar equivalência a partir de $p_{\text{adj}} \ge \alpha$.
- **Reason**: Atender aos requisitos `RF5.5`, `RF5.6`, `CA-E5-02`, `ADR-005`, `STAT-09`–`STAT-11` e `XCUT-02`.
- **Trade-off**: Fronteira de Pareto exige cobertura completa (`VALID`) por padrão para impedir dominância espúria por configurações parciais.
- **Scope**: Módulos `experimental_ml.statistics.multiobjective`, `acquisition`, `synthesis`, `types` e `__init__`.
- **Date**: 2026-11-16
- **Status**: active

### AD-016
- **Decision**: Persistência JSON atômica, portão de estágio da Etapa 5 (`verify_statistics_gate`) e CLI `expml stats` (Sub-marco M6.4, encerrando o Marco M6):
  1. Persistência sob `{experiment_dir}/statistics/` (`descriptive_consolidation.json`, `method_suitability.json`, `statistical_comparisons.json`, `structured_conclusion.json`, `statistics_manifest.json` e `pareto_summary.json` opcional) com `write_json_atomic`, proteção `force=False` (`STORE-05`) e codificação explícita de não-finitos (`{"__nonfinite__": "NaN"|"Inf"|"-Inf"}`) em conformidade RFC 8259 (`ADR-005`).
  2. `verify_statistics_gate` valida o portão upstream Stage 4 (`verify_runs_gate`), a integridade estrutural dos artefatos de `statistics/` e o alinhamento estrito de `partition_plan_id` (`CA-GER-01`).
  3. CLI `expml stats` (`run`, `status`, `verify`) em `cli/cmd_stats.py` e `cli/main.py` com isolamento estrito de imports pesados (`CLI-10`), supressão de hashes brutos na saída (`CLI-11`) e códigos de saída padronizados `0`/`2`/`1` (`CLI-06`).
- **Reason**: Atender aos requisitos `STAT-12`–`STAT-14`, `STORE-03`, `STORE-05`, `CA-GER-01`, `CLI-06`–`CLI-11` e `XCUT-02`, entregando a Etapa 5 completa para consumo somente-leitura pela Etapa 6 (M7).
- **Trade-off**: Marcadores JSON explícitos para `NaN`/`Inf` exigem leitura via `load_statistics_artifacts` (ou decodificação consciente) em consumidores externos.
- **Scope**: Módulos `experimental_ml.statistics.storage`, `stages.stage_gates`, `cli.cmd_stats`, `cli.main` e `statistics.__init__`.
- **Date**: 2026-11-16
- **Status**: active

### AD-017
- **Decision**: Contratos de publicação, carregamento somente-leitura e construtores/renderizadores das 7 famílias de tabelas da Etapa 6 (Sub-marco M7.1) em Python/NumPy puro (`XCUT-02`):
  1. `ArtifactProvenance` exige caminhos exclusivamente relativos (`source_relative_paths`) para portabilidade (`CA-E6-02`).
  2. `load_experiment_artifacts_readonly` valida `verify_statistics_gate` e lê exclusivamente JSONs persistidos sem invocar ajuste/predição/tuning de modelos (`CA-E6-01`), enquanto `select_report_content` aplica filtragem determinística para `FULL_LAB` (A–G), `ARTICLE_COMPACT` (D, E, F) e `CUSTOM`.
  3. `build_table_model` cobre as 7 famílias (A–G), armazena valores numéricos exatos de `statistics/*.json` em `TableModel.rows` (sem arredondamento; formatação visual aplicada apenas nos renderizadores de texto), distingue `None` (`"N/A"`), `UNDEFINED_NAN` e `±Inf`, e exclui estruturalmente campos `*_hash`/`*_digest`/`sha256`/`checksum` sem afetar IDs legítimos do usuário.
- **Reason**: Atender aos requisitos `RF6.1`, `RF6.2`, `RF6.3`, `CA-E6-01`, `CA-E6-02`, `REP-01`–`REP-03` e `XCUT-02`.
- **Trade-off**: Formatação visual e precisão numérica integral (CSV) são desacopladas por coluna (`TableColumn.numeric_format`).
- **Scope**: Módulos `experimental_ml.reporting.types`, `loader`, `tables` e `__init__`.
- **Date**: 2026-11-16
- **Status**: active

### AD-018
- **Decision**: Renderização determinística de figuras (SVG, PNG 300 DPI, PDF 1.4) e composição do Relatório Científico Completo (Markdown e HTML autocontido) da Etapa 6 (Sub-marco M7.2) em Python/NumPy puro (`XCUT-02`, `RNF03`):
  1. `build_figure_spec` e `render_figure` (`figures.py`) operam 100% sem `matplotlib`/`pillow`/`scipy`, filtrando pontos não-finitos/`UNDEFINED_NAN` com registro em `notes` e produzindo bytes idênticos bit a bit (chunk PNG `pHYs = 11811` px/m para 300 DPI e PDF 1.4 com tabela `xref` exata).
  2. `render_full_report` (`report.py`) separa explicitamente *1. Declarações do Pesquisador*, *2. Fatos Computacionais Registrados* e *3. Interpretações Derivadas e Condicionadas*, mantendo paridade numérica (`CA-E6-01`), exclusão de campos `*_hash` (`CA-E6-02`), escape HTML seguro e CSS inline sem URLs externas (`RNF03`).
- **Reason**: Atender aos requisitos `RF6.1`, `RF6.2`, `RNF03`, `CA-E6-01`, `CA-E6-02`, `REP-04`, `REP-05` e `XCUT-02`.
- **Trade-off**: Renderização PNG/PDF implementada diretamente em NumPy + `zlib` + PDF 1.4 para eliminar dependências externas de runtime.
- **Scope**: Módulos `experimental_ml.reporting.figures`, `report`, `types` e `__init__`.
- **Date**: 2026-11-16
- **Status**: active

### AD-019
- **Decision**: Empacotamento de reprodutibilidade portátil e portão de integridade Stage 6 (Sub-marco M7.3) com caminhos 100% relativos POSIX e verificação SHA-256 byte-a-byte (`RF6.3`, `RF6.4`, `CA-E6-02`, `STORE-05`):
  1. `build_reproducibility_package` (`packaging.py`) exporta `tables/`, `figures/`, `reports/` e `reproducibility/` (`artifact_provenance.json`, `checksums.sha256`, `environment.json`, `seeds.json`, `REPRODUCE.md`) suportando `FULL_PACKAGE` e `REDUCED_NO_RAW_DATA`, com proteção pré-escrita `force=False` (`ContractViolationError`).
  2. `verify_report_gate` (`stage_gates.py`) valida upstream Stage 5 (`verify_statistics_gate` quando `statistics/` está presente), rejeita caminhos absolutos ou `..` traversal, garante cobertura de 100% em `artifact_provenance.json` e recalcula SHA-256 byte-a-byte, falhando com `DataIntegrityError` em qualquer divergência ou ausência.
- **Reason**: Atender aos requisitos `RF6.3`, `RF6.4`, `CA-E6-02`, `CA-GER-01`, `STORE-05`, `REP-06` e `REP-07`.
- **Trade-off**: `checksums.sha256` exclui a si mesmo da lista de digests e cobre 100% dos artefatos exportados e metadados de reprodutibilidade para compatibilidade direta com `sha256sum -c`.
- **Scope**: Módulos `experimental_ml.reporting.packaging`, `types`, `__init__` e `experimental_ml.stages.stage_gates`.
- **Date**: 2026-11-16
- **Status**: active

### AD-020
- **Decision**: Interface CLI `expml report` (`generate`, `export`, `verify`) e validação ponta a ponta Estágio 1 → Estágio 6 (Sub-marco M7.4):
  1. `cmd_report.py` e `cli/main.py` expõem `expml report generate`, `export` e `verify` com imports lazy (`CLI-10`), saída JSON sem hashes/digests brutos (`CLI-11`), proteção `--force` (`STORE-05`) e códigos de saída padronizados (`0` sucesso, `2` violação/integridade).
  2. Fluxo E2E completo validado desde `data profile` (Estágio 1) até `report verify` após movimentação do diretório do pacote (Estágio 6), mantendo `XCUT-02` (apenas stdlib + `numpy`).
- **Reason**: Atender aos requisitos `REP-08`, `REP-09`, `CLI-10`, `CLI-11`, `CA-E6-01`, `CA-E6-02` e `XCUT-02`.
- **Trade-off**: `partition_plan_id` (64-hex) é omitido do resumo JSON impresso no `stdout` do CLI para cumprimento estrito da regra `CLI-11`, permanecendo registrado nos artefatos persistidos e no retorno Python de `verify_report_gate`.
- **Scope**: Módulos `experimental_ml.cli.cmd_report` e `experimental_ml.cli.main`.
- **Date**: 2026-11-16
- **Status**: active

### AD-021
- **Decision**: Mega Auditoria Técnica Transversal do MVP (`TA-POS.1` / `pos-1-mega-auditoria-mvp`) concluída com saneamento integral de 6 achados `P0`, 16 `P1` e 6 `P2` (`0` achados `P0`/`P1` em aberto):
  1. Invariantes transversais automatizados em `tests/integration/test_mvp_audit_invariants.py` (pureza AST `XCUT-02` estática/dinâmica, 7 portões de estágio, `CLI-10` e `RNF02`) e regressões dedicadas em `tests/integration/test_mvp_audit_regressions.py`.
  2. Saneamento de isolamento de grupos/temporal em `CV_AND_HOLDOUT`/`HOLDOUT_ONLY`, aplicação de `ModelSpec.parameters` em `instantiate_fresh_model`, exclusão de `UNDEFINED_NAN` em `TOP_K_RELEVANCE`, `requires_probabilities`/`requires_kernel_matrix` em `METRICS_CATALOG`, precedência `ADR-005` + `compare_by_abs` em `mbe`, semente em `RANDOM_SEARCH`, `CLI-11` em `cmd_models.py`, round-trip `Finding` e sincronização integral dos documentos de `engenharia_software/`, `README.md`, `REFERENCIAS_E_FUNDAMENTACAO.md` e `pyproject.toml`.
- **Reason**: Garantir base científica, contratual e documental 100% consistente e congelável antes do Guia Definitivo do Pesquisador (`TA-POS.2`), da entrega de Usabilidade (`TA-POS.3`) e da validação externa `CA02` (`TA-POS.4`).
- **Trade-off**: `README.md` teve apenas divergências factuais corrigidas nesta etapa, reservando seu enxugamento completo (remoção de blocos longos de código e aprofundamentos de engenharia) para `TA-POS.2`.
- **Scope**: Todo o pacote `src/experimental_ml/`, suíte `tests/`, `docs/engenharia_software/*.md`, `README.md`, `docs/REFERENCIAS_E_FUNDAMENTACAO.md` e `pyproject.toml`.
- **Date**: 2026-11-16
- **Status**: active

### AD-022
- **Decision**: Sub-marco `TA-POS.2` (`pos-2-guia-pesquisador-cookbook`) concluído em português com arquitetura modular sob `docs/` (`docs/README.md`, `docs/guia/`, `docs/guias_praticos/`, `docs/referencia/`), enxugamento do `README.md` e suíte de integridade documental (`tests/unit/test_documentation_integrity.py`).
- **Reason**: Alinhar a usabilidade pedagógica e de referência do framework ao MVP congelado e auditado, mantendo o `README.md` limpo e validando automaticamente links, sintaxe AST, imports reais da API pública, comandos CLI `expml` e execução ponta a ponta (smoke test) do Início Rápido.
- **Trade-off**: O teste legado `test_hard_12_readme_python_blocks_execute_cleanly` foi redirecionado para validar os blocos Python executáveis em `docs/`, uma vez que o `README.md` passou a ser estritamente enxuto e livre de blocos de código Python.
- **Scope**: `README.md`, `docs/`, `tests/unit/test_documentation_integrity.py` e `tests/integration/test_m1_foundation_integration.py`.
- **Date**: 2026-11-16
- **Status**: active

### AD-022B
- **Decision**: Sub-marco `pos-2b-notebooks-interativos` concluído e posteriormente reorganizado em `pos-3` para uma trilha de 4 notebooks pré-executados em `notebooks/` (`01_primeiro_experimento_do_zero.ipynb`, `02_classificacao_e_grupos_na_pratica.ipynb`, `03_tour_6_etapas.ipynb`, `04_avancado_variantes_lssvm_prognose_florestal.ipynb`), com validação automatizada em `tests/unit/test_notebooks_execution.py`.
- **Reason**: Oferecer exemplos executáveis no Jupyter/Colab alinhados à jornada progressiva do pesquisador (do básico ao avançado).
- **Trade-off**: Notebooks armazenam saídas pré-executadas para leitura imediata sem necessidade de ambiente local prévio.
- **Scope**: `notebooks/*.ipynb` e `tests/unit/test_notebooks_execution.py`.
- **Date**: 2026-11-16 (reorganizada em 2026-11-17)
- **Status**: active

### AD-023
- **Decision**: Implementação do marco pós-MVP `TA-POS.3` (`pos-3-usabilidade-acessibilidade-pesquisador`, `USAB-01` a `USAB-03`): camada aditiva de usabilidade sem remoção de contratos M1–M7 (`expml init`, `expml quickrun`, `--rules` opcional, `--metrics` em `run start`, `--experiment-dir` unificado em `run {status,verify,resume}`, fachada Python `experimental_ml.run_experiment(...)` via PEP 562 e reorganização documental pelas Jornadas e 4 notebooks).
- **Reason**: Permitir que pesquisadores e alunos de IC sem experiência prévia em CLIs, JSONs ou na arquitetura interna conduzam experimentos científicos completos em 10 linhas de Python ou 2 comandos CLI, mantendo rigor anti-leakage e pureza `XCUT-02`.
- **Trade-off**: `run_experiment` encapsula as Etapas 1–6 com defaults explícitos, mantendo integralmente os módulos puros subjacentes para estudos avançados.
- **Scope**: `src/experimental_ml/__init__.py`, `pipeline.py`, `cli/`, `docs/`, `notebooks/`, `README.md` e `tests/unit/test_usability_cli_and_facade.py`.
- **Date**: 2026-11-17
- **Status**: active

### AD-024
- **Decision**: Implementação da configuração e detecção automática de formatação CSV (`csv-format-configuration`, `CSV-01` a `CSV-06`): `CsvFormatSpec` separado de `DatasetSchemaSpec` (preservando `schema_hash`), suporte a `decimal` (`"."`, `","`, `"auto"`), `quotechar`, `encoding` (`"utf-8-sig"`, `"auto"` com fallback `cp1252`), persistência opcional em `DatasetDescriptor` (`data/codecs.py` / `reconstruct_sanitized_view`), bloco `"csv_format"` em `schema.json`, flags CLI em `data profile` e `quickrun` (flags prevalecem sobre JSON) e parâmetros equivalentes em `run_experiment`.
- **Reason**: Suportar nativamente arquivos regionais (ex.: `;` com vírgula decimal e `latin-1`/`cp1252`) sem pré-conversão manual e sem corromper combinações ambíguas (`decimal=","` + `delimiter=","`).
- **Trade-off**: `CsvFormatSpec` é persistido em `DatasetDescriptor` (e não em `DatasetSchemaSpec`) para garantir retrocompatibilidade integral dos `schema_hash` existentes.
- **Scope**: `src/experimental_ml/data/`, `pipeline.py`, `cli/`, `stages/stage_gates.py`, `docs/` e `tests/unit/{data/test_csv_format.py,cli/test_csv_format_cli.py}`.
- **Date**: 2026-11-19
- **Status**: active

## Handoff

- **Feature**: csv-format-configuration (Concluída e Aceita)
- **Phase / Task**: Concluída com Verificação Independente (`PASS`).
- **Completed**:
  - `CsvFormatSpec`, `validate_csv_format_spec`, `detect_decimal`, desempate `detect_delimiter`, `decimal`/`quotechar`/`encoding="auto"` em `parsing.py` e `loader.py`.
  - Persistência de `csv_format` em `DatasetDescriptor`, `reconstruct_sanitized_view`, `run_experiment`, `expml data profile` e `expml quickrun`.
  - Sincronização de `README.md`, guias, referências, engenharia e `.specs/STATE.md`.
- **In-progress**: none
- **Next step**: Homologação científica externa (`CA02` / `TA-POS.4`) em dados reais pelo pesquisador.
- **Blockers**: none
- **Branch**: main
