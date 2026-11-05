"""48-check automated verification suite for M1 Project Integrity Review.

Maps 1:1 to C1..C48 in .specs/features/m1-integrity-review/tasks.md.
Executes read-only checks over the audit reports, probe scripts,
the codebase AST/runtime, and the git baseline invariant.
"""

from __future__ import annotations

import ast
import pathlib
import re
import subprocess
import types

import numpy as np

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
FEATURE_DIR = pathlib.Path(__file__).resolve().parents[1]
REPORTS_DIR = FEATURE_DIR / "reports"
PROBES_DIR = FEATURE_DIR / "probes"
BASELINE_COMMIT = "6acf6f8e5d478cbc08bb29ef22ac1da267b56feb"


def _read_report(name: str) -> str:
    path = REPORTS_DIR / name
    assert path.is_file(), f"Missing report: {path}"
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Protocol & Non-Interference (C1..C4 / AUD-01..AUD-04)
# ---------------------------------------------------------------------------


def test_c01_aud_01_baseline_recorded() -> None:
    text = _read_report("00-baseline.md")
    assert BASELINE_COMMIT in text
    assert "3.12.15" in text
    assert "2.4.4" in text or "2.5.4" in text
    assert "9.0.3" in text or "9.2.0" in text
    assert "81 passed" in text


def test_c02_aud_02_non_interference_diff_empty() -> None:
    protected_paths = [
        "src/",
        "tests/",
        "pyproject.toml",
        "README.md",
        "engenharia_software/",
        ".agent/",
        ".specs/features/m1-1-setup-cli-smoke/",
        ".specs/features/m1-2-core/",
        ".specs/features/m1-3-metrics/",
        ".specs/features/m1-4-datasets-schemas/",
    ]
    res = subprocess.run(
        ["git", "diff", BASELINE_COMMIT, "--", *protected_paths],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert res.stdout == "", f"Non-empty diff on protected paths:\n{res.stdout}"


def test_c03_aud_03_findings_have_reproducible_evidence() -> None:
    text = _read_report("06-achados.md")
    blocks = re.split(r"^### `?(AUD-F-\d{3})`?", text, flags=re.MULTILINE)
    finding_ids = blocks[1::2]
    finding_bodies = blocks[2::2]
    assert len(finding_ids) == 16
    for fid, body in zip(finding_ids, finding_bodies, strict=True):
        assert "**Localização:**" in body, f"{fid} missing Localização"
        assert "**Evidência Reprodutível:**" in body, f"{fid} missing Evidência"
        assert ("`" in body) and (":" in body or "```" in body), f"{fid} lacks path:line or code block"


def test_c04_aud_04_unverifiable_criteria_marked() -> None:
    r04 = _read_report("04-qualidade-e-testes.md")
    r05 = _read_report("05-rastreabilidade.md")
    assert "NÃO VERIFICÁVEL" in r04
    assert "python3.10" in r04 and "python3.11" in r04
    assert "RNF06" in r05 and "NÃO VERIFICÁVEL" in r05


# ---------------------------------------------------------------------------
# Dimension A: Architectural Integrity (C5..C11 / ARCH-01..ARCH-07)
# ---------------------------------------------------------------------------


def test_c05_arch_01_import_graph_recorded() -> None:
    r02 = _read_report("02-arquitetura.md")
    assert "ARCH-01" in r02
    assert "57 arestas internas de importação" in r02
    assert "experimental_ml.core" in r02
    assert "experimental_ml.metrics" in r02
    assert "experimental_ml.data" in r02


def test_c06_arch_02_dependency_levels_checked() -> None:
    r02 = _read_report("02-arquitetura.md")
    assert "ARCH-02" in r02
    assert "obedece estritamente ao grafo acíclico documentado" in r02


def test_c07_arch_03_zero_import_cycles() -> None:
    r02 = _read_report("02-arquitetura.md")
    assert "ARCH-03" in r02
    assert "0` ciclos detectados" in r02 or "module_cycles: []" in r02


def test_c08_arch_04_adr008_class_taxonomy() -> None:
    r02 = _read_report("02-arquitetura.md")
    assert "30 classes" in r02
    assert "AUD-F-003" in r02
    assert "DomainIdentifier" in r02


def test_c09_arch_05_duplicate_responsibilities_listed() -> None:
    r02 = _read_report("02-arquitetura.md")
    assert "_is_missing" in r02
    assert "src/experimental_ml/data/loader.py" in r02
    assert "src/experimental_ml/core/hashing.py" in r02
    assert "AUD-F-008" in r02


def test_c10_arch_06_unreferenced_public_symbols_checked() -> None:
    r02 = _read_report("02-arquitetura.md")
    assert "ARCH-06" in r02
    assert "60 símbolos públicos" in r02


def test_c11_arch_07_doc_vs_public_api_compared() -> None:
    r02 = _read_report("02-arquitetura.md")
    assert "ARCH-07" in r02
    assert "AUD-F-001" in r02
    assert "AUD-F-002" in r02


# ---------------------------------------------------------------------------
# Dimension B: Cross-Module Integration (C12..C19 / INT-01..INT-08)
# ---------------------------------------------------------------------------


def test_c12_int_01_e2e_flow_executed() -> None:
    from experimental_ml.core.enums import TaskType
    from experimental_ml.data import DatasetSchemaSpec, get_column_array, load_dataset
    from experimental_ml.metrics import aggregate_fold_metrics, compute_metric

    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    b1 = load_dataset({"x": [1.0, 2.0, 3.0], "y": [2.0, 4.0, 6.0]}, schema)
    b2 = load_dataset({"x": [4.0, 5.0, 6.0], "y": [8.0, 10.0, 12.0]}, schema)
    y1 = get_column_array(b1, "y")
    y2 = get_column_array(b2, "y")
    m1 = compute_metric("rmse", y1, y1 + 0.5)
    m2 = compute_metric("rmse", y2, y2 - 0.5)
    agg = aggregate_fold_metrics([m1, m2])
    assert agg.mean == 0.5
    r03 = _read_report("03-integracao.md")
    assert "INT-01" in r03 and "CONFORME" in r03


def test_c13_int_02_identifier_and_enum_identity() -> None:
    from experimental_ml.core.enums import TaskType
    from experimental_ml.core.types import ObservationId
    from experimental_ml.data import DatasetSchemaSpec, load_dataset, slice_bundle_by_observation_ids

    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    bundle = load_dataset({"x": [1.0, 2.0], "y": [3.0, 4.0]}, schema)
    assert all(isinstance(oid, ObservationId) for oid in bundle.observation_ids)
    assert bundle.schema.task_type is TaskType.REGRESSION

    # Verify AUD-F-006 reproduction on str sequence slice
    sliced = slice_bundle_by_observation_ids(bundle, ["obs_000000"])  # type: ignore[arg-type]
    assert type(sliced.observation_ids[0]) is str
    r03 = _read_report("03-integracao.md")
    assert "AUD-F-006" in r03


def test_c14_int_03_exception_hierarchy_verified() -> None:
    import pytest
    from experimental_ml.core.enums import TaskType
    from experimental_ml.data import DatasetSchemaSpec, load_dataset

    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    with pytest.raises(OverflowError):
        load_dataset({"x": [2**63], "y": [1.0]}, schema)
    r03 = _read_report("03-integracao.md")
    assert "AUD-F-007" in r03


def test_c15_int_04_cross_format_dataset_hash_compared() -> None:
    r03 = _read_report("03-integracao.md")
    assert "INT-04" in r03
    assert "CSV" in r03 and "TSV" in r03


def test_c16_int_05_cross_process_hashseed_determinism() -> None:
    r03 = _read_report("03-integracao.md")
    assert "PYTHONHASHSEED=0" in r03 and "PYTHONHASHSEED=12345" in r03
    assert "INT-05" in r03


def test_c17_int_06_readonly_arrays_across_all_metrics() -> None:
    from experimental_ml.metrics import METRICS_CATALOG

    assert len(METRICS_CATALOG) == 15
    r03 = _read_report("03-integracao.md")
    assert "INT-06" in r03 and "15" in r03


def test_c18_int_07_bundle_vs_core_dataset_hash_relation() -> None:
    from experimental_ml.core.enums import TaskType
    from experimental_ml.core.hashing import dataset_hash
    from experimental_ml.data import DatasetSchemaSpec, load_dataset, slice_bundle_by_observation_ids

    # Verify both AUD-F-004 and AUD-F-005
    h1 = dataset_hash({"ab": [1.0], "c": [2.0]})
    h2 = dataset_hash({"a": [1.0], "bc": [2.0]})
    assert h1 == h2  # AUD-F-004 collision

    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    b = load_dataset({"x": [1.0, 1.0], "y": [2.0, 2.0]}, schema)
    s0 = slice_bundle_by_observation_ids(b, [b.observation_ids[0]])
    s1 = slice_bundle_by_observation_ids(b, [b.observation_ids[1]])
    assert s0.observation_ids != s1.observation_ids
    assert s0.dataset_hash == s1.dataset_hash  # AUD-F-005

    r03 = _read_report("03-integracao.md")
    assert "INT-07" in r03 and "AUD-F-005" in r03


def test_c19_int_08_int64_and_bool_dtype_behavior_recorded() -> None:
    from experimental_ml.core.enums import MetricStatus
    from experimental_ml.metrics import compute_metric

    res = compute_metric("precision", np.array(["no", "yes"], dtype=object), np.array(["no", "yes"], dtype=object))
    assert res.status is MetricStatus.UNDEFINED_NAN
    r03 = _read_report("03-integracao.md")
    assert "AUD-F-011" in r03


# ---------------------------------------------------------------------------
# Dimension C: Implementation Quality (C20..C25 / QUAL-01..QUAL-06)
# ---------------------------------------------------------------------------


def test_c20_qual_01_ast_code_quality_scan() -> None:
    loader_src = (REPO_ROOT / "src" / "experimental_ml" / "data" / "loader.py").read_text(encoding="utf-8")
    tree = ast.parse(loader_src)
    asserts = [n for n in ast.walk(tree) if isinstance(n, ast.Assert)]
    assert len(asserts) == 1
    r04 = _read_report("04-qualidade-e-testes.md")
    assert "AUD-F-015" in r04


def test_c21_qual_02_public_type_annotations_checked() -> None:
    r04 = _read_report("04-qualidade-e-testes.md")
    assert "QUAL-02" in r04 and "41" in r04


def test_c22_qual_03_edge_cases_probed() -> None:
    from experimental_ml.core.enums import TaskType
    from experimental_ml.data import DatasetSchemaSpec, load_dataset

    # Reproduce AUD-F-008: 2D float32 array with NaN
    arr = np.array([[1.0, np.nan], [2.0, 3.0]], dtype=np.float32)
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    bundle = load_dataset(arr, schema, column_names=("x", "y"))
    assert bundle.descriptors["y"].n_missing == 0
    assert np.isnan(bundle.columns["y"][0])

    r04 = _read_report("04-qualidade-e-testes.md")
    assert "AUD-F-008" in r04


def test_c23_qual_04_scaling_benchmark_recorded() -> None:
    r04 = _read_report("04-qualidade-e-testes.md")
    assert "QUAL-04" in r04
    assert "10.000" in r04 and "100.000" in r04


def test_c24_qual_05_adversarial_immutability_verified() -> None:
    from experimental_ml.core.enums import TaskType
    from experimental_ml.data import DatasetSchemaSpec, load_dataset

    # Reproduce AUD-F-009: SimpleNamespace in object column
    ns1 = types.SimpleNamespace(v=1)
    ns2 = types.SimpleNamespace(v=2)
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    bundle = load_dataset({"x": [ns1, ns2], "y": [1.0, 2.0]}, schema)
    bundle.columns["x"][0].v = 999
    assert bundle.columns["x"][0].v == 999

    r04 = _read_report("04-qualidade-e-testes.md")
    assert "AUD-F-009" in r04


def test_c25_qual_06_interpreter_compatibility_recorded() -> None:
    r04 = _read_report("04-qualidade-e-testes.md")
    assert "QUAL-06" in r04
    assert "NÃO VERIFICÁVEL" in r04
    assert "python3.10" in r04 and "python3.11" in r04


# ---------------------------------------------------------------------------
# Dimension D: Testing Strategy & TLC Reliability (C26..C33 / TEST-01..TEST-08)
# ---------------------------------------------------------------------------


def test_c26_test_01_line_coverage_measured() -> None:
    r04 = _read_report("04-qualidade-e-testes.md")
    assert "83.7%" in r04
    assert "cli/main.py" in r04


def test_c27_test_02_twelve_mutations_executed() -> None:
    r04 = _read_report("04-qualidade-e-testes.md")
    for mid in [f"MUT-{i:02d}" for i in range(1, 13)]:
        assert mid in r04, f"Missing mutation {mid} in 04-qualidade-e-testes.md"


def test_c28_test_03_surviving_mutations_analyzed() -> None:
    r04 = _read_report("04-qualidade-e-testes.md")
    assert "12/12 KILLED" in r04


def test_c29_test_04_cross_module_integration_tests_counted() -> None:
    r04 = _read_report("04-qualidade-e-testes.md")
    assert "AUD-F-013" in r04
    assert "TEST-04" in r04


def test_c30_test_05_test_isolation_and_ordering_verified() -> None:
    r04 = _read_report("04-qualidade-e-testes.md")
    assert "TEST-05" in r04
    assert "81 passed" in r04


def test_c31_test_06_tlc_validators_executed() -> None:
    r04 = _read_report("04-qualidade-e-testes.md")
    assert "TEST-06" in r04
    assert "AUD-F-012" in r04


def test_c32_test_07_criterion_check_proof_mapping_verified() -> None:
    r04 = _read_report("04-qualidade-e-testes.md")
    assert "TEST-07" in r04


def test_c33_test_08_tlc_validator_reliability_checked() -> None:
    r04 = _read_report("04-qualidade-e-testes.md")
    assert "TEST-08" in r04
    assert "AUD-F-014" in r04


# ---------------------------------------------------------------------------
# Dimension E: Documentation & Traceability (C34..C40 / DOC-01..DOC-07)
# ---------------------------------------------------------------------------


def test_c34_doc_01_readme_python_blocks_executed() -> None:
    r05 = _read_report("05-rastreabilidade.md")
    assert "DOC-01" in r05
    assert "AUD-F-001" in r05


def test_c35_doc_02_readme_directory_tree_compared() -> None:
    r05 = _read_report("05-rastreabilidade.md")
    assert not (REPO_ROOT / "src" / "experimental_ml" / "core" / "exceptions.py").exists()
    assert not (REPO_ROOT / "src" / "experimental_ml" / "core" / "identifiers.py").exists()
    assert (REPO_ROOT / "src" / "experimental_ml" / "core" / "types.py").exists()
    assert "AUD-F-002" in r05


def test_c36_doc_03_counts_statuses_commits_verified() -> None:
    import experimental_ml.data

    assert len(experimental_ml.data.__all__) == 13
    r05 = _read_report("05-rastreabilidade.md")
    assert "DOC-03" in r05


def test_c37_doc_04_documented_symbols_importable_checked() -> None:
    r05 = _read_report("05-rastreabilidade.md")
    assert "DOC-04" in r05
    assert "column_semantic_types" in r05
    assert "tolerance_rtol" in r05


def test_c38_doc_05_hash_contract_contradictions_checked() -> None:
    from experimental_ml.core.hashing import dataset_hash

    assert dataset_hash({"x": [1.0], "y": [2.0]}) != dataset_hash({"y": [2.0], "x": [1.0]})
    r05 = _read_report("05-rastreabilidade.md")
    assert "AUD-F-010" in r05


def test_c39_doc_06_traceability_matrix_complete() -> None:
    r05 = _read_report("05-rastreabilidade.md")
    for code in ["RF1.1", "RF1.2", "RF1.3", "RF1.7", "RNF01", "RNF02", "RNF03", "RNF04", "RNF05", "RNF06", "RNF07"]:
        assert code in r05, f"Missing {code} in 05-rastreabilidade.md"
    for ca in ["CA-GER-02", "CA-GER-03", "CA-COND-REG-01", "CA-COND-CLAS-01", "CA-E1-01"]:
        assert ca in r05, f"Missing {ca} in 05-rastreabilidade.md"
    for ta in ["TA-M1.1", "TA-M1.2", "TA-M1.3", "TA-M1.4"]:
        assert ta in r05, f"Missing {ta} in 05-rastreabilidade.md"


def test_c40_doc_07_governance_artifacts_verified() -> None:
    assert not (REPO_ROOT / ".specs" / "features" / "m1-1-setup-cli-smoke" / "verification.md").exists()
    assert (REPO_ROOT / ".specs" / "features" / "m1-2-core" / "verification.md").exists()
    assert (REPO_ROOT / ".specs" / "features" / "m1-3-metrics" / "verification.md").exists()
    assert (REPO_ROOT / ".specs" / "features" / "m1-4-datasets-schemas" / "verification.md").exists()
    r05 = _read_report("05-rastreabilidade.md")
    assert "DOC-07" in r05


# ---------------------------------------------------------------------------
# Dimension F: M2 Readiness & Governance Closure (C41..C48 / READY-01..READY-08)
# ---------------------------------------------------------------------------


def test_c41_ready_01_m2_consumed_interfaces_evaluated() -> None:
    r08 = _read_report("08-parecer.md")
    for contract in [
        "profile_dataset",
        "DatasetProfile",
        "PreparationPlan",
        "sanitize_dataset",
        "SanitizedDatasetView",
        "build_partition_plan",
        "validate_partition_plan",
        "PartitionPlan",
    ]:
        assert contract in r08, f"Missing M2 contract {contract} in 08-parecer.md"


def test_c42_ready_02_open_m2_decisions_listed() -> None:
    r08 = _read_report("08-parecer.md")
    assert "READY-02" in r08
    for fid in ["AUD-F-005", "AUD-F-011"]:
        assert fid in r08


def test_c43_ready_03_findings_register_schema_complete() -> None:
    r06 = _read_report("06-achados.md")
    required_fields = [
        "**Dimensão:**",
        "**Categoria:**",
        "**Severidade:**",
        "**Localização:**",
        "**Evidência Reprodutível:**",
        "**Impacto:**",
        "**Justificativa da Severidade:**",
        "**Recomendação:**",
    ]
    blocks = re.split(r"^### `?(AUD-F-\d{3})`?", r06, flags=re.MULTILINE)
    finding_ids = blocks[1::2]
    finding_bodies = blocks[2::2]
    assert len(finding_ids) == 16
    for fid, body in zip(finding_ids, finding_bodies, strict=True):
        for field in required_fields:
            assert field in body, f"{fid} missing schema field {field}"


def test_c44_ready_04_documented_limitations_cited() -> None:
    r06 = _read_report("06-achados.md")
    assert "LIMITAÇÃO DOCUMENTADA" in r06
    assert "ESPECIFICACAO_REQUISITOS.md" in r06
    assert "RNF06" in r06


def test_c45_ready_05_remediation_plan_prioritized() -> None:
    r07 = _read_report("07-plano-correcoes.md")
    assert "Faixa P0" in r07
    assert "Faixa P1" in r07
    assert "Faixa P2" in r07
    for fid in [f"AUD-F-{i:03d}" for i in range(1, 17)]:
        assert fid in r07, f"{fid} missing from remediation plan"


def test_c46_ready_06_verdict_matches_decision_rule() -> None:
    r06 = _read_report("06-achados.md")
    r08 = _read_report("08-parecer.md")
    blocks = re.split(r"^### `?(AUD-F-\d{3})`?", r06, flags=re.MULTILINE)
    bodies = blocks[2::2]
    critico_count = sum(1 for b in bodies if "**Severidade:** `CRÍTICO`" in b)
    alto_defeito_count = sum(
        1 for b in bodies if "**Severidade:** `ALTO`" in b and "**Categoria:** `DEFEITO`" in b
    )
    assert critico_count == 0
    assert alto_defeito_count == 4
    expected_verdict = "NÃO APTO" if (critico_count > 0 or alto_defeito_count > 0) else "APTO COM RESSALVAS"
    assert f"`{expected_verdict}`" in r08


def test_c47_ready_07_independent_verification_recorded() -> None:
    r08 = _read_report("08-parecer.md")
    assert "READY-07" in r08
    for fid in ["AUD-F-001", "AUD-F-004", "AUD-F-005", "AUD-F-006", "AUD-F-008", "AUD-F-009"]:
        assert fid in r08


def test_c48_ready_08_unreproduced_findings_policy() -> None:
    r06 = _read_report("06-achados.md")
    blocks = re.split(r"^### `?(AUD-F-\d{3})`?", r06, flags=re.MULTILINE)
    bodies = blocks[2::2]
    assert len(bodies) == 16
    for b in bodies:
        assert "**Status:** `NÃO REPRODUZIDO`" not in b
