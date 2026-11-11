"""Unit tests for PrecomputedKernelAdapter and non-leakage partition passing.

Covers PRE-06 (AC-M42-06-01 to AC-M42-06-03) and checks C20, C21, C22.
"""

from __future__ import annotations

import numpy as np
import pytest

from experimental_ml.core.findings import ContractViolationError
from experimental_ml.models.preprocessing.kernel import PrecomputedKernelAdapter


def _linear_kernel(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    return np.dot(A, B.T)


def test_m42_06_01_kernel_adapter_fit_partition_passing() -> None:
    """AC-M42-06-01 / C20: PrecomputedKernelAdapter passes (X_train, X_train) in fit and stores copy."""
    calls = []

    def tracking_kernel(A: np.ndarray, B: np.ndarray) -> np.ndarray:
        calls.append((A.copy(), B.copy()))
        return np.dot(A, B.T)

    adapter = PrecomputedKernelAdapter(tracking_kernel)
    X_train = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])

    adapter.fit(X_train)

    assert len(calls) == 1
    A_call, B_call = calls[0]
    assert np.array_equal(A_call, X_train)
    assert np.array_equal(B_call, X_train)
    assert adapter.X_train_ is not None
    assert np.array_equal(adapter.X_train_, X_train)
    assert adapter.n_train_samples_ == 3


def test_m42_06_02_kernel_adapter_transform_partition_passing() -> None:
    """AC-M42-06-02 / C21: PrecomputedKernelAdapter passes (X_eval, X_train) in transform to compute Gram matrix."""
    calls = []

    def tracking_kernel(A: np.ndarray, B: np.ndarray) -> np.ndarray:
        calls.append((A.copy(), B.copy()))
        return np.dot(A, B.T)

    adapter = PrecomputedKernelAdapter(tracking_kernel)
    X_train = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])  # 3 samples
    adapter.fit(X_train)

    X_eval = np.array([[2.0, 3.0], [4.0, 5.0]])  # 2 samples
    calls.clear()

    K_eval = adapter.transform(X_eval)

    assert len(calls) == 1
    A_eval, B_train = calls[0]
    assert np.array_equal(A_eval, X_eval)
    assert np.array_equal(B_train, X_train)
    assert K_eval.shape == (2, 3)

    # Expected: [[2*1 + 3*0, 2*0 + 3*1, 2*1 + 3*1], [4*1 + 5*0, 4*0 + 5*1, 4*1 + 5*1]]
    # = [[2, 3, 5], [4, 5, 9]]
    assert np.allclose(K_eval, [[2.0, 3.0, 5.0], [4.0, 5.0, 9.0]])


def test_m42_06_03_kernel_adapter_invalid_matrix_rejection() -> None:
    """AC-M42-06-03 / C22: PrecomputedKernelAdapter raises ContractViolationError on invalid matrices."""
    # 1. Non-square output during training
    def non_square_kernel(A: np.ndarray, B: np.ndarray) -> np.ndarray:
        return np.ones((A.shape[0], A.shape[0] + 1))

    adapter_non_square = PrecomputedKernelAdapter(non_square_kernel)
    with pytest.raises(ContractViolationError, match="must be square"):
        adapter_non_square.fit(np.array([[1.0], [2.0]]))

    # 2. Non-finite values in kernel matrix
    def nan_kernel(A: np.ndarray, B: np.ndarray) -> np.ndarray:
        k = np.dot(A, B.T)
        k[0, 0] = float("nan")
        return k

    adapter_nan = PrecomputedKernelAdapter(nan_kernel)
    with pytest.raises(ContractViolationError, match="non-finite values"):
        adapter_nan.fit(np.array([[1.0], [2.0]]))

    # 3. Dimension mismatch in transform
    adapter_valid = PrecomputedKernelAdapter(_linear_kernel)
    adapter_valid.fit(np.array([[1.0, 2.0], [3.0, 4.0]]))
    # X_eval with 3 features instead of 2
    with pytest.raises(ContractViolationError, match="Feature count mismatch"):
        adapter_valid.transform(np.array([[1.0, 2.0, 3.0]]))
