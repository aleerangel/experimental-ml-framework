# Roteiro de Aceitação e Reprodução — Auditoria de Integridade M1 (`m1-integrity-review`)

> **Marco / Atividade:** Auditoria Geral de Integridade do Projeto (M1 — Project Integrity Review)  
> **Escopo:** Avaliação transversal de arquitetura, integração (`core`, `metrics`, `data`, `cli`), qualidade de implementação, estratégia de testes, documentação/rastreabilidade e prontidão para o Marco M2.  
> **Restrição Fundamental:** Zero modificação em `src/`, `tests/`, `pyproject.toml`, `.agent/` e nos artefatos de `m1-1` a `m1-4`.

---

## 1. Pré-requisitos e Verificação do Ambiente

Na raiz do repositório, com o ambiente virtual `.venv` ativo:

```bash
# 1. Verificar interpretador e pacotes instalados
.venv/bin/python -c "import sys, numpy, pytest; print('Python:', sys.version.split()[0], '| NumPy:', numpy.__version__, '| Pytest:', pytest.__version__)"

# 2. Verificar que a suíte de testes original do projeto passa integralmente (81 testes)
.venv/bin/pytest tests/ -v
```

**Resultado esperado:** `Python: 3.12.15`, `81 passed` e código de saída `0`.

---

## 2. Reprodução das Sondas Técnicas da Auditoria (`probes/`)

Cada sonda inspeciona o repositório em modo somente-leitura, utilizando exclusivamente as interfaces públicas e a árvore sintática (`ast`):

```bash
# Passo 1: Sonda de Linha de Base e Integridade Arquitetural (Dimensão A)
.venv/bin/python .specs/features/m1-integrity-review/probes/ast_and_arch_probe.py

# Passo 2: Sonda de Integração entre Módulos core + metrics + data (Dimensão B)
.venv/bin/python .specs/features/m1-integrity-review/probes/integration_probe.py

# Passo 3: Sonda de Qualidade, Casos Extremos, Imutabilidade e Escalabilidade (Dimensão C)
.venv/bin/python .specs/features/m1-integrity-review/probes/quality_and_perf_probe.py

# Passo 4: Sonda de Cobertura, Mutações Isoladas e Validadores TLC (Dimensão D)
.venv/bin/python .specs/features/m1-integrity-review/probes/testing_and_tlc_probe.py

# Passo 5: Sonda de Documentação, Exemplos do README e Rastreabilidade (Dimensão E)
.venv/bin/python .specs/features/m1-integrity-review/probes/docs_and_traceability_probe.py
```

---

## 3. Verificação Automatizada dos 48 Critérios da Especificação (`C1` a `C48`)

Para comprovar mecanicamente que todos os 48 critérios (`AUD-01..04`, `ARCH-01..07`, `INT-01..08`, `QUAL-01..06`, `TEST-01..08`, `DOC-01..07`, `READY-01..08`) foram avaliados, que os 8 entregáveis existem e que nenhum arquivo do projeto foi modificado:

```bash
.venv/bin/pytest .specs/features/m1-integrity-review/probes/test_audit_checks.py -v
```

**Resultado esperado:** `48 passed` com código de saída `0`.

---

## 4. Comprovação de Não Interferência (Invariante `AUD-02`)

```bash
git diff 6acf6f8 -- src tests pyproject.toml .agent \
  .specs/features/m1-1-setup-cli-smoke \
  .specs/features/m1-2-core \
  .specs/features/m1-3-metrics \
  .specs/features/m1-4-datasets-schemas
```

**Resultado esperado:** saída vazia (`0` linhas alteradas).

---

## 5. Inspeção dos 8 Entregáveis da Auditoria

| # | Entregável | Caminho | Critério de Aceite |
| :--- | :--- | :--- | :--- |
| **0** | Linha de Base e Não Interferência | `.specs/features/m1-integrity-review/reports/00-baseline.md` | Registra commit base `6acf6f8`, versões e diff vazio ao final. |
| **1** | Especificação e Critérios da Auditoria | `.specs/features/m1-integrity-review/reports/01-especificacao-criterios.md` | Lista os 48 critérios, taxonomia de achados e regra mecânica do parecer. |
| **2** | Relatório de Integridade Arquitetural | `.specs/features/m1-integrity-review/reports/02-arquitetura.md` | Grafo AST completo, checagem ADR-008, duplicidades e comparação doc vs API. |
| **3** | Relatório de Integração entre Módulos | `.specs/features/m1-integrity-review/reports/03-integracao.md` | Fluxo ponta a ponta `data -> metrics -> core`, hashes, dtypes e determinismo. |
| **4** | Relatório de Qualidade e Estratégia de Testes | `.specs/features/m1-integrity-review/reports/04-qualidade-e-testes.md` | Cobertura por linha, $\ge 12$ mutações em `/tmp`, benchmark 10k/100k e validadores TLC. |
| **5** | Matriz de Conformidade e Rastreabilidade | `.specs/features/m1-integrity-review/reports/05-rastreabilidade.md` | Execução dos blocos do `README.md`, árvore de diretórios, símbolos e matriz `RF/RNF/CA/TA`. |
| **6** | Registro Consolidado de Achados e Riscos | `.specs/features/m1-integrity-review/reports/06-achados.md` | Achados `AUD-F-NNN` classificados por categoria e severidade com evidência e impacto. |
| **7** | Plano de Correções Priorizadas | `.specs/features/m1-integrity-review/reports/07-plano-correcoes.md` | Ordenação priorizada de ações recomendadas antes e durante o Marco M2. |
| **8** | Parecer Final de Prontidão para o M2 | `.specs/features/m1-integrity-review/reports/08-parecer.md` | Veredito formal (`APTO`, `APTO COM RESSALVAS` ou `NÃO APTO`) e verificação independente. |
