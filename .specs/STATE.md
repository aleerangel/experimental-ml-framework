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
- **Phase / Task**: EXECUTE concluído com 100% dos testes e verificações mecânicas aprovados
- **Completed**: m1-1-setup-cli-smoke (concluído); m1-2-core (SPECIFY, TASKS e EXECUTE concluídos com 18 checks C1..C18 validados)
- **In-progress**: none
- **Next step**: Validação final pelo usuário / commit do marco M1.2
- **Blockers**: none
- **Uncommitted files**: pyproject.toml, src/experimental_ml/core/, tests/unit/test_core.py, .specs/features/m1-2-core/
- **Branch**: feat/m1-2-core
