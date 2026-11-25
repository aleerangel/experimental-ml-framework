# Registro Central de Validação Contínua do MVP

**Última atualização:** 24 de Novembro de 2026  
**Estado da fase:** Validação Contínua do MVP ativa  
**Documentos correlatos:** [AUDITORIA_TECNICA_DO_MVP.md](./AUDITORIA_TECNICA_DO_MVP.md) | [PLANO_DE_VALIDACAO_DO_MVP.md](./PLANO_DE_VALIDACAO_DO_MVP.md) | [ROADMAP_EVOLUCAO.md](./ROADMAP_EVOLUCAO.md)

---

## 1. Processo Formal e Leve de Registro de Achados da Validação

A validação do `experimental-ml-framework` é um processo contínuo conduzido em conjunto entre o desenvolvedor/pesquisador (por meio de testes funcionais, execução de experimentos reais e exploração de casos de borda) e o agente de engenharia.

### 1.1. Categorias de Achados

Todo achado identificado durante a auditoria ou relatado durante a experimentação contínua é classificado em uma das três categorias:

1. **`BUG` (Falha de Implementação ou Violação de Contrato):**
   - Comportamento incorreto, erro de execução inesperado (`Exception`/crash), cálculo incorreto, artefato corrompido/vazio ou divergência direta entre o contrato especificado (`ESPECIFICACAO_REQUISITOS.md`, `ARQUITETURA_E_CONTRATOS.md`, `spec.md`) e o código em `src/experimental_ml/`.
2. **`QUALITY` (Problema de Qualidade, Usabilidade, Apresentação ou Documentação):**
   - A funcionalidade executa sem violar a integridade matemática primária, mas apresenta limitações visuais, ergonomia deficiente na CLI/API, mensagens pouco claras, tabelas/relatórios com informações incompletas ou documentação dessincronizada com o código.
3. **`ENHANCEMENT` (Oportunidade de Melhoria ou Evolução Pós-MVP):**
   - Nova funcionalidade, extensão arquitetural, novo backend de visualização, suporte a novos algoritmos ou melhoria estrutural que amplia as capacidades do framework além do escopo estrito já implementado.

### 1.2. Ciclo de Vida de um Achado

Cada registro percorre sete estados rastreáveis:

```
Identificação ──► Investigação ──► Classificação ──► Decisão ──► Encaminhamento ──► Verificação ──► Encerramento
```

| Estado do Ciclo | Descrição Objetiva | Responsável pela Transição |
| :--- | :--- | :--- |
| **1. Identificação** | O comportamento ou limitação é observado em código, teste automatizado ou experimento manual do pesquisador. | Desenvolvedor ou Agente |
| **2. Investigação** | O agente localiza os módulos, linhas de código, requisitos e ADRs relacionados e coleta evidências reprodutíveis. | Agente |
| **3. Classificação** | O achado recebe identificador (`VAL-BUG-xxx`, `VAL-QUAL-xxx`, `VAL-ENH-xxx`), prioridade (`P0`, `P1`, `P2`) e recomendação técnica. | Agente |
| **4. Decisão** | O desenvolvedor aprova o destino do achado: corrigir na estabilização do MVP (`M8`), planejar em marco futuro (`M9`, `M10`, Onda 2), abrir revisão de ADR ou aceitar como limitação conhecida. | **Desenvolvedor** (exclusivo) |
| **5. Encaminhamento** | O item é vinculado à `spec.md` e `tasks.md` do marco correspondente para execução sob o fluxo TLC. | Agente + Desenvolvedor |
| **6. Verificação** | Após a implementação no marco correspondente, um teste automatizado prova a correção e o Verificador Independente emite `verification.md: PASS`. | Agente (Verificador TLC) |
| **7. Encerramento** | O desenvolvedor homologa o comportamento via `ACCEPTANCE.md` e o status do achado passa para `ENCERRADO`. | **Desenvolvedor** |

### 1.3. Critérios Objetivos de Decisão e Encaminhamento

Para apoiar a decisão do desenvolvedor sem ambiguidade, aplicam-se cinco regras de triagem:

1. **Quando corrigir na estabilização do MVP (`Destino: Marco M8 — Estabilização do MVP`):**
   - O achado é um `BUG` de prioridade `P0` ou `P1` em funcionalidade que já faz parte do contrato aprovado da Onda 1, cuja correção é localizada, não exige nova dependência externa e não altera ADRs aprovados (ex.: Tabelas A e G vazias, `TypeError` com `None` em variáveis categóricas na Etapa 2, artefatos ausentes em `run_experiment`, `n_total_candidates` no índice de Kuncheva).
2. **Quando planejar como evolução em marco dedicado de curto prazo (`Destino: Marco M9 ou M10`):**
   - O achado envolve completar um subsistema que requer desenho de novos componentes internos ou revisão controlada de contrato (ex.: implementar `IMPUTER` e codificação categórica intra-fold conectados a `deferred_rules` e executar células `FINAL_HOLDOUT` em `M9`; redesenhar o subsistema de visualização científica e relatórios em `M10`).
3. **Quando abrir revisão arquitetural formal (`Destino: Revisão de ADR`):**
   - A melhor solução técnica entra em tensão com uma restrição arquitetural vigente (ex.: adotar `matplotlib` e/ou `pandas` na camada de relatórios/visualização frente ao `XCUT-02`, ou decidir entre mover a seleção dinâmica para dentro do loop interno do Nested CV conforme `ADR-003` vs. documentar seleção no fold externo).
4. **Quando especificar novo marco de expansão (`Destino: Roadmap Pós-MVP / Onda 2`):**
   - Trata-se de nova capacidade científica ou de engenharia fora do escopo do MVP clássico (ex.: paralelismo multi-processo distribuído, novos adaptadores de modelos, integração com circuitos quânticos na Onda 2).
5. **Quando aceitar como limitação conhecida (`Destino: Limitação Conhecida Documentada`):**
   - O custo ou complexidade de alteração supera o benefício para o ciclo atual de pesquisa, desde que o comportamento esteja explicitamente documentado e não produza resultados cientificamente inválidos de forma silenciosa.

### 1.4. Como o Desenvolvedor Pode Relatar Novos Achados Informalmente

Durante seus testes manuais e experimentos, **o desenvolvedor não precisa preencher a ficha técnica de 15 campos**. Basta relatar a observação em linguagem natural no chat, por exemplo:

- *"Rodei o `expml quickrun` num CSV com valores ausentes na coluna `idade` usando `DEFER_INTRA_FOLD` e deu erro na Etapa 4."*
- *"Olhei a imagem `redundancy_matrix.png` do meu dataset e os nomes das colunas ficaram cortados no topo."*
- *"Notei que no `report.md` a tabela de diagnósticos do Random Forest veio vazia."*
- *"Seria muito útil poder escolher duas métricas para a fronteira de Pareto direto no `stats_config.json` pela CLI."*

Ao receber qualquer relato desse tipo, o agente executará automaticamente o protocolo:
1. Reproduzir ou inspecionar o código e os contratos associados.
2. Solicitar informações adicionais **apenas** se forem estritamente necessárias para compreender o cenário.
3. Preencher os 15 campos obrigatórios neste documento (`REGISTRO_DE_VALIDACAO_DO_MVP.md`).
4. Apresentar o diagnóstico técnico, o impacto e a recomendação de encaminhamento para decisão do desenvolvedor.
5. Atualizar `ROADMAP_EVOLUCAO.md` ou as especificações preliminares em `.specs/features/` conforme a decisão tomada.

---

## 2. Índice Resumido dos Achados Registrados

| ID | Título Resumido | Categoria | Prioridade | Módulo Afetado | Destino Recomendado | Status Atual |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| [`VAL-BUG-001`](#val-bug-001) | Regra `DEFER_INTRA_FOLD` e `IMPUTER` não executados na Etapa 4B | `BUG` | `P0` | `data/preparation.py`, `models/preprocessing/pipeline.py`, `orchestration/execution.py` | Marco `M9` (Imputação e Encoding Intra-Fold) | `IDENTIFICADO (Aguardando Decisão)` |
| [`VAL-BUG-002`](#val-bug-002) | Tabela da Família A (`tbl_family_a`) sempre vazia (0 linhas) em experimentos reais | `BUG` | `P0` | `reporting/tables.py`, `data/codecs.py` | Marco `M8` (Estabilização do MVP) | `IDENTIFICADO (Aguardando Decisão)` |
| [`VAL-BUG-003`](#val-bug-003) | Tabela da Família G (`tbl_family_g`) lê `models.json` em vez de `runs/cells/` e fica sempre vazia | `BUG` | `P0` | `reporting/tables.py`, `reporting/loader.py` | Marco `M8` (Estabilização do MVP) | `IDENTIFICADO (Aguardando Decisão)` |
| [`VAL-BUG-004`](#val-bug-004) | `TypeError` em `compute_correlation_ratio` e `compute_cramers_v` quando há `None` em coluna categórica | `BUG` | `P0` | `features/stats.py` | Marco `M8` (Estabilização do MVP) | `IDENTIFICADO (Aguardando Decisão)` |
| [`VAL-BUG-005`](#val-bug-005) | Seleção dinâmica executada fora do loop interno do Nested CV (desvio de `ADR-003`) e `preprocessing_config` ignorado | `BUG` | `P1` | `orchestration/execution.py`, `tuning/engine.py`, `tuning/partitioning.py` | Marco `M8` (Alinhamento `ADR-003`) | `IDENTIFICADO (Aguardando Decisão)` |
| [`VAL-BUG-006`](#val-bug-006) | Falhas visuais e geométricas nos renderizadores de figuras da Etapa 6 (PNG sem texto, PDF só barras, SVG Pareto por índice) | `BUG` | `P1` | `reporting/figures.py` | Marco `M10` (Redesenho de Visualização e Relatórios) | `IDENTIFICADO (Aguardando Decisão)` |
| [`VAL-BUG-007`](#val-bug-007) | Fachada `run_experiment` grava artefatos incompletos em disco (quebrando CLI subsequente) e ignora `seed` em instâncias prontas | `BUG` | `P1` | `pipeline.py` | Marco `M8` (Estabilização do MVP) | `IDENTIFICADO (Aguardando Decisão)` |
| [`VAL-BUG-008`](#val-bug-008) | Partição `holdout_ids` nunca é executada como célula `FINAL_HOLDOUT` no regime `CV_AND_HOLDOUT` | `BUG` | `P1` | `orchestration/matrix.py`, `orchestration/execution.py` | Marco `M9` (Imputação, Encoding e Holdout Final) | `IDENTIFICADO (Aguardando Decisão)` |
| [`VAL-BUG-009`](#val-bug-009) | Kuncheva retorna `None` na CLI/fachada, Pareto na CLI é fixo em 1 objetivo e `FULL_CONFIGURATIONS` equivale a `ALL_PAIRWISE` | `BUG` | `P1` | `cli/cmd_stats.py`, `pipeline.py`, `statistics/consolidation.py`, `statistics/comparisons.py` | Marco `M8` (Estabilização do MVP) | `IDENTIFICADO (Aguardando Decisão)` |
| [`VAL-BUG-010`](#val-bug-010) | `MatrixExecutionState` não valida `scenarios_hash`/`models_hash` no resume, gera prefixo duplo `cell_cell_` e muta `_ACTIVE_INSTANCES` sem lock | `BUG` | `P2` | `orchestration/state.py`, `orchestration/storage.py`, `models/execution.py` | Marco `M8` (Estabilização do MVP) | `IDENTIFICADO (Aguardando Decisão)` |
| [`VAL-BUG-011`](#val-bug-011) | Script TLC `validate_verification.py` busca `PROCESSO_DE_ACEITE_DE_MARCOS.md` sem o prefixo `docs/` | `BUG` | `P2` | `.agent/skills/tlc-spec-driven/scripts/validate_verification.py` | Marco `M8` (Manutenção de Ferramental TLC) | `IDENTIFICADO (Aguardando Decisão)` |
| [`VAL-QUAL-001`](#val-qual-001) | Limitações tipográficas e de layout nos gráficos PNG em NumPy puro da Etapa 2 (`features/visualization.py`) | `QUALITY` | `P1` | `features/visualization.py` | Marco `M10` (Subsistema de Visualização Científica) | `IDENTIFICADO (Aguardando Decisão)` |
| [`VAL-QUAL-002`](#val-qual-002) | Tabelas B e C da Etapa 6 omitem metadados científicos e `report.md` é gerado em inglês sem glossário estatístico | `QUALITY` | `P1` | `reporting/tables.py`, `reporting/report.py` | Marco `M10` (Redesenho de Visualização e Relatórios) | `IDENTIFICADO (Aguardando Decisão)` |
| [`VAL-QUAL-003`](#val-qual-003) | `expml init` para classificação cria apenas 1 modelo (0 comparações pareadas) e `quickrun` não exporta tabelas/figuras avulsas | `QUALITY` | `P2` | `cli/cmd_init.py`, `cli/cmd_report.py`, `pipeline.py` | Marco `M8` (Estabilização do MVP) | `IDENTIFICADO (Aguardando Decisão)` |
| [`VAL-QUAL-004`](#val-qual-004) | Divergências de nomenclatura de contratos em `ARQUITETURA_E_CONTRATOS.md` e omissões em `api_python.md` / `.specs/` | `QUALITY` | `P2` | `docs/engenharia_software/ARQUITETURA_E_CONTRATOS.md`, `docs/referencia/api_python.md`, `.specs/` | Consolidação Documental + Marco `M8` | `PARCIALMENTE CORRIGIDO / AGUARDANDO DECISÃO` |
| [`VAL-ENH-001`](#val-enh-001) | Arquitetura desacoplada de visualização científica com backend `Matplotlib`/`Pandas` e revisão controlada do `XCUT-02` | `ENHANCEMENT` | `P1` | `reporting/figures.py`, `features/visualization.py` | Marco `M10` + Revisão de ADR (`XCUT-02`) | `PLANEJADO (Aguardando Decisão Arquitetural)` |
| [`VAL-ENH-002`](#val-enh-002) | Pipeline completo de Imputação (`MEAN`, `MEDIAN`, `MODE`) e Codificação Categórica (`ONE_HOT`, `ORDINAL`) Intra-Fold | `ENHANCEMENT` | `P1` | `models/preprocessing/`, `orchestration/execution.py`, `data/preparation.py` | Marco `M9` | `PLANEJADO (Aguardando Aprovação de Escopo)` |
| [`VAL-ENH-003`](#val-enh-003) | Execução, persistência e consolidação estatística de células `FINAL_HOLDOUT` no regime `CV_AND_HOLDOUT` | `ENHANCEMENT` | `P1` | `orchestration/`, `statistics/`, `reporting/` | Marco `M9` | `PLANEJADO (Aguardando Aprovação de Escopo)` |
| [`VAL-ENH-004`](#val-enh-004) | Suporte a múltiplos objetivos de Pareto e `planned_pairs` em `stats_config.json` na CLI e na fachada `run_experiment` | `ENHANCEMENT` | `P2` | `cli/cmd_stats.py`, `pipeline.py`, `statistics/comparisons.py` | Marco `M8` / `M10` | `PLANEJADO (Aguardando Aprovação de Escopo)` |

---

## 3. Fichas Detalhadas dos Achados (`BUG`, `QUALITY`, `ENHANCEMENT`)

### `VAL-BUG-001`
- **Identificador único:** `VAL-BUG-001`
- **Título:** Regra `DEFER_INTRA_FOLD` e transformador `IMPUTER` declarados na Etapa 1/3 não são executados na Etapa 4B
- **Categoria:** `BUG`
- **Data de identificação:** 2026-11-24
- **Módulo afetado:** `src/experimental_ml/data/preparation.py`, `src/experimental_ml/models/preprocessing/pipeline.py`, `src/experimental_ml/orchestration/execution.py`
- **Descrição:** O módulo de preparação da Etapa 1 permite ao pesquisador declarar regras `kind="DEFER_INTRA_FOLD"` para tratar valores ausentes (`E1_FEATURE_MISSING` com `imputation_strategy` em `MEAN`, `MEDIAN`, `MODE`), variáveis categóricas não codificadas (`E1_CATEGORICAL_UNENCODED`) e disparidade de escala (`E1_SCALE_DISPARITY`) dentro de cada fold na Etapa 4B. Porém, as regras salvas em `SanitizedDatasetView.deferred_rules` nunca são lidas pelos módulos de execução, e o transformador `"IMPUTER"` aceito na validação estática da Camada 1 não possui implementação em `_instantiate_step_transformer`.
- **Comportamento observado:**
  1. `SanitizedDatasetView.deferred_rules` (`data/preparation.py:L577`) não é referenciado em nenhum arquivo fora de `data/`.
  2. Se um dataset possui `NaN` preservado por `DEFER_INTRA_FOLD`, `fit_two_layer_preprocessing` (`models/preprocessing/pipeline.py:L199-200`) verifica `if not np.all(np.isfinite(x_arr))` antes mesmo de rodar a Camada 1 e lança `ContractViolationError: Input matrix X_train contains NaN or Inf values`.
  3. Se um `ModelSpec` inclui `PreprocessingStepSpec(layer=1, transformer_type="IMPUTER", ...)`, `validate_two_layer_preprocessing` (`pipeline.py:L42`) aprova a configuração, mas `_instantiate_step_transformer` (`pipeline.py:L126-165`) lança `ConfigurationError: Unsupported transformer_type: IMPUTER`.
  4. Se uma coluna categórica (`dtype=object`) é diferida via `DEFER_INTRA_FOLD`, `np.column_stack` em `orchestration/execution.py:L131` converte toda a matriz `X_train_cand` para `dtype=object`, falhando em `np.isfinite`.
- **Comportamento esperado:** As regras `DEFER_INTRA_FOLD` registradas na Etapa 1 (ou passos `IMPUTER` / encoders configurados na Camada 1) devem ajustar seus parâmetros (`mean`, `median`, `mode`, categorias) exclusivamente sobre `X_train` de cada fold (interno e externo) e transformar `X_train` e `X_val` sem vazamento de informação (`RF1.2`, `RF3.2`, `CA-E1-02`).
- **Evidências:** `src/experimental_ml/data/preparation.py:L141-150,L221-242,L577`; `src/experimental_ml/models/preprocessing/pipeline.py:L42,L126-165,L199-200`; `src/experimental_ml/orchestration/execution.py:L120-175`.
- **Impacto:** Alto. Qualquer experimento com dados reais que contenha `NaN` ou colunas texto e opte por imputação/codificação intra-fold (em vez de `DROP_ROWS` ou `EXCLUDE_COLUMN` na Etapa 1) falha ao chegar na Etapa 4B.
- **Prioridade:** `P0`
- **Dependências:** Relacionado a `VAL-BUG-005` (ordem de execução entre Camada 1, seleção dinâmica de atributos e Camada 2 conforme `ADR-003`).
- **Destino:** Marco `M9` (`m9-intra-fold-imputation-encoding-holdout`). Caso o desenvolvedor deseje uma proteção imediata já em `M8`, pode-se emitir um erro explícito orientativo ou implementar o `IMPUTER` numérico básico.
- **Status:** `IDENTIFICADO (Aguardando Decisão)`
- **Decisão e justificativa:** Recomendado estruturar a solução completa no Marco `M9` (Specify → Design → Tasks → Execute), pois requer definir o contrato exato de expansão de colunas para variáveis categóricas (ou restrição a encoding ordinal/numérico no MVP) e a ligação automática entre `SanitizedDatasetView.deferred_rules` e a Camada 1 de pré-processamento.

---

### `VAL-BUG-002`
- **Identificador único:** `VAL-BUG-002`
- **Título:** Tabela da Família A (`tbl_family_a` — Caracterização e Triagem de Dados) fica sempre vazia (0 linhas) em experimentos reais
- **Categoria:** `BUG`
- **Data de identificação:** 2026-11-24
- **Módulo afetado:** `src/experimental_ml/reporting/tables.py`, `src/experimental_ml/data/codecs.py`
- **Descrição:** A função `build_table_model` para `ReportFamily.A_DATA_CHARACTERIZATION` procura propriedades escalares no nível raiz do dicionário `loaded_data.dataset_profile`, mas o codec `dataset_profile_to_dict` serializa todas as informações dentro da subchave `"summary"`.
- **Comportamento observado:** Em `reporting/tables.py:L99-112`, o loop `for k, v in sorted(dp.items())` ignora chaves terminadas em `_hash` (`"source_dataset_hash"`) e exige `isinstance(v, (str, int, float, bool)) or v is None`. Como a única outra chave de topo em `data/dataset_profile.json` é `"summary"` (um `dict` contendo `n_rows`, `n_cols`, `memory_bytes`, `columns`, `findings`, `Cleanliness_score`), ela é descartada. A tabela resultante possui `rows=()` (0 linhas) e exibe `"No data available for this report family."` em todos os relatórios reais (incluindo os notebooks `01` e `02`).
- **Comportamento esperado:** `build_table_model(ReportFamily.A_DATA_CHARACTERIZATION)` deve inspecionar `dp.get("summary", dp)` e extrair as métricas de caracterização da base (`n_rows`, `n_cols`, `memory_bytes`, contagem de variáveis por tipo semântico, número de achados de triagem e regras aplicadas no `preparation_plan`).
- **Evidências:** `src/experimental_ml/reporting/tables.py:L99-112`; `src/experimental_ml/data/codecs.py:L67-77`; `tests/unit/test_reporting_tables.py:L143` (onde o teste unitário mockou `{"n_rows": 50, "n_cols": 4}` diretamente na raiz).
- **Impacto:** Alto. A primeira tabela científica do relatório (`report.md`, `report.html` e exportações `CSV`/`MD`/`LaTeX`) sai sempre em branco em execuções reais.
- **Prioridade:** `P0`
- **Dependências:** Nenhuma.
- **Destino:** Marco `M8` (`m8-mvp-stabilization-contract-alignment`).
- **Status:** `IDENTIFICADO (Aguardando Decisão)`
- **Decisão e justificativa:** Correção direta e de baixo risco no Marco `M8`, acompanhada de teste de integração usando a saída real de `dataset_profile_to_dict`.

---

### `VAL-BUG-003`
- **Identificador único:** `VAL-BUG-003`
- **Título:** Tabela da Família G (`tbl_family_g` — Artefatos Específicos por Família de Modelos) lê `configuration/models.json` em vez de `runs/cells/` e fica sempre vazia
- **Categoria:** `BUG`
- **Data de identificação:** 2026-11-24
- **Módulo afetado:** `src/experimental_ml/reporting/tables.py`, `src/experimental_ml/reporting/loader.py`
- **Descrição:** A construção da tabela da Família G busca diagnósticos ajustados (`m.get("diagnostics", {})`) dentro do catálogo declarativo `configuration/models.json`, onde eles nunca existem, pois os diagnósticos pós-treino (`ModelDiagnostics`) são persistidos individualmente nos registros de células em `runs/cells/cell_*.json`.
- **Comportamento observado:** `build_table_model(ReportFamily.G_MODEL_SPECIFIC_ARTIFACTS)` (`reporting/tables.py:L243-260`) itera sobre `loaded_data.models_catalog`. Como `models_catalog` contém apenas `ModelSpec`s serializados antes do treinamento (sem chave `"diagnostics"`), `rows` permanece vazia e o relatório exibe `"No model-specific adapter diagnostics exported."`, mesmo após o marco `sklearn-ensemble-diagnostics` ter implementado e persistido `feature_importances`, `oob_score`, `coefficients` e `n_support_vectors` nas células.
- **Comportamento esperado:** `reporting/loader.py` deve carregar (ou consolidar a partir de `runs/cells/*.json`) os objetos `diagnostics` extraídos das células concluídas, agregando por `(model_id, scenario_id)` as médias e desvios-padrão de importâncias de atributos, coeficientes lineares, `oob_score`, número de vetores de suporte e épocas de convergência na Tabela G.
- **Evidências:** `src/experimental_ml/reporting/tables.py:L243-260`; `src/experimental_ml/reporting/loader.py:L100-115`; `src/experimental_ml/orchestration/codecs.py:L36-78`.
- **Impacto:** Alto. Toda a instrumentação de diagnósticos específicos de modelos (`RF3.3` e feature `sklearn-ensemble-diagnostics`) fica invisível no relatório final da Etapa 6.
- **Prioridade:** `P0`
- **Dependências:** Nenhuma.
- **Destino:** Marco `M8` (`m8-mvp-stabilization-contract-alignment`).
- **Status:** `IDENTIFICADO (Aguardando Decisão)`
- **Decisão e justificativa:** Correção essencial no Marco `M8` para conectar a extração de diagnósticos já existente nas células à camada de relatórios da Etapa 6.

---

### `VAL-BUG-004`
- **Identificador único:** `VAL-BUG-004`
- **Título:** `TypeError` em `compute_correlation_ratio` e `compute_cramers_v` quando colunas categóricas contêm valores ausentes (`None`)
- **Categoria:** `BUG`
- **Data de identificação:** 2026-11-24
- **Módulo afetado:** `src/experimental_ml/features/stats.py`
- **Descrição:** As funções de associação para variáveis categóricas na Etapa 2 não filtram valores `None` em arrays NumPy de `dtype=object` antes de invocar `np.unique`.
- **Comportamento observado:**
  1. Em `compute_correlation_ratio` (`features/stats.py:L134-148`), `valid_mask = ~np.isnan(cont_arr)` verifica apenas o array contínuo. Se `cat_arr` (`dtype=object`) contiver `None` em uma linha onde `cont_arr` não é `NaN`, `np.unique(cat_clean)` na linha 148 falha com `TypeError: '<' not supported between instances of 'NoneType' and 'str'`.
  2. Em `compute_cramers_v` (`features/stats.py:L185-186`), `np.unique(x_arr, return_inverse=True)` é chamado diretamente sem filtrar `None` ou `NaN`, lançando o mesmo `TypeError` caso haja qualquer valor ausente nas colunas categóricas.
- **Comportamento esperado:** Ambas as funções devem construir uma máscara conjunta de validade que exclua pares com `None`, `np.nan` ou strings vazias não mapeadas tanto no vetor contínuo quanto nos vetores categóricos (de forma análoga ao tratamento pairwise já feito em `compute_pearson` e `compute_spearman`).
- **Evidências:** `src/experimental_ml/features/stats.py:L128-218`.
- **Impacto:** Alto. Impede a execução da análise exploratória da Etapa 2 em datasets com variáveis categóricas que possuam valores faltantes não removidos via `DROP_ROWS`.
- **Prioridade:** `P0`
- **Dependências:** Nenhuma.
- **Destino:** Marco `M8` (`m8-mvp-stabilization-contract-alignment`).
- **Status:** `IDENTIFICADO (Aguardando Decisão)`
- **Decisão e justificativa:** Correção pontual e determinística recomendada para o Marco `M8`.

---

### `VAL-BUG-005`
- **Identificador único:** `VAL-BUG-005`
- **Título:** Seleção dinâmica de atributos executada fora do loop interno do Nested CV (desvio do `ADR-003`), `FeatureScenario.preprocessing_config` ignorado e folds internos sem estratificação/agrupamento
- **Categoria:** `BUG`
- **Data de identificação:** 2026-11-24
- **Módulo afetado:** `src/experimental_ml/orchestration/execution.py`, `src/experimental_ml/tuning/engine.py`, `src/experimental_ml/tuning/partitioning.py`, `src/experimental_ml/features/scenarios.py`
- **Descrição:** O `ADR-003` (`ARQUITETURA_E_CONTRATOS.md:L745-781`) define a ordem estrita de operações intra-fold quando há pré-processamento em duas camadas, seleção dinâmica de atributos (`ScenarioMode.DYNAMIC`) e tuning via Nested CV: dentro de cada fold interno `(inner_train, inner_val)`, deve-se ajustar a Camada 1, selecionar os atributos dinamicamente em `inner_train`, ajustar a Camada 2 e avaliar o candidato em `inner_val`; concluído o tuning, reajusta-se todo o pipeline no `outer_train` completo. Na implementação atual, a seleção dinâmica ocorre uma única vez no `outer_train` antes do Nested CV.
- **Comportamento observado:**
  1. Em `execute_single_cell` (`orchestration/execution.py:L120-141`), `select_features_in_fold(X_train_cand, y_train, ...)` é executado no fold externo completo antes de `run_nested_tuning`. Os folds internos de tuning recebem `X_train_sel` já filtrado com uso dos rótulos `y_in_val`. (Nota: o fold de validação externo `X_val, y_val` permanece estritamente isolado).
  2. Tanto `layer1_steps` quanto `layer2_steps` de `ModelSpec.preprocessing` são executados juntos em `fit_two_layer_preprocessing` (`execution.py:L171-174`) **depois** da seleção de atributos, e o campo `FeatureScenario.preprocessing_config` (`features/scenarios.py:L59`) nunca é lido.
  3. `split_inner_folds` (`tuning/partitioning.py:L12-80`) divide `X_train` sequencialmente sem embaralhamento e sem respeitar `group_col` (`GROUP_KFOLD`), estratificação de classes (`STRATIFIED_KFOLD`) ou janela temporal (`TEMPORAL`).
- **Comportamento esperado:** Conformidade integral entre `ADR-003` e `orchestration/execution.py` + `tuning/engine.py`: (a) aplicar Camada 1 antes da seleção dinâmica, (b) executar seleção dinâmica dentro de cada fold interno durante o Nested CV (ou revisar formalmente o `ADR-003` caso se decida manter seleção no nível do fold externo) e (c) propagar a estratégia de particionamento (estratificada/agrupada/temporal) para `split_inner_folds`.
- **Evidências:** `docs/engenharia_software/ARQUITETURA_E_CONTRATOS.md:L745-781`; `src/experimental_ml/orchestration/execution.py:L120-175`; `src/experimental_ml/tuning/engine.py:L126-159`; `src/experimental_ml/tuning/partitioning.py:L12-80`.
- **Impacto:** Médio-Alto (Metodológico). Não há vazamento para o conjunto de validação externo (`X_val`), mas há vazamento entre treino interno e validação interna durante a escolha de hiperparâmetros quando `ScenarioMode.DYNAMIC` (`TOP_K_RELEVANCE`) é combinado com `GRID_SEARCH`/`RANDOM_SEARCH`.
- **Prioridade:** `P1`
- **Dependências:** Relacionado a `VAL-BUG-001`.
- **Destino:** Marco `M8` (`m8-mvp-stabilization-contract-alignment`).
- **Status:** `IDENTIFICADO (Aguardando Decisão)`
- **Decisão e justificativa:** Recomenda-se corrigir no Marco `M8` passando o callback/especificação de seleção de atributos e a estratégia de particionamento para `run_nested_tuning`, cumprindo integralmente o `ADR-003`.

---

### `VAL-BUG-006`
- **Identificador único:** `VAL-BUG-006`
- **Título:** Falhas visuais e geométricas severas nos renderizadores de figuras da Etapa 6 (PNG sem texto, PDF apenas barras azuis sem IC, SVG Pareto indexado por posição da lista)
- **Categoria:** `BUG`
- **Data de identificação:** 2026-11-24
- **Módulo afetado:** `src/experimental_ml/reporting/figures.py`
- **Descrição:** O módulo `reporting/figures.py` gera arquivos `.svg`, `.png` (300 DPI) e `.pdf` estruturalmente válidos para os testes de fumaça binários, mas com defeitos graves de renderização visual e geometria científica.
- **Comportamento observado:**
  1. **PNG (`_render_png_300dpi`, `L253-302`):** Não possui nenhuma rotina de desenho de texto (ao contrário de `features/visualization.py`). Os PNGs da Etapa 6 contêm apenas retângulos coloridos sobre duas linhas de eixo cinzas, sem título, sem nomes de modelos/cenários, sem rótulos de eixo e sem números de escala.
  2. **PDF (`_render_pdf`, `L305-356`):** Ignora `spec.plot_type`, ignora `s.y_err` (intervalos de confiança não são desenhados), usa uma única cor azul fixa para todas as séries e desenha barras verticais preenchidas (`re f`) mesmo para gráficos `PAIRED_DIFF_CI` e `PARETO_TRADEOFF`, também sem rótulos de eixo nem escala numérica.
  3. **SVG (`_render_svg`, `L193-245`):** Em `PlotType.PARETO_TRADEOFF` (`L220`), calcula a posição horizontal `cx = ml + (i + 0.5) * step` a partir do **índice `i` da série** em vez do valor numérico `s.x_values[i]`. Com isso, o primeiro ponto da série `"Dominated"` (`i=0`) é desenhado exatamente na mesma coordenada X do primeiro ponto da série `"Pareto Optimal"` (`i=0`). Além disso, o SVG não possui marcas numéricas no eixo Y, não desenha a linha $y=0$ em `PAIRED_DIFF_CI` e não renderiza legenda.
  4. **Famílias A, B, C e G (`build_figure_spec`, `L149-160`):** Caem todas em um gráfico dummy idêntico de 1 única barra (`"total_configs"`), e os tipos `SCATTER_PARITY`, `HEATMAP` e `LINE_LEARNING` (`RF6.2`) nunca são construídos.
- **Comportamento esperado:** Figuras científicas legíveis, com escalas numéricas fiéis às coordenadas reais dos dados, intervalos de confiança visíveis em todos os formatos (`SVG`, `PNG 300 DPI`, `PDF`), títulos, eixos rotulados e legendas claras (`RF6.2`, `CA-E6-02`).
- **Evidências:** `src/experimental_ml/reporting/figures.py:L50-357`; `tests/unit/test_reporting_figures.py` (os testes existentes verificam apenas `b"\x89PNG"`, `b"pHYs"` e `b"%PDF-1.4"`, sem inspecionar a geometria ou presença de texto).
- **Impacto:** Alto na apresentação científica dos resultados.
- **Prioridade:** `P1`
- **Dependências:** Diretamente conectado à avaliação arquitetural do Subsistema de Visualização (`VAL-ENH-001` / Marco `M10`).
- **Status:** `IDENTIFICADO (Aguardando Decisão)`
- **Destino:** Marco `M10` (`m10-scientific-visualization-reporting-redesign`).
- **Decisão e justificativa:** Em vez de remendar o rasterizador manual de pixels e streams PDF crus em `reporting/figures.py`, recomenda-se tratar este item no Marco `M10` adotando uma arquitetura desacoplada de visualização (com `matplotlib` na camada de apresentação/relatórios, conforme análise na Seção 3 de `ROADMAP_EVOLUCAO.md`).

---

### `VAL-BUG-007`
- **Identificador único:** `VAL-BUG-007`
- **Título:** Fachada `run_experiment` salva artefatos incompletos em disco (quebrando comandos CLI subsequentes) e ignora `seed` ao clonar instâncias prontas de modelos
- **Categoria:** `BUG`
- **Data de identificação:** 2026-11-24
- **Módulo afetado:** `src/experimental_ml/pipeline.py`
- **Descrição:** Quando o pesquisador executa um experimento pela fachada Python `run_experiment(..., experiment_dir="meu_exp")`, o diretório resultante não contém todos os artefatos canônicos que os gates da CLI `expml` exigem. Adicionalmente, a fábrica interna `_make_inst_factory` para instâncias prontas de estimadores ignora o argumento `seed`.
- **Comportamento observado:**
  1. Em `pipeline.py:L358-384`, `run_experiment` grava `data/dataset_descriptor.json` contendo apenas `{"dataset_hash": ...}` (sem `raw_source_path` e `schema_path`), e **não grava** `data/sanitized_view.json`, `partitions/splits.csv.gz`, `partitions/splits.schema.json`, `reports/exploratory_features.*` nem `statistics/pareto_summary.json` (pois não chama `compute_pareto_frontier`). Qualquer comando CLI subsequente naquele diretório (`expml partition verify`, `expml run verify`, `expml report export`) falha com `DataIntegrityError` ou `KeyError`.
  2. Em `pipeline.py:L150-163`, quando o usuário passa uma instância pronta `models={"RF": RandomForestRegressor()}` sem `random_state` pré-configurado, `_make_inst_factory` faz `copy.deepcopy(_inst)` e ignora o parâmetro `seed` recebido de `instantiate_fresh_model(spec, seed=cell_seed)` (`models/execution.py:L45`), deixando `random_state=None` (execução não determinística).
- **Comportamento esperado:**
  1. `run_experiment` deve persistir o conjunto completo de artefatos canônicos (`sanitized_view.json`, `splits.csv.gz`, `splits.schema.json`, `pareto_summary.json`, `exploratory_features.*`), garantindo 100% de interoperabilidade entre a API Python e a CLI `expml`.
  2. `_make_inst_factory` deve injetar `random_state=seed` no clone (quando o estimador possuir o atributo/parâmetro `random_state` e este estiver como `None`).
- **Evidências:** `src/experimental_ml/pipeline.py:L150-163,L320-385`.
- **Impacto:** Alto para pesquisadores que alternam entre scripts Python (`run_experiment`) e inspeção/exportação via CLI (`expml`).
- **Prioridade:** `P1`
- **Dependências:** Nenhuma.
- **Destino:** Marco `M8` (`m8-mvp-stabilization-contract-alignment`).
- **Status:** `IDENTIFICADO (Aguardando Decisão)`
- **Decisão e justificativa:** Correção recomendada para o Marco `M8`.

---

### `VAL-BUG-008`
- **Identificador único:** `VAL-BUG-008`
- **Título:** Partição `holdout_ids` nunca é executada como célula `FINAL_HOLDOUT` no regime `CV_AND_HOLDOUT`
- **Categoria:** `BUG`
- **Data de identificação:** 2026-11-24
- **Módulo afetado:** `src/experimental_ml/orchestration/matrix.py`, `src/experimental_ml/orchestration/execution.py`, `src/experimental_ml/statistics/consolidation.py`
- **Descrição:** Na Etapa 4A, o regime `ValidationRegime.CV_AND_HOLDOUT` reserva `holdout_ids` (conjunto de teste final isolado) e constrói $K$ folds de validação cruzada sobre `development_ids`. Na Etapa 4B, porém, `build_cell_matrix` gera células apenas para `partition_plan.folds` e nunca agenda nem executa a avaliação final em `holdout_ids`.
- **Comportamento observado:** Em `orchestration/matrix.py:L109`, a grade experimental é construída com `for fold in sorted_folds:` sem verificar `if partition_plan.regime == ValidationRegime.CV_AND_HOLDOUT and partition_plan.holdout_ids`. Assim, os `holdout_ids` são separados e verificados pelo gate da Etapa 4A, mas permanecem ociosos durante toda a Etapa 4B, 5 e 6 (ao contrário de `HOLDOUT_ONLY`, onde o único split é colocado dentro de `folds[0]`).
- **Comportamento esperado:** Sob `CV_AND_HOLDOUT`, além das células `DEVELOPMENT_CV` nos $K$ folds, o framework deve permitir ou executar as células de `FINAL_HOLDOUT` (treinando em `development_ids` e avaliando em `holdout_ids`), reportando as métricas de holdout final separadamente das métricas agregadas de CV para não contaminar a inferência de Nadeau-Bengio (`RF4.1`, `RF4.3`).
- **Evidências:** `src/experimental_ml/validation/partitioning.py:L368-395`; `src/experimental_ml/orchestration/matrix.py:L90-128`; `src/experimental_ml/orchestration/execution.py:L263`.
- **Impacto:** Médio-Alto para experimentos que utilizam o regime misto `CV_AND_HOLDOUT`.
- **Prioridade:** `P1`
- **Dependências:** Requer separação clara na Etapa 5 (`statistics/consolidation.py`) para que células `FINAL_HOLDOUT` não sejam misturadas aos $K$ folds de `DEVELOPMENT_CV` no cálculo da variância de Nadeau-Bengio.
- **Destino:** Marco `M9` (`m9-intra-fold-imputation-encoding-holdout`).
- **Status:** `IDENTIFICADO (Aguardando Decisão)`
- **Decisão e justificativa:** Recomendado planejar no Marco `M9`, pois exige definir o contrato de consolidação separada entre métricas de `DEVELOPMENT_CV` e métricas de `FINAL_HOLDOUT` nas Etapas 5 e 6.

---

### `VAL-BUG-009`
- **Identificador único:** `VAL-BUG-009`
- **Título:** Índice de Kuncheva retorna `None` via CLI/fachada, Pareto na CLI é fixo em 1 objetivo e `ComparisonScope.FULL_CONFIGURATIONS` equivale a `ALL_PAIRWISE`
- **Categoria:** `BUG`
- **Data de identificação:** 2026-11-24
- **Módulo afetado:** `src/experimental_ml/cli/cmd_stats.py`, `src/experimental_ml/pipeline.py`, `src/experimental_ml/statistics/consolidation.py`, `src/experimental_ml/statistics/comparisons.py`
- **Descrição:** Três lacunas de integração na Etapa 5 reduzem a utilidade prática do índice de estabilidade de Kuncheva, da fronteira de Pareto via CLI e do escopo `FULL_CONFIGURATIONS`.
- **Comportamento observado:**
  1. **Kuncheva `None`:** `cmd_stats.py:L67` e `pipeline.py:L324` chamam `consolidate_descriptive` sem informar `n_total_candidates_per_config`. O fallback em `consolidation.py:L296` usa `n_cands = len(set().union(*fold_selections))`. Quando os mesmos $k$ atributos são selecionados nos folds, $k = N$, o que torna o denominador de Kuncheva zero e retorna `mean_kuncheva = None`.
  2. **Pareto 1D na CLI:** `cmd_stats.py:L135-138` instancia `MultiObjectiveSpec` sempre com 1 único objetivo (`primary_metric`), ignorando qualquer especificação multiobjetivo em `stats_config.json`.
  3. **`FULL_CONFIGURATIONS`:** Em `statistics/comparisons.py:L53`, `if scope in (ComparisonScope.ALL_PAIRWISE, ComparisonScope.FULL_CONFIGURATIONS):` executa exatamente o mesmo produto cartesiano completo de pares.
- **Comportamento esperado:**
  1. `consolidate_descriptive` (ou seus chamadores em `cmd_stats.py` e `pipeline.py`) deve obter `len(scenario.candidate_features)` de `scenarios_catalog` para preencher `n_total_candidates_per_config`.
  2. `cmd_stats.py` deve ler `pareto_objectives` de `stats_config.json` quando presente (com fallback para `[primary_metric, mean_fit_time_s]` ou `[primary_metric]`).
  3. Documentar ou diferenciar o filtro de `FULL_CONFIGURATIONS`.
- **Evidências:** `src/experimental_ml/cli/cmd_stats.py:L67,L135-138`; `src/experimental_ml/pipeline.py:L324`; `src/experimental_ml/statistics/consolidation.py:L293-297`; `src/experimental_ml/statistics/comparisons.py:L53`.
- **Impacto:** Médio. Afeta a riqueza analítica da Etapa 5 quando acionada pela CLI ou por `run_experiment`.
- **Prioridade:** `P1`
- **Dependências:** Nenhuma.
- **Destino:** Marco `M8` (`m8-mvp-stabilization-contract-alignment`).
- **Status:** `IDENTIFICADO (Aguardando Decisão)`
- **Decisão e justificativa:** Correção simples e de alto valor analítico para o Marco `M8`.

---

### `VAL-BUG-010`
- **Identificador único:** `VAL-BUG-010`
- **Título:** Desvios no estado de retomada (`scenarios_hash`/`models_hash`), prefixo duplo `cell_cell_` em arquivos de células e ausência de lock em `_ACTIVE_INSTANCES`
- **Categoria:** `BUG`
- **Data de identificação:** 2026-11-24
- **Módulo afetado:** `src/experimental_ml/orchestration/state.py`, `src/experimental_ml/orchestration/engine.py`, `src/experimental_ml/orchestration/storage.py`, `src/experimental_ml/models/execution.py`
- **Descrição:** Pequenos desvios contratuais na orquestração da Etapa 4B:
  1. `MatrixExecutionState` (`orchestration/state.py:L26-41`) persiste e verifica `source_dataset_hash` e `partition_plan_id` no `resume`, mas não inclui `scenarios_hash` nem `models_hash` (`CA-E4B-02` / `ARQUITETURA §3.4`).
  2. `build_cell_matrix` (`matrix.py:L111`) define `cell_id = f"cell_{m}__{s}__{f}"` e `save_cell_artifacts` (`storage.py:L54-56`) prefixa `"cell_"` novamente, gerando `runs/cells/cell_cell_<m>__<s>__<f>.json`.
  3. `_ACTIVE_INSTANCES` (`models/execution.py:L66`) é mutado via `.add()` e `.discard()` sem `threading.Lock` durante execuções paralelas com `ThreadPoolExecutor` (`outer_n_jobs > 1`).
- **Comportamento observado:** Se o usuário alterar `models.json` ou `scenarios.json` sem mudar o dataset ou as partições e rodar `expml run resume`, o motor retoma sem detectar a mudança de hash de configuração dos modelos/cenários.
- **Comportamento esperado:** Verificar `scenarios_hash` e `models_hash` ao retomar `MatrixExecutionState`, proteger `_ACTIVE_INSTANCES` com `threading.Lock()` e padronizar o prefixo de `cell_id`.
- **Evidências:** `src/experimental_ml/orchestration/state.py:L26-41`; `src/experimental_ml/orchestration/engine.py:L279-325`; `src/experimental_ml/orchestration/storage.py:L54-56`; `src/experimental_ml/models/execution.py:L66-125`.
- **Impacto:** Baixo-Médio.
- **Prioridade:** `P2`
- **Dependências:** Nenhuma.
- **Destino:** Marco `M8` (`m8-mvp-stabilization-contract-alignment`).
- **Status:** `IDENTIFICADO (Aguardando Decisão)`
- **Decisão e justificativa:** Incluir a verificação de `scenarios_hash`/`models_hash` e o `threading.Lock` no Marco `M8`.

---

### `VAL-BUG-011`
- **Identificador único:** `VAL-BUG-011`
- **Título:** Script TLC `validate_verification.py` verifica caminho incorreto para `PROCESSO_DE_ACEITE_DE_MARCOS.md`
- **Categoria:** `BUG`
- **Data de identificação:** 2026-11-24
- **Módulo afetado:** `.agent/skills/tlc-spec-driven/scripts/validate_verification.py`, `.agents/skills/tlc-spec-driven/scripts/validate_verification.py`
- **Descrição:** Na linha 370 de `validate_verification.py`, a função `_check_milestone_acceptance` procura `os.path.join(root, "engenharia_software", "PROCESSO_DE_ACEITE_DE_MARCOS.md")` sem o diretório pai `"docs"`.
- **Comportamento observado:** Como o arquivo real reside em `docs/engenharia_software/PROCESSO_DE_ACEITE_DE_MARCOS.md`, `os.path.isfile(acceptance_process)` retorna sempre `False` e a verificação automatizada da presença de `ACCEPTANCE.md` e `RESULTS.md` nunca é executada pelo script.
- **Comportamento esperado:** O script deve verificar `os.path.join(root, "docs", "engenharia_software", "PROCESSO_DE_ACEITE_DE_MARCOS.md")` (ou aceitar ambos os caminhos).
- **Evidências:** `.agent/skills/tlc-spec-driven/scripts/validate_verification.py:L369-372`.
- **Impacto:** Baixo (afeta apenas a automação do script de validação TLC).
- **Prioridade:** `P2`
- **Dependências:** Nenhuma.
- **Destino:** Marco `M8`.
- **Status:** `IDENTIFICADO (Aguardando Decisão)`
- **Decisão e justificativa:** Ajuste de 1 linha nos scripts de `.agent/` e `.agents/` durante o Marco `M8`.

---

### `VAL-QUAL-001`
- **Identificador único:** `VAL-QUAL-001`
- **Título:** Limitações tipográficas e de layout nos gráficos PNG em NumPy puro da Etapa 2 (`features/visualization.py`)
- **Categoria:** `QUALITY`
- **Data de identificação:** 2026-11-24
- **Módulo afetado:** `src/experimental_ml/features/visualization.py`
- **Descrição:** O gerador de gráficos PNG da Etapa 2 (`relevance_ranking.png` e `redundancy_matrix.png`) utiliza uma fonte bitmap 5×7 desenhada pixel a pixel em arrays NumPy, apresentando limitações estéticas e de legibilidade quando comparado a gráficos científicos vetoriais/antialiased.
- **Comportamento observado:**
  1. `_to_ascii_label` (`L82-90`) remove todos os acentos do português (`"Correlação"` → `"Correlacao"`, `"Informação Mútua"` → `"Informacao Mutua"`).
  2. Os glifos 5×7 em `scale=1` (usados nas notas de rodapé e valores dentro das células do heatmap) têm apenas 7 pixels de altura e sem anti-aliasing, dificultando a leitura em monitores de alta densidade.
  3. Nomes de variáveis com mais de 25 caracteres são truncados à esquerda porque `left_margin` é limitado a `320 px` (`L141` e `L298`).
  4. No heatmap de redundância (`render_redundancy_matrix_png`), `top_margin` é limitado a `220 px` (`L299`), enquanto a legenda da barra de cores ocupa `y = 62..76`; nomes de colunas com mais de 22 caracteres desenhados verticalmente de baixo para cima colidem com a barra de cores no topo.
- **Comportamento esperado:** Gráficos com tipografia antialiased completa (suportando UTF-8 e acentuação em português), dimensionamento automático de margens sem colisão ou truncamento e qualidade visual adequada para inclusão direta em artigos e relatórios de Iniciação Científica.
- **Evidências:** `src/experimental_ml/features/visualization.py:L27-113,L140-143,L298-305,L377-432`.
- **Impacto:** Médio-Alto na qualidade de apresentação visual dos relatórios exploratórios.
- **Prioridade:** `P1`
- **Dependências:** Relacionado a `VAL-BUG-006` e `VAL-ENH-001`.
- **Destino:** Marco `M10` (`m10-scientific-visualization-reporting-redesign`).
- **Status:** `IDENTIFICADO (Aguardando Decisão)`
- **Decisão e justificativa:** Integrar ao redesenho do subsistema de visualização científica no Marco `M10`.

---

### `VAL-QUAL-002`
- **Identificador único:** `VAL-QUAL-002`
- **Título:** Tabelas B e C da Etapa 6 omitem metadados científicos relevantes e `report.md`/`report.html` são gerados em inglês sem glossário estatístico
- **Categoria:** `QUALITY`
- **Data de identificação:** 2026-11-24
- **Módulo afetado:** `src/experimental_ml/reporting/tables.py`, `src/experimental_ml/reporting/report.py`
- **Descrição:** As tabelas de configuração (Famílias B e C) e o relatório consolidado da Etapa 6 apresentam informações excessivamente resumidas e inconsistência de idioma com o restante do framework.
- **Comportamento observado:**
  1. **Tabela B (`B_FEATURE_SCENARIOS`, `tables.py:L114-127`):** Exibe apenas `(Scenario ID, Mode, Features Count)`. Para cenários `DYNAMIC`, `selected_features` é vazio na definição pré-fold, de modo que a tabela mostra `Features Count = 0` e não informa `strategy_name`, `strategy_params` (`k`, `threshold`), `candidate_features` nem `scientific_justification`.
  2. **Tabela C (`C_MODELS_CONFIG`, `tables.py:L129-143`):** Exibe `(Model ID, Family, Task Type)` onde `Task Type` é sempre `"N/A"` (pois `ModelSpec` não possui campo `task_type`), omitindo `display_name`, hiperparâmetros (`parameters`), pré-processamento (`preprocessing`) e estratégia de tuning (`search_spec`).
  3. **Idioma e Glossário (`report.py`):** O relatório `report.md` / `report.html` tem todos os títulos e textos em inglês (`# Scientific Experiment Report`, `## 1. Researcher Declarations`), ao passo que o relatório da Etapa 2 (`exploratory_features.md`) e o sumário executivo (`ExperimentRunSummary.summary()`) estão em português. Além disso, o relatório final não inclui nota explicativa para as colunas estatísticas (`CI Low`/`CI High` corrigidos por Nadeau-Bengio, `p_adj (NB)`, `p_adj (WX)`, `Cohen d_z`).
- **Comportamento esperado:** Tabelas B e C completas com os metadados experimentais declarados, idioma padronizado em português (ou configurável) e seção de guia rápido/glossário de leitura estatística no relatório final.
- **Evidências:** `src/experimental_ml/reporting/tables.py:L114-143`; `src/experimental_ml/reporting/report.py:L40-210`.
- **Impacto:** Médio (usabilidade e clareza para o pesquisador).
- **Prioridade:** `P1`
- **Dependências:** Relacionado ao Marco `M10`.
- **Destino:** Marco `M10` (`m10-scientific-visualization-reporting-redesign`).
- **Status:** `IDENTIFICADO (Aguardando Decisão)`
- **Decisão e justificativa:** Consolidar junto à reformulação de relatórios e visualização no Marco `M10`.

---

### `VAL-QUAL-003`
- **Identificador único:** `VAL-QUAL-003`
- **Título:** `expml init` para classificação cria apenas 1 modelo (resultando em 0 comparações pareadas) e `expml quickrun` não exporta tabelas/figuras avulsas
- **Categoria:** `QUALITY`
- **Data de identificação:** 2026-11-24
- **Módulo afetado:** `src/experimental_ml/cli/cmd_init.py`, `src/experimental_ml/cli/cmd_report.py`, `src/experimental_ml/pipeline.py`
- **Descrição:** Dois pontos de atrito de usabilidade nos comandos de início rápido da CLI:
  1. Enquanto `expml init --task regression` gera 2 modelos (`baseline_media` e `regressao_linear`), `expml init --task binary_classification` e `--task multiclass_classification` (`cmd_init.py:L102-115`) geram apenas **1 modelo** (`baseline_majoritario`). Quando o pesquisador roda `expml quickrun` em classificação, a Etapa 5 produz `0 comparações pareadas` porque só há 1 configuração.
  2. `expml quickrun` e `run_experiment` geram apenas `reports/report.md` e `reports/report.html`, sem exportar os arquivos individuais em `reports/tables/*.{csv,md,tex}` e `reports/figures/*.{svg,png,pdf}` (que só são criados se o usuário rodar separadamente `expml report export`).
- **Comportamento esperado:**
  1. `expml init` para classificação deve incluir um segundo modelo padrão (ex.: `regressao_logistica` com `LOGISTIC_REGRESSION`), permitindo comparação pareada imediata no `quickrun`.
  2. `expml quickrun` (ou `expml report generate --export-all`) deve oferecer a exportação integrada das tabelas e figuras.
- **Evidências:** `src/experimental_ml/cli/cmd_init.py:L102-115`; `src/experimental_ml/cli/cmd_report.py:L46-97`.
- **Impacto:** Baixo-Médio (experiência de primeiro uso em problemas de classificação).
- **Prioridade:** `P2`
- **Dependências:** Nenhuma.
- **Destino:** Marco `M8` (`m8-mvp-stabilization-contract-alignment`).
- **Status:** `IDENTIFICADO (Aguardando Decisão)`
- **Decisão e justificativa:** Melhoria rápida e de baixo impacto para o Marco `M8`.

---

### `VAL-QUAL-004`
- **Identificador único:** `VAL-QUAL-004`
- **Título:** Divergências pontuais de nomenclatura entre `ARQUITETURA_E_CONTRATOS.md` e o código, e omissões em `api_python.md`, `cli_catalogo.md` e `PROCESSO_DE_ACEITE_DE_MARCOS.md`
- **Categoria:** `QUALITY`
- **Data de identificação:** 2026-11-24
- **Módulo afetado:** `docs/engenharia_software/ARQUITETURA_E_CONTRATOS.md`, `docs/engenharia_software/PROCESSO_DE_ACEITE_DE_MARCOS.md`, `docs/engenharia_software/ETAPA_ATUAL_ENGENHARIA.md`, `docs/referencia/api_python.md`, `docs/referencia/cli_catalogo.md`, `.specs/STATE.md`
- **Descrição:** Durante a Etapa I da auditoria foram identificadas dessincronizações entre documentos de referência/governança e o estado atual do código (`HEAD 874125a`).
- **Comportamento observado:**
  1. `PROCESSO_DE_ACEITE_DE_MARCOS.md` (Seção 5) parava em `TA-POS.3` (`598/598`), omitindo as 4 features pós-MVP seguintes (até `611/611`).
  2. `ETAPA_ATUAL_ENGENHARIA.md:L18` citava `598 testes` no texto principal enquanto o cabeçalho citava `611`.
  3. `docs/referencia/api_python.md` omitia 55 símbolos públicos presentes no `__all__` dos subpacotes (`data`, `models`, `orchestration`, `statistics`, `reporting`, `stages`).
  4. `docs/referencia/cli_catalogo.md:L169-170` marcava `--run-dir` como sempre obrigatório em `expml run resume`, embora `--experiment-dir` seja aceito como alternativa.
  5. `ARQUITETURA_E_CONTRATOS.md` contém diferenças históricas de nomes de identificadores em relação ao código implementado (ex.: nomes dos códigos de achados na §3.1, nomes de enums de particionamento na §3.4, menção a `manifest.json` na §5 e Parquet no `ADR-006`).
- **Comportamento esperado:** Documentação de governança, referência de API/CLI e contratos 100% sincronizados com a implementação real.
- **Evidências:** Tabelas da Seção 2 de [AUDITORIA_TECNICA_DO_MVP.md](./AUDITORIA_TECNICA_DO_MVP.md).
- **Impacto:** Baixo-Médio (rastreabilidade documental).
- **Prioridade:** `P2`
- **Dependências:** Nenhuma.
- **Destino:** Itens 1 a 4 atualizados factualmente na Etapa VII desta atividade; item 5 (`ARQUITETURA_E_CONTRATOS.md`) reservado para alinhamento autorizado pelo desenvolvedor no Marco `M8` (em respeito à regra 2.2 de não alterar contratos ou ADRs unilateralmente).
- **Status:** `PARCIALMENTE CORRIGIDO / AGUARDANDO DECISÃO`
- **Decisão e justificativa:** Atualizações factuais de catálogo e histórico aplicadas; revisão de identificadores em `ARQUITETURA_E_CONTRATOS.md` submetida à aprovação do desenvolvedor.

---

### `VAL-ENH-001`
- **Identificador único:** `VAL-ENH-001`
- **Título:** Subsistema de Visualização Científica e Relatórios com arquitetura desacoplada e backend `Matplotlib`/`Pandas` (Revisão controlada do `XCUT-02`)
- **Categoria:** `ENHANCEMENT`
- **Data de identificação:** 2026-11-24
- **Módulo afetado:** `src/experimental_ml/reporting/figures.py`, `src/experimental_ml/features/visualization.py`, `src/experimental_ml/reporting/tables.py`, `docs/engenharia_software/ARQUITETURA_E_CONTRATOS.md`
- **Descrição:** Substituir os renderizadores manuais de pixels/bytes (`features/visualization.py` e `reporting/figures.py`) por um subsistema de visualização científica desacoplado em duas camadas (`Preparação de Dados Visuais` → `Backend de Renderização`), utilizando `matplotlib` (e opcionalmente `pandas` na camada de apresentação de tabelas/dados tabulares) para gerar figuras de qualidade de publicação em `PNG (300 DPI)`, `SVG` e `PDF`, mantendo o núcleo matemático e estatístico (`core`, `metrics`, `data`, `features/stats`, `models`, `tuning`, `validation`, `orchestration`, `statistics`) 100% puro em Python + NumPy/SciPy.
- **Comportamento observado:** A restrição original `XCUT-02` proibiu `matplotlib` e `pandas` em todo o repositório, levando à escrita manual de rasterizadores bitmap 5×7 e geradores PDF/SVG crus que sofrem dos defeitos registrados em `VAL-BUG-006` e `VAL-QUAL-001`.
- **Comportamento esperado:** Figuras científicas completas para todas as famílias de relatórios (incluindo paridade predito vs. observado, curvas de aprendizado/convergência, importância de atributos, intervalos de confiança pareados com linha zero, fronteira de Pareto 2D em escala real e heatmaps com tipografia UTF-8 acentuada).
- **Evidências:** Análise técnica comparativa detalhada na Seção 3 de [ROADMAP_EVOLUCAO.md](./ROADMAP_EVOLUCAO.md).
- **Impacto:** Muito Alto na qualidade científica e usabilidade prática do framework.
- **Prioridade:** `P1`
- **Dependências:** Requer revisão formal de ADR / `XCUT-02` aprovada pelo desenvolvedor para autorizar `matplotlib` (e opcionalmente `pandas`) exclusivamente na camada de apresentação/relatórios.
- **Destino:** Marco `M10` (`m10-scientific-visualization-reporting-redesign`).
- **Status:** `PLANEJADO (Aguardando Decisão Arquitetural)`
- **Decisão e justificativa:** Especificação preliminar elaborada em `.specs/features/m10-scientific-visualization-reporting-redesign/spec.md`.

---

### `VAL-ENH-002`
- **Identificador único:** `VAL-ENH-002`
- **Título:** Implementação completa de Imputação (`MEAN`, `MEDIAN`, `MODE`) e Codificação Categórica Intra-Fold integradas às regras `DEFER_INTRA_FOLD`
- **Categoria:** `ENHANCEMENT`
- **Data de identificação:** 2026-11-24
- **Módulo afetado:** `src/experimental_ml/models/preprocessing/`, `src/experimental_ml/orchestration/execution.py`, `src/experimental_ml/data/preparation.py`
- **Descrição:** Completar a implementação do pipeline intra-fold para que as regras `DEFER_INTRA_FOLD` definidas na Etapa 1 sejam automaticamente traduzidas e aplicadas na Camada 1 de pré-processamento dentro de cada fold da Etapa 4B, incluindo o transformador `SimpleImputer` próprio em NumPy (`MEAN`, `MEDIAN`, `MODE`) e codificação categórica controlada (`ORDINAL` / `ONE_HOT`) sem vazamento entre treino e validação.
- **Comportamento observado:** Atualmente apenas a declaração da regra existe na Etapa 1 (`VAL-BUG-001`).
- **Comportamento esperado:** Execução transparente e livre de data leakage de bases com dados ausentes e colunas categóricas diferidas para tratamento intra-fold.
- **Evidências:** `src/experimental_ml/data/preparation.py:L577`; `src/experimental_ml/models/preprocessing/pipeline.py:L126-165`.
- **Impacto:** Alto para experimentação em datasets tabulares reais com dados faltantes.
- **Prioridade:** `P1`
- **Dependências:** Resolve `VAL-BUG-001`.
- **Destino:** Marco `M9` (`m9-intra-fold-imputation-encoding-holdout`).
- **Status:** `PLANEJADO (Aguardando Aprovação de Escopo)`
- **Decisão e justificativa:** Especificação preliminar elaborada em `.specs/features/m9-intra-fold-imputation-encoding-holdout/spec.md`.

---

### `VAL-ENH-003`
- **Identificador único:** `VAL-ENH-003`
- **Título:** Execução, persistência e consolidação dedicada para células `FINAL_HOLDOUT` no regime `CV_AND_HOLDOUT`
- **Categoria:** `ENHANCEMENT`
- **Data de identificação:** 2026-11-24
- **Módulo afetado:** `src/experimental_ml/orchestration/`, `src/experimental_ml/statistics/`, `src/experimental_ml/reporting/`
- **Descrição:** Estender o gerador de matriz (`build_cell_matrix`), o executor de células (`execute_single_cell`) e o consolidador estatístico (`consolidate_descriptive` e relatórios da Etapa 6) para executar e reportar a avaliação final no conjunto `holdout_ids` quando o regime `CV_AND_HOLDOUT` for selecionado, mantendo total separação entre os $K$ folds de `DEVELOPMENT_CV` e o resultado de `FINAL_HOLDOUT`.
- **Comportamento observado:** `holdout_ids` é particionado e validado na Etapa 4A, mas ignorado na Etapa 4B (`VAL-BUG-008`).
- **Comportamento esperado:** Execução completa do protocolo de dois estágios (`DEVELOPMENT_CV` para seleção/comparação estatística com Nadeau-Bengio + `FINAL_HOLDOUT` para aferição final de generalização fora da amostra).
- **Evidências:** `src/experimental_ml/orchestration/matrix.py:L109`.
- **Impacto:** Médio-Alto para protocolos experimentais que combinam validação cruzada com teste holdout reservado.
- **Prioridade:** `P1`
- **Dependências:** Resolve `VAL-BUG-008`.
- **Destino:** Marco `M9` (`m9-intra-fold-imputation-encoding-holdout`).
- **Status:** `PLANEJADO (Aguardando Aprovação de Escopo)`
- **Decisão e justificativa:** Agrupado no Marco `M9` junto às melhorias de execução intra-fold da Etapa 4B.

---

### `VAL-ENH-004`
- **Identificador único:** `VAL-ENH-004`
- **Título:** Suporte declarativo a múltiplos objetivos de Pareto e pares planejados (`PLANNED_PAIRS`) na CLI `expml` e na fachada `run_experiment`
- **Categoria:** `ENHANCEMENT`
- **Data de identificação:** 2026-11-24
- **Módulo afetado:** `src/experimental_ml/cli/cmd_stats.py`, `src/experimental_ml/pipeline.py`, `src/experimental_ml/statistics/comparisons.py`
- **Descrição:** Permitir que `stats_config.json` (na CLI) e `run_experiment` (na API Python) recebam uma lista explícita de objetivos de Pareto (ex.: maximizar `R2` ou `F1_MACRO` e minimizar `mean_fit_time_s` ou `n_selected_features`), além de expor o filtro real para `ComparisonScope.FULL_CONFIGURATIONS` e `PLANNED_PAIRS`.
- **Comportamento observado:** O motor `compute_pareto_frontier` suporta $M \ge 2$ objetivos arbitrary-direction (métricas, tempos de execução, número de atributos), mas a CLI fixa apenas 1 objetivo e `run_experiment` não chama `compute_pareto_frontier` (`VAL-BUG-007`, `VAL-BUG-009`).
- **Comportamento esperado:** Fronteira de Pareto genuinamente multiobjetivo (ex.: Desempenho Preditivo vs. Custo Computacional / Parcimônia de Atributos) disponível diretamente via CLI e `run_experiment`.
- **Evidências:** `src/experimental_ml/cli/cmd_stats.py:L135-138`; `src/experimental_ml/statistics/pareto.py:L55-140`.
- **Impacto:** Médio. Valoriza na prática um dos diferenciais científicos já implementados no núcleo estatístico (`M6.3`).
- **Prioridade:** `P2`
- **Dependências:** Relacionado a `VAL-BUG-007` e `VAL-BUG-009`.
- **Destino:** Marco `M8` (`m8-mvp-stabilization-contract-alignment`).
- **Status:** `PLANEJADO (Aguardando Aprovação de Escopo)`
- **Decisão e justificativa:** Incluído na especificação preliminar do Marco `M8`.

---

## 4. Template Padrão para Novos Registros

Sempre que um novo achado for identificado durante os testes contínuos do desenvolvedor, adicione uma nova subseção na Seção 3 seguindo exatamente este modelo:

```markdown
### `VAL-<BUG|QUAL|ENH>-<NNN>`
- **Identificador único:** `VAL-<BUG|QUAL|ENH>-<NNN>`
- **Título:** <Título técnico conciso>
- **Categoria:** `<BUG | QUALITY | ENHANCEMENT>`
- **Data de identificação:** <AAAA-MM-DD>
- **Módulo afetado:** `<caminhos em src/ ou docs/>`
- **Descrição:** <Contexto e explicação técnica do achado>
- **Comportamento observado:** <O que realmente acontece na execução atual>
- **Comportamento esperado:** <O que deveria acontecer segundo requisitos/contratos ou necessidade científica>
- **Evidências:** <Arquivos, linhas, comandos reproduzíveis, logs ou artefatos gerados>
- **Impacto:** <Impacto científico, funcional ou de usabilidade>
- **Prioridade:** `<P0 | P1 | P2>`
- **Dependências:** <Outros achados, ADRs ou marcos relacionados>
- **Destino:** `<Marco M8 | Marco M9 | Marco M10 | Revisão de ADR | Onda 2 | Limitação Conhecida>`
- **Status:** `<IDENTIFICADO | EM INVESTIGAÇÃO | CLASSIFICADO | DECIDIDO | ENCAMINHADO | VERIFICADO | ENCERRADO>`
- **Decisão e justificativa:** <Decisão do desenvolvedor e fundamentação técnica>
```
