# Processo de Validação e Aceite de Marcos (Milestone Acceptance)

> **Experimental ML Framework**  
> **Status:** Ativo  
> **Data:** 17 de Novembro de 2026  
> **Aplicabilidade:** Retroativo aos marcos M1.1 e M1.2 e obrigatório para os marcos subsequentes (M1.3 a M7 e Pós-MVP).  
> **Documentos Relacionados:** [`ARQUITETURA_E_CONTRATOS.md`](./ARQUITETURA_E_CONTRATOS.md), [`ESPECIFICACAO_REQUISITOS.md`](./ESPECIFICACAO_REQUISITOS.md), [`ETAPA_ATUAL_ENGENHARIA.md`](./ETAPA_ATUAL_ENGENHARIA.md) e `.specs/STATE.md` (AD-002).

---

## 1. Objetivo

Este documento define os critérios e o fluxo para validação e aceite formal de cada marco (*milestone*) do framework.

Em um projeto de pesquisa aplicada, a aprovação de testes unitários ou a conclusão do código-fonte não encerram sozinhas uma entrega. Um marco é considerado aceito quando atende a três condições:
1. **Conformidade com a especificação:** Implementação aderente aos requisitos rastreáveis e às decisões de arquitetura (ADRs).
2. **Verificação automatizada:** Suíte de testes automatizados aprovada no commit avaliado, em árvore de trabalho limpa, com relatório de verificação independente (`author != verifier`).
3. **Aceitação pelo consumidor:** Validação prática de uso por meio das interfaces públicas da biblioteca, demonstrando usabilidade, clareza de diagnósticos e aderência ao fluxo experimental.

---

## 2. Estrutura Documental de Cada Marco

Cada marco mantém três registros em seu diretório sob `.specs/features/<milestone-id>/`:

```text
.specs/features/<milestone-id>/
├── SPEC.md          # 1. Escopo, requisitos e critérios de conclusão
├── ACCEPTANCE.md    # 2. Roteiro de validação para o consumidor da biblioteca
├── RESULTS.md       # 3. Evidências observadas e decisão formal de aceite
├── tasks.md         # Tarefas atômicas e critérios de checagem
├── proofs.md        # Saída dos testes automatizados gerada por check_proofs.py
└── verification.md  # Relatório do verificador independente (author != verifier)
```

### 2.1 `SPEC.md` — Especificação do Marco
- **Função:** Define propósito, escopo, requisitos funcionais e técnicos rastreáveis, exclusões explícitas e critérios de conclusão.
- **Momento:** Produzido e aprovado formalmente na fase Specify antes do início da implementação.
- **Formato:** Requisitos em formato EARS (`CORE-01`, etc.) e registro formal de aprovação (`**Approved**: <data> - user: "<palavras>"`). Vincula os critérios aos requisitos gerais do projeto (`ESPECIFICACAO_REQUISITOS.md` e `ARQUITETURA_E_CONTRATOS.md`).

### 2.2 `ACCEPTANCE.md` — Roteiro de Validação
- **Função:** Guia operacional para que um consumidor da biblioteca valide as funcionalidades entregues utilizando exclusivamente interfaces públicas.
- **Conteúdo:**
  1. Pré-requisitos de ambiente e comandos de instalação ou atualização.
  2. Exemplos executáveis por funcionalidade via terminal ou Python.
  3. Cenário integrado de ponta a ponta representando uma etapa real de um experimento de ML.
  4. Resultado esperado de cada operação e instruções para identificação de falhas.
  5. Classificação dos testes (unidade, integração e validação manual).
- **Momento:** Rascunhado na fase Tasks e finalizado antes do encerramento da fase Execute.

### 2.3 `RESULTS.md` — Registro de Validação e Decisão de Aceite
- **Função:** Registra a validação executada, indicando commit testado, ambiente computacional, evidências coletadas, problemas encontrados e a decisão final.
- **Critério de transparência:** Procedimentos ou testes manuais não executados devem permanecer explicitamente registrados como `PENDENTE`. Não se presume aprovação sem evidência correspondente.
- **Estados da decisão final:**
  - `APROVADO`: Todos os critérios automatizados e manuais foram executados e aprovados sem pendências impeditivas.
  - `APROVADO COM RESSALVAS`: Critérios essenciais atendidos, com ressalvas formalmente documentadas e aceitas.
  - `PENDENTE DE HOMOLOGAÇÃO MANUAL`: Código e testes automatizados aprovados, com homologação manual pendente de execução.
  - `REJEITADO`: Quebras de contrato, falhas em testes ou desvios metodológicos que exigem correção.

---

## 3. Regras do Processo

1. **Especificação prévia:** A implementação de um marco só inicia após a aprovação de `SPEC.md` (ou `spec.md`).
2. **Roteiro de aceitação obrigatório:** Todo marco deve possuir `ACCEPTANCE.md` orientado ao uso por interfaces públicas.
3. **Escopo de teste:** O roteiro contempla testes automatizados da base de código e validação prática pelo consumidor.
4. **Evidências verificáveis:** O encerramento exige `RESULTS.md` com ambiente, commits, comandos executados e saídas observadas.
5. **Separação de níveis de teste:** A documentação distingue:
   - *Testes de unidade:* Verificam funções puras e contratos internos (`pytest tests/unit/`).
   - *Testes de integração e fumaça:* Verificam empacotamento, CLI e interoperabilidade (`pytest tests/test_smoke.py`).
   - *Validação de aceitação:* Verificação do uso da biblioteca por suas interfaces públicas (`ACCEPTANCE.md`).
6. **Registro explícito de pendências:** Validações não executadas devem constar como `PENDENTE`. A conclusão do código não equivale ao aceite do marco.
7. **Rastreabilidade de problemas:** Inconsistências ou falhas encontradas devem ser registradas em `RESULTS.md` com referência ao requisito afetado.
8. **Decisão formal:** Um marco só transita para concluído na documentação geral quando `RESULTS.md` registrar decisão `APROVADO` ou `APROVADO COM RESSALVAS`.
9. **Atualização de estado:** O encerramento do marco exige atualização de `ETAPA_ATUAL_ENGENHARIA.md`, `README.md` e `.specs/STATE.md`.

---

## 4. Integração com o Fluxo TLC Spec-Driven

O processo de aceite integra-se às fases do TLC:

```text
┌─────────────┐       ┌─────────────┐       ┌─────────────┐       ┌────────────────────────┐
│   SPECIFY   │   →   │   DESIGN    │   →   │    TASKS    │   →   │   EXECUTE & ACCEPT     │
│  (SPEC.md)  │       │ (design.md) │       │ (ACCEPTANCE)│       │(proofs.md / RESULTS.md)│
└─────────────┘       └─────────────┘       └─────────────┘       └────────────────────────┘
```

1. **Specify:** Elaboração e aprovação de `SPEC.md`.
2. **Tasks:** Planejamento das tarefas (`tasks.md`), definição dos checks (`C1..CN`) e estruturação inicial de `ACCEPTANCE.md`.
3. **Execute:** Implementação incremental guiada por testes com commits atômicos e geração de `proofs.md`.
4. **Verify e Aceite:**
   - O verificador independente avalia os checks e gera `verification.md`.
   - Executa-se a validação com base em `ACCEPTANCE.md`.
   - Consolida-se `RESULTS.md` com as evidências e a decisão de aceite.
   - O script `validate_verification.py` confirma a presença de `SPEC.md`, `ACCEPTANCE.md` e `RESULTS.md`.

---

## 5. Situação Atual dos Marcos

| Marco | Identificador TLC | Implementação | Testes Automatizados | Verificação TLC | Validação de Aceitação | Decisão de Aceite |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **M1 (M1.1–M1.5)** | `m1-1` a `m1-5` | Concluída | 96/96 Aprovados | Aprovado (`PASS`) | Executada e aprovada | **Aprovado** |
| **M2 (M2.1–M2.5 + `REV-M2`)** | `m2-diagnostics-partitioning`, `m2-2` a `m2-5` | Concluída | 193/193 Aprovados | Aprovado (`PASS`) | Executada e aprovada | **Aprovado** |
| **M3 (M3.1–M3.4)** | `m3-1` a `m3-4` | Concluída | 236/236 Aprovados | Aprovado (`PASS`) | Executada e aprovada | **Aprovado** |
| **M4 (M4.1–M4.4)** | `m4-1` a `m4-4` | Concluída | 348/348 Aprovados | Aprovado (`PASS`) | Executada e aprovada | **Aprovado** |
| **M5 (M5.1–M5.4 + `ACH-M5`)** | `m5-1` a `m5-4` | Concluída | 471/471 Aprovados | Aprovado (`PASS`) | Executada e aprovada | **Aprovado** |
| **M6 (M6.1–M6.4)** | `m6-1` a `m6-4` | Concluída | 548/548 Aprovados | Aprovado (`PASS`) | Executada e aprovada | **Aprovado** |
| **M7 (M7.1–M7.4)** | `m7-1` a `m7-4` | Concluída | 581/581 Aprovados | Aprovado (`PASS`) | Executada e aprovada | **Aprovado** |
| **Pós-MVP (`TA-POS.1`)** | `pos-1-mega-auditoria-mvp` | Concluída | 591/591 Aprovados | Aprovado (`PASS`) | Executada e aprovada | **Aprovado** |
| **Pós-MVP (`TA-POS.2` + Notebooks)** | `pos-2-guia-pesquisador-cookbook`, `pos-2b-notebooks-interativos` | Concluída | 596/596 Aprovados | Aprovado (`PASS`) | Executada e aprovada | **Aprovado** |
| **Pós-MVP (`TA-POS.3`)** | `pos-3-usabilidade-acessibilidade-pesquisador` | Concluída | 598/598 Aprovados | Aprovado (`PASS`) | Executada e aprovada | **Aprovado** |
| **Pós-MVP (`CSV-01..06`)** | `csv-format-configuration` | Concluída | 604/604 Aprovados | Aprovado (`PASS`) | Executada e aprovada | **Aprovado** |
| **Pós-MVP (`EXPL-01..06`)** | `exploratory-features-visualization` | Concluída | 609/609 Aprovados | Sucedida por `AD-026` | Sucedida por `exploratory-visual-redesign` | **Substituído (`AD-026`)** |
| **Pós-MVP (`EXPLR-01..06`)** | `exploratory-visual-redesign` | Concluída | 610/610 Aprovados | Aprovado (`PASS`) | Executada e verificada | **Aprovado** |
| **Pós-MVP (`DIAG-01..03`)** | `sklearn-ensemble-diagnostics` | Concluída | 611/611 Aprovados | Aprovado (`PASS`) | Executada e verificada | **Aprovado** |
| **Estabilização do MVP (`M8`)** | `m8-mvp-stabilization-contract-alignment` | Concluída | 620/620 Aprovados | Aprovado (`PASS`) | Executada e aprovada | **Aprovado** |
| **Intra-Fold e Holdout Final (`M9`)** | `m9-intra-fold-imputation-encoding-holdout` | Concluída (`e372b22`) | 628/628 Aprovados | Aprovado (`PASS`) | Executada e integrada em `main` | **Aprovado** |
| **Visualização Científica e Relatórios (`M10`)** | `m10-scientific-visualization-reporting-redesign` | Concluída (`9a04409`) | 632/632 Aprovados | Aprovado (`PASS`) | Executada e integrada em `main` | **Aprovado** |
| **Treino vs. Teste (`M11.1`)** | `m11-1-train-test-diagnostics` | Verificada (`T1`–`T4`) | 637/637 Aprovados | Aprovado (`PASS`) | Executada (`main`: `9d9f8f3`) | **Aprovado** |
| **KS, *Dataset Shift* e Resíduos (`M11.2`)** | `m11-2-ks-drift-residuals` | Verificada (`T1`–`T4`) | 642/642 Aprovados | Aprovado (`PASS`) | Executada (`main`: `5c01f90`) | **Aprovado** |
| **Caracterização Ampliada (`M11.3`)** | `m11-3-dataset-characterization` | Verificada (`T1`–`T4`) | 647/647 Aprovados | Aprovado (`PASS`) | Executada (`main`: `6a8394f`) | **Aprovado** |
| **Fechamento Onda 1 (`M11.4`)** | `m11-4-wave1-polish` | Verificada (`T1`–`T3`) | 651/651 Aprovados | Aprovado (`PASS`) | Executada (`verification.md: PASS`; `ACCEPTANCE.md` pendente) | **Verificado (Aguardando Aceite)** |
| **Validação Contínua e Externa (`TA-POS.4` / `CA02`)** | [`PLANO_DE_VALIDACAO_DO_MVP.md`](./PLANO_DE_VALIDACAO_DO_MVP.md) / [`REGISTRO_DE_VALIDACAO_DO_MVP.md`](./REGISTRO_DE_VALIDACAO_DO_MVP.md) | Em andamento (Pesquisador) | 651/651 base | — | Em execução contínua em dados reais | **Em Validação** |

