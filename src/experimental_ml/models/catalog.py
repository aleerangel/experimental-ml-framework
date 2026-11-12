"""ModelsCatalog data structure, serialization codecs and factory resolution (Stage 3).

Complies with MPC-01, MPC-02, STORE-03, STORE-05, RF3.1, and ARQUITETURA §5.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.hashing import config_hash
from experimental_ml.models.baselines import AnalyticalBiometricModel, DummyBaselineModel
from experimental_ml.models.preprocessing.types import PreprocessingStepSpec, TwoLayerPreprocessingSpec
from experimental_ml.models.spec import ModelSpec, validate_models_catalog
from experimental_ml.models.types import ModelCapabilities, ModelFamily
from experimental_ml.tuning.types import HyperparameterSearchSpec, SearchStrategy

__all__ = [
    "ModelsCatalog",
    "resolve_estimator_factory",
    "model_spec_to_dict",
    "model_spec_from_dict",
    "models_catalog_to_dict",
    "models_catalog_from_dict",
]


def resolve_estimator_factory(
    factory_ref: str | Callable[[int | None], Any],
) -> Callable[[int | None], Any]:
    """Resolve an estimator factory callable from a canonical baseline identifier or import string.

    Parameters
    ----------
    factory_ref:
        A callable or a string reference.
        Built-in identifiers:
          - 'DUMMY_BASELINE_MEAN'
          - 'DUMMY_BASELINE_MEDIAN'
          - 'DUMMY_BASELINE_MOST_FREQUENT'
          - 'ANALYTICAL_BIOMETRIC'
        Custom import path:
          - 'module:qualname' (e.g. 'sklearn.linear_model:Ridge' or 'pkg.models:factory')

    Returns
    -------
    Callable[[int | None], Any]
        Resolved factory function.

    Raises
    ------
    ConfigurationError
        If the reference cannot be resolved or does not point to a callable.
    """
    if callable(factory_ref):
        return factory_ref

    if not isinstance(factory_ref, str):
        raise ConfigurationError(
            f"estimator_factory must be a callable or string reference, got {type(factory_ref).__name__}"
        )

    ref = factory_ref.strip()
    if not ref:
        raise ConfigurationError("estimator_factory reference cannot be empty")

    # 1. Built-in baselines
    if ref == "DUMMY_BASELINE_MEAN":
        return lambda seed=None: DummyBaselineModel(strategy="mean")
    if ref == "DUMMY_BASELINE_MEDIAN":
        return lambda seed=None: DummyBaselineModel(strategy="median")
    if ref == "DUMMY_BASELINE_MOST_FREQUENT":
        return lambda seed=None: DummyBaselineModel(strategy="most_frequent")
    if ref == "ANALYTICAL_BIOMETRIC":
        return lambda seed=None: AnalyticalBiometricModel()

    # 2. Dotted import path: module:qualname
    if ":" in ref:
        mod_name, qualname = ref.split(":", 1)
    elif "." in ref:
        parts = ref.rsplit(".", 1)
        mod_name, qualname = parts[0], parts[1]
    else:
        raise ConfigurationError(
            f"Cannot resolve estimator factory '{ref}'. "
            "Expected a built-in identifier (DUMMY_BASELINE_MEAN, DUMMY_BASELINE_MEDIAN, "
            "DUMMY_BASELINE_MOST_FREQUENT, ANALYTICAL_BIOMETRIC) or 'module:qualname' format"
        )

    try:
        mod = importlib.import_module(mod_name)
    except Exception as exc:
        raise ConfigurationError(
            f"Failed to import module '{mod_name}' for estimator factory '{ref}': {exc}"
        ) from exc

    try:
        obj: Any = mod
        for part in qualname.split("."):
            obj = getattr(obj, part)
    except Exception as exc:
        raise ConfigurationError(
            f"Attribute '{qualname}' not found in module '{mod_name}' for factory '{ref}': {exc}"
        ) from exc

    if not callable(obj):
        raise ConfigurationError(
            f"Resolved object '{ref}' is not callable, got {type(obj).__name__}"
        )

    return obj


def _capabilities_to_dict(caps: ModelCapabilities) -> dict[str, Any]:
    return {
        "supports_predict": caps.supports_predict,
        "requires_fit": caps.requires_fit,
        "supports_uncertainty": caps.supports_uncertainty,
        "supports_predict_proba": caps.supports_predict_proba,
        "supports_sample_weight": caps.supports_sample_weight,
        "supports_precomputed_kernel": caps.supports_precomputed_kernel,
    }


def _capabilities_from_dict(data: Mapping[str, Any]) -> ModelCapabilities:
    return ModelCapabilities(
        supports_predict=bool(data.get("supports_predict", True)),
        requires_fit=bool(data.get("requires_fit", True)),
        supports_uncertainty=bool(data.get("supports_uncertainty", False)),
        supports_predict_proba=bool(data.get("supports_predict_proba", False)),
        supports_sample_weight=bool(data.get("supports_sample_weight", False)),
        supports_precomputed_kernel=bool(data.get("supports_precomputed_kernel", False)),
    )


def _preprocessing_to_dict(spec: TwoLayerPreprocessingSpec) -> dict[str, Any]:
    return {
        "layer1_steps": [
            {
                "step_id": s.step_id,
                "transformer_type": s.transformer_type,
                "parameters": dict(s.parameters),
                "description": s.description,
            }
            for s in spec.layer1_steps
        ],
        "layer2_steps": [
            {
                "step_id": s.step_id,
                "transformer_type": s.transformer_type,
                "parameters": dict(s.parameters),
                "description": s.description,
            }
            for s in spec.layer2_steps
        ],
        "description": spec.description,
    }


def _preprocessing_from_dict(data: Mapping[str, Any]) -> TwoLayerPreprocessingSpec:
    layer1 = tuple(
        PreprocessingStepSpec(
            step_id=s["step_id"],
            transformer_type=s["transformer_type"],
            parameters=s.get("parameters", {}),
            description=s.get("description", ""),
        )
        for s in data.get("layer1_steps", [])
    )
    layer2 = tuple(
        PreprocessingStepSpec(
            step_id=s["step_id"],
            transformer_type=s["transformer_type"],
            parameters=s.get("parameters", {}),
            description=s.get("description", ""),
        )
        for s in data.get("layer2_steps", [])
    )
    return TwoLayerPreprocessingSpec(
        layer1_steps=layer1,
        layer2_steps=layer2,
        description=data.get("description", ""),
    )


def _search_spec_to_dict(spec: HyperparameterSearchSpec) -> dict[str, Any]:
    return {
        "search_strategy": spec.search_strategy.value,
        "param_grid": {k: list(v) for k, v in spec.param_grid.items()},
        "optimization_metric": spec.optimization_metric,
        "direction": spec.direction.value,
        "n_iter": spec.n_iter,
        "inner_cv_folds": spec.inner_cv_folds,
        "seed": spec.seed,
        "description": spec.description,
    }


def _search_spec_from_dict(data: Mapping[str, Any]) -> HyperparameterSearchSpec:
    return HyperparameterSearchSpec(
        search_strategy=data["search_strategy"],
        param_grid=data["param_grid"],
        optimization_metric=data["optimization_metric"],
        direction=data["direction"],
        n_iter=data.get("n_iter"),
        inner_cv_folds=data.get("inner_cv_folds", 3),
        seed=data.get("seed"),
        description=data.get("description", ""),
    )


def model_spec_to_dict(spec: ModelSpec) -> dict[str, Any]:
    """Serialize a ModelSpec instance to a JSON-compatible dictionary."""
    # Determine serializable factory reference
    factory_ref: str
    if hasattr(spec.estimator_factory, "_factory_ref"):
        factory_ref = getattr(spec.estimator_factory, "_factory_ref")
    elif spec.family == ModelFamily.BASELINE:
        strat = spec.parameters.get("strategy", "mean")
        if strat == "median":
            factory_ref = "DUMMY_BASELINE_MEDIAN"
        elif strat == "most_frequent":
            factory_ref = "DUMMY_BASELINE_MOST_FREQUENT"
        else:
            factory_ref = "DUMMY_BASELINE_MEAN"
    elif spec.family in (ModelFamily.BIOMETRIC_MODEL, ModelFamily.ANALYTICAL_EQUATION):
        factory_ref = "ANALYTICAL_BIOMETRIC"
    elif (
        hasattr(spec.estimator_factory, "__qualname__")
        and hasattr(spec.estimator_factory, "__module__")
        and "<locals>" not in spec.estimator_factory.__qualname__
        and "<lambda>" not in spec.estimator_factory.__qualname__
    ):
        factory_ref = f"{spec.estimator_factory.__module__}:{spec.estimator_factory.__qualname__}"
    else:
        factory_ref = str(getattr(spec.estimator_factory, "__name__", spec.estimator_factory))

    result: dict[str, Any] = {
        "model_id": spec.model_id,
        "display_name": spec.display_name,
        "family": spec.family.value,
        "estimator_factory": factory_ref,
        "capabilities": _capabilities_to_dict(spec.capabilities),
        "description": spec.description,
        "scientific_justification": spec.scientific_justification,
        "parameters": dict(spec.parameters),
        "random_seed_policy": spec.random_seed_policy,
    }

    if spec.preprocessing is not None:
        result["preprocessing"] = _preprocessing_to_dict(spec.preprocessing)

    if spec.search_spec is not None:
        result["search_spec"] = _search_spec_to_dict(spec.search_spec)

    return result


def model_spec_from_dict(data: Mapping[str, Any]) -> ModelSpec:
    """Deserialize a dictionary to a ModelSpec instance."""
    if not isinstance(data, Mapping):
        raise ConfigurationError(f"Expected mapping for model spec, got {type(data).__name__}")

    for req_field in ["model_id", "display_name", "family", "estimator_factory"]:
        if req_field not in data:
            raise ConfigurationError(f"Missing required field '{req_field}' in model spec")

    family_val = data["family"]
    family = ModelFamily(family_val) if isinstance(family_val, str) else family_val
    factory = resolve_estimator_factory(data["estimator_factory"])

    caps_data = data.get("capabilities", {})
    capabilities = _capabilities_from_dict(caps_data)

    prep = None
    if "preprocessing" in data and data["preprocessing"]:
        prep = _preprocessing_from_dict(data["preprocessing"])

    search = None
    if "search_spec" in data and data["search_spec"]:
        search = _search_spec_from_dict(data["search_spec"])

    return ModelSpec(
        model_id=str(data["model_id"]),
        display_name=str(data["display_name"]),
        family=family,
        estimator_factory=factory,
        capabilities=capabilities,
        description=str(data.get("description", "")),
        scientific_justification=str(data.get("scientific_justification", "")),
        parameters=data.get("parameters", {}),
        random_seed_policy=str(data.get("random_seed_policy", "fixed")),
        preprocessing=prep,
        search_spec=search,
    )


@dataclass(frozen=True, slots=True)
class ModelsCatalog:
    """Immutable catalog of experimental machine learning models."""

    models: tuple[ModelSpec, ...]
    metadata: MappingProxyType[str, Any]
    catalog_hash: str

    def __init__(
        self,
        models: Sequence[ModelSpec],
        metadata: Mapping[str, Any] | None = None,
        catalog_hash: str | None = None,
    ) -> None:
        validated_map = validate_models_catalog(models)
        models_tuple = tuple(validated_map.values())
        object.__setattr__(self, "models", models_tuple)

        meta_dict = dict(metadata or {})
        object.__setattr__(self, "metadata", MappingProxyType(meta_dict))

        if catalog_hash is None:
            # Deterministic hash derived from serializable dictionary representation
            canonical_payload = {
                "models": [model_spec_to_dict(m) for m in models_tuple],
                "metadata": meta_dict,
            }
            computed_hash = config_hash(canonical_payload)
            object.__setattr__(self, "catalog_hash", computed_hash)
        else:
            object.__setattr__(self, "catalog_hash", str(catalog_hash))

    def to_dict(self) -> dict[str, Any]:
        """Convert catalog to a JSON-compatible dictionary."""
        return models_catalog_to_dict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ModelsCatalog:
        """Construct ModelsCatalog from a dictionary."""
        return models_catalog_from_dict(data)


def models_catalog_to_dict(catalog: ModelsCatalog) -> dict[str, Any]:
    """Serialize ModelsCatalog to a JSON-compatible dictionary."""
    return {
        "models": [model_spec_to_dict(m) for m in catalog.models],
        "metadata": dict(catalog.metadata),
        "catalog_hash": catalog.catalog_hash,
    }


def models_catalog_from_dict(data: Mapping[str, Any]) -> ModelsCatalog:
    """Deserialize a dictionary to a ModelsCatalog instance."""
    if not isinstance(data, Mapping):
        raise ConfigurationError(f"Expected mapping for models catalog, got {type(data).__name__}")

    raw_models = data.get("models")
    if not isinstance(raw_models, (list, tuple)):
        raise ConfigurationError("models catalog must contain a 'models' list")

    parsed_models = [model_spec_from_dict(item) for item in raw_models]
    metadata = data.get("metadata", {})
    catalog_hash = data.get("catalog_hash")

    return ModelsCatalog(
        models=parsed_models,
        metadata=metadata,
        catalog_hash=catalog_hash,
    )
