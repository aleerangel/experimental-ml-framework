# m3-4-cli-end-to-end verification

**Verdict**: PASS
**Proofs**: `proofs.md` at e418c20
**Verifier**: independent sub-agent (author != verifier)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/unit/cli/test_cmd_features.py` `test_feat_01_features_help` | yes |
| C2 | `tests/unit/cli/test_cmd_features.py` `test_feat_02_features_explore_success` | yes |
| C3 | `tests/unit/cli/test_cmd_features.py` `test_feat_03_features_explore_overwrite_protection` | yes |
| C4 | `tests/unit/cli/test_cmd_features.py` `test_feat_04_features_scenarios_success` | yes |
| C5 | `tests/unit/cli/test_cmd_features.py` `test_feat_05_features_scenarios_rejection` | yes |
| C6 | `tests/unit/cli/test_cmd_features.py` `test_feat_06_features_verify_gate` | yes |
| C7 | `tests/unit/cli/test_cmd_features.py` `test_feat_07_cli_purity` | yes |
| C8 | `tests/integration/features/test_features_cli_integration.py` `test_feat_08_end_to_end_cli_pipeline` | yes |

## Own examples

Eight boundary, malformed input, missing directory, protected column leakage, and dictionary schema edge cases were independently executed and evaluated at `HEAD` (`e418c20`):

1. **Diretório de experimento inexistente em `explore`, `scenarios` e `verify`**:
   - Invocados `expml features explore`, `expml features scenarios` e `expml features verify` apontando `--experiment-dir /caminho/inexistente`.
   - Constatado retorno uniforme de código `2`, mensagem limpa no `stderr` (`Error: Experiment directory not found at '...'`) e ausência de traceback Python não tratado.

2. **Verificação de portão em diretório existente porém vazio (`verify`)**:
   - Invocado `expml features verify` em diretório vazio recém-criado.
   - Constatado que a reconstrução do portão detecta a ausência de descritor de dados antes de carregar visão sanitizada, falhando deterministicamente com código `2` (`Error: Dataset descriptor missing at '...'`).

3. **Arquivo de cenários inexistente (`scenarios`)**:
   - Invocado `expml features scenarios` com `--scenarios /caminho/ausente.json`.
   - Constatado retorno com código `2` e mensagem explicativa (`Error: Scenarios file not found at '...'`).

4. **Arquivo de cenários com formato JSON inválido (nem lista nem dicionário com chave `scenarios`)**:
   - Fornecido arquivo contendo apenas string primitiva JSON (`"just a string"`).
   - Constatado que `handle_features_scenarios` rejeita a estrutura com código `2` e mensagem clara: `Error: Scenarios file must contain a JSON list of scenario objects or a dictionary with 'scenarios' key`.

5. **Suporte a formato de dicionário encapsulado `{"scenarios": [...]}`**:
   - Fornecido arquivo JSON de cenários estruturado como dicionário contendo chave raiz `scenarios`.
   - Constatado parsing correto, validação contra a visão saneada, salvamento atômico em `configuration/scenarios.json` e término com código `0`.

6. **Rejeição de identificadores de cenário duplicados**:
   - Submetido arquivo com dois cenários compartilhando o mesmo `scenario_id: "dup"`.
   - Constatado que o validador de catálogo detecta a duplicidade, emitindo `Error: Duplicate scenario_id detected: 'dup'` com código `2`.

7. **Vazamento de coluna alvo (`target leakage`) em cenário de features**:
   - Submetido cenário `FIXED` incluindo explicitamente a coluna alvo `target` no conjunto `selected_features`.
   - Constatado bloqueio rigoroso com código `2` e mensagem explicativa: `Error: Fixed scenario 'leak' includes protected column 'target' (intersecting with target, group, observation_id, time, or ignore columns).`.

8. **Inclusão indevida de coluna de identificador de observação (`observation_id_col`)**:
   - Submetido cenário `FIXED` contendo o identificador de observação `id` nos preditores selecionados.
   - Constatado bloqueio imediato com código `2` impedindo vazamento de metadados de rastreabilidade para o espaço preditivo.

## Findings

None - all 8 checks formally prove their acceptance criteria, pure CLI architecture guarantees isolation without numpy/hashlib transitives in clean processes, and stage gates strictly guard Stage 2 configuration and reporting artifacts.
