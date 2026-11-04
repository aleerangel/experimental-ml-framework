"""Unit tests for experimental_ml.data module.

Covers all 29 acceptance criteria (DATA-01 to DATA-29, C1 to C29).
"""

from dataclasses import FrozenInstanceError
import unicodedata
import numpy as np
import pytest

from experimental_ml.core.enums import TaskType
from experimental_ml.core.findings import ConfigurationError, DataIntegrityError
from experimental_ml.core.hashing import config_hash
from experimental_ml.core.types import ObservationId
from experimental_ml.data.schema import ColumnSemanticType, DatasetSchemaSpec, validate_schema_spec
from experimental_ml.data.types import ColumnDescriptor, DatasetBundle
from experimental_ml.data.parsing import (
    SUPPORTED_DELIMITERS,
    detect_delimiter,
    parse_tabular_text,
)
from experimental_ml.data.validation import (
    assign_or_validate_observation_ids,
    derive_column_descriptor,
    validate_dataset_schema,
)


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

    # ColumnDescriptor test
    desc = ColumnDescriptor(
        name="target",
        index=0,
        role="target",
        physical_type="float64",
        semantic_type=ColumnSemanticType.NUMERIC_CONTINUOUS,
        is_semantic_declared=False,
        n_missing=0,
        memory_bytes=800,
    )
    with pytest.raises(FrozenInstanceError):
        desc.name = "new_name"  # type: ignore[misc]

    # DatasetBundle test
    bundle = DatasetBundle(
        schema=schema,
        n_rows=10,
        n_cols=1,
        column_names=("target",),
        feature_cols=(),
        columns={"target": np.zeros(10)},
        descriptors={"target": desc},
        observation_ids=tuple(ObservationId(f"obs_{i:06d}") for i in range(10)),
        dataset_hash="a" * 64,
        raw_source_hash="b" * 64,
        schema_hash="c" * 64,
        memory_bytes=800,
    )
    with pytest.raises(FrozenInstanceError):
        bundle.n_rows = 999  # type: ignore[misc]

    # MappingProxy encapsulation
    with pytest.raises(TypeError):
        bundle.columns["target"] = np.ones(10)  # type: ignore[index]


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


# ==============================================================================
# Phase 1: Parsing Engine & Delimiter Detection Tests (C15 - C22)
# ==============================================================================


def test_tabular_parsing_supported_delimiters_and_quotes() -> None:
    """C15: Tabular parser supports delimiters ,, ;, \t, |, whitespace and RFC 4180 quotes (DATA-15)."""
    # Test comma with RFC 4180 quotes and escaped quotes
    csv_text = [
        'id,name,value\n',
        '1,"Silva, João",10.5\n',
        '2,"Contains ""double quotes""",20.0\n',
    ]
    cols, data = parse_tabular_text(csv_text, delimiter=",")
    assert cols == ("id", "name", "value")
    assert data["name"] == ["Silva, João", 'Contains "double quotes"']

    # Test semicolon
    semicolon_text = ['a;b;c\n', '1;2;3\n']
    cols_s, data_s = parse_tabular_text(semicolon_text, delimiter=";")
    assert cols_s == ("a", "b", "c")
    assert data_s["b"] == ["2"]

    # Test tab
    tab_text = ['col1\tcol2\n', 'v1\tv2\n']
    cols_t, data_t = parse_tabular_text(tab_text, delimiter="\t")
    assert cols_t == ("col1", "col2")

    # Test pipe
    pipe_text = ['x|y\n', '10|20\n']
    cols_p, data_p = parse_tabular_text(pipe_text, delimiter="|")
    assert cols_p == ("x", "y")

    # Test whitespace sequences
    ws_text = ['f1   f2     f3\n', '10.0   "hello world"   30\n']
    cols_w, data_w = parse_tabular_text(ws_text, delimiter="whitespace")
    assert cols_w == ("f1", "f2", "f3")
    assert data_w["f2"] == ["hello world"]


def test_delimiter_sniffer_automatic_detection() -> None:
    """C16: Automatic delimiter detection verifies constant column count M >= 2 (DATA-16)."""
    sample = [
        "colA,colB,colC\n",
        "1,2,3\n",
        "4,5,6\n",
    ]
    detected = detect_delimiter(sample)
    assert detected == ","

    tsv_sample = ["a\tb\tc\n", "10\t20\t30\n"]
    assert detect_delimiter(tsv_sample) == "\t"


def test_delimiter_sniffer_ambiguity_raises_error() -> None:
    """C17: Ambiguous or non-uniform delimiters raise DataIntegrityError (DATA-17)."""
    # Equal commas and semicolons across lines: both give uniform counts
    ambiguous_sample = [
        "a,b;c,d\n",
        "1,2;3,4\n",
    ]
    with pytest.raises(DataIntegrityError, match="ambiguous"):
        detect_delimiter(ambiguous_sample)

    # Inconsistent delimiter: line 1 has 3 commas, line 2 has 1 comma
    inconsistent_sample = [
        "a,b,c\n",
        "single_token\n",
    ]
    with pytest.raises(DataIntegrityError, match="detection failed"):
        detect_delimiter(inconsistent_sample)


def test_explicit_delimiter_overrides_detection() -> None:
    """C18: Explicit delimiter overrides automatic detection and parses strictly (DATA-18)."""
    text = [
        "colA;colB;colC\n",
        "1;2;3\n",
    ]
    # Even if delimiter is explicit, parse_tabular_text parses strictly
    cols, data = parse_tabular_text(text, delimiter=";")
    assert cols == ("colA", "colB", "colC")
    assert data["colB"] == ["2"]


def test_ragged_rows_raise_data_integrity_error() -> None:
    """C19: Ragged rows raise DataIntegrityError detailing line and counts (DATA-19)."""
    ragged = [
        "a,b,c\n",
        "1,2,3\n",
        "4,5\n",  # line 3: 2 columns instead of 3
    ]
    with pytest.raises(DataIntegrityError, match="Line 3: ragged row encountered. Expected 3 columns, got 2"):
        parse_tabular_text(ragged, delimiter=",")


def test_empty_or_zero_rows_file_raises_error() -> None:
    """C20: Empty file, whitespace-only, or header-only raises DataIntegrityError (DATA-20)."""
    with pytest.raises(DataIntegrityError, match="empty or contains only whitespace"):
        parse_tabular_text([], delimiter=",")

    with pytest.raises(DataIntegrityError, match="empty or contains only whitespace"):
        parse_tabular_text(["   \n", "\t\n"], delimiter=",")

    with pytest.raises(DataIntegrityError, match="zero data rows"):
        parse_tabular_text(["col1,col2\n"], delimiter=",", has_header=True)


def test_parsing_has_header_false_and_column_names() -> None:
    """C21: has_header=False assigns column_names or generates col_j, checks length mismatch (DATA-21)."""
    text = [
        "1,2,3\n",
        "4,5,6\n",
    ]
    # Generated positional names
    cols, data = parse_tabular_text(text, delimiter=",", has_header=False)
    assert cols == ("col_0", "col_1", "col_2")
    assert data["col_0"] == ["1", "4"]

    # Explicit column names
    cols_named, data_named = parse_tabular_text(
        text, delimiter=",", has_header=False, column_names=["x", "y", "z"]
    )
    assert cols_named == ("x", "y", "z")
    assert data_named["z"] == ["3", "6"]

    # Length mismatch
    with pytest.raises(DataIntegrityError, match="does not match"):
        parse_tabular_text(text, delimiter=",", has_header=False, column_names=["x", "y"])


def test_header_validation_empty_or_duplicate_names() -> None:
    """C22: Empty header column after trimming or duplicate names raise DataIntegrityError (DATA-22)."""
    # Empty column name
    with pytest.raises(DataIntegrityError, match="empty after trimming"):
        parse_tabular_text(["a, ,c\n", "1,2,3\n"], delimiter=",")

    # Duplicate column name
    with pytest.raises(DataIntegrityError, match="duplicate column name"):
        parse_tabular_text(["a,b,a\n", "1,2,3\n"], delimiter=",")


# ==============================================================================
# Phase 2: Schema Validation & ObservationId Tests (C23 - C27)
# ==============================================================================


def test_column_descriptor_fields_and_roles() -> None:
    """C23: ColumnDescriptor correctly populated with index, role, physical, semantic, nulls (DATA-23)."""
    schema = DatasetSchemaSpec(
        target_col="price",
        task_type=TaskType.REGRESSION,
        group_col="city",
        observation_id_col="id",
        time_col="timestamp",
        ignore_cols=("junk",),
    )
    desc_target = derive_column_descriptor(
        name="price",
        index=0,
        role="target",
        physical_type="float64",
        n_missing=5,
        memory_bytes=800,
        schema=schema,
    )
    assert desc_target.name == "price"
    assert desc_target.index == 0
    assert desc_target.role == "target"
    assert desc_target.physical_type == "float64"
    assert desc_target.semantic_type == ColumnSemanticType.NUMERIC_CONTINUOUS
    assert desc_target.is_semantic_declared is False
    assert desc_target.n_missing == 5
    assert desc_target.memory_bytes == 800


def test_semantic_types_declared_vs_default_fallbacks() -> None:
    """C24: Explicit column_semantic_types sets is_declared=True, default fallbacks tested (DATA-24)."""
    schema = DatasetSchemaSpec(
        target_col="status",
        task_type=TaskType.BINARY_CLASSIFICATION,
        column_semantic_types={"feature_int": ColumnSemanticType.CATEGORICAL},
    )
    # Explicitly declared
    desc_declared = derive_column_descriptor(
        name="feature_int",
        index=1,
        role="feature",
        physical_type="int64",
        n_missing=0,
        memory_bytes=800,
        schema=schema,
    )
    assert desc_declared.semantic_type == ColumnSemanticType.CATEGORICAL
    assert desc_declared.is_semantic_declared is True

    # Fallback for target under binary classification
    desc_target = derive_column_descriptor(
        name="status",
        index=0,
        role="target",
        physical_type="object",
        n_missing=0,
        memory_bytes=800,
        schema=schema,
    )
    assert desc_target.semantic_type == ColumnSemanticType.CATEGORICAL
    assert desc_target.is_semantic_declared is False

    # Fallback for bool feature
    desc_bool = derive_column_descriptor(
        name="is_active",
        index=2,
        role="feature",
        physical_type="bool",
        n_missing=0,
        memory_bytes=100,
        schema=schema,
    )
    assert desc_bool.semantic_type == ColumnSemanticType.BOOLEAN
    assert desc_bool.is_semantic_declared is False

    # Unknown column in column_semantic_types raises error during validation
    schema_bad = DatasetSchemaSpec(
        target_col="status",
        task_type=TaskType.BINARY_CLASSIFICATION,
        column_semantic_types={"unknown_col": ColumnSemanticType.CATEGORICAL},
    )
    with pytest.raises(DataIntegrityError, match="not found in dataset columns"):
        validate_dataset_schema(["status", "feature1"], 10, schema_bad)


def test_observation_ids_positional_generation() -> None:
    """C25: observation_id_col=None generates obs_000000..obs_{N-1} deterministically (DATA-25)."""
    ids = assign_or_validate_observation_ids({}, 5, None)
    assert len(ids) == 5
    assert ids[0] == ObservationId("obs_000000")
    assert ids[1] == ObservationId("obs_000001")
    assert ids[4] == ObservationId("obs_000004")


def test_observation_ids_source_column_validation() -> None:
    """C26: observation_id_col non-nullness and strict uniqueness validation (DATA-26)."""
    # Valid IDs
    raw_valid = {"id": ["row_1", "row_2", "row_3"]}
    ids = assign_or_validate_observation_ids(raw_valid, 3, "id")
    assert ids == (ObservationId("row_1"), ObservationId("row_2"), ObservationId("row_3"))

    # Missing / Null value
    raw_null = {"id": ["row_1", None, "row_3"]}
    with pytest.raises(DataIntegrityError, match="Row 2: observation_id_col 'id' contains missing/null"):
        assign_or_validate_observation_ids(raw_null, 3, "id")

    # Duplicate ID
    raw_dup = {"id": ["row_1", "row_2", "row_1"]}
    with pytest.raises(DataIntegrityError, match="Row 3: duplicate ObservationId 'row_1'"):
        assign_or_validate_observation_ids(raw_dup, 3, "id")

    # Invalid ID character (control char / newline)
    raw_invalid = {"id": ["row\n1", "row_2"]}
    with pytest.raises(DataIntegrityError, match="invalid ObservationId format"):
        assign_or_validate_observation_ids(raw_invalid, 2, "id")


def test_dataset_schema_validation_structural_errors() -> None:
    """C27: Structural errors N=0, M=0, missing schema cols, len(feature_cols)==0 raise error (DATA-27)."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)

    # N = 0
    with pytest.raises(DataIntegrityError, match="zero rows"):
        validate_dataset_schema(["y", "x"], 0, schema)

    # M = 0
    with pytest.raises(DataIntegrityError, match="zero columns"):
        validate_dataset_schema([], 10, schema)

    # Duplicate column name
    with pytest.raises(DataIntegrityError, match="Duplicate column name"):
        validate_dataset_schema(["y", "x", "y"], 10, schema)

    # Missing target column
    with pytest.raises(DataIntegrityError, match="target_col: 'y'"):
        validate_dataset_schema(["x1", "x2"], 10, schema)

    # Zero feature columns
    schema_all_ignored = DatasetSchemaSpec(
        target_col="y",
        task_type=TaskType.REGRESSION,
        ignore_cols=("x",),
    )
    with pytest.raises(DataIntegrityError, match="zero candidate predictor feature columns"):
        validate_dataset_schema(["y", "x"], 10, schema_all_ignored)


