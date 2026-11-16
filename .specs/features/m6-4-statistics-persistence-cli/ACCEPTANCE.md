# Guia de Aceite do Consumidor — Marco M6.4 (Persistência, Portão de Estágio e CLI `expml stats`)

> **Documento de Aceite (ACCEPTANCE.md)**  
> **Identificador do Marco:** M6.4 (`m6-4-statistics-persistence-cli`)  
> **Público-alvo:** Pesquisador / Usuário consumidor da API Python e da CLI `expml stats`

---

## 1. Interfaces Públicas Validadas

- **Persistência (`experimental_ml.statistics`)**: `save_statistics_artifacts`, `load_statistics_artifacts`, `LoadedStatisticsArtifacts`.
- **Portão de Estágio (`experimental_ml.stages.stage_gates`)**: `verify_statistics_gate`.
- **Interface de Terminal (`expml stats`)**: `expml stats run`, `expml stats status`, `expml stats verify`.

---

## 2. Roteiro de Validação sob a Perspectiva do Consumidor

1. **Executar Consolidação e Comparação Estatística via CLI**:
   ```bash
   expml stats run --experiment-dir <dir> [--config comparison_spec.json] [--force]
   ```
   *Resultado esperado:* Executa Stage 5 completo (5A $\to$ 5B $\to$ Pareto $\to$ 5C), grava atomicamente todos os artefatos em `<dir>/statistics/`, suprime hashes brutos no stdout e retorna código `0`.

2. **Inspecionar Status Somente-Leitura**:
   ```bash
   expml stats status --experiment-dir <dir>
   ```
   *Resultado esperado:* Exibe configurações consolidadas, comparações executadas/ignoradas, líder observado e status de evidência estatística, retornando `0` (ou `2` se ausente).

3. **Auditar Integridade do Portão Stage 5**:
   ```bash
   expml stats verify --experiment-dir <dir>
   ```
   *Resultado esperado:* Executa `verify_statistics_gate`, validando portões upstream e linhagem de `partition_plan_id`, retornando `0` se íntegro ou `2` sem traceback em caso de falha.
