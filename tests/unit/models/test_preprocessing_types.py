"""Unit tests for preprocessing types, enums and declarative specifications.

Covers PRE-01 (AC-M42-01-01 to AC-M42-01-04) and checks C1, C2, C3, C4.
"""

from __future__ import annotations

from types import MappingProxyType
import pytest

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.models.preprocessing.types import (
    PreprocessingStepSpec,
    ScalerType,
    TwoLayerPreprocessingSpec,
    TwoLayerPreprocessingState,
)


def test_m42_01_01_scaler_type_enum() -> None:
    """AC-M42-01-01 / C1: ScalerType is a closed str, Enum with 6 canonical members."""
    expected = {
        "STANDARD": "STANDARD",
        "MINMAX": "MINMAX",
        "MAXABS": "MAXABS",
        "ROBUST": "ROBUST",
        "ANGULAR": "ANGULAR",
        "NONE": "NONE",
    }
    assert len(ScalerType) == 6
    for name, val in expected.items():
        assert hasattr(ScalerType, name)
        member = getattr(ScalerType, name)
        assert member.value == val
        assert isinstance(member, str)
        assert isinstance(member, ScalerType)


def test_m42_01_02_preprocessing_step_spec() -> None:
    """AC-M42-01-02 / C2: PreprocessingStepSpec is an immutable frozen dataclass with slots."""
    step = PreprocessingStepSpec(
        step_id="std_scaler",
        transformer_type="STANDARD",
        parameters={"with_mean": True, "with_std": True},
        description="Standard z-score scaling",
    )
    assert step.step_id == "std_scaler"
    assert step.transformer_type == "STANDARD"
    assert isinstance(step.parameters, MappingProxyType)
    assert step.parameters["with_mean"] is True
    assert step.description == "Standard z-score scaling"

    # Immutability
    with pytest.raises((AttributeError, TypeError)):
        step.step_id = "new_id"  # type: ignore[misc]

    # Validation
    with pytest.raises(ConfigurationError, match="step_id must be a non-empty string"):
        PreprocessingStepSpec(step_id="", transformer_type="STANDARD")

    with pytest.raises(ConfigurationError, match="transformer_type must be a non-empty string"):
        PreprocessingStepSpec(step_id="step1", transformer_type="")


def test_m42_01_03_two_layer_preprocessing_spec() -> None:
    """AC-M42-01-03 / C3: TwoLayerPreprocessingSpec is an immutable frozen dataclass with slots."""
    s1 = PreprocessingStepSpec(step_id="imp", transformer_type="IMPUTER")
    s2 = PreprocessingStepSpec(step_id="scale", transformer_type="STANDARD")

    spec = TwoLayerPreprocessingSpec(
        layer1_steps=[s1],
        layer2_steps=[s2],
        description="Two-layer test pipeline",
    )
    assert isinstance(spec.layer1_steps, tuple)
    assert isinstance(spec.layer2_steps, tuple)
    assert len(spec.layer1_steps) == 1
    assert len(spec.layer2_steps) == 1
    assert spec.layer1_steps[0] is s1
    assert spec.layer2_steps[0] is s2

    # Immutability
    with pytest.raises((AttributeError, TypeError)):
        spec.description = "new"  # type: ignore[misc]


def test_m42_01_04_two_layer_preprocessing_state() -> None:
    """AC-M42-01-04 / C4: TwoLayerPreprocessingState is an immutable frozen dataclass with slots."""
    spec = TwoLayerPreprocessingSpec()
    state = TwoLayerPreprocessingState(
        spec=spec,
        layer1_fitted_state=("state1",),
        layer2_fitted_state=("state2",),
    )
    assert state.spec is spec
    assert state.layer1_fitted_state == ("state1",)
    assert state.layer2_fitted_state == ("state2",)

    # Immutability
    with pytest.raises((AttributeError, TypeError)):
        state.layer1_fitted_state = ()  # type: ignore[misc]

    with pytest.raises(ConfigurationError, match="spec must be a TwoLayerPreprocessingSpec"):
        TwoLayerPreprocessingState(spec="invalid")  # type: ignore[arg-type]
