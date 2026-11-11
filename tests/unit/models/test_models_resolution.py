"""Unit tests for estimator factory resolution (MPC-02)."""

import pytest

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.models.baselines import AnalyticalBiometricModel, DummyBaselineModel
from experimental_ml.models.catalog import resolve_estimator_factory


def test_m44_02_01_resolve_builtin_baselines() -> None:
    """C4: resolve_estimator_factory resolves canonical baseline identifiers."""
    # 1. DUMMY_BASELINE_MEAN
    f_mean = resolve_estimator_factory("DUMMY_BASELINE_MEAN")
    assert callable(f_mean)
    inst_mean = f_mean(None)
    assert isinstance(inst_mean, DummyBaselineModel)
    assert inst_mean.strategy == "mean"

    # 2. DUMMY_BASELINE_MEDIAN
    f_med = resolve_estimator_factory("DUMMY_BASELINE_MEDIAN")
    inst_med = f_med(None)
    assert isinstance(inst_med, DummyBaselineModel)
    assert inst_med.strategy == "median"

    # 3. DUMMY_BASELINE_MOST_FREQUENT
    f_mf = resolve_estimator_factory("DUMMY_BASELINE_MOST_FREQUENT")
    inst_mf = f_mf(None)
    assert isinstance(inst_mf, DummyBaselineModel)
    assert inst_mf.strategy == "most_frequent"

    # 4. ANALYTICAL_BIOMETRIC
    f_bio = resolve_estimator_factory("ANALYTICAL_BIOMETRIC")
    inst_bio = f_bio(None)
    assert isinstance(inst_bio, AnalyticalBiometricModel)


def test_m44_02_02_resolve_dotted_import_path() -> None:
    """C5: resolve_estimator_factory resolves import strings in module:qualname format."""
    # Standard format module:qualname
    f_resolved = resolve_estimator_factory("experimental_ml.models.baselines:DummyBaselineModel")
    assert f_resolved is DummyBaselineModel

    # Dotted fallback module.qualname
    f_dotted = resolve_estimator_factory("experimental_ml.models.baselines.AnalyticalBiometricModel")
    assert f_dotted is AnalyticalBiometricModel

    # Direct callable passthrough
    def custom_factory(seed: int | None = None) -> str:
        return f"model_{seed}"

    assert resolve_estimator_factory(custom_factory) is custom_factory


def test_m44_02_03_resolve_invalid_reference_raises() -> None:
    """C6: resolve_estimator_factory raises ConfigurationError on unresolvable references."""
    # 1. Non-existent module
    with pytest.raises(ConfigurationError, match="Failed to import module"):
        resolve_estimator_factory("non_existent_module:MyModel")

    # 2. Non-existent attribute
    with pytest.raises(ConfigurationError, match="Attribute 'NonExistentAttr' not found"):
        resolve_estimator_factory("experimental_ml.models.baselines:NonExistentAttr")

    # 3. Non-callable object
    with pytest.raises(ConfigurationError, match="is not callable"):
        resolve_estimator_factory("experimental_ml.models.spec:_MODEL_ID_PATTERN")

    # 4. Empty or invalid string format
    with pytest.raises(ConfigurationError, match="cannot be empty"):
        resolve_estimator_factory("   ")

    with pytest.raises(ConfigurationError, match="Expected a built-in identifier"):
        resolve_estimator_factory("singlewordinvalid")
