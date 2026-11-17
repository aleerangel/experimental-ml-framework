# Receita 5: Pacotes de Reprodutibilidade e Auditoria SHA-256 para Conferências

## Contexto Científico

Ao submeter artigos para conferências e periódicos científicos (como NeurIPS, ICML ou IEEE), pesquisadores frequentemente precisam fornecer um pacote auditável de artefatos, tabelas e resultados sem vazar dados sensíveis ou caminhos absolutos locais.

O `experimental-ml` oferece na Etapa 6 (`build_reproducibility_package`) dois modos oficiais de empacotamento portátil:
1. **`FULL_PACKAGE`:** Inclui todas as 7 famílias de tabelas (`CSV`, `Markdown`, `LaTeX`), figuras (`SVG`, `PNG` 300 DPI, `PDF`), relatórios completos (`MD`, `HTML`), metadados de proveniência (`artifact_provenance.json`, `environment.json`, `seeds.json`, `REPRODUCE.md`), arquivo `reproducibility/checksums.sha256` relativo em POSIX e cópia do diretório `data/`;
2. **`REDUCED_NO_RAW_DATA`:** Preserva todos os relatórios, tabelas, figuras, metadados e checksums para auditoria de resultados, mas **exclui integralmente** os arquivos de dados brutos/saneados de `data/` (ideal para dados clínicos sob NDA ou bases muito grandes).

---

## Exportação e Auditoria via CLI

```bash
# Modo reduzido (sem dados brutos) para submissão de revisão cega
expml report export --exp-dir exp_dir --mode REDUCED_NO_RAW_DATA --output-dir pacote_conferencia

# Verificação de integridade pelo portão do framework
expml report verify --exp-dir pacote_conferencia
```

Para validar os checksums em qualquer máquina Linux/macOS a partir da raiz do pacote exportado:

```bash
sha256sum -c reproducibility/checksums.sha256
```

---

## Exportação Programática em Python

```python
# conceptual
from experimental_ml.reporting import (
    PackageMode,
    build_reproducibility_package,
    load_experiment_artifacts_readonly,
)

# Leitura estrita em modo somente-leitura das Etapas 1 a 5
loaded = load_experiment_artifacts_readonly("exp_dir")

manifest = build_reproducibility_package(
    loaded,
    output_dir="pacote_conferencia",
    mode=PackageMode.REDUCED_NO_RAW_DATA,
    source_experiment_dir="exp_dir",
    force=True,
)
assert manifest.reproduction_level == "REDUCED_NO_RAW_DATA"
```

---

## Garantias de Portabilidade

- Todos os caminhos gravados em `reproducibility/checksums.sha256` e `artifact_provenance.json` são **relativos POSIX** (sem caminhos absolutos como `/home/...`), permitindo mover ou compactar o diretório entre ambientes distintos sem quebrar a verificação de hashes.
- A proteção pré-voo contra sobrescrita (`force=False`) impede a destruição acidental de pacotes já auditados.
