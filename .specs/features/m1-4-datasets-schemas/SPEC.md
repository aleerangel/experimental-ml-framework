# Marco M1.4 — Datasets & Schemas: Esquemas Tabulares, Ingestão Imutável e Integridade Estrutural

> **Registro de Especificação do Marco (SPEC.md)**  
> **Identificador do Marco:** M1.4 (`m1-4-datasets-schemas`)  
> **Pacote Python:** `experimental_ml.data` (`src/experimental_ml/data/`)  
> **Camada Arquitetural:** Camada 1 — Definição e Triagem (Nível 1 de dependência; Etapa 1 do Pipeline Operacional)  
> **Status:** Especificação Aprovada (Fase Specify)  
> **Aprovação da Especificação:** `**Approved**: 2026-11-04 - user: "aprovado. commita e espera"`  
> **Especificação EARS Detalhada:** [`spec.md`](./spec.md)  
> **Documentos de Referência:** [`ARQUITETURA_E_CONTRATOS.md`](../../../engenharia_software/ARQUITETURA_E_CONTRATOS.md), [`ESPECIFICACAO_REQUISITOS.md`](../../../engenharia_software/ESPECIFICACAO_REQUISITOS.md), [`PROCESSO_DE_ACEITE_DE_MARCOS.md`](../../../engenharia_software/PROCESSO_DE_ACEITE_DE_MARCOS.md), [`REFERENCIAS_E_FUNDAMENTACAO.md`](../../../REFERENCIAS_E_FUNDAMENTACAO.md)

---

## 1. Propósito, Problema Abordado e Posicionamento no Roadmap

O marco **M1.4 — Datasets & Schemas** estabelece a fundação do pacote `experimental_ml.data` (Nível 1 da arquitetura), responsável pela declaração formal de papéis de variáveis (`DatasetSchemaSpec`), pela ingestão determinística e imutável de dados tabulares (`load_dataset`), pela validação de consistência entre esquema e dados (`validate_dataset_schema`) e pela construção do artefato em memória somente-leitura (`DatasetBundle`) vinculado ao `dataset_hash` canônico (**ADR-007**) e aos identificadores únicos de observação (`ObservationId`).

### 1.1 Por que isolar a Fundação da Etapa 1 no Marco M1.4?
Na especificação arquitetural consolidada ([`ARQUITETURA_E_CONTRATOS.md`](../../../engenharia_software/ARQUITETURA_E_CONTRATOS.md) Seção 7), o Marco M2 concentrava simultaneamente a leitura de dados, perfilamento diagnóstico, plano de preparação, saneamento pré-partição, plano de validação cruzada/holdout e interface de terminal (`expml data` e `expml partition`).

A introdução do **M1.4 (`m1-4-datasets-schemas`)** isola e consolida os contratos de **representação, tipagem estrutural, identificação e imutabilidade dos dados de origem** antes da construção dos algoritmos de perfilamento estatístico (`DatasetProfile`), saneamento (`PreparationPlan` / `SanitizedDatasetView`) e particionamento (`PartitionPlan`) no Marco M2.

Essa separação atende diretamente a quatro princípios estruturantes do framework:
1. **Imutabilidade dos Dados de Origem e Propriedade Exclusiva (Princípio 2, `RF1.7`, Heil et al., 2021; REFORMS, 2024):** A ingestão assume propriedade dos dados através de buffers imutáveis `bytes` e cópias defensivas estritas, protegendo as matrizes contra mutações acidentais na fonte de origem ou através de referências expostas, sem qualquer imputação ou descarte silencioso.
2. **Prevenção Estrutural contra Vazamento de Papéis de Colunas (Princípio 3, `RF1.1`, Kapoor & Narayanan, 2023):** O esquema força a disjunção estrita entre variável-alvo (`target_col`), agrupamento (`group_col`), identificador (`observation_id_col`), tempo (`time_col`) e colunas ignoradas (`ignore_cols`), derivando automaticamente o conjunto candidato de atributos preditores (`feature_cols`) sem contaminação.
3. **Vínculo de Proveniência e Rastreabilidade por Observação (Princípio 7, `CA-E1-01`, Freire et al., 2008):** Toda linha recebe um `ObservationId` único e estável, e todo `DatasetBundle` carrega seu `dataset_hash` canônico do conteúdo em memória e o `raw_source_hash` da fonte original (**ADR-007**).
4. **Ocultamento de Informação e Paradigma Funcional Sem OOP (**ADR-008**, Parnas, 1972):** O módulo expõe apenas estruturas de dados imutáveis (`@dataclass(frozen=True, slots=True)`) e funções puras, sem classes de serviço com estado interno mutável.

---

## 2. Decisões Arquiteturais e Formalização dos Três Pontos Técnicos

### 2.1 Ponto 1: Nível de Garantia de Imutabilidade dos Arrays NumPy

#### Limitação Técnica Identificada
No NumPy, quando um array possui memória própria (*owns its memory*), executar `arr.setflags(write=False)` bloqueia atribuições convencionais (`arr[0] = x` levanta `ValueError`), mas qualquer referência ao mesmo array permite a reativação da escrita via `arr.setflags(write=True)`.

#### Investigação e Solução Adotada no `DatasetBundle`
1. **Colunas Numéricas e Booleanas Primitivas (`float64`, `int64`, `bool`):**
   - Na ingestão, os dados são convertidos para bytes brutos contíguos (`bytes`) e os arrays NumPy são materializados via `np.frombuffer(bytes_buffer, dtype=...)`.
   - **Garantia Física:** Como a base de memória subjacente é um objeto `bytes` imutável de Python, o NumPy aplica nativamente `flags.writeable = False` e **recusa permanentemente** qualquer tentativa de reativar a escrita: invocar `arr.setflags(write=True)` levanta compulsoriamente `ValueError: cannot set WRITEABLE flag to True of this array`.
   - Essa solução possui custo de memória zero adicional em relação a uma cópia comum e desempenho de acesso nativo C, eliminando a mutabilidade física dos dados numéricos.
2. **Colunas Categóricas e Textuais (`dtype=object`):**
   - Arrays de tipo `object` não podem ser instanciados com `np.frombuffer` em CPython por razões de alinhamento de ponteiros.
   - Para colunas `object`, a ingestão exige que **todos os elementos sejam escalares imutáveis de Python** (`str`, `None`, `int`, `float`, `bool`). Qualquer container mutável (`list`, `dict`, `set`, `bytearray`) é expressamente rejeitado com `DataIntegrityError`.
   - O array base é congelado internamente (`setflags(write=False)`). As referências expostas em `bundle.columns` e retornadas por `get_column_array` são *views* (`arr.view()`). No NumPy, invocar `view.setflags(write=True)` sobre uma visão cuja base tem `writeable = False` levanta compulsoriamente `ValueError: cannot set WRITEABLE flag to True of this array`.
3. **Contrato de Imutabilidade da API (`get_column_array`):**
   - `get_column_array(bundle, col_name, *, copy=False)`:
     - Por padrão (`copy=False`), retorna a visão somente-leitura (`flags.writeable = False`).
     - Se o consumidor necessitar de uma matriz modificável (por exemplo, para passar a um estimador externo que modifica arrays in-place), deve solicitar explicitamente `copy=True`, recebendo uma cópia independente e desvinculada do bundle.
4. **Limite Declarado da Garantia:**
   - A garantia é inviolável no nível da API Python e das operações NumPy convencionais. A manipulação deliberada de ponteiros C via `ctypes` ou escrita direta em memória bruta fica fora do modelo de segurança da linguagem.

---

### 2.2 Ponto 2: Semântica e Canonização dos Hashes

#### Contrato Real de `core.dataset_hash` (M1.2 / ADR-007)
A função `core.dataset_hash(data_or_path, schema)` já implementa dois ramos funcionais distintos:
1. **Ramo de Arquivo em Disco (`Path` ou string de caminho):** Lê os bytes físicos brutos do arquivo em blocos de 64 KB e concatena com o `config_hash(schema)` serializado em UTF-8.
2. **Ramo Tabular em Memória (`Mapping`, `DataFrame`, 2D `ndarray`):** Concatena o digest do esquema ordenado com a representação binária determinística de cada coluna em little-endian:
   - Tamanho da coluna `<Q`;
   - Prefixo de tipo (`b"float64"`, `b"int64"`, `b"bool"`, `b"object"`);
   - Dados binários: normalização de `-0.0 -> 0.0`; quiet NaN canônico `0x7FF8000000000000`; strings normalizadas em Unicode NFC com marcador de nulo (`\x00` para `None`/`NaN` e `\x01` + tamanho `<Q` + bytes UTF-8 para texto).

#### Formalização das Três Identidades no `DatasetBundle`
1. **`raw_source_hash: str` (Hash de Bytes da Fonte Original):**
   - Calculado via `core.dataset_hash(source, schema)` sobre a fonte bruta.
   - Quando a carga decorre de arquivo em disco, é o hash exato dos bytes do arquivo físico em disco combinado com o esquema. Permite auditar se o arquivo físico foi corrompido ou adulterado em disco.
2. **`dataset_hash: str` (Hash do Conteúdo Tabular Canônico em Memória):**
   - Calculado via `core.dataset_hash(bundle.columns, schema)` sobre os dados normalizados em memória.
   - Representa a identidade matemática do conteúdo tabular carregado.
   - **Regras Estritas de Canonização:**
     - *Diferenciação Escalar:* `1` (`int64`) e `1.0` (`float64`) **não são equivalentes**. Produzem digests distintos por utilizarem prefixos e codificações binárias diferentes (`b"int64"` vs. `b"float64"`).
     - *Representação de Ausência:* Em colunas `float64`, todas as variantes de `NaN` convergem para o quiet NaN canônico `0x7FF8000000000000`; em colunas `object`, tanto `None` quanto `float("nan")` convergem para o marcador de ausência `\x00`.
     - *Normalização Unicode:* Nomes de colunas e valores textuais são normalizados para a forma canônica **Unicode NFC** antes da serialização UTF-8.
     - *Ordem das Colunas:* A ordem das colunas **faz parte da identidade**. Conjuntos de colunas permutados produzem hashes diferentes.
     - *Ordem das Observações:* A sequência de linhas **faz parte da identidade**. Linhas permutadas produzem hashes diferentes.
     - *Portabilidade entre Fontes:* Uma base com os mesmos dados, mesmos tipos físicos e mesma ordem de linhas/colunas produz **rigorosamente o mesmo `dataset_hash`**, quer tenha sido carregada de CSV (seja com quebras de linha `\r\n` ou `\n`), de TSV ou de uma estrutura em memória.
3. **`schema_hash: str` (Hash da Especificação Estrutural):**
   - Calculado via `core.config_hash(schema)`, identificando de forma unívoca e imutável os papéis de colunas e parâmetros declarados.

---

### 2.3 Ponto 3: Ordem e Estabilidade de `ObservationId`

#### Natureza dos Identificadores Gerados (`observation_id_col=None`)
- Os IDs gerados no formato `ObservationId(f"obs_{i:06d}")` ($i = 0, \dots, N-1$) identificam **posições sequenciais de linha dentro daquela carga específica**, e **não** constituem identidade ontológica persistente das entidades observadas.
- **Limitação Explícita sob Reordenação:** Se o arquivo ou estrutura de origem for reordenado antes da carga (por exemplo, linhas embaralhadas), a associação entre `obs_XXXXXX` e as respectivas observações mudará.
- **Exigência de Coluna Intrínseca:** Para rastreabilidade persistente entre cargas independentes sob reordenações da fonte, a base de dados **deve fornecer compulsoriamente uma coluna identificadora intrínseca (`observation_id_col`)**.

#### Semântica de `slice_bundle_by_observation_ids`
A função `slice_bundle_by_observation_ids(bundle, observation_ids)` foi definida formalmente com a seguinte semântica única:
- **Preservação Estrita da Ordem Solicitada pelo Chamador:**
  - As linhas do novo `DatasetBundle` gerado refletem **exatamente a ordem da sequência `observation_ids` passada pelo chamador**, e não a ordem física original do dataset.
  - *Justificativa Arquitetural:* Nos módulos subsequentes (como validação cruzada, bootstrapping e avaliação temporal no Marco M2/M4), as partições especificam sequências de observações que frequentemente requerem ordenação temporal, estratificada ou agrupada. Permitir a ordenação direta pelo chamador elimina a necessidade de etapas intermediárias de reordenação.
- **Critérios de Validação e Falha:**
  1. *Subconjunto Vazio:* Passar sequência vazia (`()`) levanta `DataIntegrityError` (a invariante do bundle exige $N \ge 1$).
  2. *Identificadores Repetidos:* A sequência `observation_ids` não pode conter duplicatas (`len(set(ids)) == len(ids)`). Qualquer duplicação levanta `DataIntegrityError` (o fatiamento é estritamente bijetivo; reamostragem com reposição será implementada por método dedicado no Marco M4).
  3. *Identificadores Inexistentes:* Se qualquer `ObservationId` solicitado não constar em `bundle.observation_ids`, a operação falha imediatamente com `DataIntegrityError` indicando o identificador não encontrado.

---

## 3. Matriz de Requisitos Rastreáveis e Critérios de Aceitação (DATA-01 a DATA-29)

| ID | Categoria | Requisito EARS (`spec.md`) | Critério Objetivo de Aceitação |
| :--- | :---: | :--- | :--- |
| **DATA-01** | Contrato | Estruturas imutáveis `DatasetSchemaSpec`, `ColumnDescriptor`, `DatasetBundle` e enum `ColumnSemanticType` | Instâncias são congeladas (`frozen=True`); tentativa de mutação levanta `FrozenInstanceError` / `AttributeError`; `ColumnSemanticType` expõe os 6 membros canônicos. |
| **DATA-02** | Esquema | Normalização NFC, deduplicação de `ignore_cols` e encapsulamento de `column_semantic_types` | Nomes em NFD e NFC produzem atributos idênticos em `DatasetSchemaSpec`; `ignore_cols` torna-se `tuple[str, ...]` sem duplicatas; `column_semantic_types` é somente-leitura. |
| **DATA-03** | Validação | Rejeição de nomes de colunas vazios, whitespace ou com caracteres de controle | Passar `""`, `"   "`, `"col\n1"` ou `"\t"` em qualquer campo de coluna de `DatasetSchemaSpec` levanta `ConfigurationError`. |
| **DATA-04** | Escopo | Bloqueio explícito de recursos da Onda 2 em `DatasetSchemaSpec` | `TaskType.MULTI_TARGET_REGRESSION`, `target_col=["y1", "y2"]` ou `target_transform_spec != None` levantam `ConfigurationError` explícito. |
| **DATA-05** | Invariante | Disjunção estrita entre papéis de colunas no `DatasetSchemaSpec` | Qualquer repetição de coluna entre `target_col`, `group_col`, `observation_id_col`, `time_col` e `ignore_cols` levanta `ConfigurationError`. |
| **DATA-06** | Hashing | Determinismo de `config_hash(schema)` sob Unicode NFC/NFD | `config_hash` de esquemas equivalentes em NFC e NFD produz exatamente o mesmo digest SHA-256 de 64 caracteres. |
| **DATA-07** | Ingestão | Ingestão com propriedade exclusiva e isolamento da fonte original | Carrega `.csv`, `.txt`, `.tsv`, `dict`, `ndarray` 2D, lista de dicts e `DataFrame` duck-typed; mutações na fonte original após a carga têm efeito zero sobre `bundle.columns`. |
| **DATA-08** | Ingestão | Cópia defensiva e isolamento de arrays numéricos e colunas | Mutar in-place a matriz original do chamador não altera os dados de `bundle.columns`. |
| **DATA-09** | Imutabilidade | Bloqueio absoluto de reativação de escrita em colunas numéricas/booleanas | Colunas numéricas/booleanas usam base imutável de bytes; invocar `arr.setflags(write=True)` no array interno ou em view exposta levanta `ValueError`. |
| **DATA-10** | Imutabilidade | Restrição de colunas `object` a escalares imutáveis com views bloqueadas | Colunas `object` contêm estritamente escalares imutáveis (`str`, `None`, `int`, `float`, `bool`), levantando `DataIntegrityError` se contiverem objetos mutáveis (`list`, `dict`, `set`), e recusam `setflags(write=True)` com `ValueError`. |
| **DATA-11** | Imutabilidade | Imutabilidade profunda em memória dos mapeamentos de `DatasetBundle` | `bundle.columns` e `bundle.descriptors` são encapsulados em `MappingProxyType`, levantando `TypeError` em tentativa de atribuição ou remoção de chaves. |
| **DATA-12** | Integridade | Preservação fiel de valores ausentes originais sem imputação ou descarte | Valores ausentes em colunas numéricas (`np.nan`) e categóricas/booleanas (`None`) são preservados; `feature_cols` exclui exatamente `{target, group, id, time} ∪ ignore_cols`. |
| **DATA-13** | Hashing | `DatasetBundle.dataset_hash` representando o conteúdo canônico em memória | `bundle.dataset_hash` reflete os dados tabulares normalizados em memória via `core.dataset_hash(bundle.columns, schema)`, onde `1` (int64) e `1.0` (float64) são tipos distintos, e cargas equivalentes de CSV (`\r\n` vs `\n`) e memória produzem o mesmo digest. |
| **DATA-14** | Hashing | `DatasetBundle.raw_source_hash` e `schema_hash` para proveniência | `bundle.raw_source_hash` preserva o hash da fonte bruta original via `core.dataset_hash(source, schema)` e `bundle.schema_hash` preserva `core.config_hash(schema)`. |
| **DATA-15** | Parsing | Parsing estrito com suporte a delimitadores `,`, `;`, `\t`, `|`, múltiplos espaços e aspas RFC 4180 | Lê delimitadores padrão e múltiplos espaços `r"[ \t]+"`, preservando delimitadores e quebras de linha dentro de aspas duplas (`"a,b"`) e convertendo `""` em `"`. |
| **DATA-16** | Parsing | Detecção automática de delimitadores sobre amostra (100 linhas) | Identifica delimitador uniforme ($M \ge 2$) em amostra de até 100 linhas não-vazias. |
| **DATA-17** | Parsing | Falha explícita sob ambiguidade ou inconsistência de delimitadores | Sob múltiplos delimitadores válidos ou contagens não uniformes na amostra, lança `DataIntegrityError` com diagnóstico em vez de adivinhar. |
| **DATA-18** | Parsing | Sobrescrita manual via parâmetro `delimiter` | Informar `delimiter` explícito desativa detecção automática e aplica estritamente o separador configurado. |
| **DATA-19** | Parsing | Falha imediata para linhas irregulares (*ragged rows*) | Qualquer linha com contagem de colunas diferente da esperada levanta `DataIntegrityError` indicando o número da linha e contagens. |
| **DATA-20** | Parsing | Validação de arquivos vazios e cabeçalhos | Arquivos vazios, compostos só por espaços ou com $N=0$ linhas de dados levantam `DataIntegrityError`; cabeçalhos com colunas vazias ou duplicadas em NFC levantam `DataIntegrityError`. |
| **DATA-21** | Parsing | Suporte a arquivos e matrizes sem cabeçalho (`has_header=False`) | Gera nomes posicionais `col_0` a `col_M-1` quando `column_names=None`, ou aplica e valida nomes fornecidos (`DataIntegrityError` se contagem divergir). |
| **DATA-22** | Metadados | `ColumnDescriptor` registrando separadamente representação física e tipo semântico | Registra `name`, `index`, `role`, `physical_type` (`"float64"`, etc.), `semantic_type`, `is_semantic_declared`, `n_missing` e `memory_bytes`. |
| **DATA-23** | Semântica | Respeito à declaração explícita de `column_semantic_types` e fallback neutro | Se declarada no schema, aplica o tipo e marca `is_semantic_declared=True`; se omitida, aplica inferência neutra padrão documentada e marca `False`. |
| **DATA-24** | Identidade | Geração posicional determinística de `ObservationId` (`obs_000000` a `obs_NNNNNN`) | Na ausência de coluna de ID, gera identificadores sequenciais com 6 dígitos baseados na ordem física de leitura da fonte (`CA-E1-01`), documentando que representam posições na carga. |
| **DATA-25** | Identidade | Validação estrita de não-nulidade e unicidade de `observation_id_col` | Extrai valores da coluna de ID e levanta `DataIntegrityError` se contiver valor ausente (`None`, `NaN`, `""`), caracteres proibidos ou duplicações. |
| **DATA-26** | Validação | Validação de existência de colunas do esquema e de preditores candidatos | Se coluna do esquema faltar nos dados ou se restar zero coluna em `feature_cols`, levanta `DataIntegrityError`. |
| **DATA-27** | Consulta | Consulta segura de coluna via `get_column_array` | Retorna array 1D com `flags.writeable == False` (recusando `setflags(write=True)` com `ValueError`) quando `copy=False`, ou cópia modificável independente quando `copy=True`. |
| **DATA-28** | Consulta | Recorte ordenado de observações via `slice_bundle_by_observation_ids` | Retorna novo `DatasetBundle` imutável contendo as observações estritamente na ordem solicitada pelo chamador com `dataset_hash` recalculado; rejeita IDs inexistentes com `DataIntegrityError`. |
| **DATA-29** | Consulta | Validação estrita de IDs duplicados e sequência vazia no fatiamento | Sequência vazia ou contendo identificadores duplicados em `slice_bundle_by_observation_ids` levanta `DataIntegrityError`. |

---

## 4. Riscos Remanescentes e Mitigações

1. **Manipulação de Baixo Nível via C-API ou `ctypes`:**
   - *Mitigação:* A garantia de imutabilidade do framework é formulada estritamente no nível da linguagem Python e da biblioteca NumPy. Tentativas deliberadas de invasão de memória via código em C ou ponteiros nativos de baixo nível extrapolam o escopo de segurança da API.
2. **Arquivos CSV com Delimitadores Complexos e Quebras de Linha em Campos de Texto:**
   - *Mitigação:* O parsing adota conformidade com a RFC 4180 via `csv.reader` da biblioteca padrão, suportando quebras de linha em campos entre aspas. Linhas com contagem inconsistente de colunas disparam `DataIntegrityError` imediato.
3. **Bases sem Coluna de ID sob Permutações Prévias:**
   - *Mitigação:* A documentação explicita que `obs_000000` rastreia posições na carga corrente; para rastreabilidade ontológica persistente, a base deve conter uma `observation_id_col` declarada.

---

## 5. Próximos Passos no Ciclo TLC

A especificação refinada permanece na fase **Specify**, aguardando sua nova revisão técnica antes de qualquer transição para a fase **Design**.
