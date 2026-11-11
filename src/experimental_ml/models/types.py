"""Domain types, enumerations, capabilities, and diagnostics for ML models.

Complies with MOD-01 (AC-M41-01-01, AC-M41-01-02, AC-M41-01-03), ADR-005,
RF3.1, RF3.2, RF3.6, and RNF07.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.types import ModelId


class ModelFamily(str, Enum):
    """Canonical model families supported by the framework."""

    CLASSICAL_ML = "CLASSICAL_ML"
    NEURAL_NETWORK = "NEURAL_NETWORK"
    QUANTUM_CIRCUIT = "QUANTUM_CIRCUIT"
    QUANTUM_KERNEL = "QUANTUM_KERNEL"
    QUANTUM_SOLVER = "QUANTUM_SOLVER"
    ANALYTICAL_EQUATION = "ANALYTICAL_EQUATION"
    BIOMETRIC_MODEL = "BIOMETRIC_MODEL"
    BASELINE = "BASELINE"
    CUSTOM = "CUSTOM"


@dataclass(frozen=True, slots=True)
class ModelCapabilities:
    """Operational and functional capabilities declared for an estimator."""

    requires_fit: bool = True
    supports_predict: bool = True
    supports_uncertainty: bool = False
    supports_predict_proba: bool = False
    supports_decision_function: bool = False
    supports_sample_weight: bool = False
    supports_precomputed_kernel: bool = False
    supports_internal_parallelism_control: bool = False
    expected_input_types: tuple[str, ...] = ("dense_numeric",)

    def __post_init__(self) -> None:
        if not isinstance(self.expected_input_types, tuple):
            if isinstance(self.expected_input_types, (list, Sequence)):
                object.__setattr__(self, "expected_input_types", tuple(self.expected_input_types))
            else:
                raise ConfigurationError(
                    f"expected_input_types must be a tuple/sequence of strings, "
                    f"got {type(self.expected_input_types).__name__}"
                )


@dataclass(frozen=True, slots=True)
class ModelDiagnostics:
    """Immutable snapshot of internal model diagnostics and execution metadata."""

    model_id: str
    phase: str
    diagnostics: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    extracted_at: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.model_id, str) or not self.model_id.strip():
            raise ConfigurationError(f"model_id must be a non-empty string, got {self.model_id!r}")
        if not isinstance(self.phase, str) or not self.phase.strip():
            raise ConfigurationError(f"phase must be a non-empty string, got {self.phase!r}")
        if not isinstance(self.extracted_at, str) or not self.extracted_at.strip():
            raise ConfigurationError(
                f"extracted_at must be a non-empty ISO 8601 string, got {self.extracted_at!r}"
            )
        if not isinstance(self.diagnostics, MappingProxyType):
            if isinstance(self.diagnostics, Mapping):
                object.__setattr__(self, "diagnostics", MappingProxyType(dict(self.diagnostics)))
            else:
                raise ConfigurationError(
                    f"diagnostics must be a mapping, got {type(self.diagnostics).__name__}"
                )


__all__ = [
    "ModelId",
    "ModelFamily",
    "ModelCapabilities",
    "ModelDiagnostics",
]
