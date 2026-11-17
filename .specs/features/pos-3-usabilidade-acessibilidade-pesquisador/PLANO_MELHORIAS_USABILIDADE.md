# Plano Priorizado de Melhorias de Usabilidade (`TA-POS.3`)

Cada intervenção abaixo está vinculada diretamente a um achado factual registrado em [`AUDITORIA_USABILIDADE.md`](./AUDITORIA_USABILIDADE.md), preservando integralmente os contratos M1–M7 e a pureza `XCUT-02`.

---

## Matriz Priorizada de Intervenções

| Prioridade | ID | Intervenção | Achado Vinculado | Impacto Esperado |
| :---: | :---: | :--- | :--- | :--- |
| **P0** | `USAB-01` | **Comando `expml init` (Scaffold de Projeto)**<br/>Gera diretório inicial com `dados_exemplo.csv` e templates JSON válidos (`schema.json`, `rules.json`, `scenarios.json`, `models.json`, `partition.json`, `stats_config.json`) + instrução do próximo comando. | #2, #3, #4, #5, #6 | Elimina criação manual de 6 JSONs desconhecidos na entrada. |
| **P0** | `USAB-02` | **Seleção de Métricas na CLI (`expml run start --metrics ...`)**<br/>Adicionar flag opcional `--metrics` em `expml run start` (mantendo `default_metrics` seguros quando omitida). | #7 | Permite avaliar `rmse_rel_pct`, `mbe`, `roc_auc`, `log_loss` pela CLI sem migrar para Python. |
| **P0** | `USAB-03` | **Saneamento Direto sem Achados (`expml data sanitize --rules` opcional)**<br/>Permitir omitir `--rules` em `expml data sanitize` quando não houver achados críticos (`rules=[]`), ou aceitar `--allow-empty-rules`. | #4 | Remove etapa artificial de criar `rules.json` contendo `[]`. |
| **P0** | `USAB-04` | **Fachada Python de Alto Nível (`experimental_ml.run_experiment`)**<br/>Função enxuta opcional que recebe dados/schema, modelos, cenários, configuração de partição e métricas, encadeando Etapas 1–6 sem substituir as APIs puras existentes. | #9 | Reduz código de cola de ~70 linhas e 8 imports para ~15 linhas explícitas mantendo decisões metodológicas visíveis. |
| **P1** | `USAB-05` | **Consistência de Flags e Orientação na CLI (`--experiment-dir` + Próximos Passos)**<br/>Aceitar `--experiment-dir` em `run status/verify/resume` (inferindo `<exp>/runs`), exibir valores válidos no `--help` e imprimir o próximo passo sugerido + caminho completo dos relatórios gerados. | #2, #6, #8, #10 | Elimina erros de nomenclatura entre subcomandos e facilita localizar `report.md`/`report.html`. |
| **P1** | `USAB-06` | **Mensagens de Erro Orientadas à Resolução**<br/>Incluir exemplo mínimo esperado nos erros de parsing JSON de `cmd_data.py`, `cmd_models.py` e `cmd_features.py`. | #4, #5 | Reduz ciclo de tentativa e erro em configurações JSON. |
| **P1** | `USAB-07` | **Documentação por Jornadas + Schemas JSON + Guia de Interpretação**<br/>Criar `docs/referencia/cli_schemas_json.md` e `docs/guia/03_interpretando_resultados.md`, e reorganizar `docs/README.md` pelas 5 Jornadas. | #5, #10, Fase 5 | Completa as Jornadas 2 e 3 separando uso científico da engenharia interna. |

---

## Escopo de Divisão Incremental Recomendada

- **Marco `M8` / `pos-3-usabilidade-acessibilidade-pesquisador` (Onda Pós-MVP — Foco em CLI, Fachada e Jornadas):**
  Implementar `USAB-01` a `USAB-07` com TDD, validação empírica ponta a ponta por CLI e Python sem acesso a módulos internos, e verificação independente (`author != verifier`).
