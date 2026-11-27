"""Pure NumPy 1:1 intra-fold categorical encoders without data leakage (M9-02, AD-030)."""

from __future__ import annotations

from collections import Counter
import math
from typing import Any, Sequence

import numpy as np

from experimental_ml.core.findings import ConfigurationError, ContractViolationError


def _is_missing_val(val: Any) -> bool:
    if val is None:
        return True
    if isinstance(val, (float, np.floating)):
        return bool(math.isnan(float(val)))
    return False


def _is_numeric_col(col_vals: np.ndarray) -> bool:
    if col_vals.dtype.kind in ("i", "u", "f"):
        return True
    for v in col_vals.tolist():
        if _is_missing_val(v):
            continue
        if isinstance(v, (bool, str, bytes)):
            return False
        if not isinstance(v, (int, float, np.number)):
            return False
    return True


def _validate_2d(X: np.ndarray, name: str = "X") -> np.ndarray:
    arr = np.asarray(X)
    if arr.ndim != 2:
        raise ContractViolationError(f"{name} must be a 2D array, got ndim={arr.ndim} with shape {arr.shape}")
    if arr.shape[0] == 0 or arr.shape[1] == 0:
        raise ContractViolationError(f"{name} must not be empty, got shape {arr.shape}")
    return arr


class _BaseCategoryEncoder:
    """Shared 1:1 intra-fold categorical encoder base."""

    def __init__(
        self,
        column_indices: Sequence[int] | None = None,
        *,
        unknown_value: float,
    ) -> None:
        self.column_indices = tuple(int(i) for i in column_indices) if column_indices is not None else None
        self.unknown_value = float(unknown_value)
        self.mappings_: dict[int, dict[str, float]] | None = None
        self.encoded_cols_: tuple[int, ...] = ()
        self.n_features_in_: int | None = None
        self.is_fitted: bool = False

    def _compute_mapping(self, non_missing_keys: list[str]) -> dict[str, float]:
        raise NotImplementedError

    def fit(self, X: np.ndarray) -> _BaseCategoryEncoder:
        arr = _validate_2d(X, "X_train")
        n_cols = arr.shape[1]
        self.n_features_in_ = n_cols

        if self.column_indices is not None:
            for col_idx in self.column_indices:
                if col_idx < 0 or col_idx >= n_cols:
                    raise ConfigurationError(
                        f"Column index {col_idx} out of bounds for X_train with {n_cols} columns"
                    )
            target_cols = self.column_indices
        else:
            target_cols = tuple(
                col_idx for col_idx in range(n_cols) if not _is_numeric_col(arr[:, col_idx])
            )

        mappings: dict[int, dict[str, float]] = {}
        for col_idx in target_cols:
            keys = [str(v) for v in arr[:, col_idx].tolist() if not _is_missing_val(v)]
            mappings[col_idx] = self._compute_mapping(keys)

        self.encoded_cols_ = target_cols
        self.mappings_ = mappings
        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted or self.mappings_ is None or self.n_features_in_ is None:
            raise ContractViolationError(f"{type(self).__name__} has not been fitted yet")
        arr = _validate_2d(X, "X")
        if arr.shape[1] != self.n_features_in_:
            raise ContractViolationError(
                f"Expected {self.n_features_in_} features in transform, got {arr.shape[1]}"
            )

        out = np.empty(arr.shape, dtype=np.float64)
        for col_idx in range(arr.shape[1]):
            col_vals = arr[:, col_idx]
            if col_idx in self.mappings_:
                mapping = self.mappings_[col_idx]
                for row_idx, val in enumerate(col_vals.tolist()):
                    if _is_missing_val(val):
                        out[row_idx, col_idx] = np.nan
                    else:
                        out[row_idx, col_idx] = mapping.get(str(val), self.unknown_value)
            else:
                for row_idx, val in enumerate(col_vals.tolist()):
                    out[row_idx, col_idx] = np.nan if _is_missing_val(val) else float(val)
        return out


class OrdinalCategoryEncoder(_BaseCategoryEncoder):
    """Deterministic 1:1 ordinal encoder (sorted categories -> 0..C-1; unseen -> -1.0)."""

    def __init__(self, column_indices: Sequence[int] | None = None) -> None:
        super().__init__(column_indices=column_indices, unknown_value=-1.0)

    def _compute_mapping(self, non_missing_keys: list[str]) -> dict[str, float]:
        unique_sorted = sorted(set(non_missing_keys))
        return {k: float(idx) for idx, k in enumerate(unique_sorted)}


class FrequencyCategoryEncoder(_BaseCategoryEncoder):
    """Deterministic 1:1 frequency encoder (empirical proportion in X_train; unseen -> 0.0)."""

    def __init__(self, column_indices: Sequence[int] | None = None) -> None:
        super().__init__(column_indices=column_indices, unknown_value=0.0)

    def _compute_mapping(self, non_missing_keys: list[str]) -> dict[str, float]:
        total = len(non_missing_keys)
        if total == 0:
            return {}
        counts = Counter(non_missing_keys)
        return {k: float(cnt / total) for k, cnt in counts.items()}
