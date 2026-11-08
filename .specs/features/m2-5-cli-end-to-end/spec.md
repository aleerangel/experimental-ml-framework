# M2.5 — CLI `data` & `partition` and End-to-End Acceptance (m2-5-cli-end-to-end) Specification

**Approved**: 2026-11-07 - user: "aprovada"

## Problem Statement

As Etapas 1 (Engenharia de Dados e Diagnóstico) e 4A (Particionamento e Validação) foram implementadas através de módulos funcionais desacoplados (`data`, `validation`, `stages`, `core`). No entanto, o pesquisador necessita de uma interface de linha de comando (`expml`) unificada, ergonômica e padronizada para operar as etapas sequenciais do pipeline de dados, inspecionar achados diagnósticos, aprovar regras de saneamento e construir planos de particionamento reprodutíveis (conforme ARQUITETURA §2.4, §7 e requisitos `CLI-01` a `CLI-12`).

A ausência de uma camada de orquestração via CLI acarreta as seguintes lacunas:
1. **Falta de Interface Unificada de Execução**: Impossibilidade de executar as etapas de perfilamento (`data profile`), saneamento (`data sanitize`), particionamento (`partition build`) e auditoria de integridade (`partition verify`) via terminal.
2. **Poluição de Saída e Vazamento de Hashes**: Sem uma camada de apresentação focada no pesquisador, erros podem vazar tracebacks complexos ou exibir hashes criptográficos em `stdout`/`stderr`, violando os princípios de usabilidade e segurança (`CLI-06`, `CLI-11`).
3. **Ausência de Padronização de Códigos de Saída**: O framework requer códigos de saída determinísticos: código `0` para sucesso (e `--help`/sem argumentos), código `2` para erros de configuração, validação, precondições de etapa ou divergência de dados (sem traceback), e código `1` para falhas sistêmicas inesperadas (`CLI-06`, `CLI-09`).
4. **Acoplamento Indevido na Camada CLI**: Risco de comandos de terminal introduzirem cálculos numéricos ou computações de hash diretamente nos manipuladores de argumentos (`CLI-10`).
5. **Falta de Homologação Ponta a Ponta**: Ausência de um cenário de aceitação integrando toda a cadeia de ponta a ponta por subprocesso executado sobre o executável instalado (`CLI-12`).

O Sub-marco M2.5 resolve essas demandas implementando os subcomandos `expml data` e `expml partition`, o despachante hierárquico com tratamento robusto de erros e a homologação formal fim a fim que fecha o Marco M2.

## Out of Scope

Explicitamente excluído para manter isolamento e controle de escopo:

| Feature | Reason |
| --- | --- |
| Subcomandos `expml model ...` e `expml experiment ...` | Pertencem às Etapas 4B e 5 nos Marcos M5 e M6 |
| Flags de atributos diretamente na CLI sem arquivo de schema/config | Decisão D3: configurações complexas e schemas são declarados exclusivamente via arquivos JSON |
| Inferência heurística automática de regras de saneamento sem aprovação | Decisão D4: toda regra estrutural deve ser declarada e versionada em arquivo pelo pesquisador |
| Dependência de bibliotecas de CLI de terceiros (e.g. `click`, `typer`) | RNF01: uso exclusivo do módulo padrão `argparse` |

---

## Assumptions & Open Questions

As premissas baseiam-se nos requisitos `CLI-01` a `CLI-12`, nas decisões D3, D4, D6, D10 do Marco M2 e nas diretrizes arquiteturais de governança:

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| D3: Entrada declarativa por arquivo | `data profile --data PATH --schema SCHEMA.json --output-dir DIR`; demais subcomandos recebem `--experiment-dir` | Evita proliferação de dezenas de flags de linha de comando para tipos, alvos e colunas | y |
| D4: Autoria e aprovação de regras | `data sanitize --experiment-dir DIR --rules RULES.json` cria o plano e, se `READY`, grava artefatos; se `INCOMPLETE`, recusa gravação e encerra com código `2` | CA-E1-02 proíbe persistir `preparation_plan.json` em estado incompleto | y |
| D10: Proteção contra sobrescrita | Comandos recusam sobrescrever artefatos existentes e encerram com código `2`, exceto se a flag `--force` for explicitada | Preserva rastreabilidade e histórico dos experimentos | y |
| CLI-06: Códigos de saída e tracebacks | Sucesso: `0`; Erros de domínio (`ExperimentalMLError`), argumentos inválidos, precondição de etapa violada: `2` (mensagem instrutiva sem traceback); Falha inesperada: `1` | Ergonomia de terminal e tratamento limpo de exceções | y |
| CLI-10: Pureza da Camada CLI | Módulos sob `experimental_ml.cli` não importam `numpy` nem `hashlib`, delegando toda a lógica para `core`, `data`, `validation` e `stages` | Garante isolamento estrito de responsabilidades arquiteturais | y |
| CLI-11: Ocultação de Hashes | A saída padrão (`stdout`) e de erro (`stderr`) nunca exibe digests ou hashes criptográficos | Mantém a saída orientada ao domínio do usuário e amigável para leitura humana | y |

**Open questions:** none - todos os contratos, argumentos e saídas foram consolidados no Marco M2.

---

## User Stories

### P1: M2.5 — CLI Modular de Dados e Particionamento ⭐ MVP

**User Story**: Como pesquisador, quero executar o diagnóstico de dados, a aplicação de regras de saneamento e a geração e verificação de partições diretamente pelo terminal via `expml`, recebendo saídas instrutivas e códigos de erro sem tracebacks para operar o pipeline de dados.

**Why P1**: Atende aos requisitos `CLI-01` a `CLI-12`, fechando o Marco M2 e viabilizando a homologação prática do pipeline de dados.

**Acceptance Criteria**:

1. WHEN `expml data profile --data PATH --schema SCHEMA.json --output-dir DIR` is run on a valid dataset THEN the system SHALL write `data/dataset_descriptor.json` and `data/dataset_profile.json`, print the dimensions and the findings with code, column and message, and exit with code 0 (CLI-01).
2. WHEN `expml data sanitize --experiment-dir DIR --rules RULES.json` is run and the plan is `READY` THEN the system SHALL write `configuration/preparation_plan.json` and `data/sanitized_view.json`, print a summary of applied rules, and exit with code 0 (CLI-02).
3. IF the plan is `INCOMPLETE` THEN the system SHALL NOT write `configuration/preparation_plan.json`, SHALL print each unresolved `CONFIRMED_ISSUE` with its code and column, and SHALL exit with code 2 (CLI-03).
4. WHEN `expml partition build --experiment-dir DIR --config CONFIG.json [--seed N]` is run on a sanitized experiment THEN the system SHALL write `partitions/partition_plan.json`, `partitions/splits.csv.gz` and `partitions/splits.schema.json`, print the regime, strategy and per-fold sizes, and exit with code 0 (CLI-04).
5. WHEN `expml partition verify --experiment-dir DIR` is run THEN the system SHALL validate the stage gates and partition invariants, exit with code 0 when all invariants hold and exit with code 2 with a natural-language message otherwise (CLI-05).
6. IF an `ExperimentalMLError`, an invalid argument, an unmet stage precondition or a hash divergence occurs THEN the system SHALL print an instructive message without a traceback and exit with code 2, and IF an unexpected failure occurs THEN the system SHALL exit with code 1 (CLI-06).
7. WHILE a required upstream artifact is missing, not `READY` or inconsistent the system SHALL refuse `partition build` and `partition verify`, exit with code 2 and write no partition artifact (CLI-07).
8. IF an output artifact already exists and `--force` is absent THEN the system SHALL exit with code 2 without modifying it (CLI-08).
9. The system SHALL preserve the M1.1 behavior of `expml` (`--version`, `--help`, no arguments exits with code 0, invalid option exits with code 2) and SHALL expose `--help` for every new subcommand (CLI-09).
10. The CLI command modules SHALL contain no numerical or business logic, importing neither `numpy` nor `hashlib` and calling only public functions of `data`, `validation`, `stages` and `core` (CLI-10).
11. The system SHALL never print a hash digest in the standard output or standard error of any subcommand (CLI-11).
12. WHEN the end-to-end sequence profile, sanitize, partition build and partition verify is run through the installed `expml` entry point on the synthetic acceptance fixture in two separate directories THEN the system SHALL exit with code 0 at every step and produce identical `partition_plan.json` bytes and identical decompressed `splits.csv.gz` content (CLI-12).

---

## Requirement Traceability

| Requirement ID | Description | Source / Rationale | Status |
| :--- | :--- | :--- | :--- |
| CLI-01 | Comando `expml data profile` com escrita de descritor e perfil e saída instrutiva | RF1.1, CA-E1-01 | proposed |
| CLI-02 | Comando `expml data sanitize` com plano READY e escrita de visão saneada | RF1.6, CA-E1-02 | proposed |
| CLI-03 | Bloqueio de plano INCOMPLETE em `expml data sanitize` com código 2 e sem gravação | CA-E1-02, D4 | proposed |
| CLI-04 | Comando `expml partition build` com geração de plano, splits comprimidos e esquema | RF4.1, CA-E4A-01 | proposed |
| CLI-05 | Comando `expml partition verify` com verificação de invariantes e saída instrutiva | CA-E4A-01, CA-E4A-02 | proposed |
| CLI-06 | Códigos de saída padronizados (0, 1, 2) e supressão de tracebacks em erros de domínio | RNF07, D10 | proposed |
| CLI-07 | Bloqueio de subcomandos quando artefatos a montante estão ausentes ou inconsistentes | CA-GER-01, STORE-05 | proposed |
| CLI-08 | Proteção de sobrescrita com código 2 a menos que `--force` seja fornecido | D10, STORE-07 | proposed |
| CLI-09 | Preservação de compatibilidade com CLI base M1.1 (`--version`, `--help`, sem args) | RNF05, M1.1 | proposed |
| CLI-10 | Pureza arquitetural da camada CLI sem importação de `numpy` ou `hashlib` | XCUT-01, ADR-002 | proposed |
| CLI-11 | Ocultação de hashes criptográficos na saída padrão e de erro | RNF04, Usabilidade | proposed |
| CLI-12 | Homologação fim a fim por subprocesso com reprodutibilidade determinística de bytes | CA-E4A-02, D8 | proposed |
