# Marco M1.4 — Datasets & Schemas: Esquemas Tabulares, Ingestão Imutável e Integridade Estrutural

> **Registro de Especificação do Marco (SPEC.md)**  
> **Identificador do Marco:** M1.4 (`m1-4-datasets-schemas`)  
> **Pacote Python:** `experimental_ml.data` (`src/experimental_ml/data/`)  
> **Camada Arquitetural:** Camada 1 — Definição e Triagem (Nível 1 de dependência; Etapa 1 do Pipeline Operacional)  
> **Status:** Proposta de Especificação Submetida à Revisão (Fase Specify)  
> **Aprovação da Especificação:** *Pendente de revisão do usuário*  
> **Especificação EARS Detalhada:** [`spec.md`](./spec.md)  
> **Documentos de Referência:** [`ARQUITETURA_E_CONTRATOS.md`](../../../engenharia_software/ARQUITETURA_E_CONTRATOS.md), [`ESPECIFICACAO_REQUISITOS.md`](../../../engenharia_software/ESPECIFICACAO_REQUISITOS.md), [`PROCESSO_DE_ACEITE_DE_MARCOS.md`](../../../engenharia_software/PROCESSO_DE_ACEITE_DE_MARCOS.md), [`REFERENCIAS_E_FUNDAMENTACAO.md`](../../../REFERENCIAS_E_FUNDAMENTACAO.md)

---

## 1. Propósito, Problema Abordado e Posicionamento no Roadmap

O marco **M1.4 — Datasets & Schemas** estabelece a fundação do pacote `experimental_ml.data` (Nível 1 da arquitetura), responsável pela declaração formal de papéis de variáveis (`DatasetSchemaSpec`), pela ingestão determinística e imutável de dados tabulares (`load_dataset`), pela validação de consistência entre esquema e dados (`validate_dataset_schema`) e pela construção do artefato em memória somente-leitura (`DatasetBundle`) vinculado ao `dataset_hash` canônico (**ADR-007**) e aos identificadores únicos de observação (`ObservationId`).

### 1.1 Por que dividir a Etapa 1 entre M1.4 e M2?
Na especificação arquitetural original ([`ARQUITETURA_E_CONTRATOS.md`](../../../engenharia_software/ARQUITETURA_E_CONTRATOS.md) Seção 7), o Marco M2 concentrava simultaneamente toda a Etapa 1 (`load_dataset`, `profile_dataset`, `create_preparation_plan`, `sanitize_dataset`), toda a Etapa 4A (`build_partition_plan`, `validate_partition_plan`) e dois subcomandos de CLI (`expml data`, `expml partition`).

A introdução do **M1.4 (`m1-4-datasets-schemas`)** como entrega final da fundação M1 isola e consolida os contratos de **representação, tipagem estrutural, identificação e imutabilidade dos dados de origem** antes da construção dos algoritmos de perfilamento estatístico (`DatasetProfile`), saneamento (`PreparationPlan` / `SanitizedDatasetView`) e particionamento (`PartitionPlan`) no Marco M2.

Essa separação atende diretamente a quatro princípios estruturantes do framework:
1. **Imutabilidade dos Dados de Origem e Zero Transformação Silenciosa (Princípio 2, `RF1.7`, Heil et al., 2021; REFORMS, 2024):** A ingestão não descarta observações com valores ausentes, não preenche lacunas, não codifica categorias nem altera escalas. Os dados originais ficam protegidos em buffers somente-leitura (`flags.writeable = False`).
2. **Prevenção Estrutural contra Vazamento de Papéis de Colunas (Princípio 3, `RF1.1`, Kapoor & Narayanan, 2023):** O esquema força a disjunção estrita entre variável-alvo (`target_col`), agrupamento (`group_col`), identificador (`observation_id_col`), tempo (`time_col`) e colunas ignoradas (`ignore_cols`), derivando automaticamente o conjunto candidato de atributos preditores (`feature_cols`) sem contaminação.
3. **Vínculo de Proveniência e Rastreabilidade por Observação (Princípio 7, `CA-E1-01`, Freire et al., 2008):** Toda linha recebe um `ObservationId` único, estável e não-nulo desde o instante da leitura, e todo `DatasetBundle` carrega seu `dataset_hash` (`SHA-256`) calculado pelo `core` (**ADR-007**).
4. **Ocultamento de Informação e Paradigma Funcional Sem OOP (**ADR-008**, Parnas, 1972):** O módulo expõe apenas estruturas de dados imutáveis (`@dataclass(frozen=True, slots=True)`) e funções puras, sem classes de serviço com estado interno mutável.

---

## 2. Limites de Responsabilidade e Escopo do Marco

### 2.1 Incluído no Marco M1.4 (`src/experimental_ml/data/`)
1. **Tipagem Semântica e Estruturas Imutáveis (`types.py` / `schema.py`):**
   - Enumeração `ColumnSemanticType(StrEnum)` com os 6 tipos semânticos estruturais: `"NUMERIC_CONTINUOUS"`, `"NUMERIC_DISCRETE"`, `"CATEGORICAL"`, `"BOOLEAN"`, `"TEMPORAL"` e `"IDENTIFIER"`.
   - Estrutura declarativa imutável `DatasetSchemaSpec` com validação intrínseca de papéis de colunas, normalização Unicode NFC e fronteira Onda 1 vs. Onda 2.
   - Estrutura descritiva por coluna `ColumnDescriptor` (`name`, `index`, `role`, `semantic_type`, `dtype_str`, `n_missing`, `memory_bytes`).
   - Estrutura imutável `DatasetBundle` representando a base carregada em modo somente-leitura, metadados estruturais, `observation_ids` e `dataset_hash`.
2. **Validação de Esquema e Consistência Esquema-Dados (`validation.py`):**
   - Validação intrínseca do `DatasetSchemaSpec` (nomes válidos, disjunção de papéis, restrições da Onda 1).
   - Função pública `validate_dataset_schema(columns, schema)` verificando existência de todas as colunas declaradas, ausência de colunas duplicadas após normalização NFC, homogeneidade de comprimento ($N \ge 1$), existência de pelo menos 1 coluna preditora candidata (`len(feature_cols) >= 1`) e validade/unicidade de `observation_id_col`.
3. **Ingestão Tabular Determinística e Consultas Somente-Leitura (`loader.py`):**
   - Função pública `load_dataset(source, schema, *, delimiter=None, has_header=True, column_names=None, encoding="utf-8") -> DatasetBundle`.
   - Suporte a arquivos em disco (`.csv`, `.txt`, `.tsv` com delimitadores explícitos, auto-detectados ou sequências de espaços em branco `r"\s+"`, com ou sem cabeçalho) e estruturas tabulares em memória (`Mapping[str, Sequence]`, `np.ndarray` 2D, `Sequence[Mapping[str, Any]]` e objetos `DataFrame` via *duck-typing*).
   - Funções utilitárias puras de consulta: `get_column_array(bundle, col_name) -> np.ndarray` e `slice_bundle_by_observation_ids(bundle, observation_ids) -> DatasetBundle`.
   - Re-exportação pública em `src/experimental_ml/data/__init__.py` via `__all__`.
4. **Suíte de Testes Unitários (`tests/unit/test_data_schemas.py`):**
   - Cobertura verificável 1:1 dos 20 requisitos (`DATA-01` a `DATA-20`).

### 2.2 Explicitamente Fora de Escopo (Não Antecipado no M1.4)
Para preservar a modularidade e respeitar as restrições de não antecipar contratos de marcos futuros:
- **Diagnóstico Estatístico e Perfilamento Completo (`profile_dataset`, `DatasetProfile`):** Cálculo de quartis, assimetria, amplitude, diferenças de ordem de grandeza, linhas duplicadas, colunas quase-constantes e emissão de diagnósticos `CONFIRMED_ISSUE` vs. `HEURISTIC_WARNING` sobre anomalias estatísticas — pertencem ao **Marco M2**.
- **Plano de Preparação e Saneamento Pré-Partição (`create_preparation_plan`, `PreparationPlan`, `sanitize_dataset`, `SanitizedDatasetView`):** Regras declarativas de resolução de `CONFIRMED_ISSUE` e filtragem estrutural de linhas com `target` nulo — pertencem ao **Marco M2**.
- **Particionamento e Validação Cruzada (`build_partition_plan`, `validate_partition_plan`, `PartitionPlan`):** Estratégias K-Fold, Stratified K-Fold, Group K-Fold e Holdout — pertencem ao **Marco M2 (`experimental_ml.validation`)**.
- **Subcomandos da CLI (`expml data profile`, `expml data sanitize`, `expml partition`):** A CLI permanece inalterada no M1.4 (inclusive mantendo a verificação de `tests/test_smoke.py`); os subcomandos `cmd_data.py` e `cmd_partition.py` pertencem ao **Marco M2**.
- **Funcionalidades da Onda 2 do MVP:** Regressão multialvo (`MULTI_TARGET_REGRESSION` com `target_col: Sequence[str]`), transformações reversíveis da variável-alvo (`TargetTransformSpec` / `fit_apply_target_transform`) e conjunto externo não rotulado (`unlabeled_pool`) — pertencem à **Onda 2** (`ARQUITETURA_E_CONTRATOS.md` Seção 6.1).
- **Transformações de Pré-processamento ou Seleção de Atributos:** Imputação, codificação de categorias (`OneHot`, `Ordinal`), escalonamento ou filtragem de variáveis — pertencem às Etapas 2 e 3 (**Marcos M3 e M4**).

---

## 3. Dependências e Integração com `core` e `metrics` (Sem Duplicação)

O pacote `experimental_ml.data` situa-se no **Nível 1** de dependências (`ARQUITETURA_E_CONTRATOS.md` Seção 2.3) e importa **exclusivamente** a biblioteca padrão do Python, `numpy>=1.24.0` e `experimental_ml.core` (Nível 0). Não há dependência entre `experimental_ml.data` e `experimental_ml.metrics` (ambos são pacotes independentes de Nível 1).

| Componente de `experimental_ml.core` | Uso em `experimental_ml.data` (M1.4) | Responsabilidade Preservada (Sem Duplicação) |
| :--- | :--- | :--- |
| `ObservationId` (`core.types`) | Identificador validado de cada linha em `DatasetBundle.observation_ids`. | A validação contra strings vazias, whitespace e caracteres de controle é feita pelo construtor `ObservationId` já existente no `core`. |
| `TaskType`, `StrEnum` (`core.enums`) | Tipagem da modalidade em `DatasetSchemaSpec.task_type` e base para `ColumnSemanticType`. | Reutiliza `TaskType` canônico sem recriar enums de tarefa. |
| `config_hash`, `dataset_hash` (`core.hashing`) | Cálculo de `DatasetBundle.dataset_hash` e serialização canônica de `DatasetSchemaSpec`. | `load_dataset` delega 100% do cálculo de hash a `dataset_hash(source, schema)` do `core` (**ADR-007**), sem reimplementar SHA-256 ou serialização binária. |
| `ConfigurationError`, `DataIntegrityError` (`core.findings`) | Exceções para configuração inválida de esquema (`ConfigurationError`) ou violação estrutural dos dados (`DataIntegrityError`). | Reutiliza a hierarquia oficial de exceções do `core`. |

---

## 4. Decisões Arquiteturais, Requisitos Não Funcionais e Restrições

### 4.1 Decisões Arquiteturais do Marco
1. **DA-M1.4-01 — Unificação no Pacote `experimental_ml.data`:**
   - Embora o título descritivo do marco no roadmap seja *Datasets & Schemas*, o módulo físico é `src/experimental_ml/data/` conforme definido na Seção 2.3 de `ARQUITETURA_E_CONTRATOS.md` e em `tests/test_smoke.py`. Isso evita criar um pacote órfão `experimental_ml.datasets` que quebraria os caminhos de importação previstos para o Marco M2.
2. **DA-M1.4-02 — Armazenamento Colunar Imutável Baseado em `numpy.ndarray` + `MappingProxyType` (Zero Dependência de `pandas`):**
   - Cada coluna é armazenada em `DatasetBundle.columns` como um array `numpy.ndarray` 1D de comprimento $N$ com `arr.flags.writeable = False`, exposto através de `types.MappingProxyType`.
   - Objetos `pandas.DataFrame` passados em memória pelo usuário são suportados via protocolo *duck-typing* (`hasattr(source, "columns") and hasattr(source, "__getitem__")`), extraindo cópias imutáveis das colunas sem exigir `pandas` no `pyproject.toml` (`RNF03`, `RNF04`).
3. **DA-M1.4-03 — Preservação Fiel de Valores Ausentes e Tipos Sem Coerção Destrutiva:**
   - Colunas numéricas com valores ausentes em arquivos texto (`""`, `"NA"`, `"NaN"`, `"null"`, `"None"`, `"nan"`) são convertidas para `float64` com `np.nan` nas posições ausentes.
   - Colunas inteiras sem valores ausentes utilizam `int64` (`np.int64`).
   - Colunas booleanas sem valores ausentes utilizam `bool` (`np.bool_`); se contiverem valores ausentes, utilizam dtype `object` contendo apenas `True`, `False` e `None` (evitando converter `None` em `False` ou em `float`).
   - Colunas textuais, categóricas, temporais ou identificadoras utilizam dtype `object` com strings normalizadas em Unicode NFC e entradas ausentes mapeadas para `None`.
4. **DA-M1.4-04 — Fronteira Explícita Onda 1 vs. Onda 2 em `DatasetSchemaSpec`:**
   - A assinatura de `DatasetSchemaSpec` inclui `target_col: str | Sequence[str]`, `task_type: TaskType`, `group_col: str | None = None`, `observation_id_col: str | None = None`, `time_col: str | None = None`, `ignore_cols: Sequence[str] = ()` e `target_transform_spec: Any | None = None`.
   - Na Onda 1 (`ARQUITETURA_E_CONTRATOS.md` Seção 6.1), `DatasetSchemaSpec.__post_init__` valida que `task_type` pertence a `{REGRESSION, BINARY_CLASSIFICATION, MULTICLASS_CLASSIFICATION}`, que `target_col` é `str` (alvo univariado) e que `target_transform_spec is None`. Caso o usuário acione `MULTI_TARGET_REGRESSION`, passe uma sequência de múltiplos alvos em `target_col` ou forneça `target_transform_spec`, é lançado `ConfigurationError` instrutivo informando que o recurso pertence à Onda 2.

### 4.2 Requisitos Não Funcionais e Restrições Aplicáveis
- **`RNF01` (Determinismo):** A leitura de arquivos, a inferência de tipos, a geração de `observation_ids` e o cálculo de `dataset_hash` são 100% determinísticos e independentes de estado global.
- **`RNF02` (Independência de Domínio):** Nenhum nome de coluna de domínio específico (ex.: inventário florestal) é assumido por padrão.
- **`RNF03` e `RNF06` (Autossuficiência Offline e Compatibilidade):** Implementação restrita à biblioteca padrão do Python (`>=3.10`, testada em `3.12`) e `numpy>=1.24.0`.
- **`RNF04` (Eficiência de Memória):** Representação colunar 1D contígua em NumPy com estimativa exata de consumo de memória em bytes (`memory_bytes`).
- **`ADR-008` (Sem OOP para Lógica de Negócio):** Todas as estruturas são `@dataclass(frozen=True, slots=True)` e todas as operações são funções puras.

---

## 5. Contratos Públicos e Invariantes (`experimental_ml.data`)

### 5.1 Enumeração `ColumnSemanticType(StrEnum)`
Classifica a natureza estrutural e semântica de cada coluna em `ColumnDescriptor`:
- `NUMERIC_CONTINUOUS = "NUMERIC_CONTINUOUS"` (valores em ponto flutuante `float64`)
- `NUMERIC_DISCRETE = "NUMERIC_DISCRETE"` (valores inteiros `int64`)
- `CATEGORICAL = "CATEGORICAL"` (strings/categorias nominais ou ordinais)
- `BOOLEAN = "BOOLEAN"` (valores lógicos booleanos)
- `TEMPORAL = "TEMPORAL"` (coluna designada como `time_col` no esquema)
- `IDENTIFIER = "IDENTIFIER"` (coluna designada como `observation_id_col` no esquema)

### 5.2 Estrutura `DatasetSchemaSpec`
```python
@dataclass(frozen=True, slots=True)
class DatasetSchemaSpec:
    target_col: str | Sequence[str]
    task_type: TaskType
    group_col: str | None = None
    observation_id_col: str | None = None
    time_col: str | None = None
    ignore_cols: tuple[str, ...] = ()
    target_transform_spec: Any | None = None
```
- **Invariantes garantidas em `__post_init__`:**
  1. `task_type` é instância de `TaskType` (ou string canônica convertida para `TaskType`); se `task_type == TaskType.MULTI_TARGET_REGRESSION`, levanta `ConfigurationError` (Onda 2).
  2. `target_col` na Onda 1 deve ser `str` não vazia (rejeitando `Sequence[str]` não-string com `ConfigurationError` da Onda 2 e strings vazias/whitespace/caracteres de controle com `ConfigurationError`).
  3. `target_transform_spec` deve ser `None` na Onda 1 (caso contrário, levanta `ConfigurationError`).
  4. Todos os nomes de colunas (`target_col`, `group_col`, `observation_id_col`, `time_col` e itens de `ignore_cols`) são normalizados via `unicodedata.normalize("NFC", col.strip())` (rejeitando strings vazias, somente espaços ou com caracteres de controle `\n`, `\r`, `\t`, `\x00`).
  5. `ignore_cols` é armazenado como `tuple[str, ...]` imutável e sem duplicatas internas (preservando a ordem de declaração).
  6. **Disjunção Estrita de Papéis:** Os conjuntos `{target_col}`, `{group_col}` (se não nulo), `{observation_id_col}` (se não nulo), `{time_col}` (se não nulo) e `set(ignore_cols)` são mutuamente disjuntos dois a dois. Qualquer colisão levanta `ConfigurationError`.

### 5.3 Estrutura `ColumnDescriptor`
```python
@dataclass(frozen=True, slots=True)
class ColumnDescriptor:
    name: str
    index: int
    role: str  # "target" | "group" | "observation_id" | "time" | "ignored" | "feature"
    semantic_type: ColumnSemanticType
    dtype_str: str
    n_missing: int
    memory_bytes: int
```
- **Invariantes:** `index >= 0`, `0 <= n_missing <= n_rows`, `memory_bytes >= 0`, e `role` reflete exatamente o papel atribuído por `DatasetSchemaSpec` (ou `"feature"` para as demais colunas).

### 5.4 Estrutura `DatasetBundle`
```python
@dataclass(frozen=True, slots=True)
class DatasetBundle:
    schema: DatasetSchemaSpec
    n_rows: int
    n_cols: int
    column_names: tuple[str, ...]
    feature_cols: tuple[str, ...]
    columns: Mapping[str, np.ndarray]
    descriptors: Mapping[str, ColumnDescriptor]
    observation_ids: tuple[ObservationId, ...]
    dataset_hash: str
    memory_bytes: int
    source_path: str | None = None
```
- **Invariantes de Integridade:**
  1. `n_rows >= 1` e `n_cols >= 2` (ao menos 1 coluna de `target_col` e 1 coluna em `feature_cols`).
  2. `len(column_names) == n_cols` e `len(set(column_names)) == n_cols` (nomes únicos em NFC).
  3. `len(feature_cols) >= 1`, mantendo a ordem original em `column_names` e satisfazendo `set(feature_cols) == set(column_names) - ({target_col, group_col, observation_id_col, time_col} | set(ignore_cols))`.
  4. `columns` e `descriptors` são encapsulados em `MappingProxyType` (somente-leitura).
  5. Para todo `c in column_names`, `columns[c]` é um `np.ndarray` 1D com `shape == (n_rows,)` e `columns[c].flags.writeable is False`.
  6. `len(observation_ids) == n_rows`, todos os elementos são instâncias válidas de `ObservationId` e `len(set(observation_ids)) == n_rows` (`CA-E1-01`).
  7. `len(dataset_hash) == 64` (digest SHA-256 hexadecimal minúsculo idêntico a `core.dataset_hash(source, schema)`).

### 5.5 Funções Públicas do Módulo
1. **`validate_dataset_schema(columns: Mapping[str, np.ndarray], schema: DatasetSchemaSpec) -> tuple[str, ...]`:**
   - Verifica a consistência estrutural entre o dicionário ordenado de colunas e o `DatasetSchemaSpec`.
   - Confirma que todas as colunas referenciadas no esquema existem em `columns`, que todas as colunas têm o mesmo comprimento $N \ge 1$, que a coluna `observation_id_col` (quando declarada) não possui nulos nem duplicatas, e que resta pelo menos uma coluna preditora candidata (`feature_cols`), retornando a tupla ordenada `feature_cols`.
   - Lança `DataIntegrityError` em qualquer violação estrutural.
2. **`load_dataset(source, schema, *, delimiter=None, has_header=True, column_names=None, encoding="utf-8") -> DatasetBundle`:**
   - Carrega dados tabulares de caminho em disco (`str | Path`) ou estrutura em memória (`Mapping[str, Sequence]`, `np.ndarray` 2D, `Sequence[Mapping[str, Any]]` ou `DataFrame` duck-typed).
   - Em arquivos texto (`.csv`, `.txt`, `.tsv`):
     - Se `delimiter` for informado, utiliza-o diretamente no parser CSV.
     - Se `delimiter=None`, detecta automaticamente entre `","`, `";"`, `"\t"`, `"|"` ou, quando se tratar de arquivo separado por espaços em branco múltiplos (comum em `.txt` científicos), divide por sequências de espaços `r"\s+"`.
     - Verifica que todas as linhas possuem o mesmo número de colunas $M$ (lançando `DataIntegrityError` para linhas irregulares/truncadas ou arquivo vazio).
     - Se `has_header=True`, extrai os nomes das colunas da primeira linha não vazia (rejeitando nomes vazios ou duplicados após normalização NFC com `DataIntegrityError`).
     - Se `has_header=False`, utiliza `column_names` (validando `len(column_names) == M`) ou gera `("col_0", "col_1", ..., f"col_{M-1}")`.
   - Infere os tipos colunares sem coerção destrutiva, congela os arrays (`writeable = False`), valida o esquema via `validate_dataset_schema`, extrai/gera `observation_ids`, constrói `ColumnDescriptor` por coluna, calcula `dataset_hash` via `core.dataset_hash(source, schema)` e retorna `DatasetBundle`.
3. **`get_column_array(bundle: DatasetBundle, col_name: str) -> np.ndarray`:**
   - Retorna o array 1D somente-leitura correspondente a `col_name` (normalizado em NFC), ou levanta `DataIntegrityError` se a coluna não existir no `bundle`.
4. **`slice_bundle_by_observation_ids(bundle: DatasetBundle, observation_ids: Sequence[ObservationId | str]) -> DatasetBundle`:**
   - Retorna um novo `DatasetBundle` imutável contendo exclusivamente as linhas correspondentes aos `observation_ids` solicitados, na exata ordem informada, recalculando `n_rows`, `descriptors`, `memory_bytes` e o `dataset_hash` em memória (`core.dataset_hash(sliced_columns, bundle.schema)`).
   - Rejeita sequência vazia, IDs duplicados na requisição ou IDs ausentes do `bundle` original com `DataIntegrityError`.

---

## 6. Matriz de Requisitos Rastreáveis e Critérios de Aceitação (DATA-01 a DATA-20)

| ID | Categoria | Requisito EARS (`spec.md`) | Critério Objetivo de Aceitação |
| :--- | :---: | :--- | :--- |
| **DATA-01** | Funcional / Contrato | Estruturas imutáveis `DatasetSchemaSpec`, `ColumnDescriptor`, `DatasetBundle` e enum `ColumnSemanticType` | Instâncias são congeladas (`frozen=True`); tentativa de mutação levanta `FrozenInstanceError` / `AttributeError`; `ColumnSemanticType` expõe os 6 membros canônicos. |
| **DATA-02** | Funcional / Esquema | Normalização Unicode NFC e deduplicação ordenada de `ignore_cols` em `DatasetSchemaSpec` | Nomes em NFD e NFC produzem atributos idênticos em `DatasetSchemaSpec`; `ignore_cols` torna-se `tuple[str, ...]` sem duplicatas preservando a ordem. |
| **DATA-03** | Funcional / Validação | Rejeição de nomes de colunas vazios, whitespace ou com caracteres de controle | Passar `""`, `"   "`, `"col\n1"` ou `"\t"` em qualquer campo de coluna de `DatasetSchemaSpec` levanta `ConfigurationError`. |
| **DATA-04** | Restrição / Escopo | Bloqueio explícito de recursos da Onda 2 em `DatasetSchemaSpec` | `TaskType.MULTI_TARGET_REGRESSION`, `target_col=["y1", "y2"]` ou `target_transform_spec != None` levantam `ConfigurationError` explícito. |
| **DATA-05** | Funcional / Invariante | Disjunção estrita entre papéis de colunas no `DatasetSchemaSpec` | Qualquer repetição de coluna entre `target_col`, `group_col`, `observation_id_col`, `time_col` e `ignore_cols` levanta `ConfigurationError`. |
| **DATA-06** | Não Funcional / Hash | Determinismo de `config_hash(schema)` sob Unicode NFC/NFD | `config_hash` de esquemas equivalentes em NFC e NFD produz exatamente o mesmo digest SHA-256 de 64 caracteres. |
| **DATA-07** | Funcional / Ingestão | Ingestão via `load_dataset` de arquivos `.csv`/`.txt` e estruturas em memória | Carrega `.csv`, `.txt`, `dict` de colunas, `ndarray` 2D, lista de dicts e objeto `DataFrame` duck-typed sem mutar os objetos de entrada. |
| **DATA-08** | Funcional / Ingestão | Suporte a delimitadores explícitos, auto-detectados e múltiplos espaços em `.txt` | `load_dataset` lê corretamente arquivos separados por `,`, `;`, `\t`, `\|` e múltiplos espaços em branco (`delimiter=None`), rejeitando linhas irregulares com `DataIntegrityError`. |
| **DATA-09** | Funcional / Ingestão | Suporte a arquivos e matrizes sem cabeçalho (`has_header=False` e `column_names`) | Gera `("col_0", ..., f"col_{M-1}")` quando `has_header=False` e `column_names=None`, ou aplica `column_names` validando comprimento $M$ (`DataIntegrityError` se divergir). |
| **DATA-10** | Não Funcional / Imutabilidade | Imutabilidade em memória dos arrays colunares e mapeamentos em `DatasetBundle` | Todo array em `bundle.columns.values()` possui `flags.writeable == False` (mutação in-place levanta `ValueError`) e `bundle.columns` / `bundle.descriptors` são `MappingProxyType` (`TypeError` ao atribuir chave). |
| **DATA-11** | Funcional / Integridade | Preservação de valores ausentes sem imputação ou descarte silencioso e derivação de `feature_cols` | Valores ausentes em colunas numéricas (`np.nan`) e categóricas (`None`) são preservados nas linhas originais; `feature_cols` exclui exatamente `{target, group, id, time} ∪ ignore_cols`. |
| **DATA-12** | Não Funcional / Hash | Paridade exata de `DatasetBundle.dataset_hash` com `core.dataset_hash(source, schema)` | `bundle.dataset_hash` coincide bit a bit com `dataset_hash(source, schema)` para arquivos em disco e dados em memória (`CA-E1-01`, **ADR-007**). |
| **DATA-13** | Funcional / Identidade | Geração determinística de `ObservationId` quando `observation_id_col=None` | Produz `("obs_0", "obs_1", ..., f"obs_{N-1}")` como instâncias válidas de `ObservationId` (`CA-E1-01`). |
| **DATA-14** | Funcional / Identidade | Extração e validação de `observation_id_col` explícita | Converte os valores da coluna em `ObservationId` preservando a ordem das linhas quando todos os $N$ valores são válidos, não-nulos e únicos. |
| **DATA-15** | Funcional / Validação | Rejeição de `observation_id_col` com valores ausentes, inválidos ou duplicados | Qualquer `None`, `NaN`, string vazia ou identificador repetido em `observation_id_col` levanta `DataIntegrityError`. |
| **DATA-16** | Funcional / Validação | Validação de existência das colunas do esquema nos dados (`validate_dataset_schema`) | Se `target_col`, `group_col`, `observation_id_col`, `time_col` ou item de `ignore_cols` não existir nos dados, levanta `DataIntegrityError`. |
| **DATA-17** | Funcional / Validação | Rejeição de bases vazias, cabeçalhos duplicados, colunas de tamanhos distintos ou sem `feature_cols` | $N = 0$, $M = 0$, nomes de colunas duplicados, tamanhos de colunas divergentes ou `len(feature_cols) == 0` levantam `DataIntegrityError`. |
| **DATA-18** | Funcional / Metadados | Preenchimento exato de `ColumnDescriptor` e `ColumnSemanticType` por coluna | `bundle.descriptors[col]` registra `name`, `index`, `role`, `semantic_type`, `dtype_str`, `n_missing` e `memory_bytes` consistentes com os dados carregados. |
| **DATA-19** | Funcional / Consulta | Consulta segura de coluna via `get_column_array` | Retorna array 1D com `flags.writeable == False` para coluna existente e levanta `DataIntegrityError` para coluna inexistente. |
| **DATA-20** | Funcional / Consulta | Recorte imutável de observações via `slice_bundle_by_observation_ids` | Retorna novo `DatasetBundle` imutável na ordem solicitada de `observation_ids` com `dataset_hash` atualizado, sem alterar o `bundle` original; rejeita IDs ausentes, vazios ou duplicados com `DataIntegrityError`. |

---

## 7. Riscos Identificados, Casos-Limite e Mitigações

| Risco / Caso-Limite | Impacto Potencial | Mitigação Especificada no M1.4 |
| :--- | :--- | :--- |
| **R1: Mutação acidental de arrays em etapas consumidoras** | Alteração in-place de valores em `bundle.columns[col][i] = ...` corromperia a base original sem atualizar `dataset_hash`, violando `CA-E1-01`. | Todos os arrays NumPy internos são copiados/convertidos na entrada e marcados com `arr.setflags(write=False)`, e os dicionários são protegidos com `MappingProxyType` (**DATA-10**). |
| **R2: Coerção silenciosa de booleanos ou inteiros com valores ausentes** | Em NumPy padrão, converter `[True, None]` para `bool` transforma `None` em `False`, e converter `[1, None]` para `int64` falha ou corrompe dados. | Colunas inteiras com ausentes são promovidas para `float64` com `np.nan`; colunas booleanas com ausentes e colunas textuais/categóricas preservam `None` em array `object` imutável (**DATA-11**, **DA-M1.4-03**). |
| **R3: Ambiguidade de delimitadores em arquivos `.txt` / `.csv`** | `csv.Sniffer` da biblioteca padrão pode falhar em arquivos pequenos ou separados por múltiplos espaços (comuns em bases científicas legadas). | `load_dataset` implementa detecção determinística sobre as linhas de amostra priorizando delimitadores explícitos (`,`, `;`, `\t`, `\|`) e fallback para separação por blocos de espaços em branco (`r"\s+"`), exigindo contagem constante de colunas em todas as linhas (**DATA-08**). |
| **R4: Divergência de `dataset_hash` entre arquivo em disco e estrutura em memória** | Se `load_dataset` calculasse o hash sobre os arrays já convertidos quando a entrada foi um caminho de arquivo, o hash divergiria de `core.dataset_hash(path, schema)` especificado no **ADR-007**. | `load_dataset` invoca diretamente `core.dataset_hash(source, schema)` sobre o argumento `source` original (caminho de arquivo quando carregado de disco; estrutura tabular quando carregado em memória), garantindo paridade de 100% com o M1.2 (**DATA-12**). |
| **R5: Colisões de nomes de colunas por variantes Unicode (NFD vs. NFC)** | Duas colunas com mesma aparência visual mas bytes UTF-8 distintos poderiam burlar a verificação de unicidade ou falhar no casamento com `DatasetSchemaSpec`. | Normalização obrigatória Unicode NFC tanto nos campos de `DatasetSchemaSpec` quanto nos nomes de colunas lidos do arquivo/memória antes da verificação de unicidade (**DATA-02**, **DATA-17**). |

---

## 8. Pontos Submetidos à Revisão e Validação do Usuário

Antes de avançarmos para a fase **Design** do TLC, submetemos à sua revisão as decisões estruturais registradas na seção *Assumptions & Open Questions* de [`spec.md`](./spec.md):
1. **Alocação física em `src/experimental_ml/data/`:** Confirmação de que o M1.4 inaugura o pacote oficial `experimental_ml.data` (Nível 1 de `ARQUITETURA_E_CONTRATOS.md`), entregando os contratos de esquemas e ingestão imutável (`DatasetSchemaSpec`, `ColumnDescriptor`, `DatasetBundle`, `load_dataset`, `validate_dataset_schema`, `get_column_array`, `slice_bundle_by_observation_ids`), enquanto `profile_dataset`, `create_preparation_plan`, `sanitize_dataset`, `validation` e CLI permanecem no Marco M2.
2. **Zero dependência obrigatória de `pandas`:** Confirmação do uso exclusivo de `stdlib` + `numpy>=1.24.0` para leitura e armazenamento colunar imutável, mantendo suporte a objetos `DataFrame` em memória por *duck-typing*.
3. **Tratamento da Onda 2 em `DatasetSchemaSpec`:** Confirmação de que `time_col` já é aceito e validado estruturalmente na disjunção de colunas, enquanto `MULTI_TARGET_REGRESSION`, múltiplos alvos (`target_col: Sequence[str]`) e `target_transform_spec` levantam `ConfigurationError` explícito informando que pertencem à Onda 2.

