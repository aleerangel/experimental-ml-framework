"""Unit tests for feature models, scopes, and serialization contracts (EXP-01, EXP-07)."""

from dataclasses import FrozenInstanceError
import json
import math
from types import MappingProxyType

import pytest

from experimental_ml.core.enums import MetricStatus, TaskType
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.features.types import (
    METHODOLOGICAL_WARNINGS,
    SCOPE_EXPLORATORY_FULL_DATA,
    AssociationMeasure,
    ExploratoryFeatureReport,
    RedundancyPair,
)


def test_scope_and_warnings_constants() -> None:
    """Verify that scope constant and methodological warnings adhere to EXP-01 and CA-E2-01."""
    assert SCOPE_EXPLORATORY_FULL_DATA == "EXPLORATORY_FULL_DATA"
    assert len(METHODOLOGICAL_WARNINGS) == 3
    assert any("causalidade" in w.lower() for w in METHODOLOGICAL_WARNINGS)
    assert any("multivariada" in w.lower() for w in METHODOLOGICAL_WARNINGS)
    assert any("exploratória" in w.lower() or "leakage" in w.lower() for w in METHODOLOGICAL_WARNINGS)


def test_association_measure_immutability_and_validation() -> None:
    """Verify immutability and contract validation for AssociationMeasure."""
    measure = AssociationMeasure(
        feature_name="feat_a",
        target_name="target",
        metric_name="pearson",
        value=0.75,
        status=MetricStatus.VALID,
        details={"df": 100},
    )

    assert measure.feature_name == "feat_a"
    assert measure.metric_name == "PEARSON"
    assert measure.value == 0.75
    assert measure.status == MetricStatus.VALID
    assert isinstance(measure.details, MappingProxyType)
    assert measure.details["df"] == 100

    with pytest.raises(FrozenInstanceError):
        measure.value = 0.80  # type: ignore

    with pytest.raises(ConfigurationError, match="feature_name"):
        AssociationMeasure(
            feature_name="",
            target_name="target",
            metric_name="PEARSON",
            value=0.5,
            status=MetricStatus.VALID,
        )


def test_redundancy_pair_immutability_and_validation() -> None:
    """Verify immutability and validation for RedundancyPair."""
    pair = RedundancyPair(
        feature_a="feat_x",
        feature_b="feat_y",
        metric_name="spearman",
        value=0.92,
        status=MetricStatus.VALID,
    )

    assert pair.feature_a == "feat_x"
    assert pair.feature_b == "feat_y"
    assert pair.metric_name == "SPEARMAN"
    assert pair.value == 0.92

    with pytest.raises(FrozenInstanceError):
        pair.value = 0.5  # type: ignore

    with pytest.raises(ConfigurationError, match="feature_b"):
        RedundancyPair(
            feature_a="feat_x",
            feature_b="",
            metric_name="SPEARMAN",
            value=0.5,
            status=MetricStatus.VALID,
        )


def test_report_scope_enforcement() -> None:
    """Verify that ExploratoryFeatureReport rejects scopes other than EXPLORATORY_FULL_DATA."""
    with pytest.raises(ConfigurationError, match="Invalid scope"):
        ExploratoryFeatureReport(
            scope="FEATURE_SELECTION_SUBSET",
            dataset_hash="hash123",
            task_type=TaskType.REGRESSION,
            target_associations=(),
            pairwise_redundancy_matrix={},
            high_redundancy_pairs=(),
        )


def test_exp_07_roundtrip_serialization() -> None:
    """Proof C7: Verify lossless roundtrip serialization and reconstruction (EXP-07)."""
    assoc1 = AssociationMeasure(
        feature_name="f1",
        target_name="y",
        metric_name="PEARSON",
        value=0.8542,
        status=MetricStatus.VALID,
        details={"n": 200},
    )
    assoc2 = AssociationMeasure(
        feature_name="f2",
        target_name="y",
        metric_name="SPEARMAN",
        value=float("nan"),
        status=MetricStatus.UNDEFINED_NAN,
    )
    pair1 = RedundancyPair(
        feature_a="f1",
        feature_b="f2",
        metric_name="PEARSON",
        value=0.912,
        status=MetricStatus.VALID,
    )
    matrix = {
        "f1": {"f1": 1.0, "f2": 0.912},
        "f2": {"f1": 0.912, "f2": 1.0},
    }

    report = ExploratoryFeatureReport(
        scope=SCOPE_EXPLORATORY_FULL_DATA,
        dataset_hash="abc456def789",
        task_type=TaskType.REGRESSION,
        target_associations=(assoc1, assoc2),
        pairwise_redundancy_matrix=matrix,
        high_redundancy_pairs=(pair1,),
        metadata={"created_by": "test_suite"},
    )

    # 1. Serialization to dict
    serialized = report.to_dict()

    # 2. Assert strict JSON RFC 8259 compliance (no raw NaN causing dump errors)
    json_str = json.dumps(serialized, indent=2, ensure_ascii=False, allow_nan=False)
    assert "EXPLORATORY_FULL_DATA" in json_str
    assert "abc456def789" in json_str

    # 3. Deserialization from dict
    deserialized_data = json.loads(json_str)
    reconstructed = ExploratoryFeatureReport.from_dict(deserialized_data)

    # 4. Check semantic equivalence
    assert reconstructed.scope == report.scope
    assert reconstructed.dataset_hash == report.dataset_hash
    assert reconstructed.task_type == report.task_type
    assert len(reconstructed.target_associations) == 2

    r_assoc1 = reconstructed.target_associations[0]
    assert r_assoc1.feature_name == "f1"
    assert pytest.approx(r_assoc1.value, abs=1e-6) == 0.8542
    assert r_assoc1.status == MetricStatus.VALID

    r_assoc2 = reconstructed.target_associations[1]
    assert r_assoc2.feature_name == "f2"
    assert math.isnan(r_assoc2.value)
    assert r_assoc2.status == MetricStatus.UNDEFINED_NAN

    assert len(reconstructed.high_redundancy_pairs) == 1
    assert reconstructed.high_redundancy_pairs[0].feature_a == "f1"
    assert reconstructed.high_redundancy_pairs[0].feature_b == "f2"
    assert pytest.approx(reconstructed.high_redundancy_pairs[0].value, abs=1e-6) == 0.912

    assert reconstructed.pairwise_redundancy_matrix["f1"]["f2"] == pytest.approx(0.912, abs=1e-6)
    assert reconstructed.warnings == METHODOLOGICAL_WARNINGS
