"""Unit tests for models domain types, enums, capabilities and diagnostics.

Covers MOD-01 (AC-M41-01-01, AC-M41-01-02, AC-M41-01-03) and checks C1, C2, C3.
"""

from __future__ import annotations

from types import MappingProxyType
import pytest

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.models.types import (
    ModelCapabilities,
    ModelDiagnostics,
    ModelFamily,
    ModelId,
)


def test_m41_01_01_model_family_enum() -> None:
    """AC-M41-01-01 / C1: ModelFamily is a closed str, Enum with 9 canonical members."""
    expected_members = {
        "CLASSICAL_ML": "CLASSICAL_ML",
        "NEURAL_NETWORK": "NEURAL_NETWORK",
        "QUANTUM_CIRCUIT": "QUANTUM_CIRCUIT",
        "QUANTUM_KERNEL": "QUANTUM_KERNEL",
        "QUANTUM_SOLVER": "QUANTUM_SOLVER",
        "ANALYTICAL_EQUATION": "ANALYTICAL_EQUATION",
        "BIOMETRIC_MODEL": "BIOMETRIC_MODEL",
        "BASELINE": "BASELINE",
        "CUSTOM": "CUSTOM",
    }
    assert len(ModelFamily) == 9
    for name, value in expected_members.items():
        assert hasattr(ModelFamily, name)
        member = getattr(ModelFamily, name)
        assert member.value == value
        assert isinstance(member, str)
        assert isinstance(member, ModelFamily)


def test_m41_01_02_model_capabilities_dataclass() -> None:
    """AC-M41-01-02 / C2: ModelCapabilities is an immutable frozen dataclass with slots."""
    caps = ModelCapabilities()
    assert caps.requires_fit is True
    assert caps.supports_predict is True
    assert caps.supports_uncertainty is False
    assert caps.supports_predict_proba is False
    assert caps.supports_decision_function is False
    assert caps.supports_sample_weight is False
    assert caps.supports_precomputed_kernel is False
    assert caps.supports_internal_parallelism_control is False
    assert caps.expected_input_types == ("dense_numeric",)

    # Immutability check
    with pytest.raises((AttributeError, TypeError)):
        caps.requires_fit = False  # type: ignore[misc]

    # Custom options
    custom_caps = ModelCapabilities(
        requires_fit=False,
        supports_predict=True,
        supports_uncertainty=True,
        expected_input_types=["sparse_numeric", "dense_numeric"],
    )
    assert custom_caps.requires_fit is False
    assert custom_caps.supports_uncertainty is True
    assert custom_caps.expected_input_types == ("sparse_numeric", "dense_numeric")

    # Invalid input type
    with pytest.raises(ConfigurationError):
        ModelCapabilities(expected_input_types=123)  # type: ignore[arg-type]


def test_m41_01_03_model_diagnostics_dataclass() -> None:
    """AC-M41-01-03 / C3: ModelDiagnostics is an immutable frozen dataclass with slots."""
    diag = ModelDiagnostics(
        model_id="ridge_regressor",
        phase="fit",
        diagnostics={"n_iter_": 15, "loss_": 0.042},
        extracted_at="2026-11-11T12:00:00Z",
    )
    assert diag.model_id == "ridge_regressor"
    assert diag.phase == "fit"
    assert isinstance(diag.diagnostics, MappingProxyType)
    assert diag.diagnostics["n_iter_"] == 15
    assert diag.diagnostics["loss_"] == 0.042
    assert diag.extracted_at == "2026-11-11T12:00:00Z"

    # Immutability check
    with pytest.raises((AttributeError, TypeError)):
        diag.phase = "predict"  # type: ignore[misc]

    with pytest.raises((AttributeError, TypeError)):
        diag.diagnostics["new_key"] = 1  # type: ignore[index]

    # Validation checks
    with pytest.raises(ConfigurationError, match="model_id must be a non-empty string"):
        ModelDiagnostics(model_id="", phase="fit", extracted_at="2026-11-11T12:00:00Z")

    with pytest.raises(ConfigurationError, match="phase must be a non-empty string"):
        ModelDiagnostics(model_id="test", phase="", extracted_at="2026-11-11T12:00:00Z")

    with pytest.raises(ConfigurationError, match="extracted_at must be a non-empty ISO 8601 string"):
        ModelDiagnostics(model_id="test", phase="fit", extracted_at="")

    with pytest.raises(ConfigurationError, match="diagnostics must be a mapping"):
        ModelDiagnostics(
            model_id="test",
            phase="fit",
            diagnostics=["invalid"],  # type: ignore[arg-type]
            extracted_at="2026-11-11T12:00:00Z",
        )
