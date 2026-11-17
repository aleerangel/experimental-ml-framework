# POS-2 Results — `pos-2-guia-pesquisador-cookbook` (`TA-POS.2`)

## Summary

- **Guia do Pesquisador (`docs/README.md`, `docs/guia/`)**: Portal unificado em português com mapa pedagógico em 4 níveis, Início Rápido em 5 passos com fluxo CLI e script Python executável, e Tutorial Completo cobrindo rigorosamente as **6 etapas oficiais** da arquitetura (com 4A Particionamento e 4B Execução Matricial na Etapa 4).
- **Scientific Cookbook (`docs/cookbook/`)**: 5 receitas práticas autocontidas cobrindo modelos analíticos (`requires_fit=False`) vs treinados, métricas quânticas (`KTA`, `PrecomputedKernelAdapter`) e probabilísticas (`ROC-AUC`, `Log-Loss`), validação cruzada agrupada (`GroupKFold` / `CV_AND_HOLDOUT`), otimização multiobjetivo na Fronteira de Pareto e pacotes herméticos (`FULL_PACKAGE` / `REDUCED_NO_RAW_DATA`) para conferências.
- **Catálogos de Referência (`docs/referencia/`)**: Referência da API pública delimitada às exportações de `__init__.py`/`__all__` dos 11 pacotes (`core`, `data`, `metrics`, `features`, `models`, `tuning`, `validation`, `orchestration`, `statistics`, `reporting`, `stages`) e catálogo completo da CLI `expml` com códigos de saída reais (`0`, `1`, `2`).
- **README.md Enxuto (`README.md`)**: Reestruturado em landing page equilibrada (55 linhas), removendo código longo e detalhamento de engenharia/requisitos, mantendo badges, instalação, fluxo CLI de 1 linha por etapa e tabela completa de navegação.
- **Integridade Documental em 5 Níveis (`tests/unit/test_documentation_integrity.py`)**: Validação de links e âncoras, sintaxe AST, resolução estática de imports públicos, validação léxica CLI e smoke test executável.

## Verification

- `check_proofs.py pos-2-guia-pesquisador-cookbook`: **4 pass, 0 fail** (`HEAD: 995422c`)
- `.venv/bin/pytest tests/ -q`: **595 passed in 19.10s**
- `verification.md`: **PASS** (`Independent Verifier 6524b05e-136f-49b2-99e4-1a33b3bd6043`)
