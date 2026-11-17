# Começando do Zero (Sem Experiência com Frameworks, JSON ou Terminal)

Se você entende o básico de Aprendizado de Máquina (tem um arquivo `.csv` com colunas de entrada e uma coluna alvo para prever), você **não precisa saber** o que é JSON, linha de comando complexa ou arquitetura interna para usar o `experimental-ml`.

---

## Caminho A — Em Python ou Google Colab (10 Linhas, Zero JSON)

1. **Prepare seu `.csv`**: uma tabela normal com cabeçalho na primeira linha (cada linha é uma amostra; uma coluna é o alvo que você quer prever, ex.: `"volume"` ou `"diagnostico"`).
2. **Passe seus modelos em um dicionário Python** (`{"Nome": seu_modelo}`): qualquer objeto com `.fit(X, y)` e `.predict(X)` funciona diretamente.
3. **Execute `run_experiment` e leia o resumo em português**:

```python
from experimental_ml import run_experiment
from experimental_ml.models import DummyBaselineModel

# Exemplo pronto para copiar e rodar (ou passe o caminho de um arquivo .csv em `data=...`)
dados = {
    "dap": [12.0, 14.5, 16.0, 18.2, 20.1, 22.4, 24.0, 26.5, 28.0, 30.2],
    "altura": [10.1, 11.4, 12.0, 13.5, 14.2, 15.8, 16.4, 17.9, 18.5, 19.8],
    "volume": [0.12, 0.18, 0.23, 0.31, 0.39, 0.48, 0.56, 0.68, 0.77, 0.91],
}

resultado = run_experiment(
    data=dados,                     # ou "meus_dados.csv"
    target="volume",                # nome da coluna que você quer prever
    task="regression",              # "regression", "binary_classification" ou "multiclass_classification"
    models={
        "Baseline Média": DummyBaselineModel(strategy="mean"),
        "Baseline Mediana": DummyBaselineModel(strategy="median"),
    },
    output_dir="meu_experimento",   # pasta onde relatórios e gráficos serão salvos
    cv_folds=5,                     # validação cruzada em 5 dobras
    metrics=["rmse", "r2"],
)

print(resultado.summary())
```

> [!TIP]
> O próprio framework cuida automaticamente de isolar treino e validação em cada dobra, impedir vazamento de dados (*data leakage*), calcular estatísticas e salvar `report.md` e `report.html` dentro de `meu_experimento/reports/`.

---

## Caminho B — Pelo Terminal em 2 Comandos (Sem Escrever Python)

Se preferir usar o terminal sem editar JSON do zero, use `expml init` para gerar uma pasta pronta com dados e arquivos de exemplo, e depois `expml quickrun` para rodar tudo de uma vez:

```bash
expml init --output-dir meu_experimento --task regression
expml quickrun --experiment-dir meu_experimento
```

Depois de testar com os dados de exemplo, basta substituir `dados_exemplo.csv` pelo seu arquivo e ajustar o nome da coluna alvo em `schema.json`.
