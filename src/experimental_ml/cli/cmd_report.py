"""CLI handlers for Stage 6 reporting, reproducibility packaging, and gate verification (expml report).

Conforms to CLI-10 (lazy imports), CLI-11 (no raw hashes on stdout), CA-E6-01, CA-E6-02, and STORE-05.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile


def _write_text_atomic(path: Path, text: str, *, overwrite: bool) -> None:
    from experimental_ml.core.findings import ContractViolationError

    if path.exists() and not overwrite:
        raise ContractViolationError(f"Destination report already exists (use --force): {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp_path, path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def _build_selection(args: argparse.Namespace):
    from experimental_ml.reporting.types import ReportAudience, ReportContentSelection, ReportFamily

    audience = ReportAudience(getattr(args, "audience", "FULL_LAB"))
    families_arg = getattr(args, "families", None)
    families = (
        tuple(ReportFamily(f.strip()) for f in families_arg.split(",") if f.strip())
        if families_arg
        else ()
    )
    return ReportContentSelection(audience=audience, families=families)


def handle_report_generate(args: argparse.Namespace) -> int:
    """Handle `expml report generate`."""
    from experimental_ml.core.findings import ContractViolationError
    from experimental_ml.reporting import (
        ResearcherDeclarations,
        load_experiment_artifacts_readonly,
        render_full_report,
        select_report_content,
    )

    exp_dir = Path(args.experiment_dir).resolve()
    out_dir = Path(args.output_dir).resolve() if getattr(args, "output_dir", None) else (exp_dir / "reports")
    force = bool(getattr(args, "force", False))
    fmt = getattr(args, "format", "both")

    loaded = load_experiment_artifacts_readonly(exp_dir)
    sel = select_report_content(loaded, _build_selection(args))
    declarations = ResearcherDeclarations(scientific_objective=getattr(args, "objective", "") or "")

    targets: list[tuple[str, Path]] = []
    if fmt in ("markdown", "both"):
        targets.append(("markdown", out_dir / "report.md"))
    if fmt in ("html", "both"):
        targets.append(("html", out_dir / "report.html"))

    if not force:
        for _, target_path in targets:
            if target_path.exists():
                raise ContractViolationError(f"Destination report already exists (use --force): {target_path}")

    written: list[str] = []
    for render_fmt, target_path in targets:
        content = render_full_report(loaded, fmt=render_fmt, selection=sel, declarations=declarations)
        _write_text_atomic(target_path, content, overwrite=force)
        written.append(target_path.name)

    sys.stdout.write(
        json.dumps(
            {
                "status": "GENERATED",
                "experiment_id": loaded.experiment_id,
                "audience": sel.audience.value,
                "output_dir": str(out_dir),
                "files": written,
                "file_paths": [str(out_dir / f) for f in written],
                "note": "Para gerar tabelas (CSV/MD/LaTeX) e figuras (SVG/PNG/PDF), execute: expml report export",
            },
            indent=2,
        )
        + "\n"
    )
    return 0


def handle_report_export(args: argparse.Namespace) -> int:
    """Handle `expml report export`."""
    from experimental_ml.reporting import (
        PackageMode,
        ResearcherDeclarations,
        build_reproducibility_package,
        load_experiment_artifacts_readonly,
        select_report_content,
    )

    exp_dir = Path(args.experiment_dir).resolve()
    out_dir = Path(args.output_dir).resolve() if getattr(args, "output_dir", None) else exp_dir
    mode = PackageMode(getattr(args, "mode", "full_package"))
    force = bool(getattr(args, "force", False))

    loaded = load_experiment_artifacts_readonly(exp_dir)
    sel = select_report_content(loaded, _build_selection(args))
    declarations = ResearcherDeclarations(scientific_objective=getattr(args, "objective", "") or "")

    manifest = build_reproducibility_package(
        loaded,
        output_dir=out_dir,
        mode=mode,
        selection=sel,
        declarations=declarations,
        source_experiment_dir=exp_dir,
        force=force,
    )

    sys.stdout.write(
        json.dumps(
            {
                "status": "EXPORTED",
                "experiment_id": manifest.experiment_id,
                "package_mode": manifest.package_mode.value,
                "reproduction_level": manifest.reproduction_level,
                "exported_files_count": len(manifest.exported_files),
                "checksums_file": manifest.checksums_file,
                "provenance_file": manifest.provenance_file,
            },
            indent=2,
        )
        + "\n"
    )
    return 0


def handle_report_verify(args: argparse.Namespace) -> int:
    """Handle `expml report verify`."""
    from experimental_ml.stages.stage_gates import verify_report_gate

    pkg_dir = Path(args.experiment_dir).resolve()
    summary = verify_report_gate(pkg_dir)
    cli_summary = {k: v for k, v in summary.items() if k != "partition_plan_id"}
    sys.stdout.write(json.dumps(cli_summary, indent=2) + "\n")
    return 0
