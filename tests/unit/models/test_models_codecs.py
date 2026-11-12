"""Unit tests for ModelsCatalog and JSON codecs (MPC-01)."""

import json
import numpy as np
import pytest

from experimental_ml.core.enums import MetricDirection
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.models.baselines import DummyBaselineModel
from experimental_ml.models.catalog import (
    ModelsCatalog,
    callable_to_reference,
    model_spec_from_dict,
    model_spec_to_dict,
    models_catalog_from_dict,
    models_catalog_to_dict,
    resolve_estimator_factory,
)
from experimental_ml.models.preprocessing.pipeline import fit_two_layer_preprocessing
from experimental_ml.models.preprocessing.types import PreprocessingStepSpec, TwoLayerPreprocessingSpec
from experimental_ml.models.spec import ModelSpec
from experimental_ml.models.types import ModelCapabilities, ModelFamily
from experimental_ml.tuning.types import HyperparameterSearchSpec, SearchStrategy


def canonical_test_kernel(X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
    """Importable top-level kernel function for AUD-M4-01 roundtrip testing."""
    return np.asarray(X1) @ np.asarray(X2).T


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


def test_aud_m4_01_precomputed_kernel_callable_serialization_and_roundtrip() -> None:
    """AUD-M4-01: PRECOMPUTED_KERNEL steps with importable callables serialize to JSON and reconstruct cleanly."""
    prep = TwoLayerPreprocessingSpec(
        layer1_steps=(),
        layer2_steps=(
            PreprocessingStepSpec(
                step_id="q_kernel",
                transformer_type="PRECOMPUTED_KERNEL",
                parameters={"kernel_func": canonical_test_kernel},
                description="Quantum / Gram kernel step",
            ),
        ),
    )
    spec = ModelSpec(
        model_id="kernel_model",
        display_name="Kernel Regressor",
        family=ModelFamily.QUANTUM_KERNEL,
        estimator_factory=resolve_estimator_factory("DUMMY_BASELINE_MEAN"),
        capabilities=ModelCapabilities(supports_precomputed_kernel=True),
        description="Quantum kernel model",
        scientific_justification="Gram matrix regression",
        preprocessing=prep,
    )
    catalog = ModelsCatalog(models=[spec])

    # 1. to_dict produces clean serializable dictionary
    catalog_dict = models_catalog_to_dict(catalog)
    step_params = catalog_dict["models"][0]["preprocessing"]["layer2_steps"][0]["parameters"]
    assert "kernel_func" in step_params
    expected_ref = f"{canonical_test_kernel.__module__}:{canonical_test_kernel.__qualname__}"
    assert step_params["kernel_func"] == expected_ref

    # 2. JSON dumps succeeds without TypeError (AUD-M4-01)
    json_str = json.dumps(catalog_dict, indent=2)
    assert expected_ref in json_str

    # 3. Reconstruct from JSON dictionary
    loaded_dict = json.loads(json_str)
    reconstructed_catalog = models_catalog_from_dict(loaded_dict)
    reconstructed_spec = reconstructed_catalog.models[0]
    assert reconstructed_spec.preprocessing is not None

    # 4. Fit two-layer preprocessing on reconstructed spec resolves importable kernel callable
    X_train = np.array([[1.0, 2.0], [3.0, 4.0]])
    state = fit_two_layer_preprocessing(reconstructed_spec.preprocessing, X_train)
    assert len(state.layer2_fitted_state) == 1
    assert state.layer2_fitted_state[0] is not None
    assert state.layer2_fitted_state[0].is_fitted is True


def test_aud_m4_04_lambda_and_local_functions_rejected_on_serialization() -> None:
    """AUD-M4-04: Local functions and lambdas without _factory_ref are rejected explicitly at serialization time."""
    # Local estimator factory
    def local_factory(seed):
        return DummyBaselineModel()

    spec_local = ModelSpec(
        model_id="local_model",
        display_name="Local Model",
        family=ModelFamily.CUSTOM,
        estimator_factory=local_factory,
        capabilities=ModelCapabilities(),
        description="Local factory",
        scientific_justification="Testing AUD-M4-04",
    )
    with pytest.raises(ConfigurationError, match="local functions and lambdas cannot be persisted"):
        model_spec_to_dict(spec_local)

    # Local kernel_func in preprocessing
    def local_kernel(x1, x2):
        return x1 @ x2.T

    spec_local_kernel = ModelSpec(
        model_id="local_kernel_model",
        display_name="Local Kernel Model",
        family=ModelFamily.QUANTUM_KERNEL,
        estimator_factory="DUMMY_BASELINE_MEAN",
        capabilities=ModelCapabilities(supports_precomputed_kernel=True),
        description="Local kernel",
        scientific_justification="Testing AUD-M4-04",
        preprocessing=TwoLayerPreprocessingSpec(
            layer1_steps=(),
            layer2_steps=(
                PreprocessingStepSpec(
                    step_id="step_k",
                    transformer_type="PRECOMPUTED_KERNEL",
                    parameters={"kernel_func": local_kernel},
                ),
            ),
        ),
    )
    with pytest.raises(ConfigurationError, match="local functions and lambdas cannot be persisted"):
        model_spec_to_dict(spec_local_kernel)


def test_aud_m4_04_factory_ref_attribute_allows_reconstructible_lambdas() -> None:
    """AUD-M4-04: Functions or lambdas with _factory_ref attribute serialize cleanly to that reference."""
    factory = lambda seed: DummyBaselineModel(strategy="mean")
    factory._factory_ref = "DUMMY_BASELINE_MEAN"

    spec = ModelSpec(
        model_id="annotated_lambda",
        display_name="Annotated Lambda",
        family=ModelFamily.CUSTOM,
        estimator_factory=factory,
        capabilities=ModelCapabilities(),
        description="Annotated lambda with _factory_ref",
        scientific_justification="Testing AUD-M4-04",
    )
    data = model_spec_to_dict(spec)
    assert data["estimator_factory"] == "DUMMY_BASELINE_MEAN"

    reconstructed = model_spec_from_dict(data)
    assert reconstructed.model_id == "annotated_lambda"
    inst = reconstructed.estimator_factory(None)
    assert isinstance(inst, DummyBaselineModel)

