# Roteiro de Validação e Aceitação — Marco M1.2

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M1.2 (`m1-2-core`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e consumidores da biblioteca `experimental-ml-framework`.  
> **Premissa de Acesso:** Validação através **exclusivamente das interfaces públicas** exportadas em `experimental_ml.core`.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e o pacote instalado com NumPy:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de versão e importação do módulo core
python -c "import experimental_ml.core; print('Core importado com sucesso! Exportacoes:', len(experimental_ml.core.__all__))"
```

- **Resultado Esperado:** Mensagem confirmando importação e 25 símbolos públicos em `__all__`.
- **Critério de Falha:** `ModuleNotFoundError` para `experimental_ml.core` ou `numpy`.

---

## 2. Roteiro de Testes Manuais de Aceitação por Capacidade

### 2.1 Identificadores de Domínio Imutáveis

```python
from experimental_ml.core import (
    ExperimentId,
    ModelId,
    ObservationId,
    PartitionPlanId,
    ScenarioId,
)

# 1. Instanciação e sanitização automática de whitespace nas bordas
exp_id = ExperimentId("   exp_boston_housing_v1   ")
assert exp_id == "exp_boston_housing_v1"
assert isinstance(exp_id, str)

# 2. Verificação de imutabilidade (subtipo de str)
try:
    exp_id[0] = "X"
except TypeError:
    print("✓ Imutabilidade garantida: identificadores rejeitam mutação in-place.")

# 3. Validação e rejeição de entradas inválidas
casos_invalidos = ["", "   ", "\n", "id\ncom_quebra", "id\tcom_tab", 12345]

for invalido in casos_invalidos:
    try:
        ExperimentId(invalido)
    except (ValueError, TypeError):
        continue
    else:
        raise AssertionError(f"Deveria ter rejeitado: {repr(invalido)}")

print("✓ Validação e rejeição de identificadores inválidos confirmada.")
```

- **Resultado Esperado:** IDs são instanciados e sanitizados; mutações in-place e valores vazios/inválidos são rejeitados com `ValueError`/`TypeError`.
- **Critério de Falha:** ID aceitar string vazia, manter whitespace nas bordas ou permitir mutação in-place.

---

### 2.2 Enumerações Canônicas e Serialização JSON

```python
import json
from experimental_ml.core import (
    AggregationScope,
    ErrorPolicy,
    ExecutionStatus,
    FindingSeverity,
    MetricDirection,
    MetricStatus,
    TaskType,
)

# 1. Igualdade direta com strings literais
assert TaskType.REGRESSION == "REGRESSION"
assert ExecutionStatus.COMPLETED == "COMPLETED"
assert MetricDirection.MINIMIZE == "MINIMIZE"
assert FindingSeverity.CONFIRMED_ISSUE == "CONFIRMED_ISSUE"
assert AggregationScope.FOLD_AGGREGATION == "FOLD_AGGREGATION"
assert MetricStatus.UNDEFINED_NAN == "UNDEFINED_NAN"
assert ErrorPolicy.FAIL_FAST == "FAIL_FAST"

# 2. Serialização JSON nativa
payload = {"task": TaskType.REGRESSION, "policy": ErrorPolicy.FAIL_FAST}
dumped = json.dumps(payload)
carregado = json.loads(dumped)
assert carregado["task"] == "REGRESSION"
assert carregado["policy"] == "FAIL_FAST"
print("✓ Enumerações compatíveis com strings e serializáveis nativamente para JSON.")
```

- **Resultado Esperado:** Membros comparam diretamente com strings e são serializados pelo `json.dumps()` sem custom encoders.
- **Critério de Falha:** Erro de serialização JSON (`TypeError: Object of type TaskType is not JSON serializable`).

---

### 2.3 Derivação Hierárquica Determinística de Sementes

```python
from experimental_ml.core import derive_seeds, spawn_child_seeds

# 1. Determinismo estrito sob a mesma semente mestre
s1 = derive_seeds(master_seed=42, count=5)
s2 = derive_seeds(master_seed=42, count=5)
assert s1 == s2, "FALHA: Quebra de determinismo em derive_seeds!"
assert len(set(s1)) == 5, "FALHA: Colisão entre sementes geradas!"

# 2. Spawning de sequências filhas independentes
filhos = spawn_child_seeds(parent_seed=s1[0], count=3)
assert len(filhos) == 3 and len(set(filhos)) == 3

# 3. Validação de count < 1
try:
    derive_seeds(master_seed=42, count=0)
    raise AssertionError("FALHA: Deveria ter rejeitado count=0!")
except ValueError:
    pass


print("✓ Derivação determinística de sementes confirmada.")
```

- **Resultado Esperado:** Tuplas de inteiros idênticas entre invocações com mesma semente mestre; sementes independentes; rejeição de `count < 1` com `ValueError`.
- **Critério de Falha:** Divergência entre tuplas geradas ou aceitação de contagem zero/negativa.

---

### 2.4 Hashing Canônico de Configurações (`config_hash`) — ADR-007

```python
import math
import unicodedata
from experimental_ml.core import config_hash, TaskType

# 1. Invariância Unicode NFC vs NFD
s_nfc = "coração"
s_nfd = unicodedata.normalize("NFD", s_nfc)
assert config_hash({"texto": s_nfc}) == config_hash({"texto": s_nfd})

# 2. Invariância à ordem de inserção das chaves
assert config_hash({"a": 1, "b": 2}) == config_hash({"b": 2, "a": 1})

# 3. Distinção estrita de escalares
assert config_hash(True) != config_hash(1)
assert config_hash(False) != config_hash(0)
assert config_hash(1) != config_hash(1.0)

# 4. Normalização de -0.0 vs 0.0 e tratamento de NaN/Inf
assert config_hash(-0.0) == config_hash(0.0)
assert config_hash(float("nan")) == config_hash(math.nan)
assert config_hash(float("inf")) != config_hash(float("-inf"))

# 5. Distinção entre tuplas e listas, e ordenação de conjuntos
assert config_hash([1, 2]) != config_hash((1, 2))
assert config_hash({30, 10, 20}) == config_hash({10, 20, 30})

print("✓ Regras canônicas do ADR-007 em config_hash validadas.")
```

- **Resultado Esperado:** Hashes com 64 caracteres hexadecimais em minúsculas; respeito integral às equivalências (NFC/NFD, ordem de chaves, -0.0) e distinções obrigatórias (`bool != int != float`, `tuple != list`).
- **Critério de Falha:** Colisão de hash entre `True` e `1`, ou diferença entre `-0.0` e `+0.0`.

---

### 2.5 Hashing Estrutural de Datasets (`dataset_hash`)

```python
from pathlib import Path
import tempfile
from experimental_ml.core import dataset_hash

# 1. Arquivo CSV em disco com esquema
with tempfile.NamedTemporaryFile("w+", suffix=".csv", delete=False) as tmp:
    tmp.write("feat1,feat2,target\n1.0,2.0,10.0\n3.0,4.0,20.0\n")
    tmp_path = Path(tmp.name)

try:
    h_sem_esquema = dataset_hash(tmp_path)
    h_com_esquema = dataset_hash(tmp_path, schema={"target": "target"})
    assert h_sem_esquema != h_com_esquema
finally:
    tmp_path.unlink()

# 2. Dados tabulares em memória (diferenciação de nomes, tipos e ordem)
d_base = {"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]}
h_base = dataset_hash(d_base)
assert dataset_hash({"c": [1, 2, 3], "b": [4.0, 5.0, 6.0]}) != h_base   # outro nome
assert dataset_hash({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]}) != h_base # outro tipo
assert dataset_hash({"a": [2, 1, 3], "b": [5.0, 4.0, 6.0]}) != h_base   # outra ordem

# 3. Rejeição de arquivo inexistente
try:
    dataset_hash("arquivo_inexistente_12345.csv")
    raise AssertionError("FALHA: Deveria ter lançado FileNotFoundError!")
except FileNotFoundError:
    pass

print("✓ Hashing de datasets para arquivos e memória validado com sucesso.")
```

- **Resultado Esperado:** Hashes diferenciam esquemas, nomes de colunas, ordenação e tipagem; arquivos ausentes disparam `FileNotFoundError`.
- **Critério de Falha:** Hash idêntico para colunas renomeadas ou ausência de erro em arquivo inexistente.

---

### 2.6 Diagnósticos Estruturados e Exceções de Integridade

```python
from experimental_ml.core import (
    ConfigurationError,
    ContractViolationError,
    DataIntegrityError,
    ExperimentalMLError,
    Finding,
    FindingSeverity,
    make_finding,
    make_warning,
)

# 1. Construtores de achados
issue = make_finding(code="E1_ZERO_VARIANCE", message="Variância zero.")
warning = make_warning(code="W1_HIGH_CARD", message="Possível ID.")
assert issue.severity == FindingSeverity.CONFIRMED_ISSUE
assert warning.severity == FindingSeverity.HEURISTIC_WARNING

# 2. Imutabilidade
try:
    issue.code = "OUTRO"
except (AttributeError, TypeError):
    pass

# 3. Exceções de domínio
assert issubclass(ContractViolationError, ExperimentalMLError)
assert issubclass(DataIntegrityError, ExperimentalMLError)
assert issubclass(ConfigurationError, ExperimentalMLError)
print("✓ Diagnósticos imutáveis e hierarquia de exceções validados.")
```

- **Resultado Esperado:** Achados criados com severidades corretas; instância `Finding` congelada; exceções subtipadas em `ExperimentalMLError`.
- **Critério de Falha:** Mutação in-place permitida em `Finding` ou exceções não herdarem de `ExperimentalMLError`.

---

## 3. Cenário Integrado de Aceitação (Preparação de Experimento)

Execute o comando integrado completo no terminal:

```bash
python - << 'EOF'
from experimental_ml.core import (
    ExperimentId, ModelId, ScenarioId, PartitionPlanId,
    TaskType, ErrorPolicy, derive_seeds, config_hash, dataset_hash,
    make_warning, ContractViolationError
)

# 1. IDs do Experimento
exp_id = ExperimentId("exp_biomassa_2026")
model_id = ModelId("rf_regressor")
scenario_id = ScenarioId("cenario_atributos_quimicos")
part_id = PartitionPlanId("kfold_5")

# 2. Configuração e config_hash
config = {
    "model_id": model_id,
    "task": TaskType.REGRESSION,
    "policy": ErrorPolicy.FAIL_FAST,
    "params": {"n_estimators": 100, "max_depth": 10}
}
h_cfg = config_hash(config)
assert len(h_cfg) == 64

# 3. Dados e dataset_hash
dados = {"dap": [15.2, 18.5, 22.1], "altura": [12.0, 14.2, 16.8]}
h_data = dataset_hash(dados, schema={"target": "volume"})
assert len(h_data) == 64

# 4. Derivação de sementes para 5 folds
sementes = derive_seeds(master_seed=2026, count=5)
assert len(sementes) == 5

# 5. Emissão de alerta pedagógico
alerta = make_warning("W_AMOSTRA_PEQUENA", "Base pequena de teste.")
assert alerta.severity == "HEURISTIC_WARNING"

print("✓ CENÁRIO INTEGRADO DO M1.2 EXECUTADO COM 100% DE SUCESSO!")
EOF
```

- **Resultado Esperado:** Saída `✓ CENÁRIO INTEGRADO DO M1.2 EXECUTADO COM 100% DE SUCESSO!` e código de saída 0.
- **Critério de Falha:** Qualquer exceção lançada ou interrupção prematura.

---

## 4. Matriz de Critérios de Aprovação do Marco M1.2

| Item | Descrição do Teste | Tipo | Responsável | Critério de Aceite |
| :--- | :--- | :--- | :--- | :--- |
| **AC-M1.2-1** | Imutabilidade e validação dos 8 IDs | Funcional / Robustez | Consumidor | Rejeição estrita de inválidos e imutabilidade |
| **AC-M1.2-2** | Enumerações e serialização JSON | Funcional | Consumidor | Igualdade a strings e JSON nativo |
| **AC-M1.2-3** | Derivação determinística de sementes | Algorítmico / RNF01 | Consumidor | Reprodutibilidade exata e independência |
| **AC-M1.2-4** | Hashing canônico ADR-007 (`config_hash`) | Integridade / ADR-007 | Consumidor | Cumprimento de 100% das regras canônicas |
| **AC-M1.2-5** | Hashing estrutural (`dataset_hash`) | Integridade / RNF06 | Consumidor | Sensibilidade a esquema, nomes, dtypes e ordem |
| **AC-M1.2-6** | Diagnósticos e exceções formais | Arquitetural / ADR-002 | Consumidor | Finding congelado e exceções padronizadas |
| **AC-M1.2-7** | Suíte `tests/unit/test_core.py` | Automatizado | Runner / Pytest | 18/18 testes aprovados |
| **AC-M1.2-8** | Suíte geral do projeto (`pytest tests/`) | Regressão | Runner / Pytest | 30/30 testes aprovados (12 smoke + 18 core) |
| **AC-M1.2-9** | Portão TLC (`validate_verification.py`) | Verificação Mecânica | Agente Verificador | 0 erros, 0 avisos |

