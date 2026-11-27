# Resultados de Homologação — Marco M8: Estabilização do MVP e Alinhamento Contratual

- **Marco:** `M8` (`m8-mvp-stabilization-contract-alignment`)
- **Branch:** `feat/m8-stabilization`
- **Status:** `APROVADO` (Verificado com `PASS` e homologado pelo desenvolvedor em 2026-11-27)
- **Decisão:** `APROVADO`

---

## 1. Evidências Automatizadas e Verificação Independente

- **Suíte completa de testes:** `620 passed` em `.venv/bin/pytest tests/ -q`.
- **Provas TLC (`proofs.md`):** `8 pass, 0 fail` (`Build` + `C1`–`C7`) executadas sobre `HEAD a18cb82` (com `docs/referencia/api_python.md` pré-existente modificado no workspace).
- **Verificação Independente (`verification.md`):** Veredito **`PASS`**, `Findings: none`, confirmando conformidade integral com `D1` (`AD-028` / `ADR-003`) e `D2` (`AD-029`).

## 2. Tarefas Executadas e Commits Atômicos (`feat/m8-stabilization`)

| Tarefa | Commit | Descrição |
| :--- | :--- | :--- |
| **T1** | `6b6806b` | `fix(reporting): povoar tabelas A e G com dados reais do perfil e celulas` |
| **T2** | `a1e3f34` | `fix(features): filtrar None e NaN em estatisticas categoricas` |
| **T3** | `c1ade82` | `fix(orchestration): normalizar nomes de celulas, hashes e lock` |
| **T4** | `a8290b6` | `fix(tuning): isolar selecao dinamica e split_inner_folds no Nested CV` |
| **T5** | `d4619b6` | `fix(pipeline): persistir artefatos completos e propagar seed` |
| **T6** | `57ab6f3` | `fix(statistics): ativar Kuncheva real e pareto multiobjetivo na CLI` |
| **T7** | `a18cb82` | `fix(cli): adicionar segundo baseline em classificacao e script TLC` |

## 3. Validação Manual pelo Consumidor (`ACCEPTANCE.md`)

- **Estado:** `PENDENTE` — executar os Passos 1 e 2 de `ACCEPTANCE.md` antes do merge de `feat/m8-stabilization` em `main`.
