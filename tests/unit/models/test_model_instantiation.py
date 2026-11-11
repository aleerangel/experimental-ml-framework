"""Unit tests for fresh model instantiation and instance isolation.

Covers MOD-03 (AC-M41-03-01 to AC-M41-03-05) and checks C8, C9, C10, C11, C12.
"""

from __future__ import annotations

import pytest

from experimental_ml.core.findings import ConfigurationError, ContractViolationError
from experimental_ml.models.execution import (
    instantiate_fresh_model,
    reset_active_instances,
)
from experimental_ml.models.spec import ModelSpec
from experimental_ml.models.types import ModelCapabilities, ModelFamily


class DummyEstimator:
    def __init__(self, seed: int | None = None) -> None:
        self.seed = seed
        self.weights = [1.0, 2.0]
        self.fitted = False


@pytest.fixture(autouse=True)
def clean_registry() -> None:
    reset_active_instances()
    yield
    reset_active_instances()


def _make_spec(factory) -> ModelSpec:
    return ModelSpec(
        model_id="dummy_model",
        display_name="Dummy Model",
        family=ModelFamily.CLASSICAL_ML,
        estimator_factory=factory,
        capabilities=ModelCapabilities(),
        description="A dummy test model",
        scientific_justification="Unit testing isolation",
    )


def test_m41_03_01_instantiate_fresh_model_with_seed() -> None:
    """AC-M41-03-01 / C8: instantiate_fresh_model passes seed to factory and returns fresh instance."""
    spec = _make_spec(lambda seed: DummyEstimator(seed=seed))
    m1 = instantiate_fresh_model(spec, seed=42)
    assert isinstance(m1, DummyEstimator)
    assert m1.seed == 42


def test_m41_03_02_instantiate_fresh_model_seed_none() -> None:
    """AC-M41-03-02 / C9: instantiate_fresh_model passes None to factory when seed is None."""
    spec = _make_spec(lambda seed: DummyEstimator(seed=seed))
    m = instantiate_fresh_model(spec, seed=None)
    assert isinstance(m, DummyEstimator)
    assert m.seed is None


def test_m41_03_03_instantiate_fresh_model_singleton_rejection() -> None:
    """AC-M41-03-03 / C10: instantiate_fresh_model rejects singleton or active instance."""
    singleton_instance = DummyEstimator()
    spec = _make_spec(lambda seed: singleton_instance)

    # First call succeeds and registers instance
    inst1 = instantiate_fresh_model(spec, seed=1)
    assert inst1 is singleton_instance

    # Second call returns the exact same object -> ContractViolationError
    with pytest.raises(ContractViolationError, match="Instance isolation breach"):
        instantiate_fresh_model(spec, seed=2)


def test_m41_03_04_instantiate_fresh_model_factory_error_handling() -> None:
    """AC-M41-03-04 / C11: instantiate_fresh_model wraps factory errors in ConfigurationError."""
    # Factory that rejects arguments
    def rejecting_factory():
        return DummyEstimator()

    spec_reject = _make_spec(rejecting_factory)
    with pytest.raises(ConfigurationError, match="Failed to instantiate model"):
        instantiate_fresh_model(spec_reject, seed=42)

    # Factory that raises an unhandled exception
    def crashing_factory(seed):
        raise ValueError("Invalid hyperparameter configuration")

    spec_crash = _make_spec(crashing_factory)
    with pytest.raises(ConfigurationError, match="Failed to instantiate model"):
        instantiate_fresh_model(spec_crash, seed=42)

    # Factory that returns None
    spec_none = _make_spec(lambda seed: None)
    with pytest.raises(ConfigurationError, match="returned None"):
        instantiate_fresh_model(spec_none, seed=42)


def test_m41_03_05_instantiate_fresh_model_instance_isolation() -> None:
    """AC-M41-03-05 / C12: Multiple instances are uncoupled in memory state (CA-E3-01)."""
    spec = _make_spec(lambda seed: DummyEstimator(seed=seed))
    inst1 = instantiate_fresh_model(spec, seed=10)
    inst2 = instantiate_fresh_model(spec, seed=20)

    assert inst1 is not inst2

    # Mutate inst1
    inst1.weights.append(99.9)
    inst1.fitted = True

    # Verify inst2 is untouched
    assert inst2.weights == [1.0, 2.0]
    assert inst2.fitted is False
