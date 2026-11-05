"""Tabular text parsing engine and strict delimiter detection.

Provides RFC 4180 compliant parsing, safe delimiter sniffing, ragged row
detection, and header validation for .csv, .txt, and .tsv tabular sources.
"""

from __future__ import annotations

import csv
import io
import re
from typing import Any, Iterable, Sequence
import unicodedata

from experimental_ml.core.findings import DataIntegrityError

SUPPORTED_DELIMITERS: tuple[str, ...] = (",", ";", "\t", "|", "whitespace")

MISSING_TOKENS: frozenset[str] = frozenset(
    {"", "NA", "NaN", "null", "None", "nan", "NULL"}
)


def _tokenize_row(line: str, delimiter: str) -> list[str]:
    """Tokenize a single tabular text line honoring RFC 4180 double-quoted fields."""
    stripped_line = line.rstrip("\r\n")
    if delimiter in (",", ";", "\t", "|"):
        reader = csv.reader([stripped_line], delimiter=delimiter, quotechar='"', doublequote=True)
        try:
            row = next(reader)
            return row
        except StopIteration:
            return []
    elif delimiter == "whitespace":
        # Custom whitespace tokenizer supporting RFC 4180 quotes
        tokens: list[str] = []
        i = 0
        n = len(stripped_line)
        while i < n:
            # Skip whitespace before token
            while i < n and stripped_line[i] in " \t":
                i += 1
            if i >= n:
                break
            if stripped_line[i] == '"':
                # Quoted token
                i += 1
                buf: list[str] = []
                while i < n:
                    if stripped_line[i] == '"':
                        if i + 1 < n and stripped_line[i + 1] == '"':
                            buf.append('"')
                            i += 2
                        else:
                            i += 1
                            break
                    else:
                        buf.append(stripped_line[i])
                        i += 1
                tokens.append("".join(buf))
            else:
                # Unquoted token
                start = i
                while i < n and stripped_line[i] not in " \t":
                    i += 1
                tokens.append(stripped_line[start:i])
        return tokens
    else:
        raise DataIntegrityError(f"Unsupported delimiter: {repr(delimiter)}")


def detect_delimiter(sample_lines: Sequence[str]) -> str:
    """Detect delimiter from sample lines by verifying constant column count M >= 2.

    Inspects up to the first 100 non-empty lines across supported delimiters.
    Raises DataIntegrityError if detection is ambiguous or fails.
    """
    non_empty_lines = [line for line in sample_lines if line.strip() != ""][:100]
    if not non_empty_lines:
        raise DataIntegrityError("Cannot detect delimiter: input contains zero non-empty lines")

    valid_candidates: list[tuple[str, int]] = []

    for delim in SUPPORTED_DELIMITERS:
        try:
            first_row = _tokenize_row(non_empty_lines[0], delim)
            m = len(first_row)
            if m < 2:
                continue

            # Verify that every sampled line produces exact same count m
            all_match = True
            for line in non_empty_lines[1:]:
                row = _tokenize_row(line, delim)
                if len(row) != m:
                    all_match = False
                    break

            if all_match:
                valid_candidates.append((delim, m))
        except Exception:
            continue

    if len(valid_candidates) > 1:
        candidate_names = [c[0] for c in valid_candidates]
        # Disambiguate tab vs generic whitespace:
        # If '\t' is a candidate and all sampled lines use tab without spaces between columns,
        # '\t' is the specific delimiter, not generic whitespace.
        if "\t" in candidate_names and "whitespace" in candidate_names:
            has_space_delimiter = any("  " in line or (" " in line and "\t" not in line) for line in non_empty_lines)
            if not has_space_delimiter:
                valid_candidates = [c for c in valid_candidates if c[0] != "whitespace"]

    if len(valid_candidates) == 1:
        return valid_candidates[0][0]

    if len(valid_candidates) == 0:
        raise DataIntegrityError(
            "Automatic delimiter detection failed: no supported delimiter "
            "(',', ';', '\\t', '|', whitespace) produced a uniform column count M >= 2 "
            "across sampled lines. Please specify delimiter explicitly."
        )

    # Multiple candidates
    candidate_names = [c[0] for c in valid_candidates]
    raise DataIntegrityError(
        f"Automatic delimiter detection ambiguous: candidates {candidate_names} all "
        f"produced uniform column counts across sampled lines. Please specify delimiter explicitly."
    )


def parse_tabular_text(
    lines: Iterable[str],
    *,
    delimiter: str,
    has_header: bool = True,
    column_names: Sequence[str] | None = None,
) -> tuple[tuple[str, ...], dict[str, list[Any]]]:
    """Parse tabular text lines with RFC 4180 quotes, ragged rows check and missing values.

    Returns:
        tuple of (column_names, raw_columns_dict)
    """
    line_iter = enumerate(lines, start=1)
    first_non_empty = None
    first_line_num = 0

    for line_num, line in line_iter:
        if line.strip() != "":
            first_non_empty = line
            first_line_num = line_num
            break

    if first_non_empty is None:
        raise DataIntegrityError("Tabular file is empty or contains only whitespace")

    first_row = _tokenize_row(first_non_empty, delimiter)
    m = len(first_row)
    if m == 0:
        raise DataIntegrityError(f"Line {first_line_num}: parsed 0 columns")

    final_col_names: list[str] = []
    data_rows: list[list[str]] = []

    if has_header:
        # Validate header row
        for idx, col in enumerate(first_row):
            trimmed = col.strip()
            if not trimmed:
                raise DataIntegrityError(
                    f"Line {first_line_num}: header column at index {idx} is empty after trimming"
                )
            nfc_col = unicodedata.normalize("NFC", trimmed)
            if nfc_col in final_col_names:
                raise DataIntegrityError(
                    f"Line {first_line_num}: duplicate column name '{nfc_col}' in header "
                    f"after Unicode NFC normalization"
                )
            final_col_names.append(nfc_col)

        if column_names is not None:
            if len(column_names) != m:
                raise DataIntegrityError(
                    f"Specified column_names length ({len(column_names)}) does not match "
                    f"header column count ({m})"
                )
    else:
        # No header
        if column_names is not None:
            if len(column_names) != m:
                raise DataIntegrityError(
                    f"Specified column_names length ({len(column_names)}) does not match "
                    f"first row column count ({m})"
                )
            for idx, col in enumerate(column_names):
                trimmed = col.strip()
                if not trimmed:
                    raise DataIntegrityError(
                        f"Specified column name at index {idx} is empty after trimming"
                    )
                nfc_col = unicodedata.normalize("NFC", trimmed)
                if nfc_col in final_col_names:
                    raise DataIntegrityError(
                        f"Duplicate column name '{nfc_col}' in specified column_names"
                    )
                final_col_names.append(nfc_col)
        else:
            final_col_names = [f"col_{j}" for j in range(m)]

        data_rows.append(first_row)

    # Read remaining rows
    for line_num, line in line_iter:
        if line.strip() == "":
            continue  # ignore blank lines
        row = _tokenize_row(line, delimiter)
        if len(row) != m:
            raise DataIntegrityError(
                f"Line {line_num}: ragged row encountered. Expected {m} columns, got {len(row)}"
            )
        data_rows.append(row)

    if len(data_rows) == 0:
        raise DataIntegrityError("Tabular data contains zero data rows (N = 0)")

    # Build columnar dictionary
    n_rows = len(data_rows)
    raw_columns: dict[str, list[Any]] = {col: [None] * n_rows for col in final_col_names}

    for row_idx, row in enumerate(data_rows):
        for col_idx, col_name in enumerate(final_col_names):
            val = row[col_idx].strip()
            if val in MISSING_TOKENS:
                raw_columns[col_name][row_idx] = None
            else:
                raw_columns[col_name][row_idx] = val

    return tuple(final_col_names), raw_columns
