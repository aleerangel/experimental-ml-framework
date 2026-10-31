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
- **Phase / Task**: EXECUTE concluído (T1 a T5 finalizados) / Aguardando revisão do usuário
- **Completed**: T1, T2, T3, T4, T5 (12/12 checks aprovados)
- **In-progress**: none
- **Next step**: Apresentar os resultados ao usuário e aguardar autorização de commit/merge
- **Blockers**: none
- **Uncommitted files**: pyproject.toml, src/, tests/, .specs/features/m1-1-setup-cli-smoke/tasks.md, .specs/STATE.md, .specs/features/m1-1-setup-cli-smoke/proofs.md
- **Branch**: chore/tlc-adoption-review
