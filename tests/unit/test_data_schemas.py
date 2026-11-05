"""Unit tests for experimental_ml.data module.

Covers all 29 acceptance criteria (DATA-01 to DATA-29, C1 to C29).
"""

from dataclasses import FrozenInstanceError
from typing import Any
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
from experimental_ml.data.loader import load_dataset
from experimental_ml.data.query import (
    get_column_array,
    slice_bundle_by_observation_ids,
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


# ==============================================================================
# Phase 2: Ingestion & Immutability Tests (C7 - C14)
# ==============================================================================


def test_load_dataset_sources_and_bundle_ownership(tmp_path: Any) -> None:
    """C7: load_dataset loads tabular files and memory structures returning DatasetBundle (DATA-07)."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)

    # 1. CSV file
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("y,x1,x2\n10.0,1.0,2.0\n20.0,3.0,4.0\n", encoding="utf-8")
    bundle_csv = load_dataset(str(csv_file), schema)
    assert isinstance(bundle_csv, DatasetBundle)
    assert bundle_csv.n_rows == 2
    assert bundle_csv.n_cols == 3
    assert bundle_csv.column_names == ("y", "x1", "x2")

    # 2. In-memory dict
    data_dict = {"y": [1.0, 2.0], "x1": [10.0, 20.0]}
    bundle_dict = load_dataset(data_dict, schema)
    assert isinstance(bundle_dict, DatasetBundle)
    assert bundle_dict.n_rows == 2

    # 3. 2D ndarray
    arr_2d = np.array([[10.0, 1.0], [20.0, 2.0]])
    bundle_arr = load_dataset(arr_2d, schema, column_names=["y", "x1"])
    assert isinstance(bundle_arr, DatasetBundle)
    assert bundle_arr.n_rows == 2

    # 4. Sequence of row dicts
    records = [{"y": 1.0, "x1": 10.0}, {"y": 2.0, "x1": 20.0}]
    bundle_rec = load_dataset(records, schema)
    assert isinstance(bundle_rec, DatasetBundle)
    assert bundle_rec.n_rows == 2


def test_load_dataset_defensive_copies_isolation() -> None:
    """C8: Ingestion creates defensive memory copies so modifying caller source has 0 effect (DATA-08)."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    orig_y = [10.0, 20.0]
    orig_x = [1.0, 2.0]
    orig_dict = {"y": orig_y, "x": orig_x}

    bundle = load_dataset(orig_dict, schema)

    # Mutate caller source
    orig_y[0] = 9999.0
    orig_dict["x"] = [888.0, 777.0]

    assert bundle.columns["y"][0] == 10.0
    assert bundle.columns["x"][0] == 1.0


def test_bundle_numeric_columns_buffer_immutability() -> None:
    """C9: Numeric/boolean columns backed by bytes buffers refuse setflags writeable=True (DATA-09)."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    data = {"y": [1.5, 2.5], "count": [10, 20], "flag": [True, False]}

    bundle = load_dataset(data, schema)

    # 1. float64 array
    y_arr = bundle.columns["y"]
    assert y_arr.flags.writeable is False
    with pytest.raises(ValueError):
        y_arr[0] = 999.0
    with pytest.raises(ValueError, match="cannot set WRITEABLE flag to True of this array"):
        y_arr.setflags(write=True)

    # 2. int64 array
    count_arr = bundle.columns["count"]
    assert count_arr.flags.writeable is False
    with pytest.raises(ValueError):
        count_arr[0] = 999
    with pytest.raises(ValueError, match="cannot set WRITEABLE flag to True of this array"):
        count_arr.setflags(write=True)

    # 3. bool array
    flag_arr = bundle.columns["flag"]
    assert flag_arr.flags.writeable is False
    with pytest.raises(ValueError):
        flag_arr[0] = False
    with pytest.raises(ValueError, match="cannot set WRITEABLE flag to True of this array"):
        flag_arr.setflags(write=True)


def test_bundle_object_columns_scalar_immutability() -> None:
    """C10: Object columns contain strictly immutable scalars, mutable objects raise error (DATA-10)."""
    schema = DatasetSchemaSpec(target_col="label", task_type=TaskType.BINARY_CLASSIFICATION)

    # Valid string and None scalars
    valid_data = {"label": ["pos", "neg"], "cat": ["A", None]}
    bundle = load_dataset(valid_data, schema)
    assert bundle.columns["cat"].flags.writeable is False

    # Mutable objects (list, dict, set) must raise DataIntegrityError
    invalid_data = {
        "label": ["pos", "neg"],
        "bad_col": [["mutable", "list"], ["ok"]],
    }
    with pytest.raises(DataIntegrityError, match="mutable object of type 'list'"):
        load_dataset(invalid_data, schema)

    invalid_dict = {
        "label": ["pos", "neg"],
        "bad_col": [{"key": "val"}, {"key": "val2"}],
    }
    with pytest.raises(DataIntegrityError, match="mutable object of type 'dict'"):
        load_dataset(invalid_dict, schema)


def test_load_dataset_preserves_missing_values(tmp_path: Any) -> None:
    """C11: Ingestion preserves original missing values (np.nan in float, None in object) (DATA-11)."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    csv_file = tmp_path / "missing.csv"
    csv_file.write_text(
        "y,num_feat,obj_feat\n"
        "10.0,1.5,hello\n"
        "20.0,NA,null\n"
        "30.0,NaN,\n",
        encoding="utf-8",
    )
    bundle = load_dataset(str(csv_file), schema)
    assert bundle.n_rows == 3

    # Float feature: NA and NaN become np.nan without dropping rows
    num_arr = bundle.columns["num_feat"]
    assert num_arr[0] == 1.5
    assert np.isnan(num_arr[1])
    assert np.isnan(num_arr[2])

    # Object feature: "null" and "" become None
    obj_arr = bundle.columns["obj_feat"]
    assert obj_arr[0] == "hello"
    assert obj_arr[1] is None
    assert obj_arr[2] is None


def test_bundle_structural_metadata_completeness(tmp_path: Any) -> None:
    """C12: DatasetBundle records complete structural metadata including descriptors and hashes (DATA-12)."""
    schema = DatasetSchemaSpec(
        target_col="y",
        task_type=TaskType.REGRESSION,
        group_col="grp",
        ignore_cols=("drop_me",),
    )
    csv_file = tmp_path / "meta.csv"
    csv_file.write_text(
        "y,grp,x1,x2,drop_me\n"
        "10.0,A,1.0,2.0,junk1\n"
        "20.0,B,3.0,4.0,junk2\n",
        encoding="utf-8",
    )
    bundle = load_dataset(str(csv_file), schema)

    assert bundle.schema == schema
    assert bundle.n_rows == 2
    assert bundle.n_cols == 5
    assert bundle.column_names == ("y", "grp", "x1", "x2", "drop_me")
    assert bundle.feature_cols == ("x1", "x2")
    assert set(bundle.columns.keys()) == set(bundle.column_names)
    assert set(bundle.descriptors.keys()) == set(bundle.column_names)
    assert len(bundle.observation_ids) == 2
    assert len(bundle.dataset_hash) == 64
    assert len(bundle.raw_source_hash) == 64
    assert len(bundle.schema_hash) == 64
    assert bundle.memory_bytes > 0
    assert bundle.source_path == str(csv_file.resolve())


def test_dataset_hash_canonical_in_memory_digest(tmp_path: Any) -> None:
    """C13: dataset_hash matches between CSV and memory and distinguishes int vs float (DATA-13)."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)

    # CRLF CSV
    csv_crlf = tmp_path / "data_crlf.csv"
    csv_crlf.write_bytes(b"y,x\r\n10.0,1.0\r\n20.0,2.0\r\n")

    # LF CSV
    csv_lf = tmp_path / "data_lf.csv"
    csv_lf.write_bytes(b"y,x\n10.0,1.0\n20.0,2.0\n")

    bundle_crlf = load_dataset(str(csv_crlf), schema)
    bundle_lf = load_dataset(str(csv_lf), schema)

    # In-memory dict
    mem_data = {"y": [10.0, 20.0], "x": [1.0, 2.0]}
    bundle_mem = load_dataset(mem_data, schema)

    # All produce identical canonical in-memory dataset_hash
    assert bundle_crlf.dataset_hash == bundle_lf.dataset_hash
    assert bundle_crlf.dataset_hash == bundle_mem.dataset_hash

    # int64 vs float64 produces distinct hashes (ADR-007)
    mem_data_int = {"y": [10.0, 20.0], "x": [1, 2]}  # x is int64 here
    bundle_mem_int = load_dataset(mem_data_int, schema)
    assert bundle_mem_int.dataset_hash != bundle_mem.dataset_hash


def test_raw_source_hash_file_and_memory(tmp_path: Any) -> None:
    """C14: raw_source_hash computes digest of raw source input matching disk or memory (DATA-14)."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    csv_file = tmp_path / "source.csv"
    csv_file.write_text("y,x\n1.0,2.0\n", encoding="utf-8")

    bundle_file = load_dataset(str(csv_file), schema)
    assert len(bundle_file.raw_source_hash) == 64

    mem_data = {"y": [1.0], "x": [2.0]}
    bundle_mem = load_dataset(mem_data, schema)
    assert len(bundle_mem.raw_source_hash) == 64


# ==============================================================================
# Phase 2: Query Utilities Tests (C28 - C29)
# ==============================================================================


def test_get_column_array_view_and_copy() -> None:
    """C28: get_column_array returns read-only view or writeable copy, checks errors (DATA-28)."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    data = {"y": [10.0, 20.0], "feat": [1.0, 2.0]}
    bundle = load_dataset(data, schema)

    # 1. Non-existent column raises DataIntegrityError
    with pytest.raises(DataIntegrityError, match="does not exist"):
        get_column_array(bundle, "non_existent_col")

    # 2. copy=False returns read-only array backed by bytes buffer (cannot set writeable)
    view = get_column_array(bundle, "feat", copy=False)
    assert view.flags.writeable is False
    with pytest.raises(ValueError):
        view[0] = 999.0
    with pytest.raises(ValueError, match="cannot set WRITEABLE flag to True of this array"):
        view.setflags(write=True)

    # 3. copy=True returns writeable independent copy
    copied = get_column_array(bundle, "feat", copy=True)
    assert copied.flags.writeable is True
    copied[0] = 999.0
    assert bundle.columns["feat"][0] == 1.0


def test_slice_bundle_by_observation_ids_ordering_and_hash() -> None:
    """C29: slice_bundle_by_observation_ids orders sub-bundle, recalculates hash (DATA-29)."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    data = {"y": [10.0, 20.0, 30.0], "feat": [1.0, 2.0, 3.0]}
    bundle = load_dataset(data, schema)
    orig_ids = bundle.observation_ids
    assert len(orig_ids) == 3

    # Slice in reverse order: [obs_2, obs_0]
    requested_order = (orig_ids[2], orig_ids[0])
    sliced = slice_bundle_by_observation_ids(bundle, requested_order)

    assert isinstance(sliced, DatasetBundle)
    assert sliced.n_rows == 2
    assert sliced.observation_ids == requested_order
    assert sliced.columns["y"][0] == 30.0
    assert sliced.columns["y"][1] == 10.0
    assert sliced.columns["feat"][0] == 3.0
    assert sliced.columns["feat"][1] == 1.0
    assert sliced.dataset_hash != bundle.dataset_hash

    # Original bundle unchanged
    assert bundle.n_rows == 3

    # Empty sequence raises error
    with pytest.raises(DataIntegrityError, match="cannot be empty"):
        slice_bundle_by_observation_ids(bundle, ())

    # Duplicate IDs raise error
    with pytest.raises(DataIntegrityError, match="Duplicate ObservationId"):
        slice_bundle_by_observation_ids(bundle, (orig_ids[0], orig_ids[0]))

    # Unknown ID raises error
    with pytest.raises(DataIntegrityError, match="not present in DatasetBundle"):
        slice_bundle_by_observation_ids(bundle, (ObservationId("unknown_id"),))


# ==============================================================================
# Phase 2 Hardening: HARD-04, HARD-06, HARD-07, HARD-08, HARD-09, HARD-10, HARD-11
# ==============================================================================


def test_hard_04_bundle_dataset_hash_delegates_observation_ids() -> None:
    """Validate that DatasetBundle.dataset_hash matches core.dataset_hash with observation_ids (HARD-04)."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    b_dup = load_dataset({"x": [1.0, 1.0], "y": [2.0, 2.0]}, schema)
    s0 = slice_bundle_by_observation_ids(b_dup, ["obs_000000"])
    s1 = slice_bundle_by_observation_ids(b_dup, ["obs_000001"])

    # Rows have identical values, but distinct observation_ids produce distinct hashes
    assert s0.dataset_hash != s1.dataset_hash

    # Equivalence contract: bundle.dataset_hash == core.dataset_hash(bundle.columns, bundle.schema, observation_ids=bundle.observation_ids)
    from experimental_ml.core import dataset_hash as core_dataset_hash
    assert s0.dataset_hash == core_dataset_hash(s0.columns, s0.schema, observation_ids=s0.observation_ids)
    assert s1.dataset_hash == core_dataset_hash(s1.columns, s1.schema, observation_ids=s1.observation_ids)


def test_hard_06_numpy_floating_nan_counted_across_data_layer() -> None:
    """Validate that np.float16, np.float32, and np.float64 NaNs are counted accurately in n_missing (HARD-06)."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)

    # 1. Float32 array with NaN
    arr_f32 = np.array([[1.0, np.nan], [2.0, 3.0]], dtype=np.float32)
    b_f32 = load_dataset(arr_f32, schema, column_names=("x", "y"))
    assert b_f32.descriptors["y"].n_missing == 1

    # 2. In-memory dict with np.float16(np.nan)
    dict_f16 = {"x": [1.0, 2.0], "y": [10.0, np.float16(np.nan)]}
    b_f16 = load_dataset(dict_f16, schema)
    assert b_f16.descriptors["y"].n_missing == 1

    # 3. Slicing recount with np.floating NaN
    s = slice_bundle_by_observation_ids(b_f16, ["obs_000001"])
    assert s.descriptors["y"].n_missing == 1


def test_hard_07_slice_bundle_preserves_observation_id_instances() -> None:
    """Validate that slice_bundle_by_observation_ids returns ObservationId instances in requested order (HARD-07)."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    data = {"y": [1.0, 2.0, 3.0], "x": [10.0, 20.0, 30.0]}
    bundle = load_dataset(data, schema)

    # Calling with sequence of plain strings
    req_str_order = ["obs_000002", "obs_000000"]
    sliced = slice_bundle_by_observation_ids(bundle, req_str_order)

    assert isinstance(sliced.observation_ids, tuple)
    assert len(sliced.observation_ids) == 2
    assert isinstance(sliced.observation_ids[0], ObservationId)
    assert isinstance(sliced.observation_ids[1], ObservationId)
    assert sliced.observation_ids[0] == ObservationId("obs_000002")
    assert sliced.observation_ids[1] == ObservationId("obs_000000")


def test_hard_08_slice_bundle_rejects_invalid_observation_id_inputs() -> None:
    """Validate that slice_bundle_by_observation_ids raises DataIntegrityError on malformed inputs (HARD-08)."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    data = {"y": [1.0, 2.0], "x": [10.0, 20.0]}
    bundle = load_dataset(data, schema)

    # 1. Bare string or bytes
    with pytest.raises(DataIntegrityError, match="non-string Sequence"):
        slice_bundle_by_observation_ids(bundle, "obs_000000")  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError, match="non-string Sequence"):
        slice_bundle_by_observation_ids(bundle, b"obs_000000")  # type: ignore[arg-type]

    # 2. Non-str/ObservationId element (int, None)
    with pytest.raises(DataIntegrityError, match="Invalid observation_id element type"):
        slice_bundle_by_observation_ids(bundle, [123, 456])  # type: ignore[list-item]
    with pytest.raises(DataIntegrityError, match="Invalid observation_id element type"):
        slice_bundle_by_observation_ids(bundle, [None])  # type: ignore[list-item]

    # 3. Invalid ObservationId string format (empty or whitespace)
    with pytest.raises(DataIntegrityError, match="Invalid ObservationId string format"):
        slice_bundle_by_observation_ids(bundle, [""])


def test_hard_09_object_column_missingness_and_semantic_preservation() -> None:
    """Validate unified missingness in object columns and preservation of semantic types (HARD-09)."""
    from experimental_ml.core.enums import StrEnum

    class Category(StrEnum):
        A = "CAT_A"
        B = "CAT_B"

    schema = DatasetSchemaSpec(
        target_col="y",
        task_type=TaskType.REGRESSION,
        column_semantic_types={"cat": ColumnSemanticType.CATEGORICAL},
    )

    # Mix of None, float NaN, np.float32(np.nan), StrEnum and DomainIdentifier
    data = {
        "y": [1.0, 2.0, 3.0, 4.0],
        "cat": [Category.A, np.float32(np.nan), None, float("nan")],
    }
    bundle = load_dataset(data, schema)

    cat_arr = bundle.columns["cat"]
    assert cat_arr[0] == "CAT_A"
    assert cat_arr[1] is None
    assert cat_arr[2] is None
    assert cat_arr[3] is None
    assert bundle.descriptors["cat"].n_missing == 3
    assert bundle.descriptors["cat"].semantic_type == ColumnSemanticType.CATEGORICAL
    assert bundle.descriptors["cat"].is_semantic_declared is True


def test_hard_10_object_column_rejects_non_whitelisted_types() -> None:
    """Validate that load_dataset rejects mutable containers, objects, subclasses and complex numbers (HARD-10)."""
    import types
    from decimal import Decimal
    from fractions import Fraction

    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)

    # 1. SimpleNamespace
    with pytest.raises(DataIntegrityError, match="non-whitelisted or mutable object"):
        load_dataset({"y": [1.0, 2.0], "x": [types.SimpleNamespace(a=1), types.SimpleNamespace(a=2)]}, schema)

    # 2. Mutable container (list, dict)
    with pytest.raises(DataIntegrityError, match="non-whitelisted or mutable object"):
        load_dataset({"y": [1.0, 2.0], "x": [[1, 2], [3, 4]]}, schema)

    # 3. Custom subclass with __dict__
    class MutableStr(str):
        pass

    with pytest.raises(DataIntegrityError, match="non-whitelisted or mutable object"):
        load_dataset({"y": [1.0, 2.0], "x": [MutableStr("val1"), MutableStr("val2")]}, schema)

    # 4. Special numeric types (complex, Decimal, Fraction)
    with pytest.raises(DataIntegrityError, match="non-whitelisted or mutable object"):
        load_dataset({"y": [1.0, 2.0], "x": [1 + 2j, 3 + 4j]}, schema)
    with pytest.raises(DataIntegrityError, match="non-whitelisted or mutable object"):
        load_dataset({"y": [1.0, 2.0], "x": [Decimal("1.23"), Decimal("4.56")]}, schema)
    with pytest.raises(DataIntegrityError, match="non-whitelisted or mutable object"):
        load_dataset({"y": [1.0, 2.0], "x": [Fraction(1, 2), Fraction(3, 4)]}, schema)


def test_hard_11_int64_overflow_raises_data_integrity_error() -> None:
    """Validate that integers outside signed 64-bit boundaries raise DataIntegrityError (HARD-11)."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)

    # Exact boundary values must pass: -2**63 and 2**63 - 1
    min_int64 = -9223372036854775808
    max_int64 = 9223372036854775807
    bundle_boundary = load_dataset({"y": [1.0, 2.0], "x": [min_int64, max_int64]}, schema)
    assert bundle_boundary.columns["x"][0] == min_int64
    assert bundle_boundary.columns["x"][1] == max_int64

    # Values exceeding 64-bit range must raise DataIntegrityError
    with pytest.raises(DataIntegrityError, match="exceeds signed 64-bit integer limits"):
        load_dataset({"y": [1.0, 2.0], "x": [2**63, 10]}, schema)

    with pytest.raises(DataIntegrityError, match="exceeds signed 64-bit integer limits"):
        load_dataset({"y": [1.0, 2.0], "x": [-(2**63) - 1, 10]}, schema)





