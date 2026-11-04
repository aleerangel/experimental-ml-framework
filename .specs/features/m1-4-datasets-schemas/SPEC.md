# Marco M1.4 — Datasets & Schemas: Esquemas Tabulares, Ingestão Imutável e Integridade Estrutural

> **Registro de Especificação do Marco (SPEC.md)**  
> **Identificador do Marco:** M1.4 (`m1-4-datasets-schemas`)  
> **Pacote Python:** `experimental_ml.data` (`src/experimental_ml/data/`)  
> **Camada Arquitetural:** Camada 1 — Definição e Triagem (Nível 1 de dependência; Etapa 1 do Pipeline Operacional)  
> **Status:** Proposta de Especificação Refinada Submetida à Revisão (Fase Specify)  
> **Aprovação da Especificação:** *Pendente de revisão técnica do usuário*  
> **Especificação EARS Detalhada:** [`spec.md`](./spec.md)  
> **Documentos de Referência:** [`ARQUITETURA_E_CONTRATOS.md`](../../../engenharia_software/ARQUITETURA_E_CONTRATOS.md), [`ESPECIFICACAO_REQUISITOS.md`](../../../engenharia_software/ESPECIFICACAO_REQUISITOS.md), [`PROCESSO_DE_ACEITE_DE_MARCOS.md`](../../../engenharia_software/PROCESSO_DE_ACEITE_DE_MARCOS.md), [`REFERENCIAS_E_FUNDAMENTACAO.md`](../../../REFERENCIAS_E_FUNDAMENTACAO.md)

---

## 1. Propósito, Problema Abordado e Posicionamento no Roadmap

O marco **M1.4 — Datasets & Schemas** estabelece a fundação do pacote `experimental_ml.data` (Nível 1 da arquitetura), responsável pela declaração formal de papéis de variáveis (`DatasetSchemaSpec`), pela ingestão determinística e imutável de dados tabulares (`load_dataset`), pela validação de consistência entre esquema e dados (`validate_dataset_schema`) e pela construção do artefato em memória somente-leitura (`DatasetBundle`) vinculado ao `dataset_hash` canônico (**ADR-007**) e aos identificadores únicos de observação (`ObservationId`).

### 1.1 Por que isolar a Fundação da Etapa 1 no Marco M1.4?
Na especificação arquitetural consolidada ([`ARQUITETURA_E_CONTRATOS.md`](../../../engenharia_software/ARQUITETURA_E_CONTRATOS.md) Seção 7), o Marco M2 concentrava simultaneamente a leitura de dados, perfilamento diagnóstico, plano de preparação, saneamento pré-partição, plano de validação cruzada/holdout e interface de terminal (`expml data` e `expml partition`).

A introdução do **M1.4 (`m1-4-datasets-schemas`)** isola e consolida os contratos de **representação, tipagem estrutural, identificação e imutabilidade dos dados de origem** antes da construção dos algoritmos de perfilamento estatístico (`DatasetProfile`), saneamento (`PreparationPlan` / `SanitizedDatasetView`) e particionamento (`PartitionPlan`) no Marco M2.

Essa separação atende diretamente a quatro princípios estruturantes do framework:
1. **Imutabilidade dos Dados de Origem e Propriedade Exclusiva (Princípio 2, `RF1.7`, Heil et al., 2021; REFORMS, 2024):** A ingestão assume propriedade dos dados através de cópias defensivas estritas (`copy=True`), protegendo as matrizes contra mutações acidentais na fonte de origem ou através de referências expostas, sem qualquer imputação ou descarte silencioso.
2. **Prevenção Estrutural contra Vazamento de Papéis de Colunas (Princípio 3, `RF1.1`, Kapoor & Narayanan, 2023):** O esquema força a disjunção estrita entre variável-alvo (`target_col`), agrupamento (`group_col`), identificador (`observation_id_col`), tempo (`time_col`) e colunas ignoradas (`ignore_cols`), derivando automaticamente o conjunto candidato de atributos preditores (`feature_cols`) sem contaminação.
3. **Vínculo de Proveniência e Rastreabilidade por Observação (Princípio 7, `CA-E1-01`, Freire et al., 2008):** Toda linha recebe um `ObservationId` único, estável e não-nulo desde a leitura, e todo `DatasetBundle` carrega seu `dataset_hash` canônico do conteúdo em memória e o `raw_source_hash` da fonte original (**ADR-007**).
4. **Ocultamento de Informação e Paradigma Funcional Sem OOP (**ADR-008**, Parnas, 1972):** O módulo expõe apenas estruturas de dados imutáveis (`@dataclass(frozen=True, slots=True)`) e funções puras, sem classes de serviço com estado interno mutável.

---

## 2. Decisões Arquiteturais e Aprofundamento dos 5 Pontos de Revisão

### 2.1 Ponto 1: Imutabilidade e Propriedade dos Dados

#### O Problema Identificado
A aplicação isolada de `arr.flags.writeable = False` é insuficiente para garantir imutabilidade real em dois cenários críticos:
1. **Compartilhamento de Memória com a Fonte:** Se o array NumPy foi criado por `np.asarray(orig_data)` ou fatiamento de um array existente, `write=False` afeta apenas aquela visão (*view*), mas alterações na matriz ou buffer original do chamador modificariam silenciosamente os dados internos do bundle.
2. **Colunas com `dtype=object` e Objetos Mutáveis Internos:** Em arrays de objetos do NumPy, a flag `writeable = False` impede apenas a reatribuição de ponteiros no array (ex.: `arr[0] = novo_objeto`), mas **não impede** a mutação interna do objeto referenciado (ex.: `arr[0].append(x)` ou `arr[0]["chave"] = y`).

#### Regras Formais Adotadas
1. **Propriedade Exclusiva e Cópia Defensiva na Ingestão:**
   - O `DatasetBundle` assume propriedade integral e exclusiva dos dados.
   - Na função `load_dataset`, toda coluna é materializada através de cópia defensiva contígua (`np.array(..., copy=True)` ou clonagem de buffers) completamente desacoplada da estrutura de entrada do chamador.
   - Qualquer mutação posterior na estrutura original do chamador (ex.: `orig_dict["col"][0] = 999`, `orig_array[0, 0] = 999` ou `orig_df.iloc[0, 0] = 999`) tem **efeito zero** sobre `DatasetBundle.columns`.
2. **Tratamento Rigoroso de Colunas `object`:**
   - Colunas com tipo físico `object` são permitidas exclusivamente para representação de textos/categorias (`str`), identificadores (`str`), ou colunas booleanas com valores ausentes (`True`, `False`, `None`).
   - É terminantemente **proibido** armazenar objetos mutáveis (como `list`, `dict`, `set`, `bytearray`, instâncias de classes mutáveis) dentro de colunas do `DatasetBundle`. A ingestão inspeciona os elementos e lança `DataIntegrityError` se qualquer elemento mutável for detectado.
   - Strings são convertidas em objetos `str` imutáveis normalizados em Unicode NFC.
3. **Garantias Oferecidas ao Consumidor:**
   - `bundle.columns` é um `types.MappingProxyType` imutável (`bundle.columns["nova"] = ...` levanta `TypeError`).
   - Cada array colunar `bundle.columns[col]` tem `flags.writeable = False` (`bundle.columns[col][0] = ...` levanta `ValueError`).
   - A função `get_column_array(bundle, col_name)` retorna um array com `flags.writeable = False` diretamente ou visão segura; se o consumidor tentar forçar `arr.setflags(write=True)` em uma cópia desacoplada, o estado interno de `bundle.columns` permanece protegido contra efeitos colaterais.

---

### 2.2 Ponto 2: Semântica Tripartite do `dataset_hash`

#### O Problema Identificado
Identificar um dataset apenas pelos bytes brutos do arquivo físico em disco confunde a *identidade do transporte* com a *identidade matemática/estrutural do conteúdo*. Por exemplo, um mesmo conjunto de dados salvo com quebras de linha Windows (`\r\n`) ou Unix (`\n`), ou carregado de um arquivo TSV vs. de um dicionário em memória (após normalização NFC de strings, coerção correta de tipos e padronização de nulos), possui representações em disco com SHA-256 distintos, mas contém rigorosamente a mesma informação experimental.

#### Formalização das Três Identidades no M1.4
Sem alterar os contratos já implementados no Core (**ADR-007**, `hashing.py`), o `DatasetBundle` explicita e distingue três resumos criptográficos (`SHA-256` de 64 caracteres hexadecimais):

1. **Identidade do Conteúdo Tabular Efetivo (`dataset_hash: str`):**
   - É o digest criptográfico SHA-256 calculado diretamente sobre os arrays normalizados, congelados e ordenados em memória (`bundle.columns`), vinculados à ordem dos `observation_ids` e ao `schema`, através do ramo in-memory da função existente:
     `core.dataset_hash(bundle.columns, schema)`.
   - **Garantia Invariante:** Se a mesma informação tabular for carregada de um arquivo CSV (com qualquer padrão de quebras de linha `\r\n` ou `\n`), de um TSV ou de uma estrutura em memória (`dict`, `DataFrame`), o `DatasetBundle.dataset_hash` resultante será **rigorosamente idêntico bit a bit**.
   - É este `dataset_hash` que serve de chave primária para a proveniência dos artefatos das etapas subsequentes (Marco M2 a M7).
2. **Identidade da Fonte Original (`raw_source_hash: str`):**
   - Registra o hash da fonte bruta de entrada antes do parsing:
     - Quando carregado de arquivo em disco (`.csv`, `.txt`, `.tsv`): é o hash dos bytes físicos do arquivo em disco combinado com o esquema, calculado via `core.dataset_hash(source_path, schema)`.
     - Quando carregado de estrutura em memória: é o hash da estrutura original antes de qualquer cópia interna.
   - Permite verificar a integridade física do arquivo em disco (detectando se o arquivo físico foi adulterado ou corrompido).
3. **Identidade do Esquema Estrutural (`schema_hash: str`):**
   - É o digest canônico do `DatasetSchemaSpec` calculado via `core.config_hash(schema)`.

---

### 2.3 Ponto 3: Parsing e Detecção de Delimitadores

#### Regras de Parsing e Suporte a Delimitadores
1. **Delimitadores Suportados:**
   - Vírgula (`,`), ponto-e-vírgula (`;`), tabulação (`\t`), barra vertical (`|`), e blocos de espaços em branco contíguos (`r"[ \t]+"`) para arquivos científicos tabulares `.txt`.
2. **Regras de Detecção Automática (`delimiter=None`):**
   - Lê uma amostra inicial de até 100 linhas não-vazias do arquivo.
   - Avalia os delimitadores candidatos na ordem: `,`, `;`, `\t`, `|`.
   - Utiliza `csv.Sniffer` restrito a esses delimitadores e verifica se a contagem de colunas $M$ é estritamente uniforme em todas as linhas da amostra ($M \ge 2$).
   - Se nenhum delimitador caractere produzir contagem uniforme $\ge 2$, avalia divisão por múltiplos espaços (`r"[ \t]+"`), verificando contagem uniforme de campos em todas as linhas.
3. **Tratamento de Ambiguidade ou Falha na Detecção:**
   - Se múltiplos delimitadores produzirem contagens válidas concorrentes, ou se nenhum delimitador produzir contagem de colunas estritamente uniforme em todas as linhas da amostra, `load_dataset` **não adivinha** nem assume valores padrão: lança `DataIntegrityError` com diagnóstico detalhado instruindo o pesquisador a especificar o delimitador manualmente via parâmetro `delimiter`.
4. **Sobrescrita Manual:**
   - Passar `delimiter=","`, `";"`, `"\t"`, `"|"` ou `" "` desativa integralmente a detecção automática e aplica estritamente o delimitador informado.
5. **Tratamento de Campos Entre Aspas (Quoting — RFC 4180):**
   - Campos delimitados por aspas duplas (`"`) são processados conforme a RFC 4180: caracteres delimitadores e quebras de linha contidos dentro de aspas são preservados como texto literal do campo; aspas duplas escapadas (`""`) são convertidas para uma única aspa literal (`"`).
6. **Linhas Irregulares (*Ragged Rows*):**
   - Toda linha de dados (exceto linhas em branco descartadas) deve conter exatamente o mesmo número de colunas $M$.
   - Se qualquer linha contiver número divergente de colunas em relação ao cabeçalho ou à primeira linha, a leitura falha imediatamente com `DataIntegrityError` indicando o número da linha (1-based), a contagem esperada e a contagem encontrada. Nenhuma linha é descartada silenciosamente e nenhuma coluna é preenchida com valores nulos artificiais.
7. **Arquivos Vazios e Cabeçalhos:**
   - Arquivos com zero bytes ou compostos apenas por espaços/linhas em branco lançam `DataIntegrityError`.
   - Arquivos contendo apenas a linha de cabeçalho e nenhuma linha de dados ($N = 0$) lançam `DataIntegrityError` (a base exige $N \ge 1$).
   - Cabeçalhos com nomes de coluna vazios (`col1,,col3`) ou nomes duplicados após normalização NFC lançam `DataIntegrityError`.

---

### 2.4 Ponto 4: Tipagem Semântica das Colunas vs. Representação Física

#### Distinção Conceitual
A representação computacional de um dado em memória não determina unívocamente seu papel científico:
- Uma coluna física `int64` pode representar uma contagem discreta (`NUMERIC_DISCRETE`), um código de categoria (`CATEGORICAL`) ou um identificador (`IDENTIFIER`).
- Uma coluna física `float64` pode representar uma grandeza contínua (`NUMERIC_CONTINUOUS`) ou uma variável discreta com valores ausentes.
- Uma coluna física `object` (string) pode representar texto/categoria (`CATEGORICAL`), data/hora (`TEMPORAL`) ou código identificador (`IDENTIFIER`).

#### Repartição de Responsabilidades
1. **Semântica Intrínseca a Papéis do Esquema:**
   - A coluna designada como `observation_id_col` recebe compulsoriamente `ColumnSemanticType.IDENTIFIER`.
   - A coluna designada como `time_col` recebe compulsoriamente `ColumnSemanticType.TEMPORAL`.
   - A coluna designada como `group_col` recebe compulsoriamente `ColumnSemanticType.CATEGORICAL`.
2. **Declaração Explícita pelo Pesquisador no Schema:**
   - O `DatasetSchemaSpec` suporta o campo opcional:
     `column_semantic_types: Mapping[str, ColumnSemanticType] = MappingProxyType({})`
   - O pesquisador pode explicitar, por exemplo, `column_semantic_types={"cod_ibge": ColumnSemanticType.CATEGORICAL}`, impedindo que códigos inteiros sejam tratados como contagens matemáticas.
3. **Inferência Padrão Neutra (Fallback Documentado):**
   - Quando o pesquisador não declarar o tipo semântico de uma coluna de atributo (`feature_cols`):
     - `physical_type == "bool"` (ou booleano com nulos): `ColumnSemanticType.BOOLEAN`.
     - `physical_type == "float64"`: `ColumnSemanticType.NUMERIC_CONTINUOUS`.
     - `physical_type == "int64"`: `ColumnSemanticType.NUMERIC_DISCRETE`.
     - `physical_type == "object"` (strings): `ColumnSemanticType.CATEGORICAL`.
   - Para a variável `target_col`:
     - Em `REGRESSION`: `NUMERIC_CONTINUOUS` (se float) ou `NUMERIC_DISCRETE` (se int).
     - Em `BINARY_CLASSIFICATION` ou `MULTICLASS_CLASSIFICATION`: `CATEGORICAL` (ou `BOOLEAN` se bool).
4. **Estrutura `ColumnDescriptor`:**
   - Registra explicitamente:
     - `physical_type: str`: `"float64"`, `"int64"`, `"bool"`, `"object"`.
     - `semantic_type: ColumnSemanticType`: classificação semântica efetiva.
     - `is_semantic_declared: bool`: `True` se informada explicitamente pelo usuário no schema; `False` se resultante da inferência padrão neutra.

---

### 2.5 Ponto 5: Geração e Estabilidade de `ObservationId`

#### Geração na Ausência de Coluna Identificadora (`observation_id_col=None`)
1. **Regra de Geração:**
   - O framework gera determinísticamente $N$ identificadores únicos com formato padronizado:
     `ObservationId(f"obs_{i:06d}")` para $i \in \{0, \dots, N-1\}$.
   - Exemplos: `obs_000000`, `obs_000001`, ..., `obs_000999`.
2. **Ordem de Atribuição:**
   - Em arquivos em disco: a atribuição segue estritamente a sequência física de leitura das linhas de dados (linha 1 de dados $\rightarrow$ `obs_000000`, linha 2 $\rightarrow$ `obs_000001`).
   - Em estruturas em memória (`Mapping[str, Sequence]`, `np.ndarray` 2D, `DataFrame` duck-typed): segue estritamente a indexação posicional de linhas ($0 \le i < N$).
3. **Determinismo e Estabilidade sob Reordenação:**
   - Duas leituras da mesma fonte preservando a ordem das linhas produzem exatamente a mesma tupla de `observation_ids`.
   - Se a fonte for reordenada antes da leitura (por exemplo, linhas embaralhadas no CSV), os IDs posicionais acompanharão a nova ordem de leitura. A especificação documenta explicitamente que **bases que necessitem de estabilidade sob permutações arbitrárias de linhas devem conter uma coluna identificadora intrínseca na fonte (`observation_id_col`)**.

#### Validação Quando `observation_id_col` é Fornecida
1. **Extração e Normalização:**
   - Extrai os valores originais da coluna na ordem das observações.
   - Converte e normaliza strings em Unicode NFC.
2. **Validação Estrita de Integridade:**
   - Nenhum valor pode ser ausente (`None`, `NaN`, string vazia `""` ou whitespace puro `"   "`).
   - Nenhum valor pode conter caracteres inválidos para identificadores (`\n`, `\r`, `\t`, `\x00`).
   - Unicidade estrita: se houver qualquer repetição (`len(set(ids)) < N`), a carga é abortada imediatamente com `DataIntegrityError`, identificando o primeiro valor duplicado e as linhas onde ocorre.

#### Vínculo com Particionamento e Rastreabilidade Futura (Marcos M2 a M7)
- No Marco M2, o `PartitionPlan` registrará partições utilizando exclusivamente as tuplas de `ObservationId` (`train_ids`, `val_ids`, `holdout_ids`).
- A função pura `slice_bundle_by_observation_ids(bundle, observation_ids)` do M1.4 garante que qualquer partição futura recupere exatamente os registros originais através de busca por identificador estável, eliminando desalinhamentos por índices inteiros voláteis.

---

## 3. Matriz de Requisitos Rastreáveis e Critérios de Aceitação (DATA-01 a DATA-25)

| ID | Categoria | Requisito EARS (`spec.md`) | Critério Objetivo de Aceitação |
| :--- | :---: | :--- | :--- |
| **DATA-01** | Contrato | Estruturas imutáveis `DatasetSchemaSpec`, `ColumnDescriptor`, `DatasetBundle` e enum `ColumnSemanticType` | Instâncias são congeladas (`frozen=True`); tentativa de mutação levanta `FrozenInstanceError` / `AttributeError`; `ColumnSemanticType` expõe os 6 membros canônicos. |
| **DATA-02** | Esquema | Normalização NFC, deduplicação de `ignore_cols` e encapsulamento de `column_semantic_types` | Nomes em NFD e NFC produzem atributos idênticos em `DatasetSchemaSpec`; `ignore_cols` torna-se `tuple[str, ...]` sem duplicatas; `column_semantic_types` é somente-leitura. |
| **DATA-03** | Validação | Rejeição de nomes de colunas vazios, whitespace ou com caracteres de controle | Passar `""`, `"   "`, `"col\n1"` ou `"\t"` em qualquer campo de coluna de `DatasetSchemaSpec` levanta `ConfigurationError`. |
| **DATA-04** | Escopo | Bloqueio explícito de recursos da Onda 2 em `DatasetSchemaSpec` | `TaskType.MULTI_TARGET_REGRESSION`, `target_col=["y1", "y2"]` ou `target_transform_spec != None` levantam `ConfigurationError` explícito. |
| **DATA-05** | Invariante | Disjunção estrita entre papéis de colunas no `DatasetSchemaSpec` | Qualquer repetição de coluna entre `target_col`, `group_col`, `observation_id_col`, `time_col` e `ignore_cols` levanta `ConfigurationError`. |
| **DATA-06** | Hashing | Determinismo de `config_hash(schema)` sob Unicode NFC/NFD | `config_hash` de esquemas equivalentes em NFC e NFD produz exatamente o mesmo digest SHA-256 de 64 caracteres. |
| **DATA-07** | Ingestão | Ingestão com propriedade exclusiva e cópia defensiva da fonte de dados | Carrega `.csv`, `.txt`, `.tsv`, `dict`, `ndarray` 2D, lista de dicts e `DataFrame` duck-typed; mutações na fonte original após a carga não afetam `bundle.columns`. |
| **DATA-08** | Ingestão | Cópia defensiva e isolamento de arrays numéricos e colunas | Mutar in-place a matriz original do chamador tem efeito zero sobre `bundle.columns`. |
| **DATA-09** | Integridade | Proibição de tipos mutáveis em colunas de tipo físico `object` | Tentar carregar coluna `object` contendo `list`, `dict`, `set` ou `bytearray` levanta `DataIntegrityError`; apenas escalares imutáveis (`str`, `int`, `float`, `bool`, `None`) são aceitos. |
| **DATA-10** | Imutabilidade | Imutabilidade profunda em memória dos arrays colunares e mapeamentos em `DatasetBundle` | Todo array em `bundle.columns.values()` possui `flags.writeable == False` (mutação levanta `ValueError`) e `bundle.columns` / `bundle.descriptors` são `MappingProxyType` (`TypeError` ao atribuir). |
| **DATA-11** | Integridade | Preservação fiel de valores ausentes originais sem imputação ou descarte | Valores ausentes em colunas numéricas (`np.nan`) e categóricas/booleanas (`None`) são preservados; `feature_cols` exclui exatamente `{target, group, id, time} ∪ ignore_cols`. |
| **DATA-12** | Hashing | `DatasetBundle.dataset_hash` representando o conteúdo canônico em memória | `bundle.dataset_hash` reflete os dados tabulares normalizados em memória via `core.dataset_hash(bundle.columns, schema)`, sendo idêntico para mesma base via CSV (`\r\n` vs `\n`) ou dict. |
| **DATA-13** | Hashing | `DatasetBundle.raw_source_hash` e `schema_hash` para proveniência | `bundle.raw_source_hash` preserva o hash da fonte bruta original via `core.dataset_hash(source, schema)` e `bundle.schema_hash` preserva `core.config_hash(schema)`. |
| **DATA-14** | Parsing | Parsing estrito com suporte a delimitadores `,`, `;`, `\t`, `|`, múltiplos espaços e aspas RFC 4180 | Lê delimitadores padrão e múltiplos espaços `r"[ \t]+"`, preservando delimitadores e quebras de linha dentro de aspas duplas (`"a,b"`) e convertendo `""` em `"`. |
| **DATA-15** | Parsing | Detecção automática de delimitadores sobre amostra (100 linhas) | Identifica delimitador uniforme ($M \ge 2$) em amostra de até 100 linhas não-vazias. |
| **DATA-16** | Parsing | Falha explícita sob ambiguidade ou inconsistência de delimitadores | Sob múltiplos delimitadores válidos ou contagens não uniformes na amostra, lança `DataIntegrityError` com diagnóstico em vez de adivinhar. |
| **DATA-17** | Parsing | Sobrescrita manual via parâmetro `delimiter` | Informar `delimiter` explícito desativa detecção automática e aplica estritamente o separador configurado. |
| **DATA-18** | Parsing | Falha imediata para linhas irregulares (*ragged rows*) | Qualquer linha com contagem de colunas diferente da esperada levanta `DataIntegrityError` indicando o número da linha e contagens. |
| **DATA-19** | Metadados | `ColumnDescriptor` registrando separadamente representação física e tipo semântico | Registra `name`, `index`, `role`, `physical_type` (`"float64"`, etc.), `semantic_type`, `is_semantic_declared`, `n_missing` e `memory_bytes`. |
| **DATA-20** | Semântica | Respeito à declaração explícita de `column_semantic_types` e fallback neutro | Se declarada no schema, aplica o tipo e marca `is_semantic_declared=True`; se omitida, aplica inferência neutra padrão documentada e marca `False`. |
| **DATA-21** | Identidade | Geração determinística de `ObservationId` (`obs_000000` a `obs_NNNNNN`) | Na ausência de coluna de ID, gera identificadores sequenciais com 6 dígitos baseados na ordem física de leitura da fonte (`CA-E1-01`). |
| **DATA-22** | Identidade | Validação estrita de não-nulidade e unicidade de `observation_id_col` | Extrai valores da coluna de ID e levanta `DataIntegrityError` se contiver valor ausente (`None`, `NaN`, `""`), caracteres proibidos ou duplicações. |
| **DATA-23** | Validação | Validação de existência de colunas do esquema e de preditores candidatos | Se coluna do esquema faltar nos dados ou se restar zero coluna em `feature_cols`, levanta `DataIntegrityError`. |
| **DATA-24** | Consulta | Consulta segura de coluna via `get_column_array` | Retorna array 1D com `flags.writeable == False` para coluna existente e levanta `DataIntegrityError` para coluna inexistente. |
| **DATA-25** | Consulta | Recorte imutável de observações via `slice_bundle_by_observation_ids` | Retorna novo `DatasetBundle` imutável na ordem solicitada de `observation_ids` com `dataset_hash` recalculado; rejeita IDs inexistentes ou duplicados com `DataIntegrityError`. |

---

## 4. Riscos Remanescentes e Mitigações

1. **Tentativa de contornar `arr.flags.writeable = False` por consumidores via código C ou APIs internas:**
   - *Mitigação:* `DatasetBundle` é congelado (`slots=True`, `frozen=True`) e encapsula arrays em `MappingProxyType`. `get_column_array` e `slice_bundle_by_observation_ids` retornam referências controladas. O consumidor é orientado metodologicamente a tratar os arrays como somente-leitura.
2. **Arquivos texto com encodings exóticos ou caracteres corrompidos:**
   - *Mitigação:* `load_dataset` aceita o parâmetro explícito `encoding="utf-8"`, com detecção e falha imediata via `DataIntegrityError` em caso de erro de decodificação, sem mascarar bytes corrompidos.
3. **Bases tabulares com volume muito grande de linhas ($N > 10^7$):**
   - *Mitigação:* A representação colunar em NumPy contíguo (`float64`, `int64`) oferece a máxima eficiência de memória disponível em Python puro. O diagnóstico registra `memory_bytes` para permitir verificações de consumo na Etapa 1 do Marco M2.

---

## 5. Próximos Passos no Ciclo TLC

A especificação refinada permanece na fase **Specify**, aguardando sua revisão técnica detalhada dos pontos consolidados antes de ser submetida à aprovação formal.
