# Roteiro de Validação e Aceitação — Marco M3.2 (Definição e Validação de Cenários de Features)

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M3.2 (`m3-2-feature-scenarios`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e consumidores da biblioteca `experimental-ml-framework`.  
> **Premissa de Acesso:** Validação através **exclusivamente das interfaces públicas** exportadas em `experimental_ml.features` e `experimental_ml.stages`.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e o pacote instalado com suporte a desenvolvimento:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de versão e exportações dos módulos features e stages
python -c "
import experimental_ml.features as f
import experimental_ml.stages as s
assert 'FeatureScenario' in f.__all__
assert 'ScenarioMode' in f.__all__
assert 'ScenariosCatalog' in f.__all__
assert 'validate_scenarios' in f.__all__
assert 'save_scenarios' in f.__all__
assert 'load_scenarios' in f.__all__
assert 'verify_scenarios_gate' in s.__all__
print('Módulos features e stages importados com sucesso!')
"
```

- **Resultado Esperado:** Mensagem confirmando importação bem-sucedida de todas as interfaces públicas da funcionalidade.
- **Critério de Falha:** `ModuleNotFoundError` ou ausência dos símbolos públicos exportados em `__all__`.

---

## 2. Roteiro de Testes Manuais de Aceitação por Capacidade

### 2.1 Modelagem Declarativa e Imutabilidade (`FeatureScenario`)

```python
from dataclasses import FrozenInstanceError
from types import MappingProxyType
import pytest
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.features import FeatureScenario, ScenarioMode

# 1. Instanciação válida com parâmetros imutáveis
scenario = FeatureScenario(
    scenario_id="biometric_baseline",
    name="Biometric Baseline",
    description="Subconjunto biométrico mínimo de preditores",
    scientific_justification="Base estabelecida na literatura florestal",
    mode=ScenarioMode.FIXED,
    selected_features=("dap", "ht"),
    preprocessing_config={"scale": True},
)

# 2. Garantia de congelamento e imutabilidade de atributos
try:
    scenario.name = "Mutated"
    assert False, "Deveria ter lançado FrozenInstanceError"
except FrozenInstanceError:
    pass

assert isinstance(scenario.preprocessing_config, MappingProxyType)
assert scenario.preprocessing_config["scale"] is True

# 3. Rejeição de slug inválido (com espaços ou caracteres não permitidos)
try:
    FeatureScenario(
        scenario_id="invalid slug with spaces!",
        name="Invalid",
        description="Desc",
        scientific_justification="Just",
        mode=ScenarioMode.FIXED,
        selected_features=("dap",),
    )
    assert False, "Deveria ter lançado ConfigurationError"
except ConfigurationError:
    pass
```

- **Resultado Esperado:** Instâncias `FeatureScenario` congeladas (`frozen=True, slots=True`), dicionários convertidos para `MappingProxyType`, e slugs validados via regex canônico.

---

### 2.2 Restrições de Modo e Invariante Anti-Leakage (`FIXED` vs `DYNAMIC`)

```python
from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.features import FeatureScenario, ScenarioMode

# 1. Modo FIXED exige sequência não-vazia e rejeita estratégia dinâmica
try:
    FeatureScenario(
        scenario_id="fixed_empty",
        name="Empty",
        description="Desc",
        scientific_justification="Just",
        mode=ScenarioMode.FIXED,
        selected_features=(),
    )
    assert False, "FIXED com features vazias deveria falhar"
except ConfigurationError:
    pass

try:
    FeatureScenario(
        scenario_id="fixed_with_strategy",
        name="Invalid",
        description="Desc",
        scientific_justification="Just",
        mode=ScenarioMode.FIXED,
        selected_features=("dap",),
        strategy_name="PCA",
    )
    assert False, "FIXED com strategy_name deveria falhar"
except ConfigurationError:
    pass

# 2. Modo DYNAMIC exige strategy_name e proíbe terminantemente selected_features pré-partição
dynamic_scen = FeatureScenario(
    scenario_id="dynamic_mi_top_k",
    name="Top K Mutual Information",
    description="Seleção intra-fold sem vazamento pré-partição",
    scientific_justification="Prevenção de selection bias",
    mode=ScenarioMode.DYNAMIC,
    strategy_name="MUTUAL_INFO_TOP_K",
    strategy_params={"k": 5},
)
assert dynamic_scen.selected_features == ()

try:
    FeatureScenario(
        scenario_id="dynamic_leaked",
        name="Leaked",
        description="Desc",
        scientific_justification="Just",
        mode=ScenarioMode.DYNAMIC,
        strategy_name="MUTUAL_INFO_TOP_K",
        selected_features=("dap", "ht"),  # Vazamento pré-partição proibido!
    )
    assert False, "DYNAMIC com selected_features deveria lançar ContractViolationError"
except ContractViolationError:
    pass
```

- **Resultado Esperado:** Cenários `FIXED` contêm apenas features estáticas sem parâmetros de estratégia; cenários `DYNAMIC` proíbem estritamente features pré-calculadas para impedir vazamento de dados pré-partição (RF2.4, ADR-002).

---

### 2.3 Validação de Catálogo e Disjunção de Colunas Protegidas (`validate_scenarios`)

```python
import numpy as np
from experimental_ml.core.enums import TaskType
from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.data import (
    DatasetSchemaSpec,
    PreparationRule,
    create_preparation_plan,
    load_dataset,
    profile_dataset,
    sanitize_dataset,
)
from experimental_ml.features import (
    FeatureScenario,
    ScenarioMode,
    validate_scenarios,
)

# Criação de base saneada
data = {
    "dap": [10.0, 20.0, 30.0, 40.0],
    "ht": [12.0, 22.0, 31.0, 39.0],
    "parcela": [1, 1, 2, 2],
    "admin_id": [101, 102, 103, 104],
    "volume": [0.1, 0.4, 0.9, 1.6],
}
schema = DatasetSchemaSpec(
    target_col="volume",
    task_type=TaskType.REGRESSION,
    group_col="parcela",
    ignore_cols=("admin_id",),
)
bundle = load_dataset(data, schema=schema)
profile = profile_dataset(bundle)
plan = create_preparation_plan(profile, [])
view = sanitize_dataset(bundle, profile, plan)

s_valid_1 = FeatureScenario("s1_dap", "DAP Only", "Desc", "Just", ScenarioMode.FIXED, ("dap",))
s_valid_2 = FeatureScenario("s2_all", "All Predictors", "Desc", "Just", ScenarioMode.FIXED, ("dap", "ht"))

# Validação com sucesso
catalog = validate_scenarios([s_valid_1, s_valid_2], view)
assert catalog.dataset_hash == view.dataset_hash
assert len(catalog.scenarios) == 2

# Rejeição de cenário contendo coluna protegida (alvo)
s_protected_target = FeatureScenario("s_tgt", "With Target", "Desc", "Just", ScenarioMode.FIXED, ("dap", "volume"))
try:
    validate_scenarios([s_protected_target], view)
    assert False, "Deveria rejeitar inclusão de target_col"
except ContractViolationError:
    pass

# Rejeição de cenário contendo coluna protegida (grupo)
s_protected_group = FeatureScenario("s_grp", "With Group", "Desc", "Just", ScenarioMode.FIXED, ("dap", "parcela"))
try:
    validate_scenarios([s_protected_group], view)
    assert False, "Deveria rejeitar inclusão de group_col"
except ContractViolationError:
    pass
```

- **Resultado Esperado:** Validação estrita assegurando que apenas atributos em `view.candidate_feature_cols` sejam usados, garantindo disjunção com `{target_col, group_col, observation_id_col, time_col} ∪ ignore_cols`, e vinculando o catálogo a `view.dataset_hash`.

---

### 2.4 Serialização Lossless e Reconstrução JSON (`to_dict` / `from_dict`)

```python
import json
from experimental_ml.features import ScenariosCatalog

# Serialização para dict primitivo
serialized = catalog.to_dict()
json_text = json.dumps(serialized, indent=2, ensure_ascii=False)

# Reconstrução a partir do JSON
reconstructed = ScenariosCatalog.from_dict(json.loads(json_text))
assert reconstructed.dataset_hash == catalog.dataset_hash
assert len(reconstructed.scenarios) == len(catalog.scenarios)
assert reconstructed.scenarios[0].scenario_id == catalog.scenarios[0].scenario_id
assert reconstructed.scenarios[0].selected_features == catalog.scenarios[0].selected_features
```

- **Resultado Esperado:** Serialização JSON RFC 8259 determinística com roundtrip 100% fiel e sem perda de metadados ou ordem.

---

### 2.5 Persistência Atômica e Portão de Etapa (`save_scenarios`, `verify_scenarios_gate`)

```python
from pathlib import Path
import tempfile
from experimental_ml.core.findings import ConfigurationError, DataIntegrityError
from experimental_ml.features import load_scenarios, save_scenarios
from experimental_ml.stages import SCENARIOS_CATALOG_REL_PATH, verify_scenarios_gate

with tempfile.TemporaryDirectory() as tmpdir:
    exp_dir = Path(tmpdir)
    scen_path = exp_dir / SCENARIOS_CATALOG_REL_PATH

    # 1. Escrita atômica e proteção contra sobreescrita acidental
    save_scenarios(catalog, scen_path, overwrite=False)
    assert scen_path.exists()

    try:
        save_scenarios(catalog, scen_path, overwrite=False)
        assert False, "Deveria proibir overwrite sem flag explícita"
    except ConfigurationError:
        pass

    # 2. Verificação do portão de etapa
    verified_catalog = verify_scenarios_gate(scen_path, view)
    assert verified_catalog.dataset_hash == view.dataset_hash

    # 3. Rejeição imediata em caso de adulteração de hash
    tampered_data = catalog.to_dict()
    tampered_data["dataset_hash"] = "divergent_hash_corrupted"
    scen_path.write_text(json.dumps(tampered_data), encoding="utf-8")

    try:
        verify_scenarios_gate(scen_path, view)
        assert False, "Portão deveria rejeitar hash adulterado"
    except DataIntegrityError:
        pass
```

- **Resultado Esperado:** `save_scenarios` grava com segurança transacional via `write_json_atomic`; o portão `verify_scenarios_gate` bloqueia artefatos inexistentes, hashes adulterados ou cenários com esquema divergente da visão saneada ativa.

---

## 3. Resumo dos Critérios de Aceitação Verificados

| Critério | Descrição | Status |
| :--- | :--- | :---: |
| **SCN-01** | `FeatureScenario` declarativo, imutável (`frozen=True, slots=True`), validação de campos e `MappingProxyType` | **APROVADO** |
| **SCN-02** | Cenários `FIXED` exigem sequência não-vazia de atributos únicos e proíbem campos de estratégia | **APROVADO** |
| **SCN-03** | Cenários `DYNAMIC` exigem `strategy_name` e proíbem terminantemente `selected_features` pré-partição (anti-leakage) | **APROVADO** |
| **SCN-04** | `validate_scenarios` valida unicidade de IDs, pertinência a `candidate_feature_cols` e vincula `dataset_hash` | **APROVADO** |
| **SCN-05** | Rejeição tipada de IDs duplicados, atributos desconhecidos ou inclusão de papéis protegidos (alvo, grupo, id, ignore) | **APROVADO** |
| **SCN-06** | Serialização determinística bidirecional (`to_dict` / `from_dict`) compatível com JSON RFC 8259 | **APROVADO** |
| **SCN-07** | Persistência atômica segura via `save_scenarios` com proteção de sobreescrita e restauração via `load_scenarios` | **APROVADO** |
| **SCN-08** | Portão de etapa `verify_scenarios_gate` com verificação de integridade física, hash matching e re-validação estrutural | **APROVADO** |
