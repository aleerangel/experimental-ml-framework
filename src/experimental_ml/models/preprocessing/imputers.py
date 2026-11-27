"""Pure NumPy intra-fold SimpleImputer (MEAN, MEDIAN, MODE) without data leakage."""

from __future__ import annotations

from collections import Counter
import math
from typing import Any, Sequence

import numpy as np

from experimental_ml.core.findings import (
    ConfigurationError,
    ContractViolationError,
    DataIntegrityError,
)

_SUPPORTED_STRATEGIES = ("MEAN", "MEDIAN", "MODE")


def _is_missing_scalar(val: Any) -> bool:
    if val is None:
        return True
    if isinstance(val, (float, np.floating)):
        return bool(math.isnan(float(val)))
    return False


def _validate_2d(X: np.ndarray, name: str = "X") -> np.ndarray:
    arr = np.asarray(X)
    if arr.ndim != 2:
        raise ContractViolationError(f"{name} must be a 2D array, got ndim={arr.ndim} with shape {arr.shape}")
    if arr.shape[0] == 0 or arr.shape[1] == 0:
        raise ContractViolationError(f"{name} must not be empty, got shape {arr.shape}")
    return arr


class SimpleImputer:
    """Impute missing values (NaN/None) per column using statistics fitted strictly on X_train."""

    def __init__(
        self,
        strategy: str = "MEDIAN",
        column_indices: Sequence[int] | None = None,
    ) -> None:
        norm = str(strategy).strip().upper()
        if norm not in _SUPPORTED_STRATEGIES:
            raise ConfigurationError(
                f"Unsupported imputation strategy {strategy!r}. Expected one of {_SUPPORTED_STRATEGIES}"
            )
        self.strategy = norm
        self.column_indices = tuple(int(i) for i in column_indices) if column_indices is not None else None
        self.statistics_: dict[int, Any] | None = None
        self.n_features_in_: int | None = None
        self.is_fitted: bool = False

    def fit(self, X: np.ndarray) -> SimpleImputer:
        arr = _validate_2d(X, "X_train")
        n_cols = arr.shape[1]
        self.n_features_in_ = n_cols
        target_cols = self.column_indices if self.column_indices is not None else tuple(range(n_cols))

        stats: dict[int, Any] = {}
        for col_idx in target_cols:
            if col_idx < 0 or col_idx >= n_cols:
                raise ConfigurationError(
                    f"Column index {col_idx} out of bounds for X_train with {n_cols} columns"
                )
            col_vals = arr[:, col_idx]
            if col_vals.dtype.kind in ("f", "i", "u"):
                col_float = col_vals.astype(float, copy=False)
                valid = col_float[~np.isnan(col_float)]
                if len(valid) == 0:
                    raise DataIntegrityError(
                        f"Column index {col_idx} in X_train is 100% missing; cannot fit {self.strategy} imputer."
                    )
                if self.strategy == "MEAN":
                    stats[col_idx] = float(np.mean(valid))
                elif self.strategy == "MEDIAN":
                    stats[col_idx] = float(np.median(valid))
                else:  # MODE
                    counts = Counter(valid.tolist())
                    max_c = max(counts.values())
                    cands = [k for k, c in counts.items() if c == max_c]
                    stats[col_idx] = sorted(cands, key=lambda v: (float(v), str(v)))[0]
            else:
                valid_list = [v for v in col_vals.tolist() if not _is_missing_scalar(v)]
                if not valid_list:
                    raise DataIntegrityError(
                        f"Column index {col_idx} in X_train is 100% missing; cannot fit {self.strategy} imputer."
                    )
                if self.strategy == "MODE":
                    counts = Counter(valid_list)
                    max_c = max(counts.values())
                    cands = [k for k, c in counts.items() if c == max_c]
                    stats[col_idx] = sorted(cands, key=str)[0]
                else:
                    try:
                        num_vals = np.array([float(v) for v in valid_list], dtype=float)
                    except (TypeError, ValueError) as exc:
                        raise ConfigurationError(
                            f"Strategy '{self.strategy}' requires numeric values in column {col_idx}: {exc}"
                        ) from exc
                    stats[col_idx] = (
                        float(np.mean(num_vals)) if self.strategy == "MEAN" else float(np.median(num_vals))
                    )

        self.statistics_ = stats
        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted or self.statistics_ is None or self.n_features_in_ is None:
            raise ContractViolationError("SimpleImputer has not been fitted yet")
        arr = _validate_2d(X, "X")
        if arr.shape[1] != self.n_features_in_:
            raise ContractViolationError(
                f"Expected {self.n_features_in_} features in transform, got {arr.shape[1]}"
            )

        out = arr.copy()
        for col_idx, fill_val in self.statistics_.items():
            col_vals = out[:, col_idx]
            if col_vals.dtype.kind in ("f", "i", "u"):
                if col_vals.dtype.kind in ("i", "u"):
                    continue
                mask = np.isnan(col_vals)
                if np.any(mask):
                    out[mask, col_idx] = float(fill_val)
            else:
                for row_idx in range(out.shape[0]):
                    if _is_missing_scalar(out[row_idx, col_idx]):
                        out[row_idx, col_idx] = fill_val
        return out
