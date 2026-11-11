"""Domain types, enumerations, and immutable specifications for two-layer preprocessing.

Complies with PRE-01 (AC-M42-01-01 to AC-M42-01-04), ADR-002, RF3.4, and RNF07.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from experimental_ml.core.findings import ConfigurationError


class ScalerType(str, Enum):
    """Canonical scaler types supported in Layer 2 or Layer 1."""

    STANDARD = "STANDARD"
    MINMAX = "MINMAX"
    MAXABS = "MAXABS"
    ROBUST = "ROBUST"
    ANGULAR = "ANGULAR"
    NONE = "NONE"


@dataclass(frozen=True, slots=True)
class PreprocessingStepSpec:
    """Declarative specification for an individual data preprocessing transformation step."""

    step_id: str
    transformer_type: str
    parameters: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    description: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.step_id, str) or not self.step_id.strip():
            raise ConfigurationError(f"step_id must be a non-empty string, got {self.step_id!r}")
        if not isinstance(self.transformer_type, str) or not self.transformer_type.strip():
            raise ConfigurationError(
                f"transformer_type must be a non-empty string, got {self.transformer_type!r}"
            )
        if not isinstance(self.parameters, MappingProxyType):
            if isinstance(self.parameters, Mapping):
                object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))
            else:
                raise ConfigurationError(
                    f"parameters must be a mapping, got {type(self.parameters).__name__}"
                )


@dataclass(frozen=True, slots=True)
class TwoLayerPreprocessingSpec:
    """Declarative specification of the two-layer preprocessing pipeline."""

    layer1_steps: tuple[PreprocessingStepSpec, ...] = ()
    layer2_steps: tuple[PreprocessingStepSpec, ...] = ()
    description: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.layer1_steps, tuple):
            if isinstance(self.layer1_steps, (list, Sequence)):
                object.__setattr__(self, "layer1_steps", tuple(self.layer1_steps))
            else:
                raise ConfigurationError(
                    f"layer1_steps must be a sequence of PreprocessingStepSpec, got {type(self.layer1_steps).__name__}"
                )
        if not isinstance(self.layer2_steps, tuple):
            if isinstance(self.layer2_steps, (list, Sequence)):
                object.__setattr__(self, "layer2_steps", tuple(self.layer2_steps))
            else:
                raise ConfigurationError(
                    f"layer2_steps must be a sequence of PreprocessingStepSpec, got {type(self.layer2_steps).__name__}"
                )


@dataclass(frozen=True, slots=True)
class TwoLayerPreprocessingState:
    """Immutable snapshot of the two-layer preprocessing state fitted intra-fold."""

    spec: TwoLayerPreprocessingSpec
    layer1_fitted_state: tuple[Any, ...] = ()
    layer2_fitted_state: tuple[Any, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.spec, TwoLayerPreprocessingSpec):
            raise ConfigurationError(
                f"spec must be a TwoLayerPreprocessingSpec, got {type(self.spec).__name__}"
            )
        if not isinstance(self.layer1_fitted_state, tuple):
            if isinstance(self.layer1_fitted_state, (list, Sequence)):
                object.__setattr__(self, "layer1_fitted_state", tuple(self.layer1_fitted_state))
            else:
                raise ConfigurationError(
                    f"layer1_fitted_state must be a tuple, got {type(self.layer1_fitted_state).__name__}"
                )
        if not isinstance(self.layer2_fitted_state, tuple):
            if isinstance(self.layer2_fitted_state, (list, Sequence)):
                object.__setattr__(self, "layer2_fitted_state", tuple(self.layer2_fitted_state))
            else:
                raise ConfigurationError(
                    f"layer2_fitted_state must be a tuple, got {type(self.layer2_fitted_state).__name__}"
                )


__all__ = [
    "ScalerType",
    "PreprocessingStepSpec",
    "TwoLayerPreprocessingSpec",
    "TwoLayerPreprocessingState",
]
