"""Declarative model specifications and catalog validation in memory.

Complies with MOD-02 (AC-M41-02-01 to AC-M41-02-04), MOD-07 (AC-M41-07-01,
AC-M41-07-02), ADR-005, RF3.1, RF3.2, and RNF07.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Callable, Mapping, Sequence

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.models.types import ModelCapabilities, ModelFamily

if TYPE_CHECKING:
    from experimental_ml.models.preprocessing.types import TwoLayerPreprocessingSpec
    from experimental_ml.tuning.types import HyperparameterSearchSpec

_MODEL_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


@dataclass(frozen=True, slots=True)
class ModelSpec:
    """Declarative specification for an experimental machine learning model."""

    model_id: str
    display_name: str
    family: ModelFamily
    estimator_factory: Callable[[int | None], Any]
    capabilities: ModelCapabilities
    description: str
    scientific_justification: str
    parameters: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    random_seed_policy: str = "fixed"
    preprocessing: Any | None = None
    search_spec: Any | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.parameters, MappingProxyType):
            if isinstance(self.parameters, Mapping):
                object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))
            else:
                raise ConfigurationError(
                    f"parameters must be a mapping, got {type(self.parameters).__name__}"
                )


def validate_model_spec(spec: ModelSpec) -> ModelSpec:
    """Perform pure declarative validation of a ModelSpec.

    Validates structural consistency, required fields, and capability coherence
    without executing training, mock fittings, or dummy inference.

    Args:
        spec: ModelSpec to validate.

    Returns:
        The validated ModelSpec instance unmodified.

    Raises:
        ConfigurationError: If any field is invalid, missing, or if capabilities
            are contradictory.
    """
    if not isinstance(spec, ModelSpec):
        raise ConfigurationError(f"Expected ModelSpec, got {type(spec).__name__}")

    if not isinstance(spec.model_id, str) or not _MODEL_ID_PATTERN.match(spec.model_id.strip()):
        raise ConfigurationError(
            f"model_id must be a non-empty string matching '^[a-zA-Z0-9_-]+$', "
            f"got {spec.model_id!r}"
        )

    if not isinstance(spec.display_name, str) or not spec.display_name.strip():
        raise ConfigurationError(
            f"display_name must be a non-empty string, got {spec.display_name!r}"
        )

    if not isinstance(spec.family, ModelFamily):
        raise ConfigurationError(
            f"family must be a valid ModelFamily enum member, got {spec.family!r}"
        )

    if not callable(spec.estimator_factory):
        raise ConfigurationError(
            f"estimator_factory must be callable, got {type(spec.estimator_factory).__name__}"
        )

    if not isinstance(spec.capabilities, ModelCapabilities):
        raise ConfigurationError(
            f"capabilities must be a ModelCapabilities instance, "
            f"got {type(spec.capabilities).__name__}"
        )

    if not isinstance(spec.description, str) or not spec.description.strip():
        raise ConfigurationError(
            f"description must be a non-empty string, got {spec.description!r}"
        )

    if not isinstance(spec.scientific_justification, str) or not spec.scientific_justification.strip():
        raise ConfigurationError(
            f"scientific_justification must be a non-empty string, "
            f"got {spec.scientific_justification!r}"
        )

    # Capability coherence checks (AC-M41-02-04)
    if not spec.capabilities.supports_predict:
        raise ConfigurationError("ModelCapabilities must declare supports_predict=True")

    if not spec.capabilities.requires_fit and spec.capabilities.supports_sample_weight:
        raise ConfigurationError(
            "Contradictory capabilities: requires_fit=False cannot be combined "
            "with supports_sample_weight=True"
        )

    if spec.preprocessing is not None:
        from experimental_ml.models.preprocessing.pipeline import validate_two_layer_preprocessing
        validate_two_layer_preprocessing(spec.preprocessing)

    if spec.search_spec is not None:
        from experimental_ml.tuning.validation import validate_search_spec
        validate_search_spec(spec.search_spec)

    return spec


def validate_models_catalog(specs: Sequence[ModelSpec]) -> MappingProxyType[str, ModelSpec]:
    """Validate a sequence of ModelSpec instances as an in-memory catalog.

    Verifies each specification individually and enforces uniqueness of model_id.

    Args:
        specs: Sequence of ModelSpec instances to validate.

    Returns:
        Immutable MappingProxyType mapping model_id to validated ModelSpec.

    Raises:
        ConfigurationError: If any spec is invalid or duplicate model_id values are found.
    """
    if not isinstance(specs, (list, tuple, Sequence)) or isinstance(specs, (str, bytes, Mapping)):
        raise ConfigurationError(
            f"specs must be a sequence of ModelSpec objects, got {type(specs).__name__}"
        )

    catalog: dict[str, ModelSpec] = {}
    for i, spec in enumerate(specs):
        validated_spec = validate_model_spec(spec)
        mid = validated_spec.model_id
        if mid in catalog:
            raise ConfigurationError(
                f"Duplicate model_id detected at index {i}: {mid!r} already registered"
            )
        catalog[mid] = validated_spec

    return MappingProxyType(catalog)


__all__ = [
    "ModelSpec",
    "validate_model_spec",
    "validate_models_catalog",
]
