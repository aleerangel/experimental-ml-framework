"""Precomputed kernel adapter with non-leakage partition passing.

Complies with PRE-06 (AC-M42-06-01 to AC-M42-06-03), ADR-001, ADR-002, and RF3.4.
"""

from __future__ import annotations

from typing import Any, Callable
import numpy as np

from experimental_ml.core.findings import ConfigurationError, ContractViolationError


class PrecomputedKernelAdapter:
    """Adapter for external precomputed kernel functions preventing data leakage.

    Passes (X_train, X_train) during fold fitting and stores a defensive reference
    to X_train to evaluate (X_eval, X_train) during inference.
    """

    def __init__(self, kernel_func: Callable[[np.ndarray, np.ndarray], np.ndarray]) -> None:
        if not callable(kernel_func):
            raise ConfigurationError(
                f"kernel_func must be a callable, got {type(kernel_func).__name__}"
            )
        self.kernel_func = kernel_func
        self.is_fitted = False
        self.X_train_: np.ndarray | None = None
        self.n_features_in_: int | None = None
        self.n_train_samples_: int | None = None

    def fit(self, X_train: np.ndarray) -> PrecomputedKernelAdapter:
        """Fit precomputed kernel on training partition."""
        if not isinstance(X_train, np.ndarray):
            X_train = np.asarray(X_train)
        if X_train.ndim != 2:
            raise ContractViolationError(f"X_train must be 2D array, got ndim={X_train.ndim}")
        n_train, n_features = X_train.shape
        if n_train == 0 or n_features == 0:
            raise ContractViolationError("X_train must not be empty")

        try:
            k_matrix = self.kernel_func(X_train, X_train)
        except Exception as exc:
            raise ContractViolationError(f"Failed to evaluate kernel_func on (X_train, X_train): {exc}") from exc

        if not isinstance(k_matrix, np.ndarray):
            k_matrix = np.asarray(k_matrix)
        if k_matrix.ndim != 2:
            raise ContractViolationError(f"Kernel matrix must be 2D, got ndim={k_matrix.ndim}")
        if k_matrix.shape != (n_train, n_train):
            raise ContractViolationError(
                f"Kernel matrix must be square with shape ({n_train}, {n_train}), got {k_matrix.shape}"
            )
        if not np.all(np.isfinite(k_matrix)):
            raise ContractViolationError("Kernel matrix contains non-finite values (NaN or Inf)")

        # Store defensive copy of X_train for subsequent projection (RF3.4, AC-M42-06-01)
        self.X_train_ = np.array(X_train, copy=True)
        self.n_features_in_ = n_features
        self.n_train_samples_ = n_train
        self.is_fitted = True
        return self

    def transform(self, X_eval: np.ndarray) -> np.ndarray:
        """Evaluate precomputed Gram matrix (X_eval, X_train) on evaluation data."""
        if not self.is_fitted or self.X_train_ is None or self.n_train_samples_ is None:
            raise ContractViolationError("PrecomputedKernelAdapter has not been fitted")
        if not isinstance(X_eval, np.ndarray):
            X_eval = np.asarray(X_eval)
        if X_eval.ndim != 2:
            raise ContractViolationError(f"X_eval must be 2D array, got ndim={X_eval.ndim}")
        if X_eval.shape[1] != self.n_features_in_:
            raise ContractViolationError(
                f"Feature count mismatch: fitted on {self.n_features_in_}, got {X_eval.shape[1]}"
            )

        n_eval = X_eval.shape[0]
        try:
            k_matrix = self.kernel_func(X_eval, self.X_train_)
        except Exception as exc:
            raise ContractViolationError(f"Failed to evaluate kernel_func on (X_eval, X_train): {exc}") from exc

        if not isinstance(k_matrix, np.ndarray):
            k_matrix = np.asarray(k_matrix)
        if k_matrix.ndim != 2 or k_matrix.shape != (n_eval, self.n_train_samples_):
            raise ContractViolationError(
                f"Evaluation Gram matrix shape must be ({n_eval}, {self.n_train_samples_}), got {k_matrix.shape}"
            )
        if not np.all(np.isfinite(k_matrix)):
            raise ContractViolationError("Evaluation Gram matrix contains non-finite values")

        return k_matrix

    def fit_transform(self, X_train: np.ndarray) -> np.ndarray:
        self.fit(X_train)
        return self.transform(X_train)

    def get_state(self) -> dict[str, Any]:
        return {
            "type": "PRECOMPUTED_KERNEL",
            "is_fitted": self.is_fitted,
            "n_features_in_": self.n_features_in_,
            "n_train_samples_": self.n_train_samples_,
        }


__all__ = [
    "PrecomputedKernelAdapter",
]
