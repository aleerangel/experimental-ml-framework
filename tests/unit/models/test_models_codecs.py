"""Unit tests for ModelsCatalog and JSON codecs (MPC-01)."""

import pytest

from experimental_ml.core.enums import MetricDirection
from experimental_ml.models.baselines import DummyBaselineModel
from experimental_ml.models.catalog import (
    ModelsCatalog,
    model_spec_from_dict,
    model_spec_to_dict,
    models_catalog_from_dict,
    models_catalog_to_dict,
)
from experimental_ml.models.preprocessing.types import PreprocessingStepSpec, TwoLayerPreprocessingSpec
from experimental_ml.models.spec import ModelSpec
from experimental_ml.models.types import ModelCapabilities, ModelFamily
from experimental_ml.tuning.types import HyperparameterSearchSpec, SearchStrategy


def _sample_model_spec() -> ModelSpec:
    return ModelSpec(
        model_id="baseline_mean",
        display_name="Baseline Mean Regressor",
        family=ModelFamily.BASELINE,
        estimator_factory=lambda seed: DummyBaselineModel(strategy="mean"),
        capabilities=ModelCapabilities(requires_fit=True, supports_uncertainty=True),
        description="Predicts the mean of y_train",
        scientific_justification="Minimal baseline comparator",
        parameters={"strategy": "mean"},
        random_seed_policy="none",
        preprocessing=TwoLayerPreprocessingSpec(
            layer1_steps=(
                PreprocessingStepSpec(
                    step_id="step_dummy",
                    transformer_type="PASSTHROUGH",
                ),
            ),
            description="Dummy scenario prep",
        ),
        search_spec=HyperparameterSearchSpec(
            search_strategy=SearchStrategy.FIXED,
            param_grid={"strategy": ("mean",)},
            optimization_metric="rmse",
            direction=MetricDirection.MINIMIZE,
            inner_cv_folds=3,
        ),
    )


def test_m44_01_01_models_catalog_dataclass() -> None:
    """C1: ModelsCatalog is defined as an immutable frozen dataclass with slots."""
    spec = _sample_model_spec()
    catalog = ModelsCatalog(
        models=[spec],
        metadata={"created_by": "test"},
    )
    assert len(catalog.models) == 1
    assert catalog.models[0].model_id == "baseline_mean"
    assert catalog.metadata["created_by"] == "test"
    assert isinstance(catalog.catalog_hash, str) and len(catalog.catalog_hash) == 64

    # Immutability
    with pytest.raises(Exception):
        catalog.catalog_hash = "modified"  # type: ignore[misc]

    with pytest.raises(Exception):
        catalog.models = ()  # type: ignore[misc]


def test_m44_01_02_models_catalog_to_dict() -> None:
    """C2: models_catalog_to_dict serializes models, capabilities, and parameters to JSON dict."""
    spec = _sample_model_spec()
    catalog = ModelsCatalog(models=[spec], metadata={"version": "1.0"})
    data = models_catalog_to_dict(catalog)

    assert "models" in data
    assert "metadata" in data
    assert "catalog_hash" in data
    assert len(data["models"]) == 1

    m_dict = data["models"][0]
    assert m_dict["model_id"] == "baseline_mean"
    assert m_dict["family"] == "BASELINE"
    assert m_dict["capabilities"]["requires_fit"] is True
    assert m_dict["capabilities"]["supports_uncertainty"] is True
    assert "preprocessing" in m_dict
    assert "search_spec" in m_dict
    assert m_dict["search_spec"]["optimization_metric"] == "rmse"


def test_m44_01_03_models_catalog_from_dict() -> None:
    """C3: models_catalog_from_dict reconstructs immutable ModelsCatalog from dictionary."""
    raw_dict = {
        "models": [
            {
                "model_id": "dummy_mean",
                "display_name": "Dummy Mean",
                "family": "BASELINE",
                "estimator_factory": "DUMMY_BASELINE_MEAN",
                "capabilities": {
                    "supports_predict": True,
                    "requires_fit": True,
                    "supports_uncertainty": True,
                },
                "description": "Baseline mean",
                "scientific_justification": "Baseline reference",
                "parameters": {"strategy": "mean"},
                "random_seed_policy": "none",
            }
        ],
        "metadata": {"source": "unit_test"},
    }

    catalog = models_catalog_from_dict(raw_dict)
    assert len(catalog.models) == 1
    reconstructed = catalog.models[0]
    assert reconstructed.model_id == "dummy_mean"
    assert reconstructed.family == ModelFamily.BASELINE
    assert reconstructed.capabilities.requires_fit is True
    assert reconstructed.capabilities.supports_uncertainty is True

    # Factory works
    instance = reconstructed.estimator_factory(None)
    assert isinstance(instance, DummyBaselineModel)
