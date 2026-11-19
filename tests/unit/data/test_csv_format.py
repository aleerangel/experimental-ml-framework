"""Unit tests for CsvFormatSpec and regional CSV formatting/auto-detection."""

from __future__ import annotations

import pytest

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.data import CsvFormatSpec, validate_csv_format_spec


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
