"""Unit test suite for experimental_ml.core.

Covers all 18 requirements and acceptance checks (C1-C18) for milestone M1.2:
- Domain identifiers and immutability (CORE-01, CORE-02, CORE-03)
- Fundamental enums and serialization (CORE-04, CORE-05, CORE-06)
- Deterministic seed derivation (CORE-07, CORE-08, CORE-09)
- Canonical config_hash compliant with ADR-007 (CORE-10, CORE-11, CORE-12, CORE-13)
- Tabular dataset_hash for disk and memory (CORE-14, CORE-15, CORE-16)
- Diagnostic findings and core exceptions (CORE-17, CORE-18)
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import unicodedata

import numpy as np
import pytest

from experimental_ml.core import (
    AggregationScope,
    ArtifactId,
    CellId,
    ComparisonId,
    ConfigurationError,
    ContractViolationError,
    DataIntegrityError,
    ErrorPolicy,
    ExecutionStatus,
    ExperimentId,
    ExperimentalMLError,
    Finding,
    FindingSeverity,
    MetricDirection,
    MetricStatus,
    ModelId,
    ObservationId,
    PartitionPlanId,
    ScenarioId,
    TaskType,
    config_hash,
    dataset_hash,
    derive_seeds,
    make_finding,
    make_warning,
    spawn_child_seeds,
)


# =============================================================================
# C1: Domain identifiers are immutable string types (CORE-01)
# =============================================================================
def test_identifier_types_immutable() -> None:
    """Validate that all 8 domain identifier types inherit from str and are immutable."""
    id_classes = [
        ExperimentId,
        PartitionPlanId,
        ScenarioId,
        ModelId,
        CellId,
        ComparisonId,
        ArtifactId,
        ObservationId,
    ]
    for cls in id_classes:
        instance = cls("test_value_123")
        assert isinstance(instance, str)
        assert isinstance(instance, cls)
        assert instance == "test_value_123"

        # Check immutability (cannot reassign string buffer or modify contents)
        with pytest.raises((TypeError, AttributeError)):
            instance[0] = "X"  # type: ignore[index]


# =============================================================================
# C2: Identifier constructors validate non-empty and stripped strings (CORE-02)
# =============================================================================
def test_identifier_validation_non_empty() -> None:
    """Validate that identifier constructors strip whitespace and preserve valid identifiers."""
    id_classes = [
        ExperimentId,
        PartitionPlanId,
        ScenarioId,
        ModelId,
        CellId,
        ComparisonId,
        ArtifactId,
        ObservationId,
    ]
    for cls in id_classes:
        instance = cls("   valid_id_42   ")
        assert instance == "valid_id_42"
        assert len(instance) == len("valid_id_42")


# =============================================================================
# C3: Empty or invalid identifiers raise ValueError (CORE-03)
# =============================================================================
def test_identifier_invalid_value_error() -> None:
    """Validate that empty strings, whitespace-only, newlines, tabs, and non-strings raise ValueError/TypeError."""
    id_classes = [
        ExperimentId,
        PartitionPlanId,
        ScenarioId,
        ModelId,
        CellId,
        ComparisonId,
        ArtifactId,
        ObservationId,
    ]
    invalid_inputs = ["", "   ", "\t", "\n", "id_with_\n_newline", "id_with_\r_return", "id_with_\t_tab"]
    for cls in id_classes:
        for bad_input in invalid_inputs:
            with pytest.raises(ValueError):
                cls(bad_input)

        with pytest.raises((TypeError, ValueError)):
            cls(12345)  # type: ignore[arg-type]


# =============================================================================
# C4: TaskType and ExecutionStatus define exact specified canonical members (CORE-04)
# =============================================================================
def test_task_type_and_execution_status_enums() -> None:
    """Validate TaskType and ExecutionStatus have all canonical members and direct str equality."""
    assert TaskType.REGRESSION == "REGRESSION"
    assert TaskType.MULTI_TARGET_REGRESSION == "MULTI_TARGET_REGRESSION"
    assert TaskType.BINARY_CLASSIFICATION == "BINARY_CLASSIFICATION"
    assert TaskType.MULTICLASS_CLASSIFICATION == "MULTICLASS_CLASSIFICATION"
    assert len(TaskType) == 4

    assert ExecutionStatus.PENDING == "PENDING"
    assert ExecutionStatus.RUNNING == "RUNNING"
    assert ExecutionStatus.COMPLETED == "COMPLETED"
    assert ExecutionStatus.FAILED == "FAILED"
    assert ExecutionStatus.CANCELLED == "CANCELLED"
    assert len(ExecutionStatus) == 5


# =============================================================================
# C5: FindingSeverity, MetricDirection, and AggregationScope define exact members (CORE-05)
# =============================================================================
def test_finding_metric_aggregation_enums() -> None:
    """Validate FindingSeverity, MetricDirection, and AggregationScope members."""
    assert FindingSeverity.CONFIRMED_ISSUE == "CONFIRMED_ISSUE"
    assert FindingSeverity.HEURISTIC_WARNING == "HEURISTIC_WARNING"
    assert len(FindingSeverity) == 2

    assert MetricDirection.MAXIMIZE == "MAXIMIZE"
    assert MetricDirection.MINIMIZE == "MINIMIZE"
    assert len(MetricDirection) == 2

    assert AggregationScope.FOLD_AGGREGATION == "FOLD_AGGREGATION"
    assert AggregationScope.REPETITION_AGGREGATION == "REPETITION_AGGREGATION"
    assert AggregationScope.OVERALL_AGGREGATION == "OVERALL_AGGREGATION"
    assert len(AggregationScope) == 3


# =============================================================================
# C6: MetricStatus and ErrorPolicy define exact members and serialize to JSON (CORE-06)
# =============================================================================
def test_metric_status_and_error_policy_enums() -> None:
    """Validate MetricStatus and ErrorPolicy members and standard JSON serialization."""
    assert MetricStatus.VALID == "VALID"
    assert MetricStatus.UNDEFINED_NAN == "UNDEFINED_NAN"
    assert MetricStatus.PARTIAL_COVERAGE == "PARTIAL_COVERAGE"
    assert MetricStatus.UNRANKABLE == "UNRANKABLE"
    assert len(MetricStatus) == 4

    assert ErrorPolicy.FAULT_TOLERANT == "FAULT_TOLERANT"
    assert ErrorPolicy.FAIL_FAST == "FAIL_FAST"
    assert len(ErrorPolicy) == 2

    # Direct JSON serialization test
    payload = {
        "status": MetricStatus.UNDEFINED_NAN,
        "policy": ErrorPolicy.FAIL_FAST,
    }
    dumped = json.dumps(payload)
    loaded = json.loads(dumped)
    assert loaded["status"] == "UNDEFINED_NAN"
    assert loaded["policy"] == "FAIL_FAST"


# =============================================================================
# C7: Function derive_seeds produces tuple of integers via SeedSequence (CORE-07)
# =============================================================================
def test_derive_seeds_returns_tuple() -> None:
    """Validate that derive_seeds returns a tuple of integers with the requested count."""
    seeds = derive_seeds(12345, 5)
    assert isinstance(seeds, tuple)
    assert len(seeds) == 5
    for s in seeds:
        assert isinstance(s, int)


# =============================================================================
# C8: Same master seed produces identical seed tuple deterministically (CORE-08)
# =============================================================================
def test_derive_seeds_determinism() -> None:
    """Validate that derive_seeds is strictly deterministic and distinct seeds are produced."""
    seeds_a = derive_seeds(42, 10)
    seeds_b = derive_seeds(42, 10)
    assert seeds_a == seeds_b

    # Seeds within the tuple should be distinct with high probability
    assert len(set(seeds_a)) == 10

    # Different master seed produces different seeds
    seeds_c = derive_seeds(43, 10)
    assert seeds_a != seeds_c


# =============================================================================
# C9: Function spawn_child_seeds derives independent seeds and rejects count < 1 (CORE-09)
# =============================================================================
def test_spawn_child_seeds_validation() -> None:
    """Validate spawn_child_seeds functionality and input validation."""
    children = spawn_child_seeds(100, 4)
    assert isinstance(children, tuple)
    assert len(children) == 4
    assert len(set(children)) == 4

    # Validation: count < 1
    with pytest.raises(ValueError):
        spawn_child_seeds(100, 0)
    with pytest.raises(ValueError):
        spawn_child_seeds(100, -5)

    with pytest.raises(ValueError):
        derive_seeds(100, 0)
    with pytest.raises(ValueError):
        derive_seeds(100, -2)


# =============================================================================
# C10: Function config_hash returns 64-character lowercase hexadecimal SHA-256 (CORE-10)
# =============================================================================
def test_config_hash_sha256_format() -> None:
    """Validate that config_hash returns a 64-character lowercase hexadecimal SHA-256 string."""
    h = config_hash({"model": "random_forest", "n_estimators": 100})
    assert isinstance(h, str)
    assert len(h) == 64
    assert h.islower()
    assert all(c in "0123456789abcdef" for c in h)


# =============================================================================
# C11: Function config_hash normalizes Unicode NFC and sorts mapping keys (CORE-11)
# =============================================================================
def test_config_hash_unicode_and_key_order() -> None:
    """Validate NFC normalization and key order invariance in config_hash."""
    # Unicode NFC vs NFD
    s_nfc = "coração"
    s_nfd = unicodedata.normalize("NFD", s_nfc)
    assert s_nfc != s_nfd  # different code points in memory
    assert config_hash({"text": s_nfc}) == config_hash({"text": s_nfd})

    # Key insertion order invariance
    dict_1 = {"alpha": 1, "beta": 2, "gamma": 3}
    dict_2 = {"gamma": 3, "alpha": 1, "beta": 2}
    assert config_hash(dict_1) == config_hash(dict_2)


# =============================================================================
# C12: Function config_hash strictly distinguishes scalar & collection types (CORE-12)
# =============================================================================
def test_config_hash_strict_types() -> None:
    """Validate strict differentiation of bool vs int, int vs float, and tuple vs list."""
    assert config_hash(True) != config_hash(1)
    assert config_hash(False) != config_hash(0)
    assert config_hash(1) != config_hash(1.0)
    assert config_hash({"k": True}) != config_hash({"k": 1})
    assert config_hash({"k": 1}) != config_hash({"k": 1.0})

    # Tuple vs list
    assert config_hash([1, 2, 3]) != config_hash((1, 2, 3))

    # Set order invariance
    set_1 = {10, 20, 30}
    set_2 = {30, 10, 20}
    assert config_hash(set_1) == config_hash(set_2)


# =============================================================================
# C13: Function config_hash normalizes -0.0 to 0.0 and canonicalizes NaN/Inf (CORE-13)
# =============================================================================
def test_config_hash_special_floats() -> None:
    """Validate normalization of -0.0 to 0.0 and canonical handling of NaN and Inf."""
    assert config_hash(-0.0) == config_hash(0.0)
    assert config_hash({"zero": -0.0}) == config_hash({"zero": 0.0})

    # NaN payloads normalization
    h_nan_1 = config_hash(float("nan"))
    h_nan_2 = config_hash(np.nan)
    assert h_nan_1 == h_nan_2

    # Inf and -Inf
    h_pos_inf = config_hash(float("inf"))
    h_neg_inf = config_hash(float("-inf"))
    assert h_pos_inf != h_neg_inf
    assert h_pos_inf != h_nan_1

    # Circular reference check
    circular: list[object] = []
    circular.append(circular)
    with pytest.raises(ValueError, match="Circular reference"):
        config_hash(circular)


# =============================================================================
# C14: Function dataset_hash computes SHA-256 for CSV/TXT file and schema (CORE-14)
# =============================================================================
def test_dataset_hash_file_and_schema(tmp_path: Path) -> None:
    """Validate dataset_hash on raw files with and without schema."""
    csv_file = tmp_path / "dataset.csv"
    csv_file.write_text("feature1,feature2,target\n1.0,2.0,10.0\n3.0,4.0,20.0\n", encoding="utf-8")

    h_no_schema = dataset_hash(csv_file)
    assert len(h_no_schema) == 64
    assert h_no_schema.islower()

    # Schema changes the hash deterministically
    schema_1 = {"target_col": "target", "task_type": "REGRESSION"}
    schema_2 = {"target_col": "target", "task_type": "BINARY_CLASSIFICATION"}

    h_schema_1 = dataset_hash(csv_file, schema=schema_1)
    h_schema_2 = dataset_hash(csv_file, schema=schema_2)

    assert h_schema_1 != h_no_schema
    assert h_schema_1 != h_schema_2
    assert dataset_hash(csv_file, schema=schema_1) == h_schema_1


# =============================================================================
# C15: Function dataset_hash computes deterministic hash for in-memory data (CORE-15)
# =============================================================================
def test_dataset_hash_in_memory() -> None:
    """Validate in-memory tabular hashing sensitivity to values, column names, types and order."""
    data_base = {"col_a": [1, 2, 3], "col_b": [4.0, 5.0, 6.0]}
    h_base = dataset_hash(data_base)
    assert len(h_base) == 64

    # Identical data produces identical hash
    data_identical = {"col_a": [1, 2, 3], "col_b": [4.0, 5.0, 6.0]}
    assert dataset_hash(data_identical) == h_base

    # Different column name
    data_diff_col = {"col_c": [1, 2, 3], "col_b": [4.0, 5.0, 6.0]}
    assert dataset_hash(data_diff_col) != h_base

    # Different data type (float instead of int)
    data_diff_type = {"col_a": [1.0, 2.0, 3.0], "col_b": [4.0, 5.0, 6.0]}
    assert dataset_hash(data_diff_type) != h_base

    # Different observation order (row 1 and 2 swapped)
    data_diff_order = {"col_a": [2, 1, 3], "col_b": [5.0, 4.0, 6.0]}
    assert dataset_hash(data_diff_order) != h_base

    # 2D NumPy array hashing
    arr_2d = np.array([[1.0, 2.0], [3.0, 4.0]], dtype="<f8")
    h_arr = dataset_hash(arr_2d)
    assert len(h_arr) == 64


# =============================================================================
# C16: Function dataset_hash raises FileNotFoundError for nonexistent file (CORE-16)
# =============================================================================
def test_dataset_hash_file_not_found() -> None:
    """Validate that dataset_hash raises FileNotFoundError for missing files."""
    missing_path = "non_existent_dataset_123456.csv"
    with pytest.raises(FileNotFoundError):
        dataset_hash(missing_path)

    missing_obj = Path("/tmp/definitely_not_existing_path_98765.txt")
    with pytest.raises(FileNotFoundError):
        dataset_hash(missing_obj)


# =============================================================================
# C17: Constructors make_finding and make_warning create structured findings (CORE-17)
# =============================================================================
def test_make_finding_and_make_warning() -> None:
    """Validate make_finding (CONFIRMED_ISSUE) and make_warning (HEURISTIC_WARNING)."""
    ctx = {"column": "feature_x", "variance": 0.0}
    issue = make_finding(code="E1_ZERO_VARIANCE", message="Column has zero variance", context=ctx)

    assert isinstance(issue, Finding)
    assert issue.severity == FindingSeverity.CONFIRMED_ISSUE
    assert issue.code == "E1_ZERO_VARIANCE"
    assert issue.message == "Column has zero variance"
    assert issue.context == ctx

    warning = make_warning(code="W1_HIGH_CARDINALITY", message="Column may be an identifier")
    assert isinstance(warning, Finding)
    assert warning.severity == FindingSeverity.HEURISTIC_WARNING
    assert warning.code == "W1_HIGH_CARDINALITY"
    assert warning.message == "Column may be an identifier"
    assert warning.context is None


# =============================================================================
# C18: Framework exceptions are defined and Finding objects are immutable (CORE-18)
# =============================================================================
def test_core_exceptions_and_finding_immutability() -> None:
    """Validate custom exceptions hierarchy, raise behavior, and Finding immutability."""
    # Exception hierarchy
    assert issubclass(ContractViolationError, ExperimentalMLError)
    assert issubclass(DataIntegrityError, ExperimentalMLError)
    assert issubclass(ConfigurationError, ExperimentalMLError)
    assert issubclass(ExperimentalMLError, Exception)

    with pytest.raises(ContractViolationError, match="Violated contract"):
        raise ContractViolationError("Violated contract")

    with pytest.raises(DataIntegrityError, match="Corrupt data"):
        raise DataIntegrityError("Corrupt data")

    with pytest.raises(ConfigurationError, match="Bad config"):
        raise ConfigurationError("Bad config")

    # Immutability of Finding
    finding = make_finding("C1", "Msg")
    with pytest.raises((TypeError, AttributeError)):
        finding.code = "C2"  # type: ignore[misc]

    with pytest.raises((TypeError, AttributeError)):
        finding.severity = FindingSeverity.HEURISTIC_WARNING  # type: ignore[misc]
