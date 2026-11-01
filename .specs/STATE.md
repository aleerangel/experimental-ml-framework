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

- **Feature**: m1-2-core (.specs/features/m1-2-core)
- **Phase / Task**: SPECIFY concluído / Aguardando aprovação do usuário
- **Completed**: m1-1-setup-cli-smoke (concluído); m1-2-core (SPECIFY elaborado e validado)
- **In-progress**: none
- **Next step**: Aguardar aprovação humana de spec.md antes de avançar para a fase TASKS
- **Blockers**: none
- **Uncommitted files**: .specs/features/m1-2-core/spec.md, .specs/STATE.md
- **Branch**: feat/m1-2-core
