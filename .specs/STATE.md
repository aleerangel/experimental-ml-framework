# STATE

## Decisions

### AD-001
- **Decision**: Adotar Hatchling (`hatchling.build`) como build-backend padronizado no `pyproject.toml` e layout `src/experimental_ml/`.
- **Reason**: Backend moderno em conformidade com PEP 517/518/621, suporte nativo ao layout `src/` e empacotamento enxuto sem dependências de compilação C/C++.
- **Trade-off**: Exige ferramentas de empacotamento compatíveis com padrões modernos (PEP 621), sem suporte nativo a extensões C legadas de `setuptools`.
- **Scope**: Todo o framework `experimental-ml-framework`.
- **Date**: 2026-10-31
- **Status**: active

## Handoff

- **Feature**: m1-1-setup-cli-smoke (.specs/features/m1-1-setup-cli-smoke)
- **Phase / Task**: Tasks review / Aguardando aprovação do usuário para EXECUTE
- **Completed**: SPECIFY, TASKS
- **In-progress**: none
- **Next step**: Aguardar aprovação humana de tasks.md antes de iniciar a execução da Feature m1-1-setup-cli-smoke
- **Blockers**: none
- **Uncommitted files**: .specs/features/m1-1-setup-cli-smoke/spec.md, .specs/features/m1-1-setup-cli-smoke/tasks.md, .specs/STATE.md
- **Branch**: chore/tlc-adoption-review
