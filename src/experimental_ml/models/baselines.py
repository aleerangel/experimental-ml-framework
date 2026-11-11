"""Canonical baseline estimators and reference analytical models in pure NumPy.

Complies with MOD-08 (AC-M41-08-01 to AC-M41-08-05), ADR-005, RF3.2, and XCUT-02.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

from experimental_ml.core.findings import ConfigurationError, ContractViolationError


class DummyBaselineModel:
    """Canonical baseline model for regression and classification benchmarks.

    Supports:
        - 'mean': outputs training mean and sample standard deviation as uncertainty.
        - 'median': outputs training median and median absolute deviation (MAD) as uncertainty.
        - 'most_frequent': outputs majority class (lexicographical tie-break) and class probabilities.
    """

    def __init__(self, strategy: str = "mean") -> None:
        if strategy not in ("mean", "median", "most_frequent"):
            raise ConfigurationError(
                f"Unknown strategy '{strategy}'. Supported strategies: 'mean', 'median', 'most_frequent'"
            )
        self.strategy = strategy
        self.is_fitted = False
        self.mean_: float | None = None
        self.std_: float | None = None
        self.median_: float | None = None
        self.mad_: float | None = None
        self.majority_class_: Any | None = None
        self.classes_: np.ndarray | None = None
        self.class_frequencies_: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray, sample_weight: np.ndarray | None = None) -> DummyBaselineModel:
        """Fit baseline statistics on training targets."""
        y_arr = np.asarray(y)
        if y_arr.ndim != 1 or y_arr.shape[0] == 0:
            raise ContractViolationError("y must be a non-empty 1D array")

        n = y_arr.shape[0]

        if self.strategy == "mean":
            self.mean_ = float(np.mean(y_arr))
            self.std_ = float(np.std(y_arr, ddof=1 if n > 1 else 0))
        elif self.strategy == "median":
            self.median_ = float(np.median(y_arr))
            self.mad_ = float(np.median(np.abs(y_arr - self.median_)))
        elif self.strategy == "most_frequent":
            unique_classes = np.unique(y_arr)
            counts = {c: int(np.sum(y_arr == c)) for c in unique_classes}
            max_count = max(counts.values())

            # Deterministic lexicographical tie-break (AC-M41-08-03)
            candidates = [c for c, count in counts.items() if count == max_count]
            self.majority_class_ = sorted(candidates, key=lambda x: str(x))[0]

            self.classes_ = unique_classes
            self.class_frequencies_ = np.array([counts[c] / n for c in unique_classes], dtype=float)

        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict baseline target for each evaluation sample."""
        if not self.is_fitted:
            raise ContractViolationError("DummyBaselineModel has not been fitted")
        X_arr = np.asarray(X)
        n = X_arr.shape[0]

        if self.strategy == "mean":
            return np.full(n, self.mean_, dtype=float)
        elif self.strategy == "median":
            return np.full(n, self.median_, dtype=float)
        elif self.strategy == "most_frequent":
            return np.full(n, self.majority_class_)
        raise ContractViolationError(f"Unsupported strategy: {self.strategy}")

    def predict_std(self, X: np.ndarray) -> np.ndarray:
        """Predict uncertainty standard deviation for regression baselines."""
        if not self.is_fitted:
            raise ContractViolationError("DummyBaselineModel has not been fitted")
        X_arr = np.asarray(X)
        n = X_arr.shape[0]

        if self.strategy == "mean":
            return np.full(n, self.std_, dtype=float)
        elif self.strategy == "median":
            return np.full(n, self.mad_, dtype=float)
        raise ContractViolationError(
            f"predict_std is not supported for classification strategy '{self.strategy}'"
        )

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict empirical class relative frequencies for classification baseline."""
        if not self.is_fitted:
            raise ContractViolationError("DummyBaselineModel has not been fitted")
        if self.strategy != "most_frequent" or self.class_frequencies_ is None:
            raise ContractViolationError(
                f"predict_proba is not supported for regression strategy '{self.strategy}'"
            )
        X_arr = np.asarray(X)
        n = X_arr.shape[0]
        return np.tile(self.class_frequencies_, (n, 1))

    def get_diagnostics(self) -> dict[str, Any]:
        """Return diagnostic snapshot of fitted baseline parameters."""
        return {
            "strategy": self.strategy,
            "is_fitted": self.is_fitted,
            "mean_": self.mean_,
            "std_": self.std_,
            "median_": self.median_,
            "mad_": self.mad_,
            "majority_class_": str(self.majority_class_) if self.majority_class_ is not None else None,
            "classes_": tuple(str(c) for c in self.classes_) if self.classes_ is not None else (),
            "class_frequencies_": tuple(self.class_frequencies_) if self.class_frequencies_ is not None else (),
        }


class AnalyticalBiometricModel:
    """Reference analytical model executing mathematical formulas without fitting.

    Complies with RF3.2 and AC-M41-08-04, AC-M41-08-05.
    """

    def __init__(
        self,
        formula_name: str = "clutter_relative",
        coefficients: Mapping[str, float] | None = None,
        required_features: Sequence[int] = (0, 1),
    ) -> None:
        self.formula_name = formula_name
        self.coefficients = dict(coefficients or {"intercept": 0.0, "w0": 1.0, "w1": 0.5})
        self.required_features = tuple(int(idx) for idx in required_features)
        self.requires_fit = False

    def fit(self, X: np.ndarray, y: np.ndarray | None = None) -> AnalyticalBiometricModel:
        """No-op fitting method for analytical models."""
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Evaluate mathematical formula directly on required features."""
        X_arr = np.asarray(X)
        if X_arr.ndim != 2:
            raise ContractViolationError(f"X must be a 2D array, got ndim={X_arr.ndim}")

        n_features = X_arr.shape[1]
        for req_idx in self.required_features:
            if req_idx >= n_features or req_idx < 0:
                raise ContractViolationError(
                    f"AnalyticalBiometricModel requires feature index {req_idx}, "
                    f"but evaluation data has only {n_features} feature columns."
                )

        intercept = self.coefficients.get("intercept", 0.0)
        w0 = self.coefficients.get("w0", 1.0)
        w1 = self.coefficients.get("w1", 1.0)

        col0 = X_arr[:, self.required_features[0]]
        col1 = X_arr[:, self.required_features[1]] if len(self.required_features) > 1 else 0.0

        return intercept + w0 * col0 + w1 * col1

    def get_diagnostics(self) -> dict[str, Any]:
        """Return diagnostic parameters of the analytical formula."""
        return {
            "formula_name": self.formula_name,
            "coefficients": dict(self.coefficients),
            "required_features": tuple(self.required_features),
            "requires_fit": False,
        }


__all__ = [
    "DummyBaselineModel",
    "AnalyticalBiometricModel",
]
