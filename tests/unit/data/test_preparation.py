"""Unit tests for preparation models, plan creation, and dataset sanitization."""

from dataclasses import FrozenInstanceError
from types import MappingProxyType

import numpy as np
import pytest

from experimental_ml.core.enums import TaskType
from experimental_ml.core.findings import (
    ConfigurationError,
    ContractViolationError,
    DataIntegrityError,
    make_finding,
    make_warning,
)
from experimental_ml.core.types import ObservationId
from experimental_ml.data import load_dataset, profile_dataset
from experimental_ml.data.preparation import (
    PreparationPlan,
    PreparationRule,
    SanitizedDatasetView,
    UnresolvedFinding,
    _validate_rule_admissibility,
    create_preparation_plan,
    sanitize_dataset,
)
from experimental_ml.data.profiling import (
    CategoryFrequency,
    DatasetProfile,
    DuplicateRowsProfile,
    TargetProfile,
)
from experimental_ml.data.schema import DatasetSchemaSpec


def test_t1_preparation_rule_immutability_and_slots() -> None:
    rule = PreparationRule(
        finding_code="E1_TARGET_MISSING",
        column="target",
        kind="DROP_ROWS",
        parameters={"threshold": 0.5},
    )
    assert rule.finding_code == "E1_TARGET_MISSING"
    assert rule.column == "target"
    assert rule.kind == "DROP_ROWS"
    assert isinstance(rule.parameters, MappingProxyType)
    assert rule.parameters["threshold"] == 0.5

    with pytest.raises(FrozenInstanceError):
        rule.column = "other"  # type: ignore[misc]

    # Slot check: should not have __dict__
    assert not hasattr(rule, "__dict__")


def test_t1_unresolved_finding_immutability_and_slots() -> None:
    unresolved = UnresolvedFinding(
        finding_code="E1_TARGET_ALL_MISSING",
        column="target",
        reason="Target column is completely missing; irresolvable.",
    )
    assert unresolved.finding_code == "E1_TARGET_ALL_MISSING"
    assert unresolved.column == "target"
    assert "Target column" in unresolved.reason

    with pytest.raises(FrozenInstanceError):
        unresolved.reason = "modified"  # type: ignore[misc]

    assert not hasattr(unresolved, "__dict__")


def test_t1_preparation_plan_immutability_and_slots() -> None:
    rule = PreparationRule(
        finding_code="E1_TARGET_MISSING",
        column="target",
        kind="DROP_ROWS",
    )
    plan = PreparationPlan(
        status="READY",
        source_dataset_hash="hash123",
        source_profile_digest="digest456",
        rules=(rule,),
        plan_digest="plan789",
    )
    assert plan.status == "READY"
    assert plan.source_dataset_hash == "hash123"
    assert plan.rules == (rule,)
    assert isinstance(plan.rules, tuple)
    assert isinstance(plan.unresolved_findings, tuple)

    with pytest.raises(FrozenInstanceError):
        plan.status = "INCOMPLETE"  # type: ignore[misc]

    assert not hasattr(plan, "__dict__")


def test_t1_sanitized_dataset_view_immutability_and_slots() -> None:
    schema = DatasetSchemaSpec(
        target_col="target",
        task_type=TaskType.BINARY_CLASSIFICATION,
    )
    col_data = np.array([1.0, 2.0], dtype=np.float64)

    view = SanitizedDatasetView(
        columns={"feat": col_data, "target": np.array([1, 0])},
        schema=schema,
        observation_ids=(ObservationId("obs_1"), ObservationId("obs_2")),
        candidate_feature_cols=("feat",),
        dropped_observation_ids=(),
        target_label_mapping={"pos": 1, "neg": 0},
        deferred_rules=(),
        source_dataset_hash="source_hash",
        source_plan_digest="plan_hash",
        dataset_hash="sanitized_hash",
    )

    assert isinstance(view.columns, MappingProxyType)
    assert isinstance(view.observation_ids, tuple)
    assert isinstance(view.target_label_mapping, MappingProxyType)
    assert view.dataset_hash == "sanitized_hash"

    with pytest.raises(FrozenInstanceError):
        view.dataset_hash = "other"  # type: ignore[misc]

    assert not hasattr(view, "__dict__")


def _make_dummy_profile(findings: tuple = (), target_classes: tuple[str, ...] = ("class_a", "class_b")) -> DatasetProfile:
    target_prof = TargetProfile(
        column_name="target",
        task_type=TaskType.BINARY_CLASSIFICATION,
        numeric_stats=None,
        skewness=None,
        outliers_count_iqr_fences=None,
        class_frequencies=tuple(CategoryFrequency(cat, 10, 0.5) for cat in target_classes),
        majority_minority_ratio=1.0,
    )
    dup_prof = DuplicateRowsProfile(
        n_duplicate_rows=0,
        duplicate_observation_ids=(),
        is_truncated=False,
    )
    return DatasetProfile(
        source_dataset_hash="hash_dummy",
        n_rows=20,
        n_cols=3,
        memory_bytes=480,
        columns=MappingProxyType({}),
        duplicate_rows=dup_prof,
        target=target_prof,
        groups=None,
        findings=findings,
    )


def test_t2_admissibility_valid_rules() -> None:
    findings = (
        make_finding("E1_TARGET_MISSING", "target missing", {"column": "target"}),
        make_finding("E1_FEATURE_MISSING", "feat missing", {"column": "num_col"}),
        make_finding("E1_CONSTANT_COLUMN", "constant column", {"column": "const_col"}),
        make_finding("E1_CATEGORICAL_UNENCODED", "unencoded cat", {"column": "cat_col"}),
        make_finding("E1_TARGET_BINARY_UNMAPPED", "binary unmapped", {"column": "target"}),
    )
    profile = _make_dummy_profile(findings=findings)

    # Valid DROP_ROWS
    r1 = PreparationRule("E1_TARGET_MISSING", "target", "DROP_ROWS")
    _validate_rule_admissibility(r1, profile)

    # Valid EXCLUDE_COLUMN
    r2 = PreparationRule("E1_CONSTANT_COLUMN", "const_col", "EXCLUDE_COLUMN")
    _validate_rule_admissibility(r2, profile)

    # Valid DEFER_INTRA_FOLD for numeric feature missing
    r3 = PreparationRule("E1_FEATURE_MISSING", "num_col", "DEFER_INTRA_FOLD", {"imputation_strategy": "MEDIAN"})
    _validate_rule_admissibility(r3, profile)

    # Valid DEFER_INTRA_FOLD for categorical unencoded
    r4 = PreparationRule("E1_CATEGORICAL_UNENCODED", "cat_col", "DEFER_INTRA_FOLD", {"encoding_strategy": "ONE_HOT"})
    _validate_rule_admissibility(r4, profile)

    # Valid ACCEPT_AS_IS
    r5 = PreparationRule("E1_FEATURE_MISSING", "num_col", "ACCEPT_AS_IS")
    _validate_rule_admissibility(r5, profile)

    # Valid MAP_BINARY_TARGET
    r6 = PreparationRule("E1_TARGET_BINARY_UNMAPPED", "target", "MAP_BINARY_TARGET", {"positive_label": "class_a"})
    _validate_rule_admissibility(r6, profile)


def test_prep_03_invalid_rule_admissibility_and_configuration_error() -> None:
    findings = (
        make_finding("E1_FEATURE_MISSING", "feat missing", {"column": "feat"}),
        make_finding("E1_TARGET_CLASS_COUNT_INVALID", "invalid count", {"column": "target"}),
        make_warning("W1_DUPLICATE_ROWS", "duplicate rows", {"column": None}),
    )
    profile = _make_dummy_profile(findings=findings)

    # 1. Unknown / non-existent finding in profile
    with pytest.raises(ConfigurationError, match="non-existent finding"):
        _validate_rule_admissibility(
            PreparationRule("E1_TARGET_MISSING", "target", "DROP_ROWS"),
            profile,
        )

    # 2. Rule targeting HEURISTIC_WARNING
    with pytest.raises(ConfigurationError, match="only CONFIRMED_ISSUE can be targeted"):
        _validate_rule_admissibility(
            PreparationRule("W1_DUPLICATE_ROWS", None, "DROP_ROWS"),
            profile,
        )

    # 3. Rule targeting irresolvable finding
    with pytest.raises(ConfigurationError, match="irresolvable"):
        _validate_rule_admissibility(
            PreparationRule("E1_TARGET_CLASS_COUNT_INVALID", "target", "DROP_ROWS"),
            profile,
        )

    # 4. EXCLUDE_COLUMN targeting target column
    finding_target = make_finding("E1_FEATURE_MISSING", "target missing", {"column": "target"})
    prof_target = _make_dummy_profile(findings=(finding_target,))
    with pytest.raises(ConfigurationError, match="Cannot apply EXCLUDE_COLUMN to target column"):
        _validate_rule_admissibility(
            PreparationRule("E1_FEATURE_MISSING", "target", "EXCLUDE_COLUMN"),
            prof_target,
        )

    # 5. Inadmissible rule kind for finding (e.g. DROP_ROWS for E1_CONSTANT_COLUMN)
    finding_const = make_finding("E1_CONSTANT_COLUMN", "const", {"column": "feat"})
    prof_const = _make_dummy_profile(findings=(finding_const,))
    with pytest.raises(ConfigurationError, match="not admissible"):
        _validate_rule_admissibility(
            PreparationRule("E1_CONSTANT_COLUMN", "feat", "DROP_ROWS"),
            prof_const,
        )

    # 6. MAP_BINARY_TARGET missing positive_label or unobserved label
    finding_bin = make_finding("E1_TARGET_BINARY_UNMAPPED", "bin unmapped", {"column": "target"})
    prof_bin = _make_dummy_profile(findings=(finding_bin,), target_classes=("yes", "no"))
    with pytest.raises(ConfigurationError, match="requires 'positive_label' parameter"):
        _validate_rule_admissibility(
            PreparationRule("E1_TARGET_BINARY_UNMAPPED", "target", "MAP_BINARY_TARGET", {}),
            prof_bin,
        )
    with pytest.raises(ConfigurationError, match="not found in target observed classes"):
        _validate_rule_admissibility(
            PreparationRule("E1_TARGET_BINARY_UNMAPPED", "target", "MAP_BINARY_TARGET", {"positive_label": "invalid_label"}),
            prof_bin,
        )

    # 7. DEFER_INTRA_FOLD with invalid strategy
    with pytest.raises(ConfigurationError, match="imputation_strategy"):
        _validate_rule_admissibility(
            PreparationRule("E1_FEATURE_MISSING", "feat", "DEFER_INTRA_FOLD", {"imputation_strategy": "INVALID"}),
            profile,
        )


def test_prep_01_ready_plan_canonical_order() -> None:
    findings = (
        make_finding("E1_FEATURE_MISSING", "col_b missing", {"column": "col_b"}),
        make_finding("E1_CONSTANT_COLUMN", "col_a const", {"column": "col_a"}),
        make_finding("E1_TARGET_BINARY_UNMAPPED", "target unmapped", {"column": "target"}),
    )
    profile = _make_dummy_profile(findings=findings, target_classes=("pos", "neg"))

    # Supply rules out of canonical order
    rules = [
        PreparationRule("E1_TARGET_BINARY_UNMAPPED", "target", "MAP_BINARY_TARGET", {"positive_label": "pos"}),
        PreparationRule("E1_FEATURE_MISSING", "col_b", "DROP_ROWS"),
        PreparationRule("E1_CONSTANT_COLUMN", "col_a", "EXCLUDE_COLUMN"),
    ]

    plan = create_preparation_plan(profile, rules)

    assert plan.status == "READY"
    assert plan.source_dataset_hash == profile.source_dataset_hash
    assert len(plan.plan_digest) == 64
    assert len(plan.source_profile_digest) == 64
    assert plan.unresolved_findings == ()

    # Check canonical ordering: E1_CONSTANT_COLUMN, E1_FEATURE_MISSING, E1_TARGET_BINARY_UNMAPPED
    rule_codes = [r.finding_code for r in plan.rules]
    assert rule_codes == [
        "E1_CONSTANT_COLUMN",
        "E1_FEATURE_MISSING",
        "E1_TARGET_BINARY_UNMAPPED",
    ]


def test_prep_02_incomplete_plan_unresolved_findings() -> None:
    findings = (
        make_finding("E1_FEATURE_MISSING", "feat missing", {"column": "col_x"}),
        make_finding("E1_TARGET_ZERO_VARIANCE", "target zero variance", {"column": "target"}),
        make_finding("E1_CONSTANT_COLUMN", "col const", {"column": "col_c"}),
    )
    profile = _make_dummy_profile(findings=findings)

    # Only provide rule for col_c, leaving col_x uncovered and target irresolvable
    rules = [
        PreparationRule("E1_CONSTANT_COLUMN", "col_c", "EXCLUDE_COLUMN"),
    ]

    plan = create_preparation_plan(profile, rules)

    assert plan.status == "INCOMPLETE"
    assert plan.plan_digest == ""
    assert len(plan.unresolved_findings) == 2

    # Verify unresolved list contains col_x and target
    unresolved_codes = [u.finding_code for u in plan.unresolved_findings]
    assert "E1_FEATURE_MISSING" in unresolved_codes
    assert "E1_TARGET_ZERO_VARIANCE" in unresolved_codes


def test_t3_duplicate_rule_and_dict_coercion() -> None:
    findings = (
        make_finding("E1_FEATURE_MISSING", "feat missing", {"column": "feat"}),
    )
    profile = _make_dummy_profile(findings=findings)

    # Coercion from dict
    dict_rule = {
        "finding_code": "E1_FEATURE_MISSING",
        "column": "feat",
        "kind": "DROP_ROWS",
    }
    plan = create_preparation_plan(profile, [dict_rule])
    assert plan.status == "READY"
    assert plan.rules[0].kind == "DROP_ROWS"

    # Duplicate rule rejection
    dup_rules = [
        PreparationRule("E1_FEATURE_MISSING", "feat", "DROP_ROWS"),
        PreparationRule("E1_FEATURE_MISSING", "feat", "ACCEPT_AS_IS"),
    ]
    with pytest.raises(ConfigurationError, match="Duplicate preparation rule"):
        create_preparation_plan(profile, dup_rules)


def test_prep_05_binding_validation_and_status_check() -> None:
    data = {
        "x1": [1.0, 2.0, 3.0],
        "target": [0, 1, 0],
    }
    schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.BINARY_CLASSIFICATION)
    bundle = load_dataset(data, schema=schema)
    profile = profile_dataset(bundle)

    # 1. Non-READY plan raises ContractViolationError
    incomplete_plan = PreparationPlan(
        status="INCOMPLETE",
        source_dataset_hash=bundle.dataset_hash,
        source_profile_digest="digest",
        rules=(),
    )
    with pytest.raises(ContractViolationError, match="status must be 'READY'"):
        sanitize_dataset(bundle, profile, incomplete_plan)

    # 2. Mismatched source_dataset_hash raises DataIntegrityError
    mismatched_plan = PreparationPlan(
        status="READY",
        source_dataset_hash="different_hash",
        source_profile_digest=incomplete_plan.source_profile_digest,
        rules=(),
    )
    with pytest.raises(DataIntegrityError, match="source_dataset_hash"):
        sanitize_dataset(bundle, profile, mismatched_plan)

    # 3. Mismatched source_profile_digest raises DataIntegrityError
    mismatched_digest_plan = PreparationPlan(
        status="READY",
        source_dataset_hash=bundle.dataset_hash,
        source_profile_digest="wrong_digest",
        rules=(),
    )
    with pytest.raises(DataIntegrityError, match="source_profile_digest"):
        sanitize_dataset(bundle, profile, mismatched_digest_plan)


def test_prep_08_binary_target_mapping_and_encoding() -> None:
    data = {
        "feat": [1.0, 2.0, 3.0, 4.0],
        "target": ["yes", "no", "yes", "no"],
    }
    schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.BINARY_CLASSIFICATION)
    bundle = load_dataset(data, schema=schema)
    profile = profile_dataset(bundle)

    # Profile should emit E1_TARGET_BINARY_UNMAPPED
    rule = PreparationRule(
        finding_code="E1_TARGET_BINARY_UNMAPPED",
        column="target",
        kind="MAP_BINARY_TARGET",
        parameters={"positive_label": "yes"},
    )
    plan = create_preparation_plan(profile, [rule])
    assert plan.status == "READY"

    view = sanitize_dataset(bundle, profile, plan)

    # Check target mapping
    assert view.target_label_mapping is not None
    assert view.target_label_mapping["yes"] == 1
    assert view.target_label_mapping["no"] == 0
    # Encoded target is np.int64
    assert view.columns["target"].dtype == np.int64
    np.testing.assert_array_equal(view.columns["target"], np.array([1, 0, 1, 0], dtype=np.int64))


def test_prep_09_empty_dataset_or_features_raises_integrity_error() -> None:
    # 1. DROP_ROWS leaving 0 rows
    data = {
        "f1": [1.0, 2.0, np.nan, np.nan],
        "f2": [np.nan, np.nan, 3.0, 4.0],
        "target": [1, 0, 1, 0],
    }
    schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.BINARY_CLASSIFICATION)
    bundle = load_dataset(data, schema=schema)
    profile = profile_dataset(bundle)

    rules = [
        PreparationRule("E1_FEATURE_MISSING", "f1", "DROP_ROWS"),
        PreparationRule("E1_FEATURE_MISSING", "f2", "DROP_ROWS"),
    ]
    plan = create_preparation_plan(profile, rules)
    assert plan.status == "READY"

    with pytest.raises(DataIntegrityError, match="0 observations after applying DROP_ROWS"):
        sanitize_dataset(bundle, profile, plan)

    # 2. EXCLUDE_COLUMN leaving 0 candidate features
    data2 = {
        "feat_only": [1.0, 1.0, 1.0],  # constant feature
        "target": [1, 0, 1],
    }
    bundle2 = load_dataset(data2, schema=schema)
    profile2 = profile_dataset(bundle2)

    rule2 = PreparationRule("E1_CONSTANT_COLUMN", "feat_only", "EXCLUDE_COLUMN")
    plan2 = create_preparation_plan(profile2, [rule2])
    assert plan2.status == "READY"

    with pytest.raises(DataIntegrityError, match="0 candidate feature columns"):
        sanitize_dataset(bundle2, profile2, plan2)


def test_t4_drop_rows_and_order_preservation() -> None:
    data = {
        "x": [10.0, np.nan, 30.0, np.nan, 50.0],
        "y": [1.0, 2.0, 3.0, 4.0, 5.0],
        "target": [1, 0, 1, 0, 1],
    }
    schema = DatasetSchemaSpec(target_col="target", task_type=TaskType.BINARY_CLASSIFICATION)
    bundle = load_dataset(data, schema=schema)
    profile = profile_dataset(bundle)

    rule = PreparationRule("E1_FEATURE_MISSING", "x", "DROP_ROWS")
    plan = create_preparation_plan(profile, [rule])
    assert plan.status == "READY"

    view = sanitize_dataset(bundle, profile, plan)

    # Rows 1 and 3 (0-indexed) were dropped
    assert len(view.observation_ids) == 3
    assert len(view.dropped_observation_ids) == 2
    assert view.dropped_observation_ids == (bundle.observation_ids[1], bundle.observation_ids[3])
    # Relative order of remaining IDs is strictly preserved
    assert view.observation_ids == (
        bundle.observation_ids[0],
        bundle.observation_ids[2],
        bundle.observation_ids[4],
    )
    np.testing.assert_array_equal(view.columns["x"], np.array([10.0, 30.0, 50.0]))
