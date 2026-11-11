"""Integration tests for models lifecycle and runtime purity.

Covers MOD-09 (AC-M41-09-01) and checks C35, testing end-to-end integration across
specifications, catalogs, lifecycle execution, predictions, diagnostics, and baselines.
"""

from __future__ import annotations

import subprocess
import sys
import numpy as np
import pytest

from experimental_ml.models import (
    AnalyticalBiometricModel,
    DummyBaselineModel,
    ModelCapabilities,
    ModelDiagnostics,
    ModelFamily,
    ModelSpec,
    extract_model_diagnostics,
    fit_model,
    instantiate_fresh_model,
    predict_model,
    validate_model_spec,
    validate_models_catalog,
)


def test_m41_09_01_runtime_purity_numpy_only() -> None:
    """AC-M41-09-01 / C35: experimental_ml.models maintains single runtime dependency (numpy>=1.24.0)."""
    check_code = (
        "import sys\n"
        "import experimental_ml.models\n"
        "forbidden = ['sklearn', 'scipy', 'torch', 'tensorflow', 'jax', 'qiskit']\n"
        "loaded_forbidden = [pkg for pkg in forbidden if any(mod.startswith(pkg) for mod in sys.modules)]\n"
        "if loaded_forbidden:\n"
        "    print(f'Forbidden packages loaded: {loaded_forbidden}')\n"
        "    sys.exit(1)\n"
        "assert 'numpy' in sys.modules, 'numpy must be loaded'\n"
        "print('PURE_NUMPY_OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", check_code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"Runtime purity violation: {result.stderr or result.stdout}"
    assert "PURE_NUMPY_OK" in result.stdout


def test_models_end_to_end_lifecycle_pipeline() -> None:
    """Verify complete end-to-end lifecycle across catalog, fresh instantiation, fit, predict, diagnostics."""
    # 1. Define specifications
    reg_spec = ModelSpec(
        model_id="baseline_regression",
        display_name="Baseline Mean Regressor",
        family=ModelFamily.BASELINE,
        estimator_factory=lambda seed: DummyBaselineModel(strategy="mean"),
        capabilities=ModelCapabilities(
            requires_fit=True,
            supports_predict=True,
            supports_uncertainty=True,
            supports_predict_proba=False,
        ),
        description="Mean baseline regression model",
        scientific_justification="Minimal regression benchmark",
    )

    clf_spec = ModelSpec(
        model_id="baseline_classification",
        display_name="Baseline Most Frequent Classifier",
        family=ModelFamily.BASELINE,
        estimator_factory=lambda seed: DummyBaselineModel(strategy="most_frequent"),
        capabilities=ModelCapabilities(
            requires_fit=True,
            supports_predict=True,
            supports_uncertainty=False,
            supports_predict_proba=True,
        ),
        description="Majority class classification benchmark",
        scientific_justification="Minimal classification benchmark",
    )

    bio_spec = ModelSpec(
        model_id="analytical_clutter",
        display_name="Analytical Clutter Biometric Model",
        family=ModelFamily.BIOMETRIC_MODEL,
        estimator_factory=lambda seed: AnalyticalBiometricModel(
            formula_name="clutter_relative",
            coefficients={"intercept": 5.0, "w0": 1.5, "w1": 2.5},
            required_features=(0, 1),
        ),
        capabilities=ModelCapabilities(
            requires_fit=False,
            supports_predict=True,
            supports_uncertainty=False,
            supports_predict_proba=False,
        ),
        description="Analytical equation without training",
        scientific_justification="Domain equation benchmark",
    )

    # 2. Validate catalog
    catalog = validate_models_catalog([reg_spec, clf_spec, bio_spec])
    assert len(catalog) == 3
    assert "baseline_regression" in catalog
    assert "baseline_classification" in catalog
    assert "analytical_clutter" in catalog

    # 3. Fresh instantiation and isolation
    inst_reg1 = instantiate_fresh_model(catalog["baseline_regression"], seed=1)
    inst_reg2 = instantiate_fresh_model(catalog["baseline_regression"], seed=2)
    assert inst_reg1 is not inst_reg2

    # 4. Train regression baseline
    X_train_reg = np.array([[10.0, 1.0], [20.0, 2.0], [30.0, 3.0], [40.0, 4.0]])
    y_train_reg = np.array([100.0, 200.0, 300.0, 400.0])
    fitted_reg, diag_reg = fit_model(inst_reg1, reg_spec, X_train_reg, y_train_reg)

    assert isinstance(diag_reg, ModelDiagnostics)
    assert diag_reg.phase == "fit"
    assert diag_reg.diagnostics["mean_"] == 250.0

    # 5. Predict regression baseline
    X_eval_reg = np.array([[15.0, 1.5], [25.0, 2.5]])
    pred_reg = predict_model(fitted_reg, reg_spec, X_eval_reg)
    assert np.allclose(pred_reg["y_pred"], [250.0, 250.0])
    assert pred_reg["y_std"] is not None
    assert np.all(pred_reg["y_std"] > 0.0)
    assert pred_reg["y_proba"] is None

    # 6. Train classification baseline
    inst_clf = instantiate_fresh_model(catalog["baseline_classification"], seed=42)
    y_train_clf = np.array(["pos", "neg", "pos", "pos"])
    fitted_clf, diag_clf = fit_model(inst_clf, clf_spec, X_train_reg, y_train_clf)

    pred_clf = predict_model(fitted_clf, clf_spec, X_eval_reg)
    assert np.array_equal(pred_clf["y_pred"], ["pos", "pos"])
    assert pred_clf["y_std"] is None
    assert pred_clf["y_proba"] is not None
    assert pred_clf["y_proba"].shape == (2, 2)
    assert np.allclose(np.sum(pred_clf["y_proba"], axis=1), 1.0)

    # 7. Analytical model evaluation with bypass
    inst_bio = instantiate_fresh_model(catalog["analytical_clutter"], seed=None)
    fitted_bio, diag_bio = fit_model(inst_bio, bio_spec, X_train_reg, y_train_reg)
    assert diag_bio.diagnostics["requires_fit"] is False

    pred_bio = predict_model(fitted_bio, bio_spec, X_eval_reg)
    # Expected: 5.0 + 1.5 * col0 + 2.5 * col1
    # Sample 1: 5.0 + 1.5*15.0 + 2.5*1.5 = 5.0 + 22.5 + 3.75 = 31.25
    # Sample 2: 5.0 + 1.5*25.0 + 2.5*2.5 = 5.0 + 37.5 + 6.25 = 48.75
    assert np.allclose(pred_bio["y_pred"], [31.25, 48.75])
    assert pred_bio["y_std"] is None
    assert pred_bio["y_proba"] is None
