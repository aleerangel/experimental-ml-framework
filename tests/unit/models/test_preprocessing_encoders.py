"""Unit tests for 1:1 intra-fold categorical encoders (M9-02, AC-M9-02, AD-030)."""

from __future__ import annotations

import numpy as np
import pytest

from experimental_ml.core.findings import ContractViolationError
from experimental_ml.models.preprocessing.encoders import (
    FrequencyCategoryEncoder,
    OrdinalCategoryEncoder,
)


def test_categorical_encoders_1to1_and_unseen_categories() -> None:
    """C2 (M9-02, AC-M9-02): Encoders learn categories strictly on X_train and map unseen categories in X_val."""
    X_train = np.array(
        [
            [1.5, "b", "x"],
            [2.5, "a", "x"],
            [3.5, "b", None],
            [4.5, "c", "y"],
        ],
        dtype=object,
    )
    X_val = np.array(
        [
            [5.0, "unseen_cat", "y"],
            [6.0, "a", "unseen_y"],
            [7.0, None, "x"],
        ],
        dtype=object,
    )

    ord_enc = OrdinalCategoryEncoder(column_indices=(1, 2)).fit(X_train)
    tr_ord = ord_enc.transform(X_train)
    va_ord = ord_enc.transform(X_val)

    assert tr_ord.shape == X_train.shape
    assert va_ord.shape == X_val.shape
    assert tr_ord.dtype == np.float64
    # Sorted categories in col 1: "a"->0.0, "b"->1.0, "c"->2.0
    assert tr_ord[0, 1] == pytest.approx(1.0)
    assert tr_ord[1, 1] == pytest.approx(0.0)
    assert np.isnan(tr_ord[2, 2])  # None preserved as NaN for imputer
    assert va_ord[0, 1] == pytest.approx(-1.0)  # unseen -> -1.0
    assert va_ord[1, 2] == pytest.approx(-1.0)  # unseen -> -1.0
    assert np.isnan(va_ord[2, 1])

    freq_enc = FrequencyCategoryEncoder(column_indices=(1, 2)).fit(X_train)
    tr_freq = freq_enc.transform(X_train)
    va_freq = freq_enc.transform(X_val)

    assert tr_freq.shape == X_train.shape
    assert tr_freq.dtype == np.float64
    # col 1 non-missing count=4: "b"=2/4=0.5, "a"=1/4=0.25
    assert tr_freq[0, 1] == pytest.approx(0.5)
    assert tr_freq[1, 1] == pytest.approx(0.25)
    assert va_freq[0, 1] == pytest.approx(0.0)  # unseen -> 0.0
    assert va_freq[1, 2] == pytest.approx(0.0)  # unseen -> 0.0
    assert np.isnan(va_freq[2, 1])


def test_categorical_encoders_auto_detect_and_unfitted_guard() -> None:
    """Auto-detect non-numeric columns when column_indices is None and guard unfitted transform."""
    enc = OrdinalCategoryEncoder()
    with pytest.raises(ContractViolationError):
        enc.transform(np.array([["a"]], dtype=object))

    X_tr = np.array([[10.0, "cat1"], [20.0, "cat2"]], dtype=object)
    out = enc.fit(X_tr).transform(X_tr)
    assert out.dtype == np.float64
    assert out[0, 0] == pytest.approx(10.0)
    assert out[0, 1] == pytest.approx(0.0)
    assert out[1, 1] == pytest.approx(1.0)
