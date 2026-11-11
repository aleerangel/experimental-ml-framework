"""Unit tests for two-layer preprocessing validation and duplication detection.

Covers PRE-02 (AC-M42-02-01 to AC-M42-02-04) and checks C5, C6, C7, C8.
"""

from __future__ import annotations

import pytest

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.models.preprocessing.pipeline import (
    validate_two_layer_preprocessing,
)
from experimental_ml.models.preprocessing.types import (
    PreprocessingStepSpec,
    TwoLayerPreprocessingSpec,
)


def test_m42_02_01_validate_two_layer_valid() -> None:
    """AC-M42-02-01 / C5: validate_two_layer_preprocessing validates valid spec without mutating fields."""
    s1 = PreprocessingStepSpec(step_id="imputer", transformer_type="IMPUTER")
    s2 = PreprocessingStepSpec(step_id="scaler", transformer_type="STANDARD")

    spec = TwoLayerPreprocessingSpec(
        layer1_steps=(s1,),
        layer2_steps=(s2,),
        description="Valid pipeline",
    )
    validated = validate_two_layer_preprocessing(spec)
    assert validated is spec
    assert validated.layer1_steps == (s1,)
    assert validated.layer2_steps == (s2,)


def test_m42_02_02_validate_two_layer_duplication_rejection() -> None:
    """AC-M42-02-02 / C6: validate_two_layer_preprocessing raises ConfigurationError on duplicate scalers (CA-E3-02)."""
    # 1. Exact same scaler type in both layers
    s1 = PreprocessingStepSpec(step_id="scale_l1", transformer_type="STANDARD")
    s2 = PreprocessingStepSpec(step_id="scale_l2", transformer_type="STANDARD")
    spec_dup = TwoLayerPreprocessingSpec(layer1_steps=(s1,), layer2_steps=(s2,))

    with pytest.raises(ConfigurationError, match="Accidental duplication detected"):
        validate_two_layer_preprocessing(spec_dup)

    # 2. Conflicting scaler types across layers (e.g. MINMAX in L1 and STANDARD in L2)
    s1_minmax = PreprocessingStepSpec(step_id="minmax_l1", transformer_type="MINMAX")
    s2_std = PreprocessingStepSpec(step_id="std_l2", transformer_type="STANDARD")
    spec_conflict = TwoLayerPreprocessingSpec(layer1_steps=(s1_minmax,), layer2_steps=(s2_std,))

    with pytest.raises(ConfigurationError, match="redundant scalers declared"):
        validate_two_layer_preprocessing(spec_conflict)


def test_m42_02_03_validate_two_layer_invalid_step() -> None:
    """AC-M42-02-03 / C7: validate_two_layer_preprocessing raises ConfigurationError on invalid step IDs or types."""
    # Invalid step ID characters (e.g. spaces or symbols)
    s_bad_id = PreprocessingStepSpec(step_id="invalid step id!", transformer_type="STANDARD")
    spec_bad_id = TwoLayerPreprocessingSpec(layer1_steps=(s_bad_id,))

    with pytest.raises(ConfigurationError, match="is invalid; must match"):
        validate_two_layer_preprocessing(spec_bad_id)

    # Unrecognized transformer type
    s_unknown_type = PreprocessingStepSpec(step_id="step1", transformer_type="UNKNOWN_TRANSFORMER")
    spec_unknown = TwoLayerPreprocessingSpec(layer1_steps=(s_unknown_type,))

    with pytest.raises(ConfigurationError, match="unrecognized transformer_type"):
        validate_two_layer_preprocessing(spec_unknown)


def test_m42_02_04_validate_two_layer_empty_passthrough() -> None:
    """AC-M42-02-04 / C8: validate_two_layer_preprocessing accepts empty spec as valid pass-through."""
    spec_empty = TwoLayerPreprocessingSpec()
    validated = validate_two_layer_preprocessing(spec_empty)
    assert validated is spec_empty
    assert len(validated.layer1_steps) == 0
    assert len(validated.layer2_steps) == 0
