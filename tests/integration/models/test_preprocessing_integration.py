"""Integration tests for two-layer preprocessing subsystem and runtime purity.

Covers PRE-07 (AC-M42-07-01, AC-M42-07-02) and checks C23, C24, testing end-to-end
pipeline integration from declarative specs to intra-fold fitting and projection.
"""

from __future__ import annotations

import subprocess
import sys
import numpy as np
import pytest

from experimental_ml.models import (
    ScalerType,
    TwoLayerPreprocessingSpec,
    TwoLayerPreprocessingState,
    apply_two_layer_preprocessing,
    fit_two_layer_preprocessing,
    validate_two_layer_preprocessing,
)
from experimental_ml.models.preprocessing import (
    AngularScaler,
    MaxAbsScaler,
    MinMaxScaler,
    PrecomputedKernelAdapter,
    PreprocessingStepSpec,
    RobustScaler,
    StandardScaler,
)


def test_m42_07_01_public_api_exports() -> None:
    """AC-M42-07-01 / C23: Preprocessing subsystem cleanly exports public API."""
    import experimental_ml.models.preprocessing as prep
    from experimental_ml.models import (
        ScalerType,
        TwoLayerPreprocessingSpec,
        TwoLayerPreprocessingState,
        apply_two_layer_preprocessing,
        fit_two_layer_preprocessing,
        validate_two_layer_preprocessing,
    )

    expected_prep_exports = [
        "ScalerType",
        "PreprocessingStepSpec",
        "TwoLayerPreprocessingSpec",
        "TwoLayerPreprocessingState",
        "StandardScaler",
        "MinMaxScaler",
        "MaxAbsScaler",
        "RobustScaler",
        "AngularScaler",
        "PrecomputedKernelAdapter",
        "validate_two_layer_preprocessing",
        "fit_two_layer_preprocessing",
        "apply_two_layer_preprocessing",
    ]
    for symbol in expected_prep_exports:
        assert hasattr(prep, symbol), f"Symbol {symbol} missing in preprocessing package"


def test_m42_07_02_runtime_purity_numpy_only() -> None:
    """AC-M42-07-02 / C24: Preprocessing maintains single runtime dependency (numpy>=1.24.0)."""
    check_code = (
        "import sys\n"
        "import experimental_ml.models.preprocessing\n"
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


def test_preprocessing_end_to_end_two_layer_pipeline() -> None:
    """Verify complete end-to-end flow: validate, fit on train, project on eval without leakage."""
    # Define Layer 1: Passthrough (scenario step)
    # Define Layer 2: StandardScaler (model-specific step)
    step1 = PreprocessingStepSpec(step_id="l1_pass", transformer_type="PASSTHROUGH")
    step2 = PreprocessingStepSpec(step_id="l2_scale", transformer_type="STANDARD")

    spec = TwoLayerPreprocessingSpec(
        layer1_steps=(step1,),
        layer2_steps=(step2,),
        description="End-to-end test specification",
    )
    validated_spec = validate_two_layer_preprocessing(spec)

    # 1. Fit strictly on X_train (4 samples, 2 features)
    X_train = np.array([
        [10.0, 100.0],
        [20.0, 200.0],
        [30.0, 300.0],
        [40.0, 400.0],
    ])
    state = fit_two_layer_preprocessing(validated_spec, X_train)

    assert isinstance(state, TwoLayerPreprocessingState)

    # 2. Project training data: mean=25, std=sqrt(125)=11.1803
    X_train_proj = apply_two_layer_preprocessing(state, X_train)
    assert np.allclose(np.mean(X_train_proj, axis=0), [0.0, 0.0])
    assert np.allclose(np.var(X_train_proj, axis=0), [1.0, 1.0])

    # 3. Project evaluation data without re-fitting
    X_eval = np.array([
        [25.0, 250.0],  # Exactly training mean -> should project to [0.0, 0.0]
    ])
    X_eval_proj = apply_two_layer_preprocessing(state, X_eval)
    assert np.allclose(X_eval_proj[0], [0.0, 0.0])
