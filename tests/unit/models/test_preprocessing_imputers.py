"""Unit tests for pure NumPy intra-fold SimpleImputer (M9-01, AC-M9-01)."""

from __future__ import annotations

import numpy as np
import pytest

from experimental_ml.core.findings import ConfigurationError, ContractViolationError, DataIntegrityError
from experimental_ml.models.preprocessing.imputers import SimpleImputer


def test_simple_imputer_mean_median_mode_and_all_missing() -> None:
    """C1 (M9-01, AC-M9-01): SimpleImputer computes stats strictly on X_train and raises DataIntegrityError on all-missing column."""
    X_train = np.array(
        [
            [1.0, 10.0, 2.0],
            [3.0, 10.0, 4.0],
            [np.nan, 20.0, 100.0],
            [5.0, np.nan, 4.0],
        ],
        dtype=float,
    )
    # Extreme values in X_val must NEVER affect fitted statistics
    X_val = np.array(
        [
            [np.nan, np.nan, np.nan],
            [1e6, 1e6, 1e6],
        ],
        dtype=float,
    )

    # MEAN: col0 mean=(1+3+5)/3=3.0, col1 mean=(10+10+20)/3=13.333..., col2 mean=(2+4+100+4)/4=27.5
    imp_mean = SimpleImputer(strategy="MEAN").fit(X_train)
    tr_mean = imp_mean.transform(X_train)
    va_mean = imp_mean.transform(X_val)
    assert np.all(np.isfinite(tr_mean))
    assert np.all(np.isfinite(va_mean))
    assert tr_mean[2, 0] == pytest.approx(3.0)
    assert va_mean[0, 0] == pytest.approx(3.0)
    assert va_mean[0, 1] == pytest.approx(40.0 / 3.0)

    # MEDIAN: col0 median=3.0, col1 median=10.0, col2 median=4.0
    imp_med = SimpleImputer(strategy="MEDIAN").fit(X_train)
    va_med = imp_med.transform(X_val)
    assert va_med[0, 0] == pytest.approx(3.0)
    assert va_med[0, 1] == pytest.approx(10.0)
    assert va_med[0, 2] == pytest.approx(4.0)

    # MODE: col1 mode=10.0, col2 mode=4.0
    imp_mode = SimpleImputer(strategy="MODE").fit(X_train)
    va_mode = imp_mode.transform(X_val)
    assert va_mode[0, 1] == pytest.approx(10.0)
    assert va_mode[0, 2] == pytest.approx(4.0)

    # 100% missing column in X_train -> DataIntegrityError
    X_all_nan = np.array([[1.0, np.nan], [2.0, np.nan]], dtype=float)
    with pytest.raises(DataIntegrityError, match="100% missing"):
        SimpleImputer(strategy="MEDIAN").fit(X_all_nan)


def test_simple_imputer_validation_and_column_indices() -> None:
    """Validate error handling and selective column_indices."""
    with pytest.raises(ConfigurationError):
        SimpleImputer(strategy="INVALID")

    imp = SimpleImputer(strategy="MEAN", column_indices=(1,))
    with pytest.raises(ContractViolationError):
        imp.transform(np.array([[1.0, 2.0]]))

    X_tr = np.array([[1.0, 10.0], [np.nan, np.nan], [3.0, 20.0]], dtype=float)
    imp.fit(X_tr)
    out = imp.transform(X_tr)
    assert np.isnan(out[1, 0])  # col 0 untouched
    assert out[1, 1] == pytest.approx(15.0)  # col 1 imputed
