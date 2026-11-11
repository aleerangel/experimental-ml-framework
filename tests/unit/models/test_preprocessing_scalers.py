"""Unit tests for pure NumPy scalers and zero-variance safeguards.

Covers PRE-05 (AC-M42-05-01 to AC-M42-05-05) and checks C15, C16, C17, C18, C19.
"""

from __future__ import annotations

import numpy as np
import pytest

from experimental_ml.models.preprocessing.scalers import (
    AngularScaler,
    MaxAbsScaler,
    MinMaxScaler,
    RobustScaler,
    StandardScaler,
)


def test_m42_05_01_standard_scaler_zero_variance() -> None:
    """AC-M42-05-01 / C15: StandardScaler centers to 0.0 and unit variance, constant col outputs 0.0."""
    # Col 0: varied, Col 1: constant 5.0
    X = np.array([[10.0, 5.0], [20.0, 5.0], [30.0, 5.0]])
    scaler = StandardScaler()
    scaler.fit(X)

    Xt = scaler.transform(X)
    assert np.allclose(np.mean(Xt[:, 0]), 0.0)
    assert np.allclose(np.var(Xt[:, 0]), 1.0, atol=1e-5)
    # Constant column outputs strictly 0.0
    assert np.allclose(Xt[:, 1], [0.0, 0.0, 0.0])


def test_m42_05_02_minmax_scaler_constant_columns() -> None:
    """AC-M42-05-02 / C16: MinMaxScaler scales into [a, b], constant col outputs lower bound a."""
    # Col 0: varied, Col 1: constant 10.0
    X = np.array([[1.0, 10.0], [5.0, 10.0], [9.0, 10.0]])
    scaler = MinMaxScaler(feature_range=(-1.0, 1.0))
    scaler.fit(X)

    Xt = scaler.transform(X)
    assert np.allclose(Xt[:, 0], [-1.0, 0.0, 1.0])
    # Constant column outputs lower bound -1.0
    assert np.allclose(Xt[:, 1], [-1.0, -1.0, -1.0])


def test_m42_05_03_maxabs_scaler_zero_columns() -> None:
    """AC-M42-05-03 / C17: MaxAbsScaler scales into [-1.0, 1.0], all-zero col outputs 0.0."""
    # Col 0: varied, Col 1: all-zero
    X = np.array([[2.0, 0.0], [-10.0, 0.0], [5.0, 0.0]])
    scaler = MaxAbsScaler()
    scaler.fit(X)

    Xt = scaler.transform(X)
    assert np.allclose(Xt[:, 0], [0.2, -1.0, 0.5])
    # All zero column outputs 0.0
    assert np.allclose(Xt[:, 1], [0.0, 0.0, 0.0])


def test_m42_05_04_robust_scaler_zero_iqr() -> None:
    """AC-M42-05-04 / C18: RobustScaler centers by median and scales by IQR, zero IQR col outputs 0.0."""
    # Col 0: varied, Col 1: majority constant so IQR=0
    X = np.array([[10.0, 7.0], [20.0, 7.0], [30.0, 7.0], [100.0, 7.0]])
    scaler = RobustScaler()
    scaler.fit(X)

    Xt = scaler.transform(X)
    assert np.allclose(np.median(Xt[:, 0]), 0.0)
    # Zero IQR column outputs 0.0
    assert np.allclose(Xt[:, 1], [0.0, 0.0, 0.0, 0.0])


def test_m42_05_05_angular_scaler_quantum_gates() -> None:
    """AC-M42-05-05 / C19: AngularScaler scales features linearly into quantum gate range [0.0, pi]."""
    X = np.array([[0.0], [50.0], [100.0]])
    scaler = AngularScaler(target_range=(0.0, np.pi))
    scaler.fit(X)

    Xt = scaler.transform(X)
    assert np.allclose(Xt[:, 0], [0.0, np.pi / 2.0, np.pi])
    assert np.all(Xt >= 0.0)
    assert np.all(Xt <= np.pi)
