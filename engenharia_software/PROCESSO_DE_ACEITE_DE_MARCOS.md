# Processo de Validação e Aceite de Marcos (Milestone Acceptance)

> **Experimental ML Framework**  
> **Status:** Ativo  
> **Data:** 02 de Novembro de 2026  
> **Aplicabilidade:** Retroativo aos marcos M1.1 e M1.2 e obrigatório para os marcos subsequentes (M1.3 a M7).  
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
| **M1.1** | `m1-1-setup-cli-smoke` | Concluída (`0840603`) | 12/12 Aprovados | Aprovado | Executada e aprovada conforme roteiro | **Aprovado** |
| **M1.2** | `m1-2-core` | Concluída (`479ee8d`) | 18/18 Aprovados (30/30 total) | Aprovado (`PASS`) | Roteiro documentado; validação manual pendente | **Pendente de homologação manual** |
| **M1.3** | `m1-3-metrics` | Não iniciada | Pendente | Pendente | Pendente | **Não Iniciado** |
| **M2 a M7**| — | Planejados | Pendente | Pendente | Pendente | **Planejado** |

