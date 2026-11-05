# Roteiro de Homologação e Aceite — M1.5 Saneamento da Fundação M1 (`m1-5-foundation-hardening`)

## 1. Pré-requisitos e Ambiente

- Diretório raiz: `/home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework`
- Ambiente virtual: `.venv/bin/python` (`Python >= 3.10`, `numpy`, `pytest`)

## 2. Verificação de Resolução dos Achados P0 e P1 Selecionados

### 2.1. Execução da Suíte Completa de Testes (Unitários, Regressão e Integração)

```bash
.venv/bin/pytest tests/ -v
```

**Critério esperado:** 100% dos testes aprovados (`PASSED`), incluindo os novos testes unitários de regressão em `tests/unit/test_core.py`, `tests/unit/test_data_schemas.py` e a suíte de integração `tests/integration/test_m1_foundation_integration.py`.

### 2.2. Verificação Prática dos 6 Achados P0 e P1 Selecionados via Interface Pública

```bash
.venv/bin/python -c '
import types
import numpy as np
from experimental_ml.core import (
    DataIntegrityError,
    ObservationId,
    TaskType,
    dataset_hash,
    is_missing_scalar,
    is_nan_scalar,
)
from experimental_ml.data import (
    DatasetSchemaSpec,
    load_dataset,
    slice_bundle_by_observation_ids,
)

# P0.1 (AUD-F-004): Ausência de colisão por concatenação de nomes de colunas
assert dataset_hash({"ab": [1.0], "c": [2.0]}) != dataset_hash({"a": [1.0], "bc": [2.0]})

# P0.2 (AUD-F-008): Detecção centralizada de NaN nativo e NumPy
for nan_val in (float("nan"), np.float16(np.nan), np.float32(np.nan), np.float64(np.nan)):
    assert is_nan_scalar(nan_val) is True
    assert is_missing_scalar(nan_val) is True
assert is_missing_scalar(None) is True
assert is_nan_scalar(True) is False

schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
arr_f32 = np.array([[1.0, np.nan], [2.0, 3.0]], dtype=np.float32)
b_f32 = load_dataset(arr_f32, schema, column_names=("x", "y"))
assert b_f32.descriptors["y"].n_missing == 1

# P0.3 (AUD-F-006) & P0.5 (AUD-F-005): Preservação de ObservationId e distinção de dataset_hash
b_dup = load_dataset({"x": [1.0, 1.0], "y": [2.0, 2.0]}, schema)
s0 = slice_bundle_by_observation_ids(b_dup, ["obs_000000"])
s1 = slice_bundle_by_observation_ids(b_dup, ["obs_000001"])
assert type(s1.observation_ids[0]) is ObservationId
assert s0.dataset_hash != s1.dataset_hash
assert s1.dataset_hash == dataset_hash(s1.columns, s1.schema, observation_ids=s1.observation_ids)

# P0.1 (AUD-F-004): Separacao de tipos escalares com mesma representacao textual
assert dataset_hash({"x": ["1"]}) != dataset_hash({"x": [1]})
assert dataset_hash({"x": [1]}) != dataset_hash({"x": [1.0]})
assert dataset_hash({"x": [1]}) != dataset_hash({"x": [True]})
assert dataset_hash({"x": ["1"]}) != dataset_hash({"x": [b"1"]})

# P0.4 (AUD-F-009): Whitelist estrita em colunas dtype=object
try:
    load_dataset({"x": [types.SimpleNamespace(a=1), types.SimpleNamespace(a=2)], "y": [1.0, 2.0]}, schema)
    raise AssertionError("Deveria rejeitar SimpleNamespace")
except DataIntegrityError:
    pass

# P1 (AUD-F-007): Captura de OverflowError como DataIntegrityError
try:
    load_dataset({"x": [2**63, 1], "y": [1.0, 2.0]}, schema)
    raise AssertionError("Deveria rejeitar inteiro >= 2**63")
except DataIntegrityError:
    pass

print("Todas as verificacoes P0 e P1 passaram com sucesso!")
'
```

## 3. Critérios de Aprovação

1. Todos os 6 achados P0 (`AUD-F-001`, `AUD-F-004`, `AUD-F-005`, `AUD-F-006`, `AUD-F-008`, `AUD-F-009`) e os 4 achados P1 selecionados (`AUD-F-002`, `AUD-F-007`, `AUD-F-010`, `AUD-F-013`) estão `RESOLVIDO`.
2. Os 6 achados fora do escopo (`AUD-F-003`, `AUD-F-011`, `AUD-F-012`, `AUD-F-014`, `AUD-F-015`, `AUD-F-016`) estão formalmente registrados como `ADIADO` com destino explícito.
3. Os validadores TLC (`validate_spec.py`, `validate_tasks.py`, `check_proofs.py`, `validate_verification.py`) e a verificação independente (`verification.md`) aprovam a entrega com `0 errors`.

