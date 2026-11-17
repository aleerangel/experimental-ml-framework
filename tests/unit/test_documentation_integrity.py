"""Testes automatizados em 5 níveis para integridade documental (TA-POS.2 / DOC-06).

Níveis validados:
1. Integridade de links relativos Markdown e âncoras internas;
2. Validação sintática via `ast.parse` de blocos Python (excluindo `# conceptual`);
3. Resolução estática AST de imports de `experimental_ml.*` contra a API pública;
4. Validação léxica de comandos `expml` em blocos shell contra os subcomandos reais;
5. Execução ponta a ponta (smoke test) de blocos marcados com `# executable-smoke-test`.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path
import re
import shlex
import unicodedata

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs"
README_PATH = REPO_ROOT / "README.md"

VALID_EXPML_COMMANDS: dict[str, set[str]] = {
    "data": {"profile", "sanitize"},
    "partition": {"build", "verify"},
    "features": {"explore", "scenarios", "verify"},
    "models": {"validate", "verify"},
    "run": {"start", "resume", "status", "verify"},
    "stats": {"run", "status", "verify"},
    "report": {"generate", "export", "verify"},
}

PUBLIC_PACKAGES: set[str] = {
    "core",
    "data",
    "metrics",
    "features",
    "models",
    "tuning",
    "validation",
    "orchestration",
    "statistics",
    "reporting",
    "stages",
}

_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
_FENCE_RE = re.compile(r"```([a-zA-Z0-9_-]*)\n(.*?)```", re.DOTALL)
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)


def _iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    if README_PATH.is_file():
        files.append(README_PATH)
    if DOCS_DIR.is_dir():
        files.extend(sorted(DOCS_DIR.rglob("*.md")))
    return files


def _slugify_github_anchor(heading_text: str) -> str:
    """Converte título Markdown em âncora GitHub Flavored Markdown aproximada."""
    cleaned = re.sub(r"`([^`]*)`", r"\1", heading_text).strip().lower()
    cleaned = unicodedata.normalize("NFKC", cleaned)
    # Remove pontuação mantendo letras unicode, dígitos, espaços e hífens
    out_chars: list[str] = []
    for ch in cleaned:
        if ch.isalnum() or ch in (" ", "-", "_"):
            out_chars.append(ch)
    slug = "".join(out_chars).replace(" ", "-")
    return slug


def _extract_anchors(md_path: Path) -> set[str]:
    text = md_path.read_text(encoding="utf-8")
    # Remove blocos de código antes de extrair cabeçalhos
    text_no_code = _FENCE_RE.sub("", text)
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for match in _HEADING_RE.finditer(text_no_code):
        base = _slugify_github_anchor(match.group(1))
        if not base:
            continue
        idx = counts.get(base, 0)
        counts[base] = idx + 1
        anchors.add(base if idx == 0 else f"{base}-{idx}")
    return anchors


def _strip_code_fences(text: str) -> str:
    return _FENCE_RE.sub("", text)


def test_markdown_links_and_anchors_valid() -> None:
    """Nível 1: Todos os links relativos e âncoras em README.md e docs/ devem existir."""
    md_files = _iter_markdown_files()
    assert md_files, "Nenhum arquivo Markdown encontrado para validação."

    broken_links: list[str] = []
    anchor_cache: dict[Path, set[str]] = {}

    for md_file in md_files:
        content = _strip_code_fences(md_file.read_text(encoding="utf-8"))
        for match in _LINK_RE.finditer(content):
            raw_target = match.group(1).strip()
            if not raw_target or raw_target.startswith(("http://", "https://", "mailto:")):
                continue
            # Remove título opcional entre aspas no link
            target_part = raw_target.split()[0]
            if "#" in target_part:
                file_part, anchor_part = target_part.split("#", 1)
            else:
                file_part, anchor_part = target_part, ""

            if not file_part:
                target_path = md_file
            else:
                if file_part.startswith("file://"):
                    continue
                target_path = (md_file.parent / file_part).resolve()

            if not target_path.exists():
                broken_links.append(f"{md_file.relative_to(REPO_ROOT)} -> {raw_target} (destino ausente)")
                continue

            if anchor_part and target_path.is_file() and target_path.suffix == ".md":
                if re.match(r"^L\d+(?:-L?\d+)?$", anchor_part):
                    continue
                if target_path not in anchor_cache:
                    anchor_cache[target_path] = _extract_anchors(target_path)
                if anchor_part not in anchor_cache[target_path]:
                    broken_links.append(
                        f"{md_file.relative_to(REPO_ROOT)} -> {raw_target} (âncora '#{anchor_part}' ausente)"
                    )

    assert not broken_links, "Links quebrados encontrados:\n" + "\n".join(broken_links)


def test_python_snippets_ast_and_public_imports() -> None:
    """Níveis 2 e 3: Blocos Python válidos via AST e imports públicos de experimental_ml reais."""
    md_files = _iter_markdown_files()
    syntax_errors: list[str] = []
    import_errors: list[str] = []

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        rel_name = str(md_file.relative_to(REPO_ROOT))
        for block_idx, match in enumerate(_FENCE_RE.finditer(text), start=1):
            lang = match.group(1).strip().lower()
            code = match.group(2)
            if lang != "python":
                continue
            first_line = code.lstrip().splitlines()[0] if code.strip() else ""
            if "# conceptual" in first_line or "# pseudocode" in first_line:
                continue

            try:
                tree = ast.parse(code, filename=f"{rel_name}#block-{block_idx}")
            except SyntaxError as exc:
                syntax_errors.append(f"{rel_name} bloco {block_idx}: {exc}")
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module == "experimental_ml":
                        pkg = importlib.import_module("experimental_ml")
                        for alias in node.names:
                            if alias.name != "*" and not hasattr(pkg, alias.name):
                                import_errors.append(
                                    f"{rel_name} bloco {block_idx}: símbolo '{alias.name}' ausente em experimental_ml"
                                )
                    elif node.module.startswith("experimental_ml."):
                        parts = node.module.split(".")
                        subpkg = parts[1]
                        if subpkg not in PUBLIC_PACKAGES:
                            import_errors.append(
                                f"{rel_name} bloco {block_idx}: subpacote '{subpkg}' não é público"
                            )
                            continue
                        try:
                            mod = importlib.import_module(node.module)
                        except ImportError as exc:
                            import_errors.append(
                                f"{rel_name} bloco {block_idx}: falha ao importar '{node.module}': {exc}"
                            )
                            continue
                        for alias in node.names:
                            if alias.name != "*" and not hasattr(mod, alias.name):
                                import_errors.append(
                                    f"{rel_name} bloco {block_idx}: '{alias.name}' ausente em '{node.module}'"
                                )

    assert not syntax_errors, "Erros de sintaxe Python:\n" + "\n".join(syntax_errors)
    assert not import_errors, "Erros de imports da API pública:\n" + "\n".join(import_errors)


def test_cli_blocks_and_quickstart_smoke_execution(tmp_path: Path) -> None:
    """Níveis 4 e 5: Validação léxica de CLI `expml` e execução smoke-test do Quickstart."""
    md_files = _iter_markdown_files()
    cli_errors: list[str] = []
    smoke_blocks: list[tuple[str, str]] = []

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        rel_name = str(md_file.relative_to(REPO_ROOT))
        for block_idx, match in enumerate(_FENCE_RE.finditer(text), start=1):
            lang = match.group(1).strip().lower()
            body = match.group(2)

            if lang in {"bash", "sh", "console"}:
                for line in body.splitlines():
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    if stripped.startswith("$ "):
                        stripped = stripped[2:].strip()
                    try:
                        tokens = shlex.split(stripped)
                    except ValueError:
                        continue
                    if not tokens:
                        continue
                    if tokens[0] == "expml":
                        if len(tokens) < 2 or tokens[1] in {"--help", "-h", "--version"}:
                            continue
                        cmd = tokens[1]
                        if cmd not in VALID_EXPML_COMMANDS:
                            cli_errors.append(
                                f"{rel_name} bloco {block_idx}: comando desconhecido 'expml {cmd}'"
                            )
                            continue
                        if len(tokens) >= 3 and not tokens[2].startswith("-"):
                            subcmd = tokens[2]
                            if subcmd not in VALID_EXPML_COMMANDS[cmd]:
                                cli_errors.append(
                                    f"{rel_name} bloco {block_idx}: subcomando desconhecido 'expml {cmd} {subcmd}'"
                                )

            if lang == "python" and "# executable-smoke-test" in body:
                smoke_blocks.append((f"{rel_name}#block-{block_idx}", body))

    assert not cli_errors, "Comandos CLI inválidos encontrados:\n" + "\n".join(cli_errors)

    for label, code in smoke_blocks:
        exec_globals: dict[str, object] = {"__name__": "__main__", "SMOKE_TMP_DIR": tmp_path}
        try:
            compiled = compile(code, label, "exec")
            exec(compiled, exec_globals)
        except Exception as exc:
            pytest.fail(f"Falha ao executar smoke-test '{label}': {exc}")


def test_readme_lean_structure_and_pointers() -> None:
    """Nível estrutural (Check C4): README.md enxuto, sem código Python e com ponteiros úteis."""
    content = README_PATH.read_text(encoding="utf-8")
    lines = content.splitlines()
    assert len(lines) <= 160, f"README.md deve ser enxuto (<= 160 linhas), possui {len(lines)}."
    assert "```python" not in content, "README.md não deve conter blocos de código Python."
    for required_target in (
        "docs/README.md",
        "docs/engenharia_software/ARQUITETURA_E_CONTRATOS.md",
        "docs/REFERENCIAS_E_FUNDAMENTACAO.md",
        "Alexandre Rangel",
        "Licença MIT",
    ):
        assert required_target in content, f"README.md deve apontar para '{required_target}'."

