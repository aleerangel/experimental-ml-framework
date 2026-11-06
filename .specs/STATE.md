# STATE

## Decisions

### AD-001
- **Decision**: Adotar Hatchling (`hatchling.build`) como build-backend padronizado no `pyproject.toml` e layout `src/experimental_ml/`.
- **Reason**: Backend moderno em conformidade com PEP 517/518/621, suporte nativo ao layout `src/` e empacotamento enxuto sem dependências de compilação C/C++.
- **Trade-off**: Exige ferramentas de empacotamento compatíveis com padrões modernos (PEP 621), sem suporte nativo a extensões C legadas de `setuptools`.
- **Scope**: Todo o framework `experimental-ml-framework`.
- **Date**: 2026-10-31
- **Status**: active

### AD-002
- **Decision**: Adotar o processo de aceite de marcos (*Milestone Acceptance*) baseado em três registros (`SPEC.md`, `ACCEPTANCE.md`, `RESULTS.md`), integrado ao fluxo TLC Spec-Driven.
- **Reason**: Diferenciar a aprovação em testes automatizados do aceite formal da entrega, prevendo validação prática por interfaces públicas sob a perspectiva do consumidor e registro explícito de pendências.
- **Trade-off**: Requer a elaboração e manutenção de três documentos por marco (`SPEC.md`, `ACCEPTANCE.md`, `RESULTS.md`), mantendo pendências manuais registradas explicitamente como PENDENTE.
- **Scope**: Todos os marcos do framework (retroativo a M1.1 e M1.2; mandatório de M1.3 a M7).
- **Date**: 2026-11-02
- **Status**: active

### AD-003
- **Decision**: Decomposição modular do Marco M2 em 5 sub-marcos controláveis (M2.1 a M2.5) e catálogo canônico fechado de 15 achados diagnósticos com severidade imutável e ordenação lexicográfica determinística.
- **Reason**: Garantir isolamento conceitual e controle granular de escopo entre triagem/diagnóstico (`m2-1`), saneamento determinístico (`m2-2`), particionamento compartilhado (`m2-3`), CLI modularizada (`m2-4`) e integração transversal (`m2-5`), evitando acoplamento indevido entre camadas.
- **Trade-off**: Requer manutenção de contratos explícitos entre as sub-etapas (ex.: `SanitizedDatasetView` recebida por `validation` sem expor lógica interna de sanitização).
- **Scope**: Marco M2 e módulos `experimental_ml.data` e `experimental_ml.validation`.
- **Date**: 2026-11-06
- **Status**: active

## Handoff

- **Feature**: m2-diagnostics-partitioning (Sub-marco M2.1 — Triagem Estatística e Diagnóstico Estrutural de Datasets)
- **Phase / Task**: Concluído e Aceito (Branch `feat/m2-1-dataset-profiling`)
- **Completed**:
  - Especificação e design do Marco M2 consolidados e aprovados com 12 decisões formais (D1 a D12).
  - Sub-marco M2.1 (`m2-1-dataset-profiling`) implementado, testado e verificado:
    - `ProfileConfig`: configuração de limiares com validação no construtor.
    - `ColumnProfile` e `DatasetProfile`: estruturas de perfil imutáveis com `slots`.
    - Distribuições numéricas completas (média, mediana, desvio padrão, min, max, quartis, IQR, skewness, outliers $1.5 \times \text{IQR}$) e categóricas (frequências e proporções).
    - Análise da variável-alvo: variância zero, ausentes, contagem de classes e detecção de alvos binários não mapeados para $\{0,1\}$ (`E1_TARGET_BINARY_UNMAPPED`).
    - Análise de agrupamento (`group_col`): grupos ausentes (`E1_GROUP_EMPTY_VALUES`) e grupos com poucas amostras (`W1_GROUP_TOO_FEW_SAMPLES`).
    - Detecção determinística de duplicatas (excluindo apenas `observation_id`).
    - Catálogo canônico fechado de 15 achados diagnósticos (8 `CONFIRMED_ISSUE` + 7 `HEURISTIC_WARNING`) com severidade imutável e ordenação canônica determinística por severidade, código do achado e coluna.
    - Função pura `profile_dataset(bundle, config)` exposta em `experimental_ml.data` (17 símbolos públicos em `__all__`), mantendo imutabilidade física e invariância do `dataset_hash`.
  - 12 requisitos de profiling (`PROF-01` a `PROF-12`) verificados por 12 checks determinísticos (`check_proofs.py`: 12 pass, 0 fail).
  - Suíte completa do repositório: 114 testes aprovados (100% de aprovação).
  - Verificação independente pelo subagente verificador (`author != verifier`) aprovada com veredito `PASS` (0 findings).
  - Portões TLC validados: `validate_spec.py`, `validate_tasks.py`, `validate_verification.py` todos com 0 erros e 0 alertas.
  - Roteiro de homologação do consumidor (`ACCEPTANCE.md`) executado com sucesso e registrado em `RESULTS.md`.
- **In-progress**: Sub-marco M2.1 concluído; pronto para avançar para o Sub-marco M2.2 (`preparation-plan-sanitization`)
- **Next step**: Iniciar o Design e Tasks do Sub-marco M2.2 (`create_preparation_plan`, `sanitize_dataset`, `SanitizedDatasetView`)
- **Blockers**: none
- **Branch**: feat/m2-1-dataset-profiling
