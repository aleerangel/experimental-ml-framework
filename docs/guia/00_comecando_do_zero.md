# Começando do Zero *(Nível 0 — Básico)*

Este guia foi escrito para quem conhece apenas o básico de Aprendizado de Máquina (sabe o que é treino, teste, regressão ou classificação) e **nunca usou frameworks, arquivos JSON ou linha de comando**.

---

## O Mínimo Obrigatório (Nível Básico)

Para rodar seu primeiro experimento científico completo, você precisa apenas de **4 informações**:
1. **`data`**: seus dados em tabela (um arquivo `.csv` ou dicionário Python);
2. **`target`**: o nome da coluna que você quer prever;
3. **`task`**: o tipo de problema (`"regression"`, `"binary_classification"` ou `"multiclass_classification"`);
4. **`models`**: seus modelos em um dicionário Python (`{"Nome do Modelo": modelo}`).

Todo o resto (separação das dobras, prevenção de vazamento de dados, estatística e relatórios) é feito automaticamente pelo framework.

---

## Passo 1 — Preparando o Ambiente

### Opção A: No Google Colab *(sem instalar nada no seu computador)*
Na primeira célula do seu notebook no Colab, execute:

```bash
pip install -q git+https://github.com/aleerangel/experimental-ml-framework.git
```

### Opção B: No seu computador *(Python `>= 3.10`)*
Dentro da pasta do repositório, crie e ative um ambiente virtual antes de instalar:

```bash
# Linux ou macOS
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

```bash
# Windows (PowerShell ou CMD)
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

### Opção C: Usando em outro projeto no seu computador
Se você já tem um projeto em outra pasta e quer importar o `experimental-ml` lá dentro, ative o `.venv` do seu outro projeto e instale apontando para a pasta onde este repositório foi clonado (ou direto do Git):

```bash
# Dentro da pasta do seu outro projeto (com o .venv dele ativado)
pip install -e /caminho/para/experimental-ml-framework

# Ou instalando direto do GitHub
pip install git+https://github.com/aleerangel/experimental-ml-framework.git
```

Para confirmar que funcionou, rode `expml --version`.

---

## Passo 2 — Como Deve Ser o Seu Arquivo `.csv`

Seu arquivo `.csv` precisa ter o nome das colunas na primeira linha e uma coluna para a variável-alvo:

```csv
dap,altura,idade,volume
12.0,10.1,4,0.12
14.5,11.4,5,0.18
16.0,12.0,5,0.23
```

> [!WARNING]
> **3 erros comuns de `.csv` no Brasil (Excel em Português):**
> 1. **Separador `;` e vírgula decimal `,`:** O padrão internacional usa **vírgula `,`** entre colunas e **ponto `.`** para decimais (`14.5`). Se o seu arquivo usar `;` e vírgula decimal (ou *encoding* `latin-1`/`cp1252`), você pode passar `delimiter=";"`, `decimal=","` e `encoding="latin-1"` (ou `"auto"` para detecção automática) direto no `run_experiment(...)` ou via flags `--delimiter`, `--decimal`, `--encoding` na CLI.
> 2. **Colunas de texto/ID esquecidas:** Se sua tabela tiver uma coluna como `nome_amostra` ou `data_coleta` que não é numérica, remova-a antes ou ignore-a usando a configuração avançada (`DatasetSchemaSpec(..., ignore_cols=...)`).
> 3. **Células vazias:** Evite deixar células em branco na coluna alvo ou nos preditores no primeiro experimento.

---

## Passo 3 — Seu Primeiro Experimento em Python

Copie e execute o código abaixo. Para trocar para seus dados reais, basta substituir `dados` pelo caminho do seu arquivo (ex.: `data="meus_dados.csv"`):

```python
from experimental_ml import run_experiment
from experimental_ml.models import DummyBaselineModel

# 1. Seus dados (ou passe o caminho de um arquivo .csv, ex.: data="meus_dados.csv")
dados = {
    "dap": [12.0, 14.5, 16.0, 18.2, 20.1, 22.4, 24.0, 26.5, 28.0, 30.2],
    "altura": [10.1, 11.4, 12.0, 13.5, 14.2, 15.8, 16.4, 17.9, 18.5, 19.8],
    "volume": [0.12, 0.18, 0.23, 0.31, 0.39, 0.48, 0.56, 0.68, 0.77, 0.91],
}

# 2. Execução completa das 6 etapas em 1 chamada
resultado = run_experiment(
    data=dados,                     # dados em dicionário ou caminho para ".csv"
    target="volume",                # nome da coluna que você quer prever
    task="regression",              # "regression", "binary_classification" ou "multiclass_classification"
    models={
        "Baseline Média": DummyBaselineModel(strategy="mean"),
        "Baseline Mediana": DummyBaselineModel(strategy="median"),
    },
    output_dir="meu_experimento",   # pasta onde os relatórios serão salvos
    cv_folds=5,                     # número de dobras da validação cruzada (K-Fold)
    metrics=["rmse", "r2"],         # métricas desejadas
)

print(resultado.summary())
```

---

## Passo 4 — Como Usar o SEU Próprio Modelo

Você não precisa criar configurações complexas para testar seus próprios modelos. Qualquer classe Python (ou estimador no padrão `scikit-learn`) que tenha `.fit(X, y)` e `.predict(X)` — recebendo `X` e `y` como arrays NumPy (`np.ndarray`) — entra direto no dicionário `models`:

```python
import numpy as np

class MeuRegressorSimples:
    def fit(self, X: np.ndarray, y: np.ndarray) -> "MeuRegressorSimples":
        # X tem formato (n_amostras, n_features) e y tem formato (n_amostras,)
        X_aug = np.column_stack([X, np.ones(len(X))])
        coef, *_ = np.linalg.lstsq(X_aug, y, rcond=None)
        self.w_ = coef[:-1]
        self.b_ = float(coef[-1])
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return X @ self.w_ + self.b_

# Depois basta passar no dicionário: models={"Meu Modelo": MeuRegressorSimples()}
```

*(Para classificação com métricas probabilísticas como `roc_auc` ou `log_loss`, basta o seu modelo também implementar `.predict_proba(X)`.)*

---

## Passo 5 — O Que Aparece Depois de Rodar

Ao executar `print(resultado.summary())`, você verá no terminal:

```text
=== Resumo do Experimento ===
Diretório: .../meu_experimento
Células concluídas: 10 (falhas: 0)
Líder observado (rmse): ('baseline_media', 'todas_features')
Status estatístico: ...

Desempenho por configuração:
  - ('baseline_media', 'todas_features'): [VALID] rmse=0.2512±0.0810, r2=-0.8120±0.4201
  - ('baseline_mediana', 'todas_features'): [VALID] rmse=0.2640±0.0915, r2=-0.9540±0.4810

Conclusão: ...
Relatório Markdown: .../meu_experimento/reports/report.md
Relatório HTML: .../meu_experimento/reports/report.html
```

Dentro da pasta `meu_experimento/`, você encontrará:
- `reports/report.md` e `reports/report.html` — relatório completo pronto para leitura;
- `runs/` — resultados brutos salvos por dobra;
- `statistics/` — consolidação descritiva e comparações estatísticas.

> [!TIP]
> **No Google Colab**, para ler o relatório direto na tela da célula sem precisar baixar arquivos, rode:
> ```python
> # conceptual
> from IPython.display import Markdown, display
> display(Markdown(resultado.report_md_path.read_text(encoding="utf-8")))
> ```

---

## Alternativa pelo Terminal (Sem Escrever Python)

Se preferir rodar pelo terminal sem escrever código Python, use apenas dois comandos:

```bash
expml init --output-dir meu_experimento --task regression
expml quickrun --experiment-dir meu_experimento
```

Depois de testar com o exemplo, substitua `dados_exemplo.csv` pelo seu CSV e altere `target_col` em `schema.json` *(cuidado para manter aspas duplas `"` e não deixar vírgula sobrando no último item do JSON)*.

---

## O Que Você Pode Fazer Depois *(Nível Avançado)*

> [!TIP]
> **Prefere acompanhar no navegador/notebook passo a passo?** Abra o [Notebook 01 — Primeiro Experimento do Zero](../../notebooks/01_primeiro_experimento_do_zero.ipynb) (regressão) ou o [Notebook 02 — Classificação e Grupos na Prática](../../notebooks/02_classificacao_e_grupos_na_pratica.ipynb).

Quando seu experimento exigir maior controle metodológico, o framework oferece recursos avançados sem que você precise reescrever tudo do zero:
- **Dados com múltiplas medições pertencentes à mesma unidade ou grupo:** passe `group_col="grupo_id"` no `run_experiment` ou configure `GroupKFold` com holdout isolado ([Guia Prático 3](../guias_praticos/03_validacao_cruzada_agrupada_holdout.md));
- **Modelos analíticos sem treino (`requires_fit=False`) ou kernels quânticos:** use `ModelSpec` ([Guia Prático 1](../guias_praticos/01_modelos_analiticos_vs_treinados.md) e [Guia Prático 2](../guias_praticos/02_metricas_quanticas_e_probabilisticas.md));
- **Busca aninhada de hiperparâmetros (*Nested CV*) e seleção de features:** veja o [Tutorial das 6 Etapas](02_tutorial_6_etapas.md);
- **Como ler e citar os resultados estatísticos no seu TCC/artigo:** siga para [Interpretando Resultados Científicos](03_interpretando_resultados.md).
