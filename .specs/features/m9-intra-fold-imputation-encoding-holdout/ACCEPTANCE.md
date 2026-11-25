# Roteiro de Aceite — Marco M9: Imputação/Codificação Intra-Fold e Holdout Final

- **Marco:** `M9` (`m9-intra-fold-imputation-encoding-holdout`)
- **Status do Marco:** Proposta Preliminar (Fase TLC: **Specify** — aguardando resolução das decisões D1, D2 e D3 pelo desenvolvedor)

---

## Passos Planejados de Validação pelo Consumidor

1. **Validação de Imputação e Encoding Intra-Fold (`DEFER_INTRA_FOLD`):**
   - Perfilar um dataset contendo `NaN` em colunas numéricas e uma coluna categórica em texto.
   - Configurar `prep_rules.json` com `kind: "DEFER_INTRA_FOLD"` e `imputation_strategy: "MEDIAN"`.
   - Executar `expml data prepare`, `expml partition build`, `expml run execute`, `expml stats compute` e `expml report generate`.
   - Confirmar que todas as células completam com status `COMPLETED` e que os parâmetros de imputação foram calculados isoladamente em cada fold de treino.
2. **Validação de `CV_AND_HOLDOUT` (`FINAL_HOLDOUT`):**
   - Configurar `partition_spec.json` com `"outer_scheme": "CV_AND_HOLDOUT"`, `"n_splits": 5` e `"holdout_fraction": 0.2`.
   - Executar a matriz e confirmar a geração das células de desenvolvimento (`fold_0` a `fold_4`) e das células de `final_holdout`, bem como a exibição separada das métricas de CV e de Holdout Final no relatório da Etapa 6.
