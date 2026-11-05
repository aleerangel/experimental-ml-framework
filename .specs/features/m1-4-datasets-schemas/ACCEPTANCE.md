# Roteiro de Validação e Aceitação — Marco M1.4

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M1.4 (`m1-4-datasets-schemas`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e consumidores da biblioteca `experimental-ml-framework`.  
> **Premissa de Acesso:** Validação através **exclusivamente das interfaces públicas** exportadas em `experimental_ml.data`.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e o pacote instalado com NumPy:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de versão e importação do módulo data
python -c "import experimental_ml.data; print('Data importado com sucesso! Exportacoes:', len(experimental_ml.data.__all__))"
```

- **Resultado Esperado:** Mensagem confirmando importação e 13 símbolos públicos exportados em `__all__`.
- **Critério de Falha:** `ModuleNotFoundError` para `experimental_ml.data` ou símbolos ausentes.

---

## 2. Roteiro de Testes Manuais de Aceitação por Capacidade

### 2.1 Especificação Declarativa e Imutável de Esquema (`DatasetSchemaSpec`)

```python
import pytest
from experimental_ml.core import TaskType, ConfigurationError
from experimental_ml.data import (
    ColumnSemanticType,
    DatasetSchemaSpec,
    validate_schema_spec,
)

# 1. Instanciação válida com normalização Unicode NFC
schema = DatasetSchemaSpec(
    target_col="preco_venda",
    task_type=TaskType.REGRESSION,
    group_col="regiao_geografica",
    ignore_cols=("id_legado", "observacao_texto"),
    column_semantic_types={"area_construida": ColumnSemanticType.NUMERIC_CONTINUOUS},
)

assert schema.target_col == "preco_venda"
assert schema.task_type == TaskType.REGRESSION
assert schema.ignore_cols == ("id_legado", "observacao_texto")
assert schema.column_semantic_types["area_construida"] == ColumnSemanticType.NUMERIC_CONTINUOUS

# 2. Validação sintática
validate_schema_spec(schema)

# 3. Rejeição de papéis sobrepostos (alvo não pode ser coluna ignorada)
try:
    DatasetSchemaSpec(
        target_col="preco",
        task_type=TaskType.REGRESSION,
        ignore_cols=("preco",),
    )
    raise AssertionError("Deveria ter lançado ConfigurationError")
except ConfigurationError:
    pass

# 4. Bloqueio de funcionalidades da Onda 2 (MULTI_TARGET_REGRESSION)
try:
    DatasetSchemaSpec(
        target_col="preco",
        task_type=TaskType.MULTI_TARGET_REGRESSION,
    )
    raise AssertionError("Deveria ter lançado ConfigurationError para Onda 2")
except ConfigurationError:
    pass

print("2.1 Especificação e Validação de Esquema: APROVADO")
```

---

### 2.2 Ingestão Tabular e Isolamento Profundo de Memória (`load_dataset`)

```python
import numpy as np
from experimental_ml.core import TaskType
from experimental_ml.data import DatasetSchemaSpec, load_dataset, DatasetBundle

schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.REGRESSION)

# Dados originais em memória
orig_matrix = np.array([[10.0, 1.0], [20.0, 2.0]], dtype=np.float64)
bundle = load_dataset(orig_matrix, schema, column_names=["target", "feature_1"])

# Verificação de propriedade exclusiva e isolamento de memória
assert isinstance(bundle, DatasetBundle)
assert bundle.n_rows == 2
assert bundle.n_cols == 2

# Mutação na fonte original NÃO afeta o bundle
orig_matrix[0, 0] = 9999.0
assert bundle.columns["target"][0] == 10.0

print("2.2 Ingestão e Isolamento de Memória: APROVADO")
```

---

### 2.3 Imutabilidade Física dos Arrays de Coluna (Buffer Imutável)

```python
import pytest
from experimental_ml.core import TaskType
from experimental_ml.data import DatasetSchemaSpec, load_dataset

schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
data = {"y": [1.0, 2.0, 3.0], "feat": [10, 20, 30]}

bundle = load_dataset(data, schema)
y_arr = bundle.columns["y"]

# 1. Array é somente-leitura
assert y_arr.flags.writeable is False

# 2. Modificação direta in-place lança ValueError
try:
    y_arr[0] = 999.0
    raise AssertionError("Deveria ter lançado ValueError")
except ValueError:
    pass

# 3. Tentativa de reativar escrita via setflags(write=True) é fisicamente bloqueada
try:
    y_arr.setflags(write=True)
    raise AssertionError("Deveria ter lançado ValueError ao tentar reativar escrita em buffer imutável")
except ValueError as e:
    assert "cannot set WRITEABLE flag to True" in str(e)

print("2.3 Imutabilidade Física de Buffers: APROVADO")
```

---

### 2.4 Parsing Estrito, Delimitadores e Linhas Irregulares (*Ragged Rows*)

```python
import tempfile
from pathlib import Path
from experimental_ml.core import TaskType, DataIntegrityError
from experimental_ml.data import DatasetSchemaSpec, load_dataset

schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)

with tempfile.TemporaryDirectory() as tmp_dir:
    # 1. Arquivo CSV bem formado com aspas RFC 4180
    valid_csv = Path(tmp_dir) / "valid.csv"
    valid_csv.write_text('y,text_col,val\n10.0,"Silva, João",1\n20.0,"Valor com ""aspas""",2\n', encoding="utf-8")
    bundle_valid = load_dataset(valid_csv, schema)
    assert bundle_valid.columns["text_col"][0] == "Silva, João"
    assert bundle_valid.columns["text_col"][1] == 'Valor com "aspas"'

    # 2. Arquivo com linha irregular (ragged row)
    ragged_csv = Path(tmp_dir) / "ragged.csv"
    ragged_csv.write_text("y,x1,x2\n1.0,2.0,3.0\n4.0,5.0\n", encoding="utf-8")
    try:
        load_dataset(ragged_csv, schema)
        raise AssertionError("Deveria ter lançado DataIntegrityError para linha irregular")
    except DataIntegrityError as e:
        assert "ragged row" in str(e).lower()
        assert "Line 3" in str(e)

    # 3. Arquivo vazio
    empty_csv = Path(tmp_dir) / "empty.csv"
    empty_csv.write_text("", encoding="utf-8")
    try:
        load_dataset(empty_csv, schema)
        raise AssertionError("Deveria ter lançado DataIntegrityError para arquivo vazio")
    except DataIntegrityError:
        pass

print("2.4 Parsing Estrito e Detecção de Delimitadores: APROVADO")
```

---

### 2.5 Tipagem Semântica Declarada vs. Padrão Neutro (`ColumnDescriptor`)

```python
from experimental_ml.core import TaskType
from experimental_ml.data import ColumnSemanticType, DatasetSchemaSpec, load_dataset

schema = DatasetSchemaSpec(
    target_col="y",
    task_type=TaskType.REGRESSION,
    column_semantic_types={"codigo_postal": ColumnSemanticType.CATEGORICAL},
)

# Coluna codigo_postal possui números inteiros, mas semântica declarada CATEGORICAL
data = {"y": [10.5, 20.5], "codigo_postal": [12345, 67890], "area": [50.0, 80.0]}
bundle = load_dataset(data, schema)

desc_cep = bundle.descriptors["codigo_postal"]
assert desc_cep.physical_type == "int64"
assert desc_cep.semantic_type == ColumnSemanticType.CATEGORICAL
assert desc_cep.is_semantic_declared is True

desc_area = bundle.descriptors["area"]
assert desc_area.physical_type == "float64"
assert desc_area.semantic_type == ColumnSemanticType.NUMERIC_CONTINUOUS
assert desc_area.is_semantic_declared is False

print("2.5 Tipagem Semântica Declarada vs Padrão Neutro: APROVADO")
```

---

### 2.6 Atribuição e Validação de `ObservationId`

```python
import pytest
from experimental_ml.core import TaskType, DataIntegrityError
from experimental_ml.data import DatasetSchemaSpec, load_dataset

# 1. Geração determinística posicional quando observation_id_col é None
schema_auto = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
data_auto = {"y": [1.0, 2.0, 3.0], "x": [10, 20, 30]}
bundle_auto = load_dataset(data_auto, schema_auto)
assert [str(obs) for obs in bundle_auto.observation_ids] == ["obs_000000", "obs_000001", "obs_000002"]

# 2. Validação estrita de unicidade e não-nulidade quando observation_id_col é informada
schema_id = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION, observation_id_col="cod_id")
data_dup = {"y": [1.0, 2.0], "cod_id": ["id_01", "id_01"], "x": [10, 20]}
try:
    load_dataset(data_dup, schema_id)
    raise AssertionError("Deveria ter lançado DataIntegrityError para ID duplicado")
except DataIntegrityError as e:
    assert "duplicate ObservationId" in str(e)

print("2.6 Atribuição e Validação de ObservationId: APROVADO")
```

---

### 2.7 Utilitários de Consulta Somente-Leitura e Fatiamento Ordenado

```python
import pytest
from experimental_ml.core import TaskType, DataIntegrityError
from experimental_ml.data import (
    DatasetSchemaSpec,
    load_dataset,
    get_column_array,
    slice_bundle_by_observation_ids,
)

schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
data = {"y": [10.0, 20.0, 30.0], "x": [1.0, 2.0, 3.0]}
bundle = load_dataset(data, schema)

# 1. Extração de array (view vs cópia)
view_x = get_column_array(bundle, "x", copy=False)
assert view_x.flags.writeable is False

copy_x = get_column_array(bundle, "x", copy=True)
assert copy_x.flags.writeable is True
copy_x[0] = 999.0
assert bundle.columns["x"][0] == 1.0

# 2. Fatiamento preservando estritamente a ordem requisitada
obs_ids = bundle.observation_ids
requested_order = (obs_ids[2], obs_ids[0])
sliced = slice_bundle_by_observation_ids(bundle, requested_order)

assert sliced.n_rows == 2
assert sliced.observation_ids == requested_order
assert sliced.columns["y"][0] == 30.0
assert sliced.columns["y"][1] == 10.0
assert sliced.dataset_hash != bundle.dataset_hash

# 3. Rejeição de sequência inválida (vazia ou com duplicata)
try:
    slice_bundle_by_observation_ids(bundle, ())
    raise AssertionError("Deveria ter lançado DataIntegrityError para sequência vazia")
except DataIntegrityError:
    pass

print("2.7 Utilitários de Consulta e Fatiamento Ordenado: APROVADO")
```

---

### 2.8 Semântica Tripartite de Identidade (`dataset_hash`, `raw_source_hash`, `schema_hash`)

```python
import tempfile
from pathlib import Path
from experimental_ml.core import TaskType
from experimental_ml.data import DatasetSchemaSpec, load_dataset

schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)

with tempfile.TemporaryDirectory() as tmp_dir:
    # CSV com finais de linha CRLF
    p_crlf = Path(tmp_dir) / "crlf.csv"
    p_crlf.write_bytes(b"y,x\r\n10.0,1.0\r\n20.0,2.0\r\n")

    # CSV com finais de linha LF
    p_lf = Path(tmp_dir) / "lf.csv"
    p_lf.write_bytes(b"y,x\n10.0,1.0\n20.0,2.0\n")

    bundle_crlf = load_dataset(p_crlf, schema)
    bundle_lf = load_dataset(p_lf, schema)
    bundle_mem = load_dataset({"y": [10.0, 20.0], "x": [1.0, 2.0]}, schema)

    # Identidade lógica em memória é idêntica
    assert bundle_crlf.dataset_hash == bundle_lf.dataset_hash == bundle_mem.dataset_hash

    # Hashes da fonte original são preservados
    assert len(bundle_crlf.raw_source_hash) == 64
    assert len(bundle_crlf.schema_hash) == 64

print("2.8 Semântica Tripartite de Hashing: APROVADO")
```

---

## 3. Matriz de Rastreabilidade e Critérios de Homologação Manual

| ID Critério | Capacidade / Requisito | Evidência de Homologação |
| --- | --- | --- |
| **AC-M1.4-1** | Imutabilidade e slots em `DatasetSchemaSpec`, `ColumnDescriptor` e `DatasetBundle` (DATA-01) | Inspeção de tipos `@dataclass(frozen=True, slots=True)` e teste 2.1 |
| **AC-M1.4-2** | Normalização NFC de colunas, disjunção de papéis e bloqueio da Onda 2 (DATA-02 a DATA-06) | Validação sintática e teste 2.1 |
| **AC-M1.4-3** | Ingestão com propriedade exclusiva e isolamento de memória (DATA-07, DATA-08) | Cópia defensiva e teste 2.2 |
| **AC-M1.4-4** | Bloqueio físico de reativação de escrita em arrays via buffers `bytes` (DATA-09, DATA-10) | Falha de `setflags(write=True)` e teste 2.3 |
| **AC-M1.4-5** | Preservação de valores ausentes sem imputação silenciosa (DATA-11) | Preservação de `np.nan` e `None` e teste 2.4 |
| **AC-M1.4-6** | Parsing estrito RFC 4180, delimitadores e rejeição de ragged rows (DATA-15 a DATA-22) | Detecção e parsing em disco e teste 2.4 |
| **AC-M1.4-7** | Tipagem semântica declarada vs. neutral default em `ColumnDescriptor` (DATA-23, DATA-24) | Descritores físicos vs semânticos e teste 2.5 |
| **AC-M1.4-8** | Atribuição determinística e unicidade estrita de `ObservationId` (DATA-25, DATA-26, DATA-27) | Sequência `obs_000000` e validação intrínseca no teste 2.6 |
| **AC-M1.4-9** | Utilitários funcionais `get_column_array` e fatiamento ordenado (DATA-28, DATA-29) | Views/cópias e ordenação com recálculo de hash no teste 2.7 |
| **AC-M1.4-10**| Canonização de hashes tripartites (`dataset_hash`, `raw_source_hash`, `schema_hash`) (DATA-13, DATA-14) | Equivalência CSV CRLF/LF e memória no teste 2.8 |

---

## 4. Estado da Homologação Manual

- [ ] **Homologação Manual**: **PENDENTE** (Aguardando execução e validação formal pelo pesquisador/usuário).

