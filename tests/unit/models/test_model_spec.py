"""Unit tests for ModelSpec and declarative validation of models and catalogs.

Covers MOD-02 (AC-M41-02-01 to AC-M41-02-04), MOD-07 (AC-M41-07-01, AC-M41-07-02),
and checks C4, C5, C6, C7, C28, C29.
"""

from __future__ import annotations

from types import MappingProxyType
import pytest

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.models.spec import (
    ModelSpec,
    validate_model_spec,
    validate_models_catalog,
)
from experimental_ml.models.types import ModelCapabilities, ModelFamily


def _dummy_factory(seed: int | None = None) -> object:
    return object()


def _make_valid_spec(
    model_id: str = "ridge_regressor",
    capabilities: ModelCapabilities | None = None,
    parameters: dict | None = None,
) -> ModelSpec:
    return ModelSpec(
        model_id=model_id,
        display_name="Ridge Regressor",
        family=ModelFamily.CLASSICAL_ML,
        estimator_factory=_dummy_factory,
        capabilities=capabilities or ModelCapabilities(),
        description="Ridge regression with L2 regularization",
        scientific_justification="Baseline linear model penalizing coefficient norm",
        parameters=parameters or {"alpha": 1.0},
        random_seed_policy="fixed",
    )


def test_m41_02_01_model_spec_dataclass() -> None:
    """AC-M41-02-01 / C4: ModelSpec is an immutable frozen dataclass with slots."""
    spec = _make_valid_spec()
    assert spec.model_id == "ridge_regressor"
    assert spec.display_name == "Ridge Regressor"
    assert spec.family == ModelFamily.CLASSICAL_ML
    assert spec.estimator_factory is _dummy_factory
    assert spec.capabilities.requires_fit is True
    assert isinstance(spec.parameters, MappingProxyType)
    assert spec.parameters["alpha"] == 1.0
    assert spec.random_seed_policy == "fixed"

    # Immutability check
    with pytest.raises((AttributeError, TypeError)):
        spec.display_name = "New Name"  # type: ignore[misc]

    with pytest.raises((AttributeError, TypeError)):
        spec.parameters["alpha"] = 2.0  # type: ignore[index]


def test_m41_02_02_validate_model_spec_valid() -> None:
    """AC-M41-02-02 / C5: validate_model_spec validates without mutating or executing."""
    spec = _make_valid_spec()
    validated = validate_model_spec(spec)
    assert validated is spec


def test_m41_02_03_validate_model_spec_invalid_fields() -> None:
    """AC-M41-02-03 / C6: validate_model_spec raises ConfigurationError on invalid fields."""
    # Invalid model_id characters
    with pytest.raises(ConfigurationError, match="model_id"):
        validate_model_spec(_make_valid_spec(model_id="invalid model id with spaces"))

    with pytest.raises(ConfigurationError, match="model_id"):
        validate_model_spec(_make_valid_spec(model_id=""))

    with pytest.raises(ConfigurationError, match="model_id"):
        validate_model_spec(_make_valid_spec(model_id="model@special!"))

    # Empty display_name
    spec_empty_display = ModelSpec(
        model_id="ridge",
        display_name="",
        family=ModelFamily.CLASSICAL_ML,
        estimator_factory=_dummy_factory,
        capabilities=ModelCapabilities(),
        description="desc",
        scientific_justification="just",
    )
    with pytest.raises(ConfigurationError, match="display_name"):
        validate_model_spec(spec_empty_display)

    # Empty description
    spec_empty_desc = ModelSpec(
        model_id="ridge",
        display_name="Ridge",
        family=ModelFamily.CLASSICAL_ML,
        estimator_factory=_dummy_factory,
        capabilities=ModelCapabilities(),
        description="",
        scientific_justification="just",
    )
    with pytest.raises(ConfigurationError, match="description"):
        validate_model_spec(spec_empty_desc)

    # Empty scientific_justification
    spec_empty_just = ModelSpec(
        model_id="ridge",
        display_name="Ridge",
        family=ModelFamily.CLASSICAL_ML,
        estimator_factory=_dummy_factory,
        capabilities=ModelCapabilities(),
        description="desc",
        scientific_justification="   ",
    )
    with pytest.raises(ConfigurationError, match="scientific_justification"):
        validate_model_spec(spec_empty_just)

    # Non-callable factory
    spec_bad_factory = ModelSpec(
        model_id="ridge",
        display_name="Ridge",
        family=ModelFamily.CLASSICAL_ML,
        estimator_factory="not-a-callable",  # type: ignore[arg-type]
        capabilities=ModelCapabilities(),
        description="desc",
        scientific_justification="just",
    )
    with pytest.raises(ConfigurationError, match="estimator_factory must be callable"):
        validate_model_spec(spec_bad_factory)


def test_m41_02_04_validate_model_spec_contradictory_capabilities() -> None:
    """AC-M41-02-04 / C7: validate_model_spec raises ConfigurationError on contradictory flags."""
    # supports_predict=False is rejected
    caps_no_predict = ModelCapabilities(supports_predict=False)
    spec_no_predict = _make_valid_spec(capabilities=caps_no_predict)
    with pytest.raises(ConfigurationError, match="supports_predict=True"):
        validate_model_spec(spec_no_predict)

    # requires_fit=False combined with supports_sample_weight=True is contradictory
    caps_contradictory = ModelCapabilities(
        requires_fit=False,
        supports_sample_weight=True,
    )
    spec_contradictory = _make_valid_spec(capabilities=caps_contradictory)
    with pytest.raises(ConfigurationError, match="requires_fit=False cannot be combined with supports_sample_weight=True"):
        validate_model_spec(spec_contradictory)


def test_m41_07_01_validate_models_catalog_valid() -> None:
    """AC-M41-07-01 / C28: validate_models_catalog validates sequence and returns mapping."""
    spec1 = _make_valid_spec(model_id="model_1")
    spec2 = _make_valid_spec(model_id="model_2")
    catalog = validate_models_catalog([spec1, spec2])

    assert isinstance(catalog, MappingProxyType)
    assert len(catalog) == 2
    assert catalog["model_1"] is spec1
    assert catalog["model_2"] is spec2

    # Verify immutability of catalog
    with pytest.raises((AttributeError, TypeError)):
        catalog["model_3"] = spec1  # type: ignore[index]


def test_m41_07_02_validate_models_catalog_duplicate_ids() -> None:
    """AC-M41-07-02 / C29: validate_models_catalog raises ConfigurationError on duplicates."""
    spec1 = _make_valid_spec(model_id="same_id")
    spec2 = _make_valid_spec(model_id="same_id")

    with pytest.raises(ConfigurationError, match="Duplicate model_id detected"):
        validate_models_catalog([spec1, spec2])
