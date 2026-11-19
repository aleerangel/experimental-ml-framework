"""Unit tests for CsvFormatSpec and regional CSV formatting/auto-detection."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pytest

from experimental_ml.core.enums import TaskType
from experimental_ml.core.findings import ConfigurationError, DataIntegrityError
from experimental_ml.data import (
    CsvFormatSpec,
    DatasetSchemaSpec,
    detect_decimal,
    detect_delimiter,
    load_dataset,
    validate_csv_format_spec,
)


def test_csv_format_spec_validation() -> None:
    """CsvFormatSpec validates defaults, 'auto' normalization, and rejects ambiguous/invalid fields."""
    default_spec = CsvFormatSpec()
    assert default_spec.delimiter is None
    assert default_spec.decimal == "."
    assert default_spec.encoding == "utf-8-sig"
    assert default_spec.has_header is True
    assert default_spec.column_names is None
    assert default_spec.quotechar == '"'
    assert validate_csv_format_spec(default_spec) is default_spec

    auto_spec = CsvFormatSpec(
        delimiter=";",
        decimal="auto",
        encoding="auto",
        has_header=False,
        column_names=("f1", "f2", "alvo"),
        quotechar="'",
    )
    assert auto_spec.decimal is None
    assert auto_spec.encoding == "auto"
    assert auto_spec.column_names == ("f1", "f2", "alvo")

    with pytest.raises(ConfigurationError, match="Ambiguous CSV configuration"):
        CsvFormatSpec(delimiter=",", decimal=",")

    with pytest.raises(ConfigurationError, match="Invalid CSV decimal separator"):
        CsvFormatSpec(decimal=":")

    with pytest.raises(ConfigurationError, match="Unsupported CSV delimiter"):
        CsvFormatSpec(delimiter="^")

    with pytest.raises(ConfigurationError, match="Invalid CSV quotechar"):
        CsvFormatSpec(quotechar="''")

    with pytest.raises(ConfigurationError, match="cannot equal delimiter"):
        CsvFormatSpec(delimiter=";", quotechar=";")

    with pytest.raises(ConfigurationError, match="Unknown CSV encoding"):
        CsvFormatSpec(encoding="not_a_real_codec_xyz")

    with pytest.raises(ConfigurationError, match="Expected CsvFormatSpec"):
        validate_csv_format_spec({"delimiter": ";"})


def test_load_dataset_regional_csv_and_hash_equivalence(tmp_path: Path) -> None:
    """load_dataset parses ';'-delimited ','-decimal latin-1 CSV with custom quotechar identically to UTF-8 dot CSV."""
    schema = DatasetSchemaSpec(target_col="alvo", task_type=TaskType.REGRESSION)

    dot_csv = tmp_path / "dot_utf8.csv"
    dot_csv.write_text(
        'nome,x1,x2,alvo\n'
        '"Ação, 1",-1.5,2.25e1,10.5\n'
        '"Região 2",0.75,-0.5,3.25\n',
        encoding="utf-8",
    )

    br_csv = tmp_path / "br_latin1.csv"
    br_csv.write_text(
        "nome;x1;x2;alvo\n"
        "'Ação, 1';-1,5;2,25e1;10,5\n"
        "'Região 2';0,75;-0,5;3,25\n",
        encoding="latin-1",
    )

    bundle_dot = load_dataset(dot_csv, schema)
    bundle_br = load_dataset(
        br_csv,
        schema,
        csv_format=CsvFormatSpec(
            delimiter=";",
            decimal=",",
            encoding="latin-1",
            quotechar="'",
        ),
    )

    assert bundle_br.dataset_hash == bundle_dot.dataset_hash
    assert np.allclose(bundle_br.columns["x1"], np.array([-1.5, 0.75]))
    assert np.allclose(bundle_br.columns["x2"], np.array([22.5, -0.5]))
    assert np.allclose(bundle_br.columns["alvo"], np.array([10.5, 3.25]))
    assert list(bundle_br.columns["nome"]) == ["Ação, 1", "Região 2"]


def test_csv_auto_detection_and_mixed_decimal_rejection(tmp_path: Path) -> None:
    """Auto-detection resolves ';'+',' tie-breaks and encoding='auto' (cp1252), rejecting mixed decimals."""
    schema = DatasetSchemaSpec(target_col="alvo", task_type=TaskType.REGRESSION)

    # Tie-break case: '1,5;2,3;3,8' has uniform count 3 for ';' and uniform count 4 for ','
    lines = ["x1;x2;alvo\n", "1,5;2,3;3,8\n", "4,2;5,1;9,3\n"]
    delim = detect_delimiter(lines, decimal=None)
    assert delim == ";"
    assert detect_decimal(lines, delimiter=delim) == ","

    cp_csv = tmp_path / "cp1252_br.csv"
    cp_csv.write_bytes("x1;x2;alvo\n1,5;2,3;3,8\n4,2;5,1;9,3\n".encode("cp1252"))
    # Include non-ASCII accent to exercise cp1252 fallback
    cp_accent = tmp_path / "cp1252_accent.csv"
    cp_accent.write_bytes("x1;região;alvo\n1,5;Norte;3,8\n4,2;Sul;9,3\n".encode("cp1252"))

    bundle = load_dataset(cp_accent, schema, delimiter=None, decimal="auto", encoding="auto")
    assert np.allclose(bundle.columns["x1"], np.array([1.5, 4.2]))
    assert np.allclose(bundle.columns["alvo"], np.array([3.8, 9.3]))

    mixed_csv = tmp_path / "mixed.csv"
    mixed_csv.write_text("x1;x2;alvo\n1,5;2.3;3,8\n4,2;5,1;9,3\n", encoding="utf-8")
    with pytest.raises(DataIntegrityError, match="Mixed decimal separators"):
        load_dataset(mixed_csv, schema, delimiter=";", decimal=None)


def test_csv_headerless_and_custom_column_names(tmp_path: Path) -> None:
    """Supports has_header=False with custom column_names and CsvFormatSpec."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    no_hdr = tmp_path / "no_header.tsv"
    no_hdr.write_text("1,2\t3,4\n5,6\t7,8\n", encoding="utf-8")

    bundle = load_dataset(
        no_hdr,
        schema,
        delimiter="\t",
        decimal=",",
        has_header=False,
        column_names=("x1", "y"),
    )
    assert bundle.n_rows == 2
    assert np.allclose(bundle.columns["x1"], np.array([1.2, 5.6]))
    assert np.allclose(bundle.columns["y"], np.array([3.4, 7.8]))
