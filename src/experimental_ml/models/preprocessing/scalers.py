"""Pure NumPy implementations of feature scalers with zero-variance safeguards.

Complies with PRE-05 (AC-M42-05-01 to AC-M42-05-05), ADR-002, RF3.4, and XCUT-02.
"""

from __future__ import annotations

from typing import Any
import numpy as np

from experimental_ml.core.findings import ConfigurationError, ContractViolationError


def _validate_2d_array(X: np.ndarray, name: str = "X") -> np.ndarray:
    """Validate that input is a 2D finite NumPy array."""
    if not isinstance(X, np.ndarray):
        X = np.asarray(X)
    if X.ndim != 2:
        raise ContractViolationError(f"{name} must be a 2D array, got ndim={X.ndim} with shape {X.shape}")
    if X.shape[0] == 0 or X.shape[1] == 0:
        raise ContractViolationError(f"{name} must not be empty, got shape {X.shape}")
    if not np.all(np.isfinite(X)):
        raise ContractViolationError(f"{name} contains non-finite values (NaN or Inf)")
    return X.astype(float, copy=False)


class StandardScaler:
    """Standardize features by removing the mean and scaling to unit variance."""

    def __init__(self, with_mean: bool = True, with_std: bool = True) -> None:
        self.with_mean = with_mean
        self.with_std = with_std
        self.is_fitted = False
        self.mean_: np.ndarray | None = None
        self.scale_: np.ndarray | None = None
        self.n_features_in_: int | None = None

    def fit(self, X: np.ndarray) -> StandardScaler:
        X_arr = _validate_2d_array(X)
        self.n_features_in_ = X_arr.shape[1]

        if self.with_mean:
            self.mean_ = np.mean(X_arr, axis=0)
        else:
            self.mean_ = np.zeros(self.n_features_in_)

        if self.with_std:
            var = np.var(X_arr, axis=0)
            scale = np.sqrt(var)
            # Safeguard against constant columns / zero variance (AC-M42-05-01)
            scale[scale == 0.0] = 1.0
            self.scale_ = scale
        else:
            self.scale_ = np.ones(self.n_features_in_)

        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted or self.mean_ is None or self.scale_ is None:
            raise ContractViolationError("StandardScaler has not been fitted")
        X_arr = _validate_2d_array(X)
        if X_arr.shape[1] != self.n_features_in_:
            raise ContractViolationError(
                f"Feature count mismatch: fitted on {self.n_features_in_}, got {X_arr.shape[1]}"
            )

        res = (X_arr - self.mean_) / self.scale_
        return res

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)

    def get_state(self) -> dict[str, Any]:
        return {
            "type": "STANDARD",
            "with_mean": self.with_mean,
            "with_std": self.with_std,
            "mean_": tuple(self.mean_) if self.mean_ is not None else (),
            "scale_": tuple(self.scale_) if self.scale_ is not None else (),
            "n_features_in_": self.n_features_in_,
        }


class MinMaxScaler:
    """Transform features by scaling each feature to a given range, default [0.0, 1.0]."""

    def __init__(self, feature_range: tuple[float, float] = (0.0, 1.0)) -> None:
        if feature_range[0] >= feature_range[1]:
            raise ConfigurationError(
                f"Invalid feature_range {feature_range}: min must be less than max"
            )
        self.feature_range = feature_range
        self.is_fitted = False
        self.data_min_: np.ndarray | None = None
        self.data_max_: np.ndarray | None = None
        self.data_range_: np.ndarray | None = None
        self.n_features_in_: int | None = None

    def fit(self, X: np.ndarray) -> MinMaxScaler:
        X_arr = _validate_2d_array(X)
        self.n_features_in_ = X_arr.shape[1]
        self.data_min_ = np.min(X_arr, axis=0)
        self.data_max_ = np.max(X_arr, axis=0)
        rng = self.data_max_ - self.data_min_

        # Safeguard against constant columns (AC-M42-05-02)
        rng[rng == 0.0] = 1.0
        self.data_range_ = rng

        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted or self.data_min_ is None or self.data_range_ is None:
            raise ContractViolationError("MinMaxScaler has not been fitted")
        X_arr = _validate_2d_array(X)
        if X_arr.shape[1] != self.n_features_in_:
            raise ContractViolationError(
                f"Feature count mismatch: fitted on {self.n_features_in_}, got {X_arr.shape[1]}"
            )

        a, b = self.feature_range
        res = a + ((X_arr - self.data_min_) / self.data_range_) * (b - a)

        # Constant columns (where data_max == data_min) map to lower bound a
        const_mask = (self.data_max_ - self.data_min_) == 0.0
        if np.any(const_mask):
            res[:, const_mask] = a

        return res

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)

    def get_state(self) -> dict[str, Any]:
        return {
            "type": "MINMAX",
            "feature_range": self.feature_range,
            "data_min_": tuple(self.data_min_) if self.data_min_ is not None else (),
            "data_max_": tuple(self.data_max_) if self.data_max_ is not None else (),
            "data_range_": tuple(self.data_range_) if self.data_range_ is not None else (),
            "n_features_in_": self.n_features_in_,
        }


class MaxAbsScaler:
    """Scale each feature by its maximum absolute value into [-1.0, 1.0]."""

    def __init__(self) -> None:
        self.is_fitted = False
        self.max_abs_: np.ndarray | None = None
        self.scale_: np.ndarray | None = None
        self.n_features_in_: int | None = None

    def fit(self, X: np.ndarray) -> MaxAbsScaler:
        X_arr = _validate_2d_array(X)
        self.n_features_in_ = X_arr.shape[1]
        max_abs = np.max(np.abs(X_arr), axis=0)

        # Safeguard against all-zero columns (AC-M42-05-03)
        scale = max_abs.copy()
        scale[scale == 0.0] = 1.0

        self.max_abs_ = max_abs
        self.scale_ = scale
        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted or self.scale_ is None:
            raise ContractViolationError("MaxAbsScaler has not been fitted")
        X_arr = _validate_2d_array(X)
        if X_arr.shape[1] != self.n_features_in_:
            raise ContractViolationError(
                f"Feature count mismatch: fitted on {self.n_features_in_}, got {X_arr.shape[1]}"
            )

        res = X_arr / self.scale_
        # All-zero columns stay 0.0
        zero_mask = self.max_abs_ == 0.0
        if np.any(zero_mask):
            res[:, zero_mask] = 0.0
        return res

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)

    def get_state(self) -> dict[str, Any]:
        return {
            "type": "MAXABS",
            "max_abs_": tuple(self.max_abs_) if self.max_abs_ is not None else (),
            "scale_": tuple(self.scale_) if self.scale_ is not None else (),
            "n_features_in_": self.n_features_in_,
        }


class RobustScaler:
    """Scale features using statistics that are robust to outliers (median and IQR)."""

    def __init__(
        self,
        with_centering: bool = True,
        with_scaling: bool = True,
        quantile_range: tuple[float, float] = (25.0, 75.0),
    ) -> None:
        self.with_centering = with_centering
        self.with_scaling = with_scaling
        self.quantile_range = quantile_range
        self.is_fitted = False
        self.center_: np.ndarray | None = None
        self.scale_: np.ndarray | None = None
        self.n_features_in_: int | None = None

    def fit(self, X: np.ndarray) -> RobustScaler:
        X_arr = _validate_2d_array(X)
        self.n_features_in_ = X_arr.shape[1]

        if self.with_centering:
            self.center_ = np.median(X_arr, axis=0)
        else:
            self.center_ = np.zeros(self.n_features_in_)

        if self.with_scaling:
            q_min, q_max = self.quantile_range
            q25 = np.percentile(X_arr, q_min, axis=0)
            q75 = np.percentile(X_arr, q_max, axis=0)
            iqr = q75 - q25
            # Safeguard against zero IQR (AC-M42-05-04)
            scale = iqr.copy()
            scale[scale == 0.0] = 1.0
            self.scale_ = scale
        else:
            self.scale_ = np.ones(self.n_features_in_)

        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted or self.center_ is None or self.scale_ is None:
            raise ContractViolationError("RobustScaler has not been fitted")
        X_arr = _validate_2d_array(X)
        if X_arr.shape[1] != self.n_features_in_:
            raise ContractViolationError(
                f"Feature count mismatch: fitted on {self.n_features_in_}, got {X_arr.shape[1]}"
            )

        res = (X_arr - self.center_) / self.scale_
        return res

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)

    def get_state(self) -> dict[str, Any]:
        return {
            "type": "ROBUST",
            "with_centering": self.with_centering,
            "with_scaling": self.with_scaling,
            "center_": tuple(self.center_) if self.center_ is not None else (),
            "scale_": tuple(self.scale_) if self.scale_ is not None else (),
            "n_features_in_": self.n_features_in_,
        }


class AngularScaler:
    """Scale features linearly into an angular interval [0.0, pi] for quantum gate encoding."""

    def __init__(self, target_range: tuple[float, float] = (0.0, np.pi)) -> None:
        self.target_range = target_range
        self.inner_minmax = MinMaxScaler(feature_range=target_range)
        self.is_fitted = False

    def fit(self, X: np.ndarray) -> AngularScaler:
        self.inner_minmax.fit(X)
        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise ContractViolationError("AngularScaler has not been fitted")
        return self.inner_minmax.transform(X)

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)

    def get_state(self) -> dict[str, Any]:
        return {
            "type": "ANGULAR",
            "target_range": self.target_range,
            "inner_state": self.inner_minmax.get_state(),
        }


__all__ = [
    "StandardScaler",
    "MinMaxScaler",
    "MaxAbsScaler",
    "RobustScaler",
    "AngularScaler",
]
