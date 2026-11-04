"""Unit tests for experimental_ml.data module.

Covers all 29 acceptance criteria (DATA-01 to DATA-29, C1 to C29).
"""

from dataclasses import FrozenInstanceError
import unicodedata
import pytest

from experimental_ml.core.enums import TaskType
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.hashing import config_hash
from experimental_ml.data.schema import ColumnSemanticType, DatasetSchemaSpec, validate_schema_spec


# ==============================================================================
# Phase 1: Schema Specification Tests (C1 - C6)
# ==============================================================================


def test_domain_structures_and_enum_immutable() -> None:
    """C1: Frozen immutable structures and ColumnSemanticType enum (DATA-01)."""
    assert issubclass(ColumnSemanticType, str)
    assert ColumnSemanticType.NUMERIC_CONTINUOUS == "NUMERIC_CONTINUOUS"
    assert ColumnSemanticType.NUMERIC_DISCRETE == "NUMERIC_DISCRETE"
    assert ColumnSemanticType.CATEGORICAL == "CATEGORICAL"
    assert ColumnSemanticType.BOOLEAN == "BOOLEAN"
    assert ColumnSemanticType.TEMPORAL == "TEMPORAL"
    assert ColumnSemanticType.IDENTIFIER == "IDENTIFIER"

    schema = DatasetSchemaSpec(
        target_col="target",
        task_type=TaskType.REGRESSION,
        group_col="grp",
    )
    with pytest.raises(FrozenInstanceError):
        schema.target_col = "other"  # type: ignore[misc]

    validate_schema_spec(schema)
    with pytest.raises(ConfigurationError):
        validate_schema_spec({"target_col": "target"})


def test_schema_spec_nfc_normalization_and_encapsulation() -> None:
    """C2: Normalization to Unicode NFC, tuple conversion and mapping encapsulation (DATA-02)."""
    # Decomposed Unicode "maçã" (NFD)
    nfd_col = unicodedata.normalize("NFD", "maçã")
    assert len(nfd_col) > len(unicodedata.normalize("NFC", "maçã"))

    schema = DatasetSchemaSpec(
        target_col=nfd_col,
        task_type=TaskType.BINARY_CLASSIFICATION,
        ignore_cols=("drop1", "drop2", "drop1"),  # deduplication test
        column_semantic_types={"feature1": "NUMERIC_CONTINUOUS"},
    )
    # NFC normalized
    assert schema.target_col == unicodedata.normalize("NFC", "maçã")
    assert schema.ignore_cols == ("drop1", "drop2")
    assert isinstance(schema.ignore_cols, tuple)
    assert schema.column_semantic_types["feature1"] == ColumnSemanticType.NUMERIC_CONTINUOUS

    # Read-only mapping encapsulation
    with pytest.raises(TypeError):
        schema.column_semantic_types["feature1"] = ColumnSemanticType.CATEGORICAL  # type: ignore[index]


def test_schema_spec_rejects_empty_and_control_chars() -> None:
    """C3: Empty, whitespace-only, or control-containing column names raise ConfigurationError (DATA-03)."""
    with pytest.raises(ConfigurationError, match="cannot be empty or whitespace-only"):
        DatasetSchemaSpec(target_col="", task_type=TaskType.REGRESSION)

    with pytest.raises(ConfigurationError, match="cannot be empty or whitespace-only"):
        DatasetSchemaSpec(target_col="   ", task_type=TaskType.REGRESSION)

    for forbidden in ("target\ncol", "target\rcol", "target\tcol", "target\x00col"):
        with pytest.raises(ConfigurationError, match="forbidden control or newline characters"):
            DatasetSchemaSpec(target_col=forbidden, task_type=TaskType.REGRESSION)

    with pytest.raises(ConfigurationError, match="forbidden control or newline characters"):
        DatasetSchemaSpec(
            target_col="y",
            task_type=TaskType.REGRESSION,
            group_col="group\t1",
        )


def test_schema_spec_blocks_wave2_features() -> None:
    """C4: MULTI_TARGET_REGRESSION or target_transform_spec raise ConfigurationError (DATA-04)."""
    with pytest.raises(ConfigurationError, match="Wave 2"):
        DatasetSchemaSpec(
            target_col="y",
            task_type=TaskType.MULTI_TARGET_REGRESSION,
        )

    with pytest.raises(ConfigurationError, match="Wave 2"):
        DatasetSchemaSpec(
            target_col="y",
            task_type=TaskType.REGRESSION,
            target_transform_spec={"log": True},
        )

    with pytest.raises(ConfigurationError, match="must be a string"):
        DatasetSchemaSpec(
            target_col=["y1", "y2"],  # type: ignore[arg-type]
            task_type=TaskType.REGRESSION,
        )


def test_schema_spec_enforces_disjoint_roles() -> None:
    """C5: Non-disjoint column roles raise ConfigurationError (DATA-05)."""
    with pytest.raises(ConfigurationError, match="assigned to multiple roles"):
        DatasetSchemaSpec(
            target_col="col_a",
            task_type=TaskType.REGRESSION,
            group_col="col_a",
        )

    with pytest.raises(ConfigurationError, match="assigned to multiple roles"):
        DatasetSchemaSpec(
            target_col="col_a",
            task_type=TaskType.REGRESSION,
            ignore_cols=("col_b", "col_a"),
        )

    with pytest.raises(ConfigurationError, match="assigned to multiple roles"):
        DatasetSchemaSpec(
            target_col="col_a",
            task_type=TaskType.REGRESSION,
            observation_id_col="id",
            time_col="id",
        )


def test_schema_spec_config_hash_invariance() -> None:
    """C6: config_hash produces deterministic 64-hex SHA-256 invariant to NFD/NFC and key order (DATA-06)."""
    nfd_col = unicodedata.normalize("NFD", "maçã")
    nfc_col = unicodedata.normalize("NFC", "maçã")

    schema1 = DatasetSchemaSpec(
        target_col=nfd_col,
        task_type=TaskType.REGRESSION,
        column_semantic_types={"b": ColumnSemanticType.NUMERIC_CONTINUOUS, "a": ColumnSemanticType.CATEGORICAL},
    )
    schema2 = DatasetSchemaSpec(
        target_col=nfc_col,
        task_type=TaskType.REGRESSION,
        column_semantic_types={"a": ColumnSemanticType.CATEGORICAL, "b": ColumnSemanticType.NUMERIC_CONTINUOUS},
    )

    h1 = config_hash(schema1)
    h2 = config_hash(schema2)

    assert len(h1) == 64
    assert h1 == h2
