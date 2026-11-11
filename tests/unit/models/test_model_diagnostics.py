"""Unit tests for internal model diagnostics snapshot and deep immutability.

Covers MOD-06 (AC-M41-06-01 to AC-M41-06-04) and checks C24, C25, C26, C27.
"""

from __future__ import annotations

from types import MappingProxyType
import numpy as np
import pytest

from experimental_ml.core.findings import ContractViolationError
from experimental_ml.models.diagnostics import extract_model_diagnostics
from experimental_ml.models.spec import ModelSpec
from experimental_ml.models.types import ModelCapabilities, ModelDiagnostics, ModelFamily


class DiagnosticModel:
    def __init__(self) -> None:
        self.n_iter_ = 10
        self.loss_ = 0.05
        self.coef_ = np.array([1.5, -2.5])
        self.nested_metrics_ = {"train_loss": [0.5, 0.2, 0.05]}

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.ones(X.shape[0]) * 100.0


def _make_spec() -> ModelSpec:
    return ModelSpec(
        model_id="diag_model",
        display_name="Diagnostic Test Model",
        family=ModelFamily.CLASSICAL_ML,
        estimator_factory=DiagnosticModel,
        capabilities=ModelCapabilities(),
        description="Model for testing diagnostics",
        scientific_justification="Diagnostic snapshot immutability test",
    )


def test_m41_06_01_extract_model_diagnostics_structure() -> None:
    """AC-M41-06-01 / C24: extract_model_diagnostics returns immutable ModelDiagnostics with native scalars."""
    spec = _make_spec()
    model = DiagnosticModel()

    diag = extract_model_diagnostics(model, spec, phase="fit")

    assert isinstance(diag, ModelDiagnostics)
    assert diag.model_id == "diag_model"
    assert diag.phase == "fit"
    assert isinstance(diag.diagnostics, MappingProxyType)
    assert diag.diagnostics["n_iter_"] == 10
    assert diag.diagnostics["loss_"] == 0.05
    assert diag.diagnostics["coef_"] == (1.5, -2.5)
    assert isinstance(diag.diagnostics["nested_metrics_"], MappingProxyType)
    assert diag.diagnostics["nested_metrics_"]["train_loss"] == (0.5, 0.2, 0.05)
    assert isinstance(diag.extracted_at, str)
    assert len(diag.extracted_at) > 0


def test_m41_06_02_extract_model_diagnostics_snapshot_independence() -> None:
    """AC-M41-06-02 / C25: Diagnostics extraction operates as an independent snapshot uncoupled from mutations."""
    spec = _make_spec()
    model = DiagnosticModel()

    diag = extract_model_diagnostics(model, spec, phase="fit")

    # Mutate model attributes after extraction
    model.n_iter_ = 999
    model.loss_ = 0.999
    model.coef_[0] = 999.0
    model.nested_metrics_["train_loss"] = [999.0]

    # Verify that the extracted diagnostics remain pristine
    assert diag.diagnostics["n_iter_"] == 10
    assert diag.diagnostics["loss_"] == 0.05
    assert diag.diagnostics["coef_"] == (1.5, -2.5)
    assert diag.diagnostics["nested_metrics_"]["train_loss"] == (0.5, 0.2, 0.05)


def test_m41_06_03_extract_model_diagnostics_unsupported_complex_rejection() -> None:
    """AC-M41-06-03 / C26: extract_model_diagnostics raises ContractViolationError on unsupported mutable objects."""
    spec = _make_spec()

    class CustomComplexObject:
        def __init__(self) -> None:
            self.state = "active"

    class BadModel:
        def __init__(self) -> None:
            self.bad_attribute_ = CustomComplexObject()

    model = BadModel()
    with pytest.raises(ContractViolationError, match="Unsupported mutable complex object"):
        extract_model_diagnostics(model, spec, phase="fit")


def test_m41_06_04_extract_model_diagnostics_model_mutation_invariance() -> None:
    """AC-M41-06-04 / C27: Diagnostics extraction never mutates model instance or its predictions."""
    spec = _make_spec()
    model = DiagnosticModel()
    X = np.array([[1.0], [2.0]])

    pred_before = model.predict(X)
    loss_before = model.loss_
    coef_before = model.coef_.copy()

    extract_model_diagnostics(model, spec, phase="fit")

    pred_after = model.predict(X)
    assert np.array_equal(pred_before, pred_after)
    assert model.loss_ == loss_before
    assert np.array_equal(model.coef_, coef_before)
