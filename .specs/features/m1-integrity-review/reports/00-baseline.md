# Protocolo e Linha de Base da Auditoria M1 (`00-baseline.md`)

**Atividade:** Auditoria Geral de Integridade do Projeto (M1 — Project Integrity Review)  
**Natureza:** Auditoria estritamente somente-leitura de diagnóstico, verificação e conformidade (sem alterações em código-fonte, suíte de testes existente, configuração de pacotes ou registros históricos de M1.1–M1.4).  
**Branch dedicada:** `audit/m1-integrity-review`  
**Commit base (`main`):** `6acf6f8e5d478cbc08bb29ef22ac1da267b56feb` (`docs: atualizar documentacao geral apos conclusao e merge do marco m1-4`)

---

## 1. Linha de Base Capturada (`AUD-01`)

A linha de base foi coletada antes da execução das sondas dimensionais por meio do script [ast_and_arch_probe.py](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/probes/ast_and_arch_probe.py) e da suíte de testes de projeto:

| Parâmetro de Linha de Base | Valor Verificado | Comando de Evidência |
| :--- | :--- | :--- |
| Commit base da branch `main` | `6acf6f8e5d478cbc08bb29ef22ac1da267b56feb` | `git rev-parse main` |
| Interpretador Python (`.venv`) | `Python 3.12.15` | `.venv/bin/python --version` |
| Versão do NumPy (`.venv`) | `2.5.4` | `.venv/bin/python -c "import numpy; print(numpy.__version__)"` |
| Versão do Pytest (`.venv`) | `9.2.0` | `.venv/bin/python -c "import pytest; print(pytest.__version__)"` |
| Interpretadores instalados no host | `/usr/bin/python3.12` (`3.12.15`), `/usr/bin/python3.14` (`3.14.0`, sem `numpy`/`pytest`); `python3.10` e `python3.11` ausentes | `which python3.10 python3.11 python3.12 python3.13 python3.14` |
| Resultado da suíte de testes existente | `81 passed in 0.25s` (12 smoke + 18 core + 22 metrics + 29 data) | `.venv/bin/pytest tests/ -v --tb=short` |

---

## 2. Escopo Estrito de Escrita e Garantia de Não Interferência (`AUD-02`, `AUD-04`)

1. **Diretório exclusivo de artefatos da auditoria:** `.specs/features/m1-integrity-review/` (contendo `spec.md`, `SPEC.md`, `design.md`, `tasks.md`, `ACCEPTANCE.md`, `RESULTS.md`, `proofs.md`, `verification.md`, `probes/*.py` e `reports/00-baseline.md` .. `08-parecer.md`).
2. **Isolamento de sondas efêmeras (`AUD-04`):** Testes de mutação manual (`TEST-03`) e execuções de validadores que escrevem artefatos (`check_proofs.py` sobre M1.1–M1.4 em `TEST-08`) operam exclusivamente sobre cópias efêmeras em `/tmp/m1-audit-*`, removidas imediatamente após a coleta das saídas.
3. **Verificação contínua de não interferência (`AUD-02`):** Ao final de cada tarefa e no encerramento da auditoria, o comando abaixo deve retornar saída vazia (0 bytes):
   ```bash
   git diff 6acf6f8e5d478cbc08bb29ef22ac1da267b56feb -- src/ tests/ pyproject.toml README.md engenharia_software/ .agent/ .specs/features/m1-1-setup-cli-smoke/ .specs/features/m1-2-core/ .specs/features/m1-3-metrics/ .specs/features/m1-4-datasets-schemas/
   ```
   **Estado verificado:** `0` bytes de diferença em todos os caminhos protegidos.

---

## 3. Taxonomia de Achados e Regra de Decisão (`AUD-03`, `READY-07`)

Todo achado registrado em [06-achados.md](file:///home/alexandrerangel/Projetos/iniciacao_cientifica/experimental-ml-framework/.specs/features/m1-integrity-review/reports/06-achados.md) recebe identificador `AUD-F-NNN`, dimensão (`ARCH`, `INT`, `QUAL`, `TEST`, `DOC`, `READY`), categoria (`DEFEITO`, `RISCO`, `MELHORIA`, `LIMITAÇÃO DOCUMENTADA`), severidade (`CRÍTICO`, `ALTO`, `MODERADO`, `BAIXO`), evidência reprodutível (`caminho:linha` ou comando + saída), análise de impacto e recomendação de encaminhamento.
