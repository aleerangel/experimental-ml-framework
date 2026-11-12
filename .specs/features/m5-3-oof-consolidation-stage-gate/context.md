# Context: m5-3-oof-consolidation-stage-gate

Decisões de produto e arquitetura acordadas com o usuário para a consolidação Out-Of-Fold (OOF) e Portão de Estágio da Etapa 4 (`verify_runs_gate`):

## Decisões Registradas

1. **Tratamento de Falhas Parciais em Modo FAULT_TOLERANT**:
   - **Decisão**: Em caso de falha de um modelo em algumas dobras (ex: 1 de 5 folds com falha em `FAULT_TOLERANT`), a consolidação OOF consolida as observações disponíveis das dobras concluídas e marca as métricas com `MetricStatus.PARTIAL_COVERAGE` e alertas (`HEURISTIC_WARNING`), registrando explicitamente a lista de observações faltantes, permitindo que a Etapa 5 avalie a cobertura parcial sem mascarar nem descartar os dados.
   - **Data**: 2026-11-12
   - **Usuário**: Aprovado via seleção direta

2. **Formato de Arquivo e Localização Canônica das Predições OOF**:
   - **Decisão**: JSON atômico padronizado (`write_json_atomic`) sob o diretório canônico `{run_dir}/oof/oof_{model_id}__{scenario_id}.json`, garantindo conformidade estrita com `XCUT-02` (dependência de runtime exclusivamente em `numpy>=1.24.0`).
   - **Data**: 2026-11-12
   - **Usuário**: Aprovado via seleção direta
