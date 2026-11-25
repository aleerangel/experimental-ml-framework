# Roteiro de Aceite — Marco M10: Redesenho do Subsistema de Visualização Científica e Relatórios

- **Marco:** `M10` (`m10-scientific-visualization-reporting-redesign`)
- **Status do Marco:** Proposta Preliminar (Fase TLC: **Specify** — aguardando decisão arquitetural sobre `XCUT-02` / `matplotlib` e aprovação da `spec.md`)

---

## Passos Planejados de Validação Visual e Documental pelo Consumidor

1. **Validação Visual dos Gráficos Exploratórios da Etapa 2:**
   - Executar `expml features explore` em um dataset com variáveis contendo acentos em português e nomes com mais de 25 caracteres.
   - Abrir `reports/relevance_ranking.png` e `reports/redundancy_matrix.png` e confirmar:
     - acentuação gráfica correta (`Correlação`, `Informação Mútua`, `Razão de Correlação`);
     - ausência de truncamento nos nomes de variáveis e ausência de colisão com a barra de cores.
2. **Validação Visual das Figuras Científicas da Etapa 6 (`PNG 300 DPI`, `SVG`, `PDF`):**
   - Executar `expml report export` em um experimento com $\ge 3$ configurações e 2 objetivos de Pareto.
   - Inspecionar visualmente `fig_family_d.{png,svg,pdf}`, `fig_family_e.{png,svg,pdf}`, `fig_family_f.{png,svg,pdf}` e `fig_family_g.{png,svg,pdf}` e confirmar:
     - presença de títulos, eixos rotulados, escala numérica, barras de erro de IC 95% e legenda nos três formatos (`PNG`, `SVG`, `PDF`);
     - posicionamento exato dos pontos de Pareto nas coordenadas $(x, y)$ reais dos dois objetivos;
     - linha de referência $\Delta = 0$ visível no gráfico de diferenças pareadas (Família E).
3. **Validação do Relatório Científico (`report.md` e `report.html`):**
   - Abrir `reports/report.html` no navegador e verificar que todas as 7 tabelas (Famílias A a G) estão completas, em português e acompanhadas do glossário estatístico interpretativo.
