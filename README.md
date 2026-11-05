# Experimental ML Framework

Framework experimental agnóstico para pesquisa científica em Aprendizado de Máquina (*Machine Learning* — ML), voltado a tarefas de regressão e classificação sobre dados tabulares.

O projeto fornece infraestrutura modular, determinística e pedagógica para condução, auditoria e publicação de experimentos científicos, priorizando a integridade metodológica, a prevenção ativa de vazamento de dados e a reprodutibilidade integral dos resultados.

---

## 1. Sobre o Projeto

### Propósito e Problema Abordado

A pesquisa experimental em Aprendizado de Máquina frequentemente enfrenta desafios metodológicos que comprometem a validade e a comparabilidade dos resultados publicados:
- **Vazamento de dados (*data leakage*):** ajuste acidental de transformações de pré-processamento, imputações ou seleção de atributos fora do laço interno de treino de cada partição.
- **Mutações silenciosas:** alterações não declaradas ou automáticas nos dados brutos de entrada (como descarte de linhas com valores ausentes ou coerção arbitrária de tipos).
- **Viés de seleção de hiperparâmetros:** ausência de validação cruzada aninhada (*Nested CV*), resultando em estimativas de erro superotimistas.
- **Inferência estatística frágil:** declaração de modelos vencedores baseada em médias simples, sem testes pareados adequados, sem correção de comparações múltiplas ou confundindo ausência de significância estatística ($p \ge \alpha$) com equivalência entre algoritmos.
- **Acoplamento entre execução e apresentação:** necessidade de reexecutar experimentos onerosos apenas para reformatar tabelas ou recalcular testes estatísticos.

O `experimental-ml-framework` aborda esses problemas estruturando o ciclo experimental em **6 etapas operacionais** regidas por contratos estritos de entrada, saída e invariantes matemáticas, projetados para reduzir falhas metodológicas por construção.

### Objetivos Principais

- **Prevenção estrutural de vazamento:** todo ajuste de parâmetros (pré-processamento, seleção de atributos e calibração de modelos) ocorre estritamente nos dados de treino de cada partição externa (**ADR-002**).
- **Zero mutações silenciosas:** a base de dados original é estritamente imutável. Toda sanitização ou imputação exige declaração explícita em um plano auditável de preparação.
- **Arquitetura agnóstica sem estimadores próprios (ADR-001):** o framework não reescreve algoritmos de ML internamente; recebe modelos e funções externas (Scikit-Learn, XGBoost, modelos analíticos sem `fit`, funções customizadas e circuitos quânticos) através de contratos funcionais uniformes.
- **Rastreabilidade e proveniência retrospectiva:** vinculação ponta a ponta entre a base de dados original, identificadores imutáveis de partição, sementes determinísticas e previsões por observação.
- **Independência entre camadas:** a geração de relatórios científicos, figuras e tabelas opera de forma somente-leitura sobre os artefatos persistidos, sem exigir retreinamento de modelos.

---

## 2. Estado de Desenvolvimento

O projeto encontra-se na **Fase 4: Implementação Guiada por Testes (TDD) do MVP**, utilizando a metodologia de desenvolvimento orientado por especificações (*TLC Spec-Driven Development*).

- **Marco M1.1 (`m1-1-setup-cli-smoke`): CONCLUÍDO E ACEITO.**  
  Implementação, testes automatizados (12/12) e homologação manual aprovados. Disponibiliza configuração de empacotamento em Python, estrutura modular do projeto, ponto de entrada da CLI (`expml`) e suíte de testes de fumaça.
- **Marco M1.2 (`core`): CONCLUÍDO E ACEITO.**  
  Implementação, testes automatizados (18/18) e homologação manual aprovados. Fornece identificadores de domínio imutáveis, enumerações, derivação determinística de sementes (`numpy.random.SeedSequence`), serialização canônica e hashing (`config_hash` e `dataset_hash` conforme ADR-007), além de diagnósticos estruturados (`Finding`) e exceções formais.
- **Marco M1.3 (`metrics`): CONCLUÍDO E ACEITO.**  
  Implementação, testes automatizados (22/22) e homologação manual aprovados. Disponibiliza catálogo centralizado `METRICS_CATALOG` com as 15 métricas canônicas, funções puramente vetorizadas em dupla precisão `float64`, mitigação de overflow quadrático intermediário, tratamento determinístico de casos degenerados via `MetricStatus.UNDEFINED_NAN` sem coerção silenciosa para zero (ADR-005), e ranqueamento lexicográfico com precedência estrita de cobertura.
- **Marco M1.4 (`datasets & schemas`): CONCLUÍDO E ACEITO.**  
  Implementação, testes automatizados (29/29) e homologação manual aprovados. Disponibiliza a camada de ingestão tabular imutável (`DatasetBundle`), especificação declarativa de papéis e tipos semânticos (`DatasetSchemaSpec`, `ColumnSemanticType`), isolamento de memória respaldado por buffers `bytes` imutáveis recusando `setflags(write=True)`, parsing estrito RFC 4180 com sniffer automático e detecção de *ragged rows*, geração/validação de `ObservationId`, cálculo de hashes tripartites (`dataset_hash`, `raw_source_hash`, `schema_hash`) e utilitários somente-leitura de consulta e fatiamento ordenado.
- **Marco M2 (`data` + `validation` + CLI `data`/`partition`): PRÓXIMO MARCO.**  
  Triagem estatística (`profile_dataset` separando problemas confirmados vs. alertas heurísticos), plano de preparação (`create_preparation_plan`), saneamento (`sanitize_dataset`) e geração/validação matemática do `PartitionPlan` (`build_partition_plan`, `validate_partition_plan`).
- **Marcos M3 a M7: PLANEJADOS.**  
  Seleção dinâmica de atributos, execução matricial, comparação estatística e geração de relatórios estão especificados e serão implementados nos marcos subsequentes.

---

## 3. Funcionalidades Disponíveis

Na versão atual da branch `main`, as seguintes capacidades estão implementadas e operacionais:

- **Empacotamento Padronizado (PEP 517 / PEP 621):** Configuração declarativa via `pyproject.toml` baseada no build backend Hatchling, com dependência declarada de `numpy>=1.24.0`.
- **Instalação Editável:** Suporte a instalação via `pip install -e ".[dev]"` em ambientes virtuais Python `>=3.10`.
- **Acesso Programático à Versão:** O pacote raiz expõe a constante pública de versão via `experimental_ml.__version__` (`0.1.0.dev0`).
- **Interface de Linha de Comando (`expml`):** Ponto de entrada executável registrado no ambiente (`PATH`), desenvolvido exclusivamente sobre a biblioteca padrão (`argparse`) sem dependências externas adicionais:
  - Opção `--version`: Exibe o identificador do executável e a versão instalada, finalizando com código de saída `0`.
  - Opção `--help` (ou `-h`): Apresenta o sumário descritivo de opções e instruções de uso, finalizando com código de saída `0`.
  - Execução sem argumentos: Exibe as instruções de uso e finaliza com código de saída `0`.
  - Tratamento de argumentos inválidos: Exibe mensagem de erro descritiva em `stderr` e finaliza com código de saída `2` (seguindo as convenções de integridade do requisito `RNF07`).
- **Núcleo Transversal de Domínio (`experimental_ml.core` — Nível 0):**
  - **Identificadores Imutáveis:** Tipos `ExperimentId`, `PartitionPlanId`, `ScenarioId`, `ModelId`, `CellId`, `ComparisonId`, `ArtifactId` e `ObservationId` (subtipos de `str` imutáveis com validação estrita contra strings vazias, quebras de linha e caracteres de controle).
  - **Enumerações Fundamentais:** `TaskType`, `ExecutionStatus`, `FindingSeverity`, `MetricDirection`, `AggregationScope`, `MetricStatus` e `ErrorPolicy` (subtipos de `str, Enum` com igualdade direta a strings e compatibilidade com serialização JSON nativa).
  - **Derivação Hierárquica de Sementes:** Funções puras `derive_seeds(master_seed, count)` e `spawn_child_seeds(parent_seed, count)` baseadas em `numpy.random.SeedSequence`, garantindo determinismo estrito e independência estatística (RNF01, ADR-007).
  - **Hashing Canônico de Configurações (`config_hash`):** Digest SHA-256 em conformidade integral com o **ADR-007** (normalização Unicode NFC, ordenação lexicográfica de chaves por bytes UTF-8, diferenciação estrita de escalares `bool` vs `int` e `int` vs `float`, normalização de `-0.0 -> 0.0`, representação canônica de `NaN`/`Inf`, distinção entre `tuple` e `list`, ordenação determinística de `set` pelo hash de seus itens e detecção de ciclos).
  - **Hashing Estrutural de Datasets (`dataset_hash`):** Digest SHA-256 para arquivos brutos combinados com o esquema, e fluxo contínuo little-endian para dados tabulares em memória sensível a nomes de colunas, ordenação de linhas e tipos.
  - **Diagnósticos e Sinalizadores de Contrato:** Estrutura imutável `Finding`, construtores `make_finding` (`CONFIRMED_ISSUE`) e `make_warning` (`HEURISTIC_WARNING`), e hierarquia de exceções (`ExperimentalMLError`, `ContractViolationError`, `DataIntegrityError`, `ConfigurationError`).
- **Camada de Métricas de Avaliação (`experimental_ml.metrics` — Nível 1):**
  - **Catálogo Centralizado (`METRICS_CATALOG`):** Registro formal das 15 especificações (`MetricSpec`), com metadados de direção, famílias e tolerâncias de referência.
  - **Funções de Regressão e Alinhamento:** Implementação vetorizada em `float64` de `mae`, `rmse`, `mbe` (preservando o viés assinado e comparando por magnitude absoluta), `r2`, `rmse_rel_pct`, `mape`, `pearson` e `kta` (com suporte a centralização $HKH$).
  - **Funções de Classificação:** Métricas discretas `accuracy`, `balanced_accuracy`, `precision`, `recall` e `f1` (com avaliação pelo próprio denominador $2TP + FP + FN$), além de probabilísticas `roc_auc` (empates exatos via postos médios e OVR) e `log_loss` (com validação estrita de distribuições e clipping $\epsilon = 10^{-15}$).
  - **Comparação, Agregação e Ranqueamento (ADR-005):** Comparador `is_better` compatível com `compare_by_abs`, agregador entre dobras `aggregate_fold_metrics` gerando `VALID`, `PARTIAL_COVERAGE` e `UNDEFINED_NAN`, e ranqueador lexicográfico `rank_configurations` com precedência estrita de cobertura.
- **Camada de Ingestão e Esquemas Tabulares (`experimental_ml.data` — Nível 1):**
  - **Especificação Estrutural e Tipagem Semântica (`DatasetSchemaSpec`):** Estrutura imutável com validação de disjunção de papéis de colunas (`target_col`, `group_col`, `observation_id_col`, `time_col`, `ignore_cols`), normalização Unicode NFC e bloqueio de vazamento da Onda 2.
  - **Ingestão Tabular com Posse Exclusiva (`load_dataset`):** Suporte a arquivos tabulares (`.csv`, `.txt`, `.tsv`) e fontes em memória (`dict`, 2D `ndarray`, sequências de registros e `DataFrame` via duck-typing), sem dependência obrigatória de `pandas`.
  - **Imutabilidade Física de Buffers:** Colunas numéricas e booleanas respaldadas por buffers `bytes` imutáveis na camada C do NumPy, recusando tentativas de reativação de escrita (`arr.setflags(write=True)` levanta `ValueError`). Colunas `object` restritas a escalares imutáveis com `writeable=False`.
  - **Parsing Estrito e Detecção Segura de Delimitadores:** Suporte a `,`, `;`, `\t`, `|` e múltiplos espaços com aspas RFC 4180, com detecção automática consistente em 100 linhas e falha explícita sob ambiguidade ou linhas irregulares (*ragged rows*).
  - **Identificadores de Observação (`ObservationId`):** Atribuição determinística sequencial `obs_000000` na ausência de coluna de ID e validação estrita de não-nulidade e unicidade quando informada na fonte.
  - **Semântica Tripartite de Hashes:** `dataset_hash` canônico do conteúdo em memória invariante a quebras de linha (`\r\n` vs `\n`), sensível à ordem das colunas e aos `observation_ids`, `raw_source_hash` para proveniência do arquivo em disco e `schema_hash` para a configuração estrutural.
  - **Utilitários de Consulta:** `get_column_array` (view somente-leitura ou cópia mutável independente) e `slice_bundle_by_observation_ids` preservando a ordem solicitada pelo chamador com recálculo de hash.
- **Suíte de Testes Automatizados:** 81 testes automatizados (12 testes de fumaça em `tests/test_smoke.py`, 18 testes unitários em `tests/unit/test_core.py`, 22 testes unitários em `tests/unit/test_metrics.py` e 29 testes unitários em `tests/unit/test_data_schemas.py`), com 100% de aprovação via `pytest`.

---

## 4. Tecnologias e Estrutura do Projeto

### Tecnologias Utilizadas

- **Linguagem:** Python (suporte declarado `>=3.10`; verificado no interpretador local `Python 3.12.15`).
- **Build Backend:** [Hatchling](https://hatch.pypa.io/latest/) (`hatchling.build`).
- **Computação Numérica:** [NumPy](https://numpy.org/) (`numpy>=1.24.0`, utilizado em `experimental_ml.core` e `experimental_ml.metrics`).
- **Testes Automatizados:** [Pytest](https://docs.pytest.org/) (`pytest>=7.0.0`).
- **Biblioteca Padrão:** Utilização estrita de módulos padrão (`argparse`, `tomllib`, `ast`, `subprocess`, `sys`, `hashlib`, `unicodedata`, `struct`, `types`, `math`) na infraestrutura da CLI, no hashing canônico e nas métricas.

### Estrutura de Diretórios

```
experimental-ml-framework/
├── .specs/                          # Especificações formais e tarefas (TLC Spec-Driven)
│   ├── STATE.md                     # Registro de decisões arquiteturais de projeto e handoff
│   └── features/
│       ├── m1-1-setup-cli-smoke/    # Artefatos da entrega M1.1 (spec.md, tasks.md, proofs.md, ACCEPTANCE.md, RESULTS.md)
│       ├── m1-2-core/               # Artefatos da entrega M1.2 (spec.md, tasks.md, proofs.md, verification.md, ACCEPTANCE.md, RESULTS.md)
│       ├── m1-3-metrics/            # Artefatos da entrega M1.3 (spec.md, tasks.md, proofs.md, verification.md, ACCEPTANCE.md, RESULTS.md)
│       └── m1-4-datasets-schemas/   # Artefatos da entrega M1.4 (spec.md, tasks.md, proofs.md, verification.md, ACCEPTANCE.md, RESULTS.md)
├── engenharia_software/             # Documentação técnica central de engenharia
│   ├── ESPECIFICACAO_REQUISITOS.md  # Especificação formal de requisitos (SRS v2.0)
│   ├── ARQUITETURA_E_CONTRATOS.md   # Arquitetura em camadas, contratos e modelo de dados
│   ├── PROCESSO_DE_ACEITE_DE_MARCOS.md # Governança de três documentos para aceite formal de marcos
│   └── ETAPA_ATUAL_ENGENHARIA.md    # Estado atual do ciclo de vida e roadmap detalhado
├── src/
│   └── experimental_ml/             # Código-fonte da biblioteca (layout src/)
│       ├── __init__.py              # Raiz do pacote (exposição de __version__)
│       ├── cli/                     # Interface de linha de comando (Nível 7)
│       │   ├── __init__.py
│       │   └── main.py              # Ponto de entrada e parser principal (expml)
│       ├── core/                    # Núcleo transversal de domínio (Nível 0)
│       │   ├── __init__.py          # Re-exportação com __all__
│       │   ├── enums.py             # Tipos de tarefas, direções e status
│       │   ├── findings.py          # Diagnósticos auditáveis, advertências e exceções formais
│       │   ├── hashing.py           # config_hash, dataset_hash, is_nan_scalar e is_missing_scalar (ADR-007)
│       │   ├── seeds.py             # Derivação hierárquica SeedSequence
│       │   └── types.py             # Identificadores canônicos e imutáveis (ObservationId, etc.)
│       ├── metrics/                 # Camada de métricas e alinhamento (Nível 1)
│       │   ├── __init__.py          # Re-exportação com __all__
│       │   ├── aggregation.py       # is_better, aggregate_fold_metrics, rank_configurations (ADR-005)
│       │   ├── catalog.py           # METRICS_CATALOG, compute_metric, get_metric_spec
│       │   ├── classification.py    # accuracy, balanced_accuracy, precision, recall, f1, roc_auc, log_loss
│       │   ├── regression.py        # mae, rmse, mbe, r2, rmse_rel_pct, mape, pearson, kta
│       │   ├── types.py             # MetricValue, AggregatedMetricValue, MetricSpec, RankedCandidate
│       │   └── validation.py        # validate_numeric_arrays, scaled_quadratic_sum
│       └── data/                    # Ingestão, esquemas e imutabilidade de datasets (Nível 1)
│           ├── __init__.py          # Re-exportação com __all__
│           ├── loader.py            # Ingestão load_dataset com buffers imutáveis e hashes tripartites
│           ├── parsing.py           # Parser RFC 4180 com detecção automática de delimitadores
│           ├── query.py             # get_column_array e slice_bundle_by_observation_ids
│           ├── schema.py            # DatasetSchemaSpec, normalização NFC e validação de papéis
│           ├── types.py             # ColumnSemanticType, ColumnDescriptor e DatasetBundle
│           └── validation.py        # Validação estrutural e integridade de ObservationId
├── tests/                           # Suíte de testes automatizados (81 testes aprovados)
│   ├── test_smoke.py                # Suíte de testes de fumaça da CLI e empacotamento (12 testes)
│   └── unit/
│       ├── test_core.py             # Suíte unitária do módulo core (18 testes)
│       ├── test_metrics.py          # Suíte unitária do módulo metrics (22 testes)
│       └── test_data_schemas.py     # Suíte unitária do módulo data / schemas (29 testes)
├── pyproject.toml                   # Configuração de build, dependências e metadados
├── README.md                        # Porta de entrada do repositório
└── REFERENCIAS_E_FUNDAMENTACAO.md   # Fundamentação teórica e referências normativas (25 fontes)
```

---

## 5. Instalação

### Pré-requisitos

- **Python:** Versão `>= 3.10` instalada no sistema operacional.
- **Git:** Para clonar o repositório.

### Instruções Passo a Passo

1. **Clonar o repositório:**
   ```bash
   git clone https://github.com/alexandrerangel/experimental-ml-framework.git
   cd experimental-ml-framework
   ```

2. **Criar e ativar o ambiente virtual isolado (`.venv`):**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
   *(No Windows: `.venv\Scripts\activate`)*

3. **Atualizar o gerenciador `pip`:**
   ```bash
   pip install --upgrade pip
   ```

4. **Instalar o pacote em modo editável com as ferramentas de teste:**
   ```bash
   pip install -e ".[dev]"
   ```

Após esse procedimento, o comando `expml` estará acessível diretamente no terminal dentro do ambiente virtual ativo.

---

## 6. Como Utilizar

### Comandos da Interface de Linha de Comando (`expml`)

Com o ambiente virtual ativado, execute os comandos abaixo para verificar o funcionamento da interface:

#### Verificar a versão instalada:
```bash
expml --version
```


#### Exibir a mensagem de ajuda e opções:
```bash
expml --help
```


#### Invocação sem argumentos:
```bash
expml
```
Imprime as informações de utilização e finaliza com código de saída `0`.

#### Teste de validação de argumentos inválidos:
```bash
expml --opcao-invalida
```

### Uso Programático em Python

#### Versão do Pacote
```python
import experimental_ml

print(experimental_ml.__version__)
# Saída: 0.1.0.dev0
```

#### Núcleo de Domínio (`experimental_ml.core`)
```python
from experimental_ml.core import (
    ExperimentId,
    TaskType,
    derive_seeds,
    config_hash,
    dataset_hash,
    make_finding,
)

# 1. Identificadores de domínio imutáveis e validados
exp_id = ExperimentId("exp_baseline_01")

# 2. Derivação hierárquica e determinística de sementes (ADR-007)
seeds = derive_seeds(master_seed=42, count=3)
# Retorna tupla de 3 inteiros determinísticos

# 3. Hashing canônico de configuração (ADR-007)
h_config = config_hash({"task": TaskType.REGRESSION, "alpha": 0.01})
# Retorna digest SHA-256 de 64 caracteres

# 4. Hashing estrutural de dados tabulares em memória ou disco
data = {"feature1": [1.0, 2.0], "feature2": [10, 20]}
h_data = dataset_hash(data)

# 5. Construtores de diagnósticos estruturados
finding = make_finding(code="E1_ZERO_VARIANCE", message="Coluna com variância nula.")
```

#### Motor de Métricas (`experimental_ml.metrics`)
```python
import numpy as np
from experimental_ml.core import MetricDirection
from experimental_ml.metrics import (
    compute_metric,
    get_metric_spec,
    is_better,
    aggregate_fold_metrics,
)

# 1. Cálculo de métricas puras vetorizadas em float64
y_true = np.array([10.0, 20.0, 30.0], dtype=np.float64)
y_pred = np.array([11.0, 19.0, 32.0], dtype=np.float64)
rmse_val = compute_metric("rmse", y_true, y_pred)
# rmse_val.value -> 1.4142..., rmse_val.status -> MetricStatus.VALID

# 2. Consulta de metadados e tolerância
spec = get_metric_spec("rmse")
# spec.direction -> MetricDirection.MINIMIZE, spec.rtol -> 1e-7

# 3. Comparação de candidatos com semântica estrita de UNDEFINED_NAN
melhor = is_better(cand_a=rmse_val, cand_b=rmse_val, direction=spec.direction)
# False (empate dentro da tolerância rtol)

# 4. Agregação entre partições com controle de cobertura
agg = aggregate_fold_metrics([rmse_val, rmse_val])
# agg.mean -> 1.4142..., agg.coverage -> 1.0, agg.status -> MetricStatus.VALID
```

#### Ingestão e Esquemas Tabulares (`experimental_ml.data`)
```python
from experimental_ml.core import TaskType
from experimental_ml.data import (
    DatasetSchemaSpec,
    ColumnSemanticType,
    load_dataset,
    get_column_array,
    slice_bundle_by_observation_ids,
)

# 1. Declaração imutável do esquema estrutural
schema = DatasetSchemaSpec(
    target_col="y",
    task_type=TaskType.REGRESSION,
    group_col="parcela",
    column_semantic_types={"y": ColumnSemanticType.NUMERIC_CONTINUOUS, "parcela": ColumnSemanticType.CATEGORICAL},
)

# 2. Ingestão com posse exclusiva e buffers imutáveis em nível C
data_source = {"feat1": [1.5, 2.5, 3.5], "parcela": ["A", "A", "B"], "y": [10.0, 20.0, 30.0]}
bundle = load_dataset(data_source, schema)
# bundle.dataset_hash -> Digest canônico do conteúdo tabular
# bundle.n_rows -> 3, len(bundle.feature_cols) -> 1

# 3. Tentativas de reativar escrita no buffer levantam ValueError
arr = get_column_array(bundle, "feat1", copy=False)
# arr.setflags(write=True) -> ValueError: cannot set WRITEABLE flag to True of this array

# 4. Fatiamento imutável preservando ordenação solicitada
sub_bundle = slice_bundle_by_observation_ids(bundle, ["obs_000002", "obs_000000"])
# sub_bundle.observation_ids -> ("obs_000002", "obs_000000")
```

---

## 7. Testes

O projeto utiliza o **Pytest** para automação de testes e garantia contínua de integridade.

### Execução da Suíte Completa de Testes

Para executar toda a suíte de testes (testes de fumaça da instalação e testes unitários):

```bash
pytest tests/ -v
```

Para executar isoladamente os módulos unitários:

```bash
pytest tests/unit/test_core.py -v
pytest tests/unit/test_metrics.py -v
pytest tests/unit/test_data_schemas.py -v
```

### Comportamento Verificado

A suíte valida deterministicamente **81 verificações** automatizadas com 100% de sucesso:
- **12 testes de fumaça (`tests/test_smoke.py`):** Declaração de build backend, dependências e metadados em `pyproject.toml`, versão `0.1.0.dev0`, ausência de importações espúrias e códigos de saída da CLI (`--version`, `--help`, invocação vazia e flags inválidas com código `2`).
- **18 testes de núcleo (`tests/unit/test_core.py`):** Imutabilidade e validação de identificadores, integridade de enumerações, determinismo da derivação de sementes (`SeedSequence`), regras canônicas de hashing do **ADR-007** (Unicode NFC, `-0.0`, `NaN`/`Inf`, coleções) e construtores de diagnósticos `Finding`.
- **22 testes de métricas (`tests/unit/test_metrics.py`):** Exatidão numérica das 15 métricas vetorizadas em `float64` sob tolerâncias rigorosas por família (`rtol`/`atol`), mitigação de overflow quadrático intermediário, tratamento determinístico de degenerescências via `MetricStatus.UNDEFINED_NAN` sem coerção silenciosa para zero (**ADR-005**) e ranqueamento lexicográfico.
- **29 testes de datasets e esquemas (`tests/unit/test_data_schemas.py`):** Imutabilidade estrutural e física de arrays via buffers `bytes` imutáveis que recusam `setflags(write=True)`, integridade RFC 4180 com sniffer automático de delimitadores, rejeição de linhas irregulares (*ragged rows*), unicidade e geração de `ObservationId`, hashes tripartites (`dataset_hash`, `raw_source_hash`, `schema_hash`) e utilitários seguros de fatiamento.

---

## 8. Roadmap

O desenvolvimento do MVP é organizado em marcos progressivos guiados por testes (TDD). A tabela a seguir distingue o que já foi implementado do que está planejado:

| Marco | Escopo e Responsabilidade | Estado |
| :--- | :--- | :---: |
| **M1.1** | **Configuração e CLI Base:** `pyproject.toml`, layout `src/experimental_ml/`, comando `expml` (`--version`, `--help`) e suíte de fumaça. | **Concluído e Aceito** |
| **M1.2** | **Contratos e Funções de Core:** Tipos de IDs imutáveis, constantes/enums, gerador `derive_seeds` (`SeedSequence`), funções `config_hash`/`dataset_hash` (ADR-007) e diagnósticos `Finding`. | **Concluído e Aceito** |
| **M1.3** | **Motor de Métricas:** Catálogo `METRICS_CATALOG`, regras para `MetricStatus.UNDEFINED_NAN` (ADR-005) e 15 funções de métricas vetorizadas com tolerâncias justificadas. | **Concluído e Aceito** |
| **M1.4** | **Datasets & Schemas:** Ingestão tabular imutável (`load_dataset`, `DatasetBundle`), buffers `bytes` imutáveis na C-API recusando reativação de escrita, parsing RFC 4180 com sniffer automático, tipagem semântica (`DatasetSchemaSpec`, `ColumnSemanticType`) e hashes tripartites. | **Concluído e Aceito** |
| **M2** | **Diagnóstico e Particionamento:** Triagem estatística (`profile_dataset` separando problemas confirmados vs. alertas heurísticos), plano de preparação (`create_preparation_plan`), saneamento (`sanitize_dataset`) e `PartitionPlan` compartilhado (`validation`). | **Próximo Marco** |
| **M3** | **Cenários de Features:** Modo exploratório rotulado (`EXPLORATORY_FULL_DATA`), cenários fixos e seleção dinâmica ajustada no treino de cada partição (`features`). | Planejado |
| **M4** | **Modelos e Tuning:** Registro de modelos (`models`), pré-processamento em duas camadas e busca aninhada de hiperparâmetros (`tuning`). | Planejado |
| **M5** | **Execução Matricial:** Orquestração da matriz $M \times C \times F$ (`orchestration`), tolerância a falhas, persistência e retomada (*Checkpoint & Resume*). | Planejado |
| **M6** | **Estatística:** Consolidação descritiva, teste $t$ corrigido de Nadeau-Bengio, Wilcoxon pareado, controle de FWER/FDR (Holm/BH), Fronteira de Pareto e conclusões estruturadas (`statistics`). | Planejado |
| **M7** | **Relatórios e Reprodutibilidade:** Relatórios em Markdown/HTML, 7 famílias de tabelas/figuras, manifesto `ArtifactProvenance` e reprodução do experimento de referência `prognose_florestal`. | Planejado |

---

## 9. Documentação Técnica

Para consultar detalhes de engenharia, requisitos, arquitetura e fundamentação científica:

| Documento | Descrição |
| :--- | :--- |
| [`engenharia_software/PROCESSO_DE_ACEITE_DE_MARCOS.md`](engenharia_software/PROCESSO_DE_ACEITE_DE_MARCOS.md) | **Processo de Aceite de Marcos:** Regras de governança, tríade documental (`SPEC.md`, `ACCEPTANCE.md`, `RESULTS.md`) e critérios objetivos de aprovação. |
| [`engenharia_software/ESPECIFICACAO_REQUISITOS.md`](engenharia_software/ESPECIFICACAO_REQUISITOS.md) | **Especificação de Requisitos de Software (SRS v2.0):** Requisitos funcionais das 6 etapas, requisitos não-funcionais e critérios de aceitação. |
| [`engenharia_software/ARQUITETURA_E_CONTRATOS.md`](engenharia_software/ARQUITETURA_E_CONTRATOS.md) | **Arquitetura, Contratos e Modelo de Dados:** Camadas, pipeline de 6 etapas, contratos de módulos, modelo de dados e pacote de reprodutibilidade. |
| [`engenharia_software/ETAPA_ATUAL_ENGENHARIA.md`](engenharia_software/ETAPA_ATUAL_ENGENHARIA.md) | **Registro de Estado da Engenharia:** Situação atual no ciclo de vida e roadmap detalhado de implementação. |
| [`REFERENCIAS_E_FUNDAMENTACAO.md`](REFERENCIAS_E_FUNDAMENTACAO.md) | **Fundamentação Teórico-Técnica e Bibliografia:** Justificativas científicas e normativas para as decisões de projeto (ADRs), com 25 referências. |
| [`.specs/features/m1-1-setup-cli-smoke/`](.specs/features/m1-1-setup-cli-smoke/) | **Artefatos da Entrega M1.1:** Especificação (`SPEC.md`), roteiro de aceitação (`ACCEPTANCE.md`) e resultados (`RESULTS.md`). |
| [`.specs/features/m1-2-core/`](.specs/features/m1-2-core/) | **Artefatos da Entrega M1.2:** Especificação (`SPEC.md`), roteiro de aceitação (`ACCEPTANCE.md`), resultados (`RESULTS.md`) e verificação independente (`verification.md`). |
| [`.specs/features/m1-3-metrics/`](.specs/features/m1-3-metrics/) | **Artefatos da Entrega M1.3:** Especificação (`SPEC.md`), roteiro de aceitação (`ACCEPTANCE.md`), resultados (`RESULTS.md`) e verificação independente (`verification.md`). |
| [`.specs/features/m1-4-datasets-schemas/`](.specs/features/m1-4-datasets-schemas/) | **Artefatos da Entrega M1.4:** Especificação (`SPEC.md`), roteiro de aceitação (`ACCEPTANCE.md`), resultados (`RESULTS.md`) e verificação independente (`verification.md`). |

---

## Licença

Este projeto é distribuído sob os termos da licença MIT (conforme declarado em [`pyproject.toml`](pyproject.toml)).
