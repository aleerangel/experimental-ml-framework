# Roteiro de Validação e Aceitação — Marco M3.4 (CLI de Features e Homologação Ponta a Ponta)

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M3.4 (`m3-4-cli-end-to-end`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e operadores de pipelines em linha de comando.  
> **Premissa de Acesso:** Execução via binário instalado `expml` no terminal e invocação padronizada dos subcomandos `features explore`, `features scenarios`, e `features verify`.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e o ponto de entrada `expml` está registrado no PATH:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de versão e subcomandos da CLI
expml --version
expml features --help
```

- **Resultado Esperado:** 
  - Impressão da versão (ex: `expml 0.1.0.dev0`) e código de saída 0.
  - Ajuda do grupo `features` exibindo descrição dos subcomandos `explore`, `scenarios` e `verify` com código de saída 0.
- **Critério de Falha:** Erro de comando não encontrado (`command not found`) ou retorno diferente de 0.

---

## 2. Roteiro de Testes Manuais de Aceitação por Subcomando

### 2.1 Preparação do Experimento Base (Etapa 1 Saneada)

Para testar a Etapa 2 de features, criamos uma visão de dados devidamente saneada com a Etapa 1:

```bash
mkdir -p /tmp/expml_m34_demo/experiment
mkdir -p /tmp/expml_m34_demo/inputs

# Criação da base de dados tabular
cat << 'EOF' > /tmp/expml_m34_demo/inputs/dataset.csv
id,biomass,canopy_height,soil_moisture,zone,target
P01,45.2,18.5,0.32,North,120.5
P02,40.1,17.0,0.28,North,112.0
P03,58.0,22.1,0.45,South,145.2
P04,52.4,20.8,0.41,South,138.0
P05,35.0,15.2,0.22,North,98.4
P06,62.1,24.0,0.48,South,155.0
P07,38.5,16.4,0.25,North,105.1
P08,49.0,19.8,0.39,South,130.8
EOF

# Criação do esquema canônico
cat << 'EOF' > /tmp/expml_m34_demo/inputs/schema.json
{
  "target_col": "target",
  "observation_id_col": "id",
  "task_type": "REGRESSION",
  "column_semantic_types": {
    "biomass": "NUMERIC_CONTINUOUS",
    "canopy_height": "NUMERIC_CONTINUOUS",
    "soil_moisture": "NUMERIC_CONTINUOUS",
    "zone": "CATEGORICAL"
  }
}
EOF

# Passo 1: Perfilamento de dados
expml data profile \
  --data /tmp/expml_m34_demo/inputs/dataset.csv \
  --schema /tmp/expml_m34_demo/inputs/schema.json \
  --output-dir /tmp/expml_m34_demo/experiment

# Passo 2: Saneamento de dados
cat << 'EOF' > /tmp/expml_m34_demo/inputs/rules.json
[
  {
    "finding_code": "E1_CATEGORICAL_UNENCODED",
    "column": "zone",
    "kind": "DEFER_INTRA_FOLD",
    "parameters": {"encoding_strategy": "ONE_HOT"}
  }
]
EOF

expml data sanitize \
  --experiment-dir /tmp/expml_m34_demo/experiment \
  --rules /tmp/expml_m34_demo/inputs/rules.json
```

- **Resultado Esperado:** Código de saída `0`, diretório `/tmp/expml_m34_demo/experiment` contendo `data/dataset_descriptor.json`, `data/dataset_profile.json`, `configuration/preparation_plan.json` e `data/sanitized_view.json`.

---

### 2.2 Análise Exploratória de Features (`FEAT-02`)

Execução da exploração estatística de relações e redundâncias sobre a base saneada:

```bash
expml features explore --experiment-dir /tmp/expml_m34_demo/experiment
```

- **Resultado Esperado:**
  - Código de saída `0`.
  - Resumo informativo no terminal:
    ```text
    Exploratory feature analysis completed successfully:
      - Target column: target
      - Features analyzed: 4
      - Redundant pairs flagged: 0
      - Report: reports/exploratory_features.json
    ```
  - Criação atômica do artefato `reports/exploratory_features.json`.
  - O conteúdo de `reports/exploratory_features.json` contém campo `"scope": "EXPLORATORY_FULL_DATA"`, matriz de redundâncias e associações com a variável alvo.

---

### 2.3 Proteção contra Sobrescrita Acidental (`FEAT-03`)

Verificação de proteção de artefatos existentes:

```bash
# Tentativa de re-execução sem --force (deve falhar)
expml features explore --experiment-dir /tmp/expml_m34_demo/experiment
```

- **Resultado Esperado:**
  - Código de saída `2`.
  - Mensagem explicativa em stderr:
    `Error: Exploratory features report already exists at '.../reports/exploratory_features.json'. Use --force to overwrite.`
  - Ausência de traceback Python.

```bash
# Re-execução com --force (deve ter sucesso)
expml features explore --experiment-dir /tmp/expml_m34_demo/experiment --force
```

- **Resultado Esperado:** Código de saída `0`, relatório sobrescrito com sucesso.

---

### 2.4 Validação e Persistência do Catálogo de Cenários (`FEAT-04`)

Definição e homologação de cenários fixos e dinâmicos:

```bash
cat << 'EOF' > /tmp/expml_m34_demo/inputs/scenarios.json
[
  {
    "scenario_id": "all_features",
    "name": "Todos os Preditores",
    "description": "Cenário completo com variáveis biométricas",
    "scientific_justification": "Linha de base dendrométrica",
    "mode": "FIXED",
    "selected_features": ["biomass", "canopy_height", "soil_moisture"]
  },
  {
    "scenario_id": "high_variance",
    "name": "Seleção por Variância",
    "description": "Filtra preditores com variância superior a 0.05",
    "scientific_justification": "Eliminação de variáveis quase-constantes",
    "mode": "DYNAMIC",
    "strategy_name": "VARIANCE_THRESHOLD",
    "strategy_params": {"threshold": 0.05}
  }
]
EOF

expml features scenarios \
  --experiment-dir /tmp/expml_m34_demo/experiment \
  --scenarios /tmp/expml_m34_demo/inputs/scenarios.json
```

- **Resultado Esperado:**
  - Código de saída `0`.
  - Resumo de sucesso no terminal:
    ```text
    Feature scenarios validated and saved successfully:
      - Scenarios validated: 2
      - Catalog: configuration/scenarios.json
    ```
  - Criação do catálogo em `configuration/scenarios.json` devidamente carimbado com o `dataset_hash` da visão saneada.

---

### 2.5 Rejeição de Cenários Inválidos e Vazamentos (`FEAT-05`)

Validação das regras de governança e integridade preditiva:

#### Caso A: Coluna Inexistente
```bash
cat << 'EOF' > /tmp/expml_m34_demo/inputs/scenarios_invalid.json
[
  {
    "scenario_id": "ghost_feature",
    "name": "Feature Inexistente",
    "description": "Teste de rejeição",
    "scientific_justification": "Validação de erro",
    "mode": "FIXED",
    "selected_features": ["biomass", "coluna_fantasma"]
  }
]
EOF

expml features scenarios \
  --experiment-dir /tmp/expml_m34_demo/experiment \
  --scenarios /tmp/expml_m34_demo/inputs/scenarios_invalid.json
```
- **Resultado Esperado:** Código de saída `2`, stderr exibindo mensagem explicativa mencionando `'coluna_fantasma'`, sem traceback.

#### Caso B: Vazamento de Coluna Alvo (`Data Leakage`)
```bash
cat << 'EOF' > /tmp/expml_m34_demo/inputs/scenarios_leakage.json
[
  {
    "scenario_id": "target_leak",
    "name": "Vazamento do Alvo",
    "description": "Inclui coluna target",
    "scientific_justification": "Validação de vazamento",
    "mode": "FIXED",
    "selected_features": ["biomass", "target"]
  }
]
EOF

expml features scenarios \
  --experiment-dir /tmp/expml_m34_demo/experiment \
  --scenarios /tmp/expml_m34_demo/inputs/scenarios_leakage.json
```
- **Resultado Esperado:** Código de saída `2`, stderr reportando:
  `Error: Fixed scenario 'target_leak' includes protected column 'target' (intersecting with target, group, observation_id, time, or ignore columns).`

---

### 2.6 Verificação Formal do Portão de Etapa (`FEAT-06`)

Auditoria de portão de validação de cenários (`verify_scenarios_gate`):

```bash
expml features verify --experiment-dir /tmp/expml_m34_demo/experiment
```

- **Resultado Esperado:**
  - Código de saída `0`.
  - Saída no terminal:
    ```text
    Feature scenarios gate verified successfully:
      - Scenarios count: 2
      - Catalog: configuration/scenarios.json
    ```

```bash
# Teste de falha de portão em diretório inexistente ou vazio
mkdir -p /tmp/expml_m34_demo/empty_exp
expml features verify --experiment-dir /tmp/expml_m34_demo/empty_exp
```
- **Resultado Esperado:** Código de saída `2` e erro claro em stderr sem traceback.

---

### 2.7 Pureza Arquitetural da CLI (`CLI-10` / `FEAT-07`)

Garantia de que invocações rápidas de terminal não carregam `numpy` ou `hashlib` na memória:

```bash
python -c "
import sys
from experimental_ml.cli.main import main
main(['--help'])
assert 'numpy' not in sys.modules, 'FALHA: numpy importado na raiz da CLI'
assert 'hashlib' not in sys.modules, 'FALHA: hashlib importado na raiz da CLI'
print('Pureza da CLI homologada com sucesso: sys.modules limpo!')
"
```

- **Resultado Esperado:** Código de saída `0` e mensagem confirmando ausência de `numpy` e `hashlib`.

---

### 2.8 Homologação Ponta a Ponta Integrada Multi-Etapa (`FEAT-08`)

Garantia de continuidade do pipeline: partição subsequente à validação dos cenários:

```bash
cat << 'EOF' > /tmp/expml_m34_demo/inputs/partition_config.json
{
  "strategy": "KFOLD",
  "n_splits": 2,
  "validation_mode": "CV_ONLY"
}
EOF

expml partition build \
  --experiment-dir /tmp/expml_m34_demo/experiment \
  --config /tmp/expml_m34_demo/inputs/partition_config.json \
  --seed 42

expml partition verify \
  --experiment-dir /tmp/expml_m34_demo/experiment
```

- **Resultado Esperado:**
  - Todos os comandos terminam com código `0`.
  - Invariantes de partição verificados com sucesso.
  - Higiene de terminal: nenhum digest hexadecimal bruto SHA-256 de 64 caracteres impresso na saída do usuário (`CLI-11`).

---

## 3. Limpeza

```bash
rm -rf /tmp/expml_m34_demo
```
