"""Reproducibility package builder for Stage 6 reporting (RF6.3, RF6.4, CA-E6-02).

Exports tables, figures, full reports, provenance, environment/seed snapshots,
and relative POSIX SHA-256 checksums without external runtime dependencies (XCUT-02).
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import platform
import shutil
import sys
import tempfile
from typing import Any

import numpy as np

from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.core.storage import write_json_atomic
from experimental_ml.reporting.figures import build_figure_spec, render_figure
from experimental_ml.reporting.loader import select_report_content
from experimental_ml.reporting.report import render_full_report
from experimental_ml.reporting.tables import (
    build_table_model,
    render_table_csv,
    render_table_latex,
    render_table_markdown,
)
from experimental_ml.reporting.types import (
    ArtifactProvenance,
    LoadedExperimentData,
    PackageMode,
    ReportContentSelection,
    ReportFamily,
    ReproducibilityPackageManifest,
    ResearcherDeclarations,
)

_FIGURE_FAMILIES: tuple[ReportFamily, ...] = (
    ReportFamily.D_PREDICTIVE_PERFORMANCE,
    ReportFamily.E_STATISTICAL_COMPARISONS,
    ReportFamily.F_STABILITY_COST_PARETO,
    ReportFamily.G_MODEL_SPECIFIC_ARTIFACTS,
)


def _write_bytes_atomic(path: Path, data: bytes, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise ContractViolationError(f"Destination artifact already exists (force=False): {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(tmp_path, path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _serialize_provenance(prov: ArtifactProvenance) -> dict[str, Any]:
    return {
        "artifact_id": prov.artifact_id,
        "artifact_type": prov.artifact_type,
        "family": prov.family.value if prov.family is not None else None,
        "experiment_id": prov.experiment_id,
        "partition_plan_id": prov.partition_plan_id,
        "model_ids": list(prov.model_ids),
        "scenario_ids": list(prov.scenario_ids),
        "metrics": list(prov.metrics),
        "source_relative_paths": list(prov.source_relative_paths),
        "created_at_utc": prov.created_at_utc,
    }


def _extract_seeds_snapshot(loaded_data: LoadedExperimentData) -> dict[str, Any]:
    seeds: dict[str, Any] = {}
    for section_name, mapping in (
        ("partition_plan", loaded_data.partition_plan),
        ("preparation_plan", loaded_data.preparation_plan),
        ("scenarios_catalog", loaded_data.scenarios_catalog),
        ("models_catalog", loaded_data.models_catalog),
        ("execution_state", loaded_data.execution_state),
    ):
        if not mapping:
            continue
        for key in ("seed", "random_seed", "global_seed", "master_seed"):
            if key in mapping:
                seeds[f"{section_name}.{key}"] = mapping[key]
    return {
        "experiment_id": loaded_data.experiment_id,
        "partition_plan_id": loaded_data.partition_plan_id,
        "seeds": seeds,
    }


def _build_reproduce_markdown(
    loaded_data: LoadedExperimentData,
    mode: PackageMode,
    reproduction_level: str,
    exported_files: tuple[str, ...],
) -> str:
    data_note = (
        "Raw/sanitized dataset files under `data/` are excluded in `REDUCED_NO_RAW_DATA` mode; "
        "results and reports can be audited against persisted statistics without raw data."
        if mode == PackageMode.REDUCED_NO_RAW_DATA
        else "Full reproducibility package mode (`FULL_PACKAGE`)."
    )
    lines = [
        f"# Reproducibility Guide — {loaded_data.experiment_id}",
        "",
        f"- **Experiment ID**: `{loaded_data.experiment_id}`",
        f"- **Partition Plan ID**: `{loaded_data.partition_plan_id}`",
        f"- **Package Mode**: `{mode.value}`",
        f"- **Reproduction Level**: `{reproduction_level}`",
        f"- **Exported Artifacts Count**: {len(exported_files)}",
        "",
        "## Data Availability",
        "",
        data_note,
        "",
        "## Integrity Verification",
        "",
        "Run from the root of this package directory:",
        "",
        "```bash",
        "sha256sum -c reproducibility/checksums.sha256",
        "```",
        "",
    ]
    return "\n".join(lines)


def build_reproducibility_package(
    loaded_data: LoadedExperimentData,
    output_dir: Path | str,
    *,
    mode: PackageMode | str = PackageMode.FULL_PACKAGE,
    selection: ReportContentSelection | None = None,
    declarations: ResearcherDeclarations | None = None,
    source_experiment_dir: Path | str | None = None,
    force: bool = False,
) -> ReproducibilityPackageManifest:
    """Build an atomic, portable Stage 6 reproducibility package (RF6.3, RF6.4, CA-E6-02)."""
    resolved_mode = mode if isinstance(mode, PackageMode) else PackageMode(mode)
    sel = select_report_content(loaded_data, selection)
    out_root = Path(output_dir)

    reproduction_level = (
        "REDUCED_NO_RAW_DATA"
        if resolved_mode == PackageMode.REDUCED_NO_RAW_DATA
        else "FULL"
    )

    staged_files: dict[str, bytes] = {}
    provenance_entries: list[dict[str, Any]] = []
    figure_rel_paths: list[str] = []

    # 1. Tables (CSV, Markdown, LaTeX)
    for family in sel.families:
        table = build_table_model(family, loaded_data, sel)
        slug = family.value.lower()
        table_renders = (
            ("csv", render_table_csv(table).encode("utf-8")),
            ("md", render_table_markdown(table).encode("utf-8")),
            ("tex", render_table_latex(table).encode("utf-8")),
        )
        for ext, payload in table_renders:
            rel_path = f"tables/table_{slug}.{ext}"
            staged_files[rel_path] = payload
            provenance_entries.append(
                {
                    "output_relative_path": rel_path,
                    "kind": "table",
                    "family": family.value,
                    "format": ext,
                    "provenance": _serialize_provenance(table.provenance),
                }
            )

    # 2. Figures (SVG, PNG 300 DPI, PDF)
    for family in _FIGURE_FAMILIES:
        if family not in sel.families:
            continue
        try:
            fig_spec = build_figure_spec(family, loaded_data, sel)
        except ConfigurationError:
            continue
        slug = family.value.lower()
        for fmt in ("svg", "png", "pdf"):
            rel_path = f"figures/fig_{slug}.{fmt}"
            staged_files[rel_path] = render_figure(fig_spec, fmt=fmt)
            if fmt == "svg":
                figure_rel_paths.append(rel_path)
            provenance_entries.append(
                {
                    "output_relative_path": rel_path,
                    "kind": "figure",
                    "family": family.value,
                    "format": fmt,
                    "provenance": _serialize_provenance(fig_spec.provenance),
                }
            )

    # 3. Full Reports (Markdown & HTML)
    report_prov = {
        "artifact_id": f"report_{loaded_data.experiment_id}",
        "artifact_type": "report",
        "family": None,
        "experiment_id": loaded_data.experiment_id,
        "partition_plan_id": loaded_data.partition_plan_id,
        "model_ids": list(sel.model_ids),
        "scenario_ids": list(sel.scenario_ids),
        "metrics": list(sel.metric_ids),
        "source_relative_paths": ["statistics/descriptive_consolidation.json"],
        "created_at_utc": loaded_data.statistics.consolidation.timestamp_utc,
    }
    for fmt, ext in (("markdown", "md"), ("html", "html")):
        rel_path = f"reports/report.{ext}"
        content = render_full_report(
            loaded_data,
            fmt=fmt,
            selection=sel,
            declarations=declarations,
            figure_paths=tuple(figure_rel_paths),
        )
        staged_files[rel_path] = content.encode("utf-8")
        provenance_entries.append(
            {
                "output_relative_path": rel_path,
                "kind": "report",
                "family": None,
                "format": fmt,
                "provenance": report_prov,
            }
        )

    # 4. Optional raw/sanitized data copy in FULL_PACKAGE mode only
    data_copies: list[tuple[Path, str]] = []
    if resolved_mode == PackageMode.FULL_PACKAGE and source_experiment_dir is not None:
        src_data_dir = Path(source_experiment_dir) / "data"
        if src_data_dir.is_dir():
            for src_file in sorted(src_data_dir.rglob("*")):
                if src_file.is_file():
                    rel_posix = f"data/{src_file.relative_to(src_data_dir).as_posix()}"
                    data_copies.append((src_file, rel_posix))
                    provenance_entries.append(
                        {
                            "output_relative_path": rel_posix,
                            "kind": "data",
                            "family": None,
                            "format": src_file.suffix.lstrip(".") or "bin",
                            "provenance": {
                                "artifact_id": rel_posix,
                                "artifact_type": "data",
                                "experiment_id": loaded_data.experiment_id,
                                "partition_plan_id": loaded_data.partition_plan_id,
                                "source_relative_paths": [rel_posix],
                            },
                        }
                    )

    exported_files = tuple(sorted([*staged_files.keys(), *(rel for _, rel in data_copies)]))

    # 5. Reproducibility metadata payloads
    prov_rel = "reproducibility/artifact_provenance.json"
    checksums_rel = "reproducibility/checksums.sha256"
    env_rel = "reproducibility/environment.json"
    seeds_rel = "reproducibility/seeds.json"
    reproduce_rel = "reproducibility/REPRODUCE.md"

    all_target_rel_paths = (
        *exported_files,
        prov_rel,
        checksums_rel,
        env_rel,
        seeds_rel,
        reproduce_rel,
    )

    # Pre-flight STORE-05 overwrite protection before any disk mutation
    if not force:
        same_data_targets = {
            rel for src_f, rel in data_copies if src_f.resolve() == (out_root / rel).resolve()
        }
        for rel_path in all_target_rel_paths:
            if rel_path in same_data_targets:
                continue
            candidate = out_root / rel_path
            if candidate.exists():
                raise ContractViolationError(
                    f"Destination artifact already exists (force=False): {candidate}"
                )

    out_root.mkdir(parents=True, exist_ok=True)

    # Write staged artifacts
    for rel_path, payload in staged_files.items():
        _write_bytes_atomic(out_root / rel_path, payload, overwrite=force)

    for src_file, rel_path in data_copies:
        dst_file = out_root / rel_path
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        if src_file.resolve() != dst_file.resolve():
            if dst_file.exists() and not force:
                raise ContractViolationError(f"Destination artifact already exists (force=False): {dst_file}")
            shutil.copy2(src_file, dst_file)
        staged_files[rel_path] = dst_file.read_bytes()

    # Write reproducibility JSON/MD files
    provenance_doc = {
        "experiment_id": loaded_data.experiment_id,
        "partition_plan_id": loaded_data.partition_plan_id,
        "package_mode": resolved_mode.value,
        "reproduction_level": reproduction_level,
        "artifacts": sorted(provenance_entries, key=lambda e: e["output_relative_path"]),
    }
    env_doc = {
        "experiment_id": loaded_data.experiment_id,
        "partition_plan_id": loaded_data.partition_plan_id,
        "package_mode": resolved_mode.value,
        "reproduction_level": reproduction_level,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy_version": np.__version__,
    }
    seeds_doc = _extract_seeds_snapshot(loaded_data)
    reproduce_md = _build_reproduce_markdown(loaded_data, resolved_mode, reproduction_level, exported_files)

    write_json_atomic(out_root / prov_rel, provenance_doc, overwrite=force)
    write_json_atomic(out_root / env_rel, env_doc, overwrite=force)
    write_json_atomic(out_root / seeds_rel, seeds_doc, overwrite=force)
    _write_bytes_atomic(out_root / reproduce_rel, reproduce_md.encode("utf-8"), overwrite=force)

    # Compute checksums over all exported files + reproducibility metadata files (excluding checksums.sha256 itself)
    checksum_targets: dict[str, bytes] = dict(staged_files)
    for meta_rel in (prov_rel, env_rel, seeds_rel, reproduce_rel):
        checksum_targets[meta_rel] = (out_root / meta_rel).read_bytes()

    checksum_lines = [
        f"{_sha256_bytes(checksum_targets[rel_path])}  {rel_path}"
        for rel_path in sorted(checksum_targets.keys())
    ]
    _write_bytes_atomic(
        out_root / checksums_rel,
        ("\n".join(checksum_lines) + "\n").encode("utf-8"),
        overwrite=force,
    )

    return ReproducibilityPackageManifest(
        experiment_id=loaded_data.experiment_id,
        partition_plan_id=loaded_data.partition_plan_id,
        package_mode=resolved_mode,
        reproduction_level=reproduction_level,
        exported_files=exported_files,
        checksums_file=checksums_rel,
        provenance_file=prov_rel,
    )
