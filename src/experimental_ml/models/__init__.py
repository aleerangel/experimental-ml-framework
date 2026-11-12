"""Models subsystem: specifications, capabilities, and lifecycle contracts.

Complies with MOD-01 to MOD-09, ADR-005, RF3.1, RF3.2, RF3.6, and XCUT-02.
"""

from __future__ import annotations

from experimental_ml.models.baselines import (
    AnalyticalBiometricModel,
    DummyBaselineModel,
)
from experimental_ml.models.catalog import (
    ModelsCatalog,
    model_spec_from_dict,
    model_spec_to_dict,
    models_catalog_from_dict,
    models_catalog_to_dict,
    resolve_estimator_factory,
)
from experimental_ml.models.diagnostics import extract_model_diagnostics
from experimental_ml.models.execution import (
    fit_model,
    instantiate_fresh_model,
    predict_model,
    reset_active_instances,
)
from experimental_ml.models.preprocessing import (
    ScalerType,
    TwoLayerPreprocessingSpec,
    TwoLayerPreprocessingState,
    apply_two_layer_preprocessing,
    fit_two_layer_preprocessing,
    validate_two_layer_preprocessing,
)
from experimental_ml.models.spec import (
    ModelSpec,
    validate_model_spec,
    validate_models_catalog,
)
from experimental_ml.models.storage import (
    load_models_catalog,
    save_models_catalog,
)
from experimental_ml.models.types import (
    ModelCapabilities,
    ModelDiagnostics,
    ModelFamily,
    ModelId,
)

__all__ = [
    "ModelId",
    "ModelFamily",
    "ModelCapabilities",
    "ModelDiagnostics",
    "ModelSpec",
    "validate_model_spec",
    "validate_models_catalog",
    "instantiate_fresh_model",
    "reset_active_instances",
    "fit_model",
    "predict_model",
    "extract_model_diagnostics",
    "DummyBaselineModel",
    "AnalyticalBiometricModel",
    "ScalerType",
    "TwoLayerPreprocessingSpec",
    "TwoLayerPreprocessingState",
    "validate_two_layer_preprocessing",
    "fit_two_layer_preprocessing",
    "apply_two_layer_preprocessing",
    "ModelsCatalog",
    "model_spec_to_dict",
    "model_spec_from_dict",
    "models_catalog_to_dict",
    "models_catalog_from_dict",
    "resolve_estimator_factory",
    "save_models_catalog",
    "load_models_catalog",
]
