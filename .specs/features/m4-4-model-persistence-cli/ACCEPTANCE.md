# Roteiro de Validação e Aceitação — Marco M4.4 (Persistência de Modelos, Portão de Validação e CLI)

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M4.4 (`m4-4-model-persistence-cli`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e integradores do subsistema de modelos e CLI do `experimental-ml-framework`.  
> **Premissa de Acesso:** Validação através **exclusivamente das interfaces públicas** exportadas em `experimental_ml.models`, `experimental_ml.stages` e comandos de terminal `expml models`.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e as exportações dos módulos estão íntegras:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de exportações dos símbolos públicos canônicos de modelos
python -c "
import experimental_ml.models as models
print('Models exportacoes publicas:', len(models.__all__))
for sym in ['ModelsCatalog', 'save_models_catalog', 'load_models_catalog', 'resolve_estimator_factory', 'models_catalog_to_dict', 'models_catalog_from_dict']:
    assert sym in models.__all__, f'Simbolo ausente: {sym}'
print('Simbolos canônicos de modelos validados com sucesso!')
"

# 3. Verificação do portão de modelos em stages
python -c "
import experimental_ml.stages as stages
assert hasattr(stages, 'verify_models_gate'), 'verify_models_gate ausente em stages'
assert stages.MODELS_CATALOG_REL_PATH == 'configuration/models.json'
print('Portão de estágio verify_models_gate validado com sucesso!')
"

# 4. Verificação de ajuda e subcomandos da CLI
python -m experimental_ml.cli.main models --help
```

- **Resultado Esperado:** Mensagens confirmando a disponibilidade dos símbolos e exibição da ajuda da CLI com os subcomandos `validate` e `verify`.
- **Critério de Falha:** `ModuleNotFoundError`, `ImportError`, ausência dos símbolos canônicos ou código de saída diferente de 0.

---

## 2. Roteiro de Testes de Aceitação por Capacidade

### 2.1 Modelo de Dados ModelsCatalog, Imutabilidade e Codecs (`MPC-01` / `US-M44-01`)

```python
from types import MappingProxyType
import pytest
from experimental_ml.models import (
    DummyBaselineModel,
    ModelCapabilities,
    ModelFamily,
    ModelsCatalog,
    ModelSpec,
    models_catalog_from_dict,
    models_catalog_to_dict,
)

# 1. Criação de especificação de modelo
spec = ModelSpec(
    model_id="baseline_mean",
    display_name="Baseline Regressor Mean",
    family=ModelFamily.BASELINE,
    estimator_factory=lambda seed: DummyBaselineModel(strategy="mean"),
    capabilities=ModelCapabilities(requires_fit=True, supports_uncertainty=True),
    description="Modelo baseline preditor da média",
    scientific_justification="Ponto de comparação fundamental",
    parameters={"strategy": "mean"},
)

# 2. Instanciação de ModelsCatalog imutável
catalog = ModelsCatalog(models=[spec], metadata={"author": "pesquisador"})
assert len(catalog.models) == 1
assert catalog.models[0].model_id == "baseline_mean"
assert isinstance(catalog.catalog_hash, str) and len(catalog.catalog_hash) == 64
assert isinstance(catalog.metadata, MappingProxyType)

# Imutabilidade estrita
with pytest.raises((AttributeError, TypeError)):
    catalog.catalog_hash = "hacked"  # type: ignore[misc]

# 3. Serialização para dicionário JSON
dict_repr = models_catalog_to_dict(catalog)
assert "models" in dict_repr and "catalog_hash" in dict_repr
assert dict_repr["models"][0]["family"] == "BASELINE"

# 4. Desserialização e preservação de integridade
reloaded = models_catalog_from_dict(dict_repr)
assert reloaded.catalog_hash == catalog.catalog_hash
assert reloaded.models[0].model_id == "baseline_mean"
```

- **Resultado Esperado:** Execução limpa; imutabilidade atestada; serialização e desserialização sem perda de atributos.
- **Critério de Falha:** Mutabilidade permitida, falta de slots, inconsistência de hash ou erro na reconstrução.

---

### 2.2 Resolução Declarativa de Fábricas de Estimadores (`MPC-02` / `US-M44-02`)

```python
import pytest
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.models import (
    AnalyticalBiometricModel,
    DummyBaselineModel,
    resolve_estimator_factory,
)

# 1. Resolução dos 4 baselines canônicos nativos
f_mean = resolve_estimator_factory("DUMMY_BASELINE_MEAN")
assert isinstance(f_mean(None), DummyBaselineModel)

f_med = resolve_estimator_factory("DUMMY_BASELINE_MEDIAN")
assert isinstance(f_med(None), DummyBaselineModel)

f_mf = resolve_estimator_factory("DUMMY_BASELINE_MOST_FREQUENT")
assert isinstance(f_mf(None), DummyBaselineModel)

f_bio = resolve_estimator_factory("ANALYTICAL_BIOMETRIC")
assert isinstance(f_bio(None), AnalyticalBiometricModel)

# 2. Resolução por formato module:qualname
f_ext = resolve_estimator_factory("experimental_ml.models.baselines:DummyBaselineModel")
assert f_ext is DummyBaselineModel

# 3. Rejeição de módulos inexistentes ou referências inválidas
with pytest.raises(ConfigurationError, match="Failed to import module"):
    resolve_estimator_factory("modulo_inexistente_xyz:Modelo")

with pytest.raises(ConfigurationError, match="Attribute 'AtributoInexistente' not found"):
    resolve_estimator_factory("experimental_ml.models.baselines:AtributoInexistente")
```

- **Resultado Esperado:** Baselines e caminhos importáveis resolvidos para instâncias funcionais; referências inválidas rejeitadas com `ConfigurationError`.
- **Critério de Falha:** Falha ao resolver baselines nativos ou supressão silenciosa de erros de importação.

---

### 2.3 Persistência Atômica e Carregamento de Catálogo (`MPC-03` / `US-M44-03`)

```python
from pathlib import Path
import tempfile
import pytest
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.models import (
    DummyBaselineModel,
    ModelCapabilities,
    ModelFamily,
    ModelsCatalog,
    ModelSpec,
    load_models_catalog,
    save_models_catalog,
)

with tempfile.TemporaryDirectory() as tmpdir:
    dest = Path(tmpdir) / "models.json"
    spec = ModelSpec(
        model_id="baseline_median",
        display_name="Baseline Median",
        family=ModelFamily.BASELINE,
        estimator_factory=lambda seed: DummyBaselineModel(strategy="median"),
        capabilities=ModelCapabilities(),
        description="Preditores da mediana",
        scientific_justification="Baseline robusto",
    )
    catalog = ModelsCatalog(models=[spec])

    # 1. Escrita atômica bem-sucedida
    saved_path = save_models_catalog(catalog, dest)
    assert saved_path == dest.resolve()
    assert dest.exists()

    # 2. Proteção contra sobrescrita acidental (STORE-03)
    with pytest.raises(ConfigurationError, match="already exists"):
        save_models_catalog(catalog, dest, overwrite=False)

    # 3. Sobrescrita explícita
    save_models_catalog(catalog, dest, overwrite=True)

    # 4. Leitura e integridade
    loaded = load_models_catalog(dest)
    assert loaded.catalog_hash == catalog.catalog_hash
    assert loaded.models[0].model_id == "baseline_median"
```

- **Resultado Esperado:** Arquivo gravado atomicamente; bloqueio estrito quando `overwrite=False`; catálogo recuperado com hash idêntico.
- **Critério de Falha:** Sobrescrita não autorizada ou corrupção do arquivo durante escrita.

---

### 2.4 Portão de Estágio de Modelos (`MPC-04` / `US-M44-04`)

```python
from pathlib import Path
import tempfile
import pytest
from experimental_ml.core.findings import ContractViolationError, DataIntegrityError
from experimental_ml.core.storage import write_json_atomic
from experimental_ml.models import (
    DummyBaselineModel,
    ModelCapabilities,
    ModelFamily,
    ModelsCatalog,
    ModelSpec,
    save_models_catalog,
)
from experimental_ml.stages import (
    DATASET_DESCRIPTOR_REL_PATH,
    DATASET_PROFILE_REL_PATH,
    MODELS_CATALOG_REL_PATH,
    PREPARATION_PLAN_REL_PATH,
    verify_models_gate,
)

with tempfile.TemporaryDirectory() as tmpdir:
    exp_dir = Path(tmpdir)

    # Configuração dos artefatos da Etapa 1
    write_json_atomic(exp_dir / DATASET_DESCRIPTOR_REL_PATH, {
        "dataset_hash": "hash_123", "n_observations": 10, "n_columns": 2,
        "column_names": ["x", "y"], "column_types": {"x": "float64", "y": "float64"}
    })
    write_json_atomic(exp_dir / DATASET_PROFILE_REL_PATH, {
        "source_dataset_hash": "hash_123", "n_rows": 10, "n_cols": 2,
        "memory_bytes": 160, "columns": {}, "findings": []
    })
    write_json_atomic(exp_dir / PREPARATION_PLAN_REL_PATH, {
        "status": "READY", "source_dataset_hash": "hash_123", "rules": []
    })

    # 1. Falha quando configuration/models.json está ausente
    with pytest.raises(DataIntegrityError, match="Models catalog missing"):
        verify_models_gate(exp_dir)

    # 2. Sucesso com modelos persistidos
    spec = ModelSpec(
        model_id="baseline_mean",
        display_name="Baseline Mean",
        family=ModelFamily.BASELINE,
        estimator_factory=lambda seed: DummyBaselineModel(),
        capabilities=ModelCapabilities(),
        description="Modelo baseline",
        scientific_justification="Ponto zero",
    )
    save_models_catalog(ModelsCatalog([spec]), exp_dir / MODELS_CATALOG_REL_PATH)
    verified = verify_models_gate(exp_dir)
    assert len(verified.models) == 1
    assert verified.models[0].model_id == "baseline_mean"
```

- **Resultado Esperado:** Verificação da pré-condição da Etapa 1 e validação integral do catálogo de modelos com retorno do `ModelsCatalog`.
- **Critério de Falha:** Avanço de estágio com artefatos faltando ou pré-condição não verificada.

---

### 2.5 Subcomando CLI `expml models validate` (`MPC-05` / `US-M44-05`)

```bash
# Execução direta via CLI
python -m experimental_ml.cli.main models validate \
  --experiment-dir <diretório_do_experimento> \
  --models <caminho_do_arquivo_models_input.json>
```

- **Resultado Esperado:**
  - Código de saída `0`
  - Saída no terminal:
    ```text
    Models catalog validated and saved successfully:
      - Models count: <N>
      - Catalog hash: <hash_sha256>
      - Destination: configuration/models.json
    ```
  - Execução subsequente sem `--force` retorna código `2` com mensagem de erro de sobreposição.
  - Execução subsequente com `--force` retorna código `0`.
- **Critério de Falha:** Código de saída diferente dos especificados ou sobrescrita silenciosa sem `--force`.

---

### 2.6 Subcomando CLI `expml models verify` (`MPC-06` / `US-M44-06`)

```bash
# Execução direta via CLI
python -m experimental_ml.cli.main models verify \
  --experiment-dir <diretório_do_experimento>
```

- **Resultado Esperado:**
  - Código de saída `0`
  - Saída no terminal:
    ```text
    Models gate verified successfully:
      - Models count: <N>
      - Catalog hash: <hash_sha256>
      - Catalog file: configuration/models.json
    ```
  - Quando a Etapa 1 ou o arquivo `configuration/models.json` estiverem ausentes, retorna código `2`.
- **Critério de Falha:** Código de saída diferente de 0 em experimentos válidos ou ausência de código 2 em experimentos corrompidos/incompletos.

---

### 2.7 Pureza de Importação e Suíte Ponta a Ponta (`MPC-07` / `US-M44-07`)

```python
import ast
from pathlib import Path
import subprocess
import sys

# 1. Inspeção AST de cmd_models.py (CLI-10)
cmd_models_path = Path("src/experimental_ml/cli/cmd_models.py")
tree = ast.parse(cmd_models_path.read_text(encoding="utf-8"))
forbidden = {"numpy", "scipy", "sklearn", "hashlib", "pandas"}

for node in tree.body:
    if isinstance(node, ast.Import):
        for alias in node.names:
            root = alias.name.split(".")[0]
            assert root not in forbidden, f"Importação de módulo pesado no topo: {root}"
    elif isinstance(node, ast.ImportFrom) and node.module:
        root = node.module.split(".")[0]
        assert root not in forbidden, f"Importação de módulo pesado no topo: {root}"

# 2. Verificação de pureza em processo isolado
code = (
    "import sys\n"
    "import experimental_ml.cli.cmd_models\n"
    "forbidden = {'numpy', 'scipy', 'sklearn', 'hashlib'}\n"
    "loaded = forbidden.intersection(sys.modules.keys())\n"
    "assert not loaded, f'Módulos proibidos carregados: {loaded}'\n"
    "print('CLI_PURITY_OK')\n"
)
res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
assert res.returncode == 0
assert "CLI_PURITY_OK" in res.stdout
```

- **Resultado Esperado:** Conformidade absoluta com `CLI-10`: zero importações pesadas no escopo do módulo da CLI.
- **Critério de Falha:** Presença de imports globais de bibliotecas numéricas em `cmd_models.py`.

---

## 3. Cenário Integrado de Ponta a Ponta (End-to-End Walkthrough)

O cenário abaixo consolida a experiência completa de um pesquisador configurando os modelos da Etapa 3 e validando os portões antes da execução da matriz experimental:

```bash
#!/usr/bin/env bash
set -e

EXP_DIR=$(mktemp -d /tmp/expml_m44_e2e_XXXXXX)
trap "rm -rf ${EXP_DIR}" EXIT

echo "=== 1. Inicializando Experimento e Etapa 1 ==="
mkdir -p "${EXP_DIR}/data" "${EXP_DIR}/configuration"

cat <<EOF > "${EXP_DIR}/data/dataset_descriptor.json"
{
  "dataset_hash": "hash_e2e_2026",
  "n_observations": 100,
  "n_columns": 3,
  "column_names": ["feat1", "feat2", "target"],
  "column_types": {"feat1": "float64", "feat2": "float64", "target": "float64"}
}
EOF

cat <<EOF > "${EXP_DIR}/data/dataset_profile.json"
{
  "source_dataset_hash": "hash_e2e_2026",
  "n_rows": 100,
  "n_cols": 3,
  "memory_bytes": 2400,
  "columns": {},
  "findings": []
}
EOF

cat <<EOF > "${EXP_DIR}/configuration/preparation_plan.json"
{
  "status": "READY",
  "source_dataset_hash": "hash_e2e_2026",
  "rules": []
}
EOF

echo "=== 2. Criando Definição de Modelos para o Experimento ==="
INPUT_MODELS="${EXP_DIR}/input_models.json"
cat <<EOF > "${INPUT_MODELS}"
[
  {
    "model_id": "dummy_mean",
    "display_name": "Dummy Regressor (Mean)",
    "family": "BASELINE",
    "estimator_factory": "DUMMY_BASELINE_MEAN",
    "capabilities": {
      "supports_predict": true,
      "requires_fit": true,
      "supports_uncertainty": true
    },
    "description": "Baseline que prediz a media de treino",
    "scientific_justification": "Linha de base essencial para regressao"
  },
  {
    "model_id": "analytical_biometric",
    "display_name": "Analytical Biometric Formulation",
    "family": "ANALYTICAL_EQUATION",
    "estimator_factory": "ANALYTICAL_BIOMETRIC",
    "capabilities": {
      "supports_predict": true,
      "requires_fit": false
    },
    "description": "Equacao biometrica deterministica",
    "scientific_justification": "Formulacao fechada teorica"
  }
]
EOF

echo "=== 3. Executando expml models validate ==="
python -m experimental_ml.cli.main models validate \
  --experiment-dir "${EXP_DIR}" \
  --models "${INPUT_MODELS}"

echo "=== 4. Verificando Portão de Modelos com expml models verify ==="
python -m experimental_ml.cli.main models verify \
  --experiment-dir "${EXP_DIR}"

echo "=== 5. Testando Salvaguarda de Sobrescrita ==="
if python -m experimental_ml.cli.main models validate \
  --experiment-dir "${EXP_DIR}" \
  --models "${INPUT_MODELS}" 2>/dev/null; then
    echo "FALHA: Deveria ter recusado a sobrescrita sem --force!"
    exit 1
else
    echo "Protecao de sobrescrita confirmada com sucesso (codigo 2)."
fi

echo "=== 6. Testando Sobrescrita com Flag --force ==="
python -m experimental_ml.cli.main models validate \
  --experiment-dir "${EXP_DIR}" \
  --models "${INPUT_MODELS}" \
  --force

echo "=== CENARIO E2E CONCLUIDO COM EXITO ==="
```

- **Resultado Esperado:** Todas as etapas do script executadas com sucesso, garantindo validação, persistência e integridade do portão de modelos.
- **Critério de Falha:** Qualquer etapa retornando código de erro inesperado ou quebrando proteções de integridade.

---

## 4. Diagnóstico e Tratamento de Falhas

| Sintoma Observado | Causa Provável | Ação de Resolução |
| :--- | :--- | :--- |
| `ConfigurationError: Models catalog already exists` | Tentativa de validação sobre arquivo existente sem `--force` | Adicionar `--force` ao comando `expml models validate` caso a sobrescrita seja intencional. |
| `ConfigurationError: Cannot resolve estimator factory` | Referência de fábrica de modelo inválida ou formato incorreto | Usar baselines nativos canônicos (`DUMMY_BASELINE_MEAN`, etc.) ou formato padrão `module:qualname`. |
| `ContractViolationError: Upstream preparation gate is not READY` | A Etapa 1 não foi concluída com status READY | Executar a preparação e sanitização dos dados antes de registrar modelos. |
| `DataIntegrityError: Models catalog missing at ...` | O arquivo `configuration/models.json` não foi criado | Executar `expml models validate` antes de chamar `verify`. |
| Código de saída `2` na CLI sem detalhes no stdout | Erro de domínio tratado de acordo com o padrão do framework | Inspecionar a saída de erro (`stderr`) para visualizar a mensagem detalhada da exceção. |

---

## 5. Matriz de Classificação dos Testes

| Identificador do Teste | Tipo | Requisito Rastreado | Arquivo de Teste |
| :--- | :---: | :---: | :--- |
| `test_m44_01_01_models_catalog_dataclass` | Unidade | `MPC-01` (AC-M44-01-01) | `tests/unit/models/test_models_codecs.py` |
| `test_m44_01_02_models_catalog_to_dict` | Unidade | `MPC-01` (AC-M44-01-02) | `tests/unit/models/test_models_codecs.py` |
| `test_m44_01_03_models_catalog_from_dict` | Unidade | `MPC-01` (AC-M44-01-03) | `tests/unit/models/test_models_codecs.py` |
| `test_m44_02_01_resolve_builtin_baselines` | Unidade | `MPC-02` (AC-M44-02-01) | `tests/unit/models/test_models_resolution.py` |
| `test_m44_02_02_resolve_dotted_import_path` | Unidade | `MPC-02` (AC-M44-02-02) | `tests/unit/models/test_models_resolution.py` |
| `test_m44_02_03_resolve_invalid_reference_raises` | Unidade | `MPC-02` (AC-M44-02-03) | `tests/unit/models/test_models_resolution.py` |
| `test_m44_03_01_save_and_load_roundtrip` | Unidade | `MPC-03` (AC-M44-03-01, 03) | `tests/unit/models/test_models_storage.py` |
| `test_m44_03_02_save_overwrite_guard` | Unidade | `MPC-03` (AC-M44-03-02) | `tests/unit/models/test_models_storage.py` |
| `test_m44_03_03_load_missing_or_corrupt` | Unidade | `MPC-03` (AC-M44-03-03) | `tests/unit/models/test_models_storage.py` |
| `test_m44_04_01_verify_models_gate_valid` | Unidade | `MPC-04` (AC-M44-04-01) | `tests/unit/stages/test_models_stage_gate.py` |
| `test_m44_04_02_verify_models_gate_missing_or_empty` | Unidade | `MPC-04` (AC-M44-04-02) | `tests/unit/stages/test_models_stage_gate.py` |
| `test_m44_04_03_verify_models_gate_unmet_precondition` | Unidade | `MPC-04` (AC-M44-04-03) | `tests/unit/stages/test_models_stage_gate.py` |
| `test_m44_05_01_models_validate_success` | Unidade | `MPC-05` (AC-M44-05-01) | `tests/unit/cli/test_cli_models_validate.py` |
| `test_m44_05_02_models_validate_overwrite_error` | Unidade | `MPC-05` (AC-M44-05-02) | `tests/unit/cli/test_cli_models_validate.py` |
| `test_m44_05_03_models_validate_invalid_input` | Unidade | `MPC-05` (AC-M44-05-03) | `tests/unit/cli/test_cli_models_validate.py` |
| `test_m44_06_01_models_verify_success` | Unidade | `MPC-06` (AC-M44-06-01) | `tests/unit/cli/test_cli_models_verify.py` |
| `test_m44_06_02_models_verify_gate_failure` | Unidade | `MPC-06` (AC-M44-06-02) | `tests/unit/cli/test_cli_models_verify.py` |
| `test_m44_06_03_models_verify_missing_dir` | Unidade | `MPC-06` (AC-M44-06-02) | `tests/unit/cli/test_cli_models_verify.py` |
| `test_m44_07_01_cli_parser_registration` | Integração | `MPC-07` (AC-M44-07-01) | `tests/integration/models/test_models_cli_integration.py` |
| `test_m44_07_02_cli_import_purity` | Integração | `MPC-07` (AC-M44-07-01) | `tests/integration/models/test_models_cli_integration.py` |
| `test_m44_07_03_e2e_cli_subprocess` | Integração | `MPC-07` (AC-M44-07-02) | `tests/integration/models/test_models_cli_integration.py` |
