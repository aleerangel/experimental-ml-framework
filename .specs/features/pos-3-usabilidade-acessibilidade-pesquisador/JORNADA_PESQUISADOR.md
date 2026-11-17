# Jornada do Pesquisador e Estratégia Documental (`TA-POS.3`)

## 1. Fluxo Atual vs. Fluxo Desejado (Sem Conhecer a Arquitetura Interna)

### Fluxo Atual (Alta Fricção)
1. O pesquisador abre o repositório e encontra `README.md`, `docs/` e `notebooks/`.
2. Se escolher a CLI (`expml`), precisa descobrir sozinho o formato de **5 arquivos JSON** (`schema.json`, `rules.json`, `scenarios.json`, `models.json`, `partition.json`) sem templates gerados pelo sistema.
3. Mesmo sem problemas nos dados, precisa criar `rules.json` vazio (`[]`) e rodar `expml data sanitize`.
4. Não consegue escolher métricas pela CLI em `expml run start`.
5. Se escolher Python, precisa importar símbolos de **8 subpacotes** e escrever ~70 linhas de código de integração manual entre `orchestration`, `statistics` e `reporting`.

### Fluxo Desejado (Progressivo)
1. **Descoberta em 1 comando (`expml init`):** Gera uma pasta de experimento pronta com templates comentados e um CSV de exemplo, indicando exatamente o próximo comando a executar.
2. **Defaults seguros na CLI e na API:** Regras vazias opcionais quando não há achados críticos, suporte a `--metrics` em `expml run start`, `--experiment-dir` consistente em todos os subcomandos `run`, e uma fachada Python enxuta para experimentos padrão sem esconder os parâmetros metodológicos.
3. **Erros orientados à resolução:** Quando falta um campo ou há erro de schema JSON, o erro informa qual campo faltou e exibe o formato esperado.
4. **Resultados autoexplicativos:** Relatórios informam o caminho completo gerado e incluem notas interpretativas breves para pesquisadores iniciantes.

---

## 2. Fase 5 — Estratégia de Documentação por Jornadas de Utilização

Para separar claramente o **uso científico** da **engenharia interna**, a documentação passa a ser organizada segundo **5 Jornadas**:

| Jornada | Público-Alvo | Escopo e Conteúdo | Onde Deve Ficar |
| :--- | :--- | :--- | :--- |
| **Jornada 1 — Primeiro Experimento** | Pesquisador iniciante / Aluno de IC | Instalação, `expml init`, dados tabulares, configuração mínima, execução e leitura dos primeiros resultados. | `docs/guia/00_comecando_do_zero.md`, `01_inicio_rapido.md` + `notebooks/01_primeiro_experimento_do_zero.ipynb`, `02_classificacao_e_grupos_na_pratica.ipynb` |
| **Jornada 2 — Construindo Experimentos** | Pesquisador conduzindo estudos | Schemas JSON completos da CLI, cenários de atributos (`FIXED`/`DYNAMIC`), modelos, validação cruzada (`GroupKFold`, `CV_AND_HOLDOUT`), seleção de métricas. | `docs/guia/02_tutorial_6_etapas.md` + `docs/referencia/cli_schemas_json.md` + `notebooks/03_tour_6_etapas.ipynb` |
| **Jornada 3 — Interpretando Resultados Científicos** | Pesquisador escrevendo artigo/TCC | Guia de interpretação de métricas (`RMSE`, `MBE`, `ROC-AUC`), inferência pareada (Nadeau-Bengio/Wilcoxon), tamanho de efeito (*d* de Cohen), controle de multiplicidade, Pareto e limitações (`p ≥ α`). | `docs/guia/03_interpretando_resultados.md` + `docs/guias_praticos/09_*` |
| **Jornada 4 — Recursos Avançados** | Pesquisador avançado | Modelos analíticos (`requires_fit=False`), kernels pré-computados (`KTA`), variantes LS-SVM, aquisição sequencial e pacotes de conferência. | `docs/guias_praticos/01..08` + `notebooks/04_avancado_variantes_lssvm_prognose_florestal.ipynb` |
| **Jornada 5 — Desenvolvimento** | Mantenedores e colaboradores de código | Arquitetura em camadas, SRS, contratos formais, invariantes AST, suíte de testes e processo de aceite de marcos. | `docs/engenharia_software/` + `docs/REFERENCIAS_E_FUNDAMENTACAO.md` (separado do fluxo do usuário) |
