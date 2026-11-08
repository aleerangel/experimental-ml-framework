# Roteiro de Validação e Aceitação — Marco M2.5 (CLI End-to-End Acceptance)

> **Roteiro Operacional de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M2.5 (`m2-5-cli-end-to-end`)  
> **Público-Alvo:** Desenvolvedores, pesquisadores e operadores de pipelines em linha de comando.  
> **Premissa de Acesso:** Execução via binário instalado `expml` no terminal e invocação padronizada dos subcomandos `data profile`, `data sanitize`, `partition build`, e `partition verify`.

---

## 1. Preparação do Ambiente e Pré-requisitos

Certifique-se de que o ambiente virtual está ativo e o ponto de entrada `expml` está registrado no PATH:

```bash
# 1. Ativação do ambiente virtual
source .venv/bin/activate

# 2. Verificação de versão e ponto de entrada da CLI
expml --version
```

- **Resultado Esperado:** Impressão da versão (ex: `expml 0.1.0.dev0`) e código de saída 0.
- **Critério de Falha:** Erro de comando não encontrado (`command not found`) ou retorno diferente de 0.

---

## 2. Roteiro de Testes Manuais de Aceitação por Subcomando

### 2.1 Perfilamento Inicial de Dados (`CLI-01`)

```bash
# Criação de diretório temporário para ensaio
mkdir -p /tmp/expml_demo/experiment

cat << 'EOF' > /tmp/expml_demo/raw.csv
id,feat_num,feat_cat,target
1,10.5,A,1
2,20.0,B,0
3,,A,1
4,40.1,C,0
5,50.3,B,1
EOF

cat << 'EOF' > /tmp/expml_demo/schema.json
{
  "target_col": "target",
  "task_type": "BINARY_CLASSIFICATION",
  "column_semantic_types": {
    "feat_num": "NUMERIC_CONTINUOUS",
    "feat_cat": "CATEGORICAL"
  }
}
EOF

# Execução do perfilamento
expml data profile \
  --data /tmp/expml_demo/raw.csv \
  --schema /tmp/expml_demo/schema.json \
  --output-dir /tmp/expml_demo/experiment
```

- **Resultado Esperado:** Código de saída `0`, resumo exibindo `Dataset profiled: 5 rows x 4 columns`, lista legível de achados diagnósticos (`E1_FEATURE_MISSING`, `E1_CATEGORICAL_UNENCODED`), geração de `data/dataset_descriptor.json` e `data/dataset_profile.json`. Nenhuma string de hash hexadecimal de 64 caracteres visível.

### 2.2 Saneamento com Bloqueio de Plano Incompleto (`CLI-03`)

```bash
# Regra parcial cobrindo apenas uma das pendências
cat << 'EOF' > /tmp/expml_demo/rules_incomplete.json
[
  {"finding_code": "E1_CATEGORICAL_UNENCODED", "column": "feat_cat", "kind": "ACCEPT_AS_IS"}
]
EOF

expml data sanitize \
  --experiment-dir /tmp/expml_demo/experiment \
  --rules /tmp/expml_demo/rules_incomplete.json
```

- **Resultado Esperado:** Código de saída `2`, impressão em stderr detalhando o achado pendente `E1_FEATURE_MISSING (column 'feat_num')`, sem traceback Python, e sem criação de `configuration/preparation_plan.json`.

### 2.3 Saneamento com Plano Completo (`CLI-02`)

```bash
# Regras completas
cat << 'EOF' > /tmp/expml_demo/rules_complete.json
[
  {"finding_code": "E1_FEATURE_MISSING", "column": "feat_num", "kind": "DROP_ROWS"},
  {"finding_code": "E1_CATEGORICAL_UNENCODED", "column": "feat_cat", "kind": "ACCEPT_AS_IS"}
]
EOF

expml data sanitize \
  --experiment-dir /tmp/expml_demo/experiment \
  --rules /tmp/expml_demo/rules_complete.json
```

- **Resultado Esperado:** Código de saída `0`, criação de `configuration/preparation_plan.json` e `data/sanitized_view.json`, resumo de observações descartadas e sobreviventes.

### 2.4 Construção de Partições com `--seed` e Splits Comprimidos (`CLI-04`)

```bash
cat << 'EOF' > /tmp/expml_demo/part_config.json
{
  "strategy": "KFOLD",
  "regime": "CV_ONLY",
  "n_splits": 2,
  "master_seed": 42
}
EOF

expml partition build \
  --experiment-dir /tmp/expml_demo/experiment \
  --config /tmp/expml_demo/part_config.json \
  --seed 1234
```

- **Resultado Esperado:** Código de saída `0`, criação de `partitions/partition_plan.json`, `partitions/splits.csv.gz` e `partitions/splits.schema.json`. Resumo com regime, estratégia e tamanhos por fold.

### 2.5 Verificação de Partições e Integridade (`CLI-05`)

```bash
expml partition verify --experiment-dir /tmp/expml_demo/experiment
```

- **Resultado Esperado:** Código de saída `0`, mensagem `Partition plan verification PASSED. All stage gates and mathematical invariants satisfied.`.

---

## 3. Limpeza

```bash
rm -rf /tmp/expml_demo
```
