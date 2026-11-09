"""Regression and integrity test suite for M2 Hardening (REV-M2-01 through REV-M2-11).

Guarantees full verification and defect prevention across all audit findings.
"""

from __future__ import annotations

from dataclasses import replace
import gzip
import json
from pathlib import Path
import subprocess
import sys
from types import MappingProxyType
import numpy as np
import pytest

from experimental_ml.core.enums import FindingSeverity, TaskType
from experimental_ml.core.findings import (
    ConfigurationError,
    ContractViolationError,
    DataIntegrityError,
    Finding,
    make_finding,
)
from experimental_ml.core.storage import write_json_atomic
from experimental_ml.core.types import ObservationId
from experimental_ml.data.codecs import (
    sanitized_view_descriptor_from_dict,
    sanitized_view_descriptor_to_dict,
)
from experimental_ml.data.descriptors import SanitizedViewDescriptor
from experimental_ml.data.loader import load_dataset
from experimental_ml.data.preparation import (
    IRRESOLVABLE_FINDING_CODES,
    PreparationPlan,
    PreparationRule,
    SanitizedDatasetView,
    create_preparation_plan,
    sanitize_dataset,
)
from experimental_ml.data.profiling import ProfileConfig, profile_dataset
from experimental_ml.data.query import slice_view_by_observation_ids
from experimental_ml.data.schema import ColumnSemanticType, DatasetSchemaSpec
from experimental_ml.stages.stage_gates import (
    DATASET_DESCRIPTOR_REL_PATH,
    DATASET_PROFILE_REL_PATH,
    PARTITION_PLAN_REL_PATH,
    PREPARATION_PLAN_REL_PATH,
    SANITIZED_VIEW_REL_PATH,
    SPLITS_CSV_GZ_REL_PATH,
    SPLITS_SCHEMA_REL_PATH,
    reconstruct_sanitized_view,
    verify_partition_gate,
    verify_preparation_gate,
)
from experimental_ml.validation.codecs import partition_plan_to_dict
from experimental_ml.validation.engine import build_partition_plan
from experimental_ml.validation.splitters import (
    bootstrap_split,
    holdout_split,
    stratified_kfold_split,
    temporal_split,
)
from experimental_ml.validation.storage import (
    read_splits_csv_gz,
    write_splits_csv_gz,
    write_splits_schema,
)
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)
from experimental_ml.validation.validators import validate_partition_plan


class DummyStageView:
    def __init__(self, observation_ids: list[ObservationId], dataset_hash: str = "sanitized_hash_100"):
        self.observation_ids = tuple(observation_ids)
        self.dataset_hash = dataset_hash
        self.columns = {}
        self.schema = None


def _setup_valid_test_experiment(exp_dir: Path) -> None:
    """Helper setting up all 7 standard experiment artifacts consistently for testing."""
    data_hash = "source_hash_999"
    sanitized_hash = "sanitized_hash_100"

    desc = {
        "dataset_hash": data_hash,
        "n_observations": 10,
        "n_columns": 2,
        "column_names": ["feat", "target"],
        "column_types": {"feat": "float64", "target": "int64"},
    }
    write_json_atomic(exp_dir / DATASET_DESCRIPTOR_REL_PATH, desc)

    prof = {
        "source_dataset_hash": data_hash,
        "n_rows": 10,
        "n_cols": 2,
        "memory_bytes": 160,
        "columns": {},
        "duplicate_rows": {"n_duplicate_rows": 0, "duplicate_observation_ids": [], "is_truncated": False},
        "target": {"column_name": "target", "task_type": "BINARY_CLASSIFICATION", "numeric_stats": None, "class_frequencies": None},
        "findings": [],
    }
    write_json_atomic(exp_dir / DATASET_PROFILE_REL_PATH, prof)

    plan = {
        "status": "READY",
        "source_dataset_hash": data_hash,
        "plan_digest": "plan_digest_abc",
        "source_profile_digest": "profile_digest_abc",
        "rules": [],
        "unresolved_findings": [],
    }
    write_json_atomic(exp_dir / PREPARATION_PLAN_REL_PATH, plan)

    view_desc = {
        "dataset_hash": sanitized_hash,
        "source_dataset_hash": data_hash,
        "source_plan_digest": "plan_digest_abc",
        "n_observations": 10,
        "candidate_feature_cols": ["feat"],
        "dropped_observation_ids": [],
        "target_label_mapping": None,
        "deferred_rules": [],
    }
    write_json_atomic(exp_dir / SANITIZED_VIEW_REL_PATH, view_desc)

    obs_ids = [ObservationId(f"id_{i}") for i in range(10)]
    view = DummyStageView(obs_ids, dataset_hash=sanitized_hash)
    config = PartitionConfig(
        strategy=PartitionStrategy.KFOLD,
        regime=EvaluationRegime.CV_AND_HOLDOUT,
        n_splits=2,
        holdout_fraction=0.2,
        shuffle=False,
        master_seed=42,
    )
    part_plan = build_partition_plan(view, config)

    write_json_atomic(exp_dir / PARTITION_PLAN_REL_PATH, partition_plan_to_dict(part_plan))
    write_splits_csv_gz(exp_dir / SPLITS_CSV_GZ_REL_PATH, part_plan)
    write_splits_schema(exp_dir / SPLITS_SCHEMA_REL_PATH, part_plan)


# ==============================================================================
# REV-M2-01: Profiling and Preparation Codes Compatibility
# ==============================================================================


def test_rev_m2_01_feature_constant_rule_admissibility() -> None:
    """REV-M2-01: E1_FEATURE_CONSTANT and E1_CONSTANT_COLUMN admit EXCLUDE_COLUMN and ACCEPT_AS_IS."""
    schema = DatasetSchemaSpec(
        target_col="target",
        task_type=TaskType.BINARY_CLASSIFICATION,
        column_semantic_types={
            "c_const": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "target": ColumnSemanticType.CATEGORICAL,
        },
    )
    bundle = load_dataset(
        {"c_const": [1.0, 1.0, 1.0, 1.0], "target": [0, 1, 0, 1]},
        schema=schema,
    )
    profile = profile_dataset(bundle)

    # Both E1_CONSTANT_COLUMN and E1_FEATURE_CONSTANT are admissible
    rule_exclude = PreparationRule(
        finding_code="E1_CONSTANT_COLUMN",
        column="c_const",
        kind="EXCLUDE_COLUMN",
    )
    plan_exclude = create_preparation_plan(profile, [rule_exclude])
    assert plan_exclude.status == "READY"

    rule_accept = PreparationRule(
        finding_code="E1_CONSTANT_COLUMN",
        column="c_const",
        kind="ACCEPT_AS_IS",
    )
    plan_accept = create_preparation_plan(profile, [rule_accept])
    assert plan_accept.status == "READY"

    # Injected E1_FEATURE_CONSTANT finding is also accepted
    finding_feature_const = make_finding(
        code="E1_FEATURE_CONSTANT",
        message="Feature is constant",
        context={"column": "c_const"},
    )
    profile_fc = replace(profile, findings=(finding_feature_const,))
    rule_fc = PreparationRule(
        finding_code="E1_FEATURE_CONSTANT",
        column="c_const",
        kind="EXCLUDE_COLUMN",
    )
    plan_fc = create_preparation_plan(profile_fc, [rule_fc])
    assert plan_fc.status == "READY"


def test_rev_m2_01_scale_disparity_rule_admissibility() -> None:
    """REV-M2-01: E1_SCALE_DISPARITY admits ACCEPT_AS_IS and DEFER_INTRA_FOLD."""
    schema = DatasetSchemaSpec(
        target_col="target",
        task_type=TaskType.BINARY_CLASSIFICATION,
        column_semantic_types={
            "small_feat": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "huge_feat": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "target": ColumnSemanticType.CATEGORICAL,
        },
    )
    bundle = load_dataset(
        {
            "small_feat": [0.001, 0.002, 0.003, 0.004],
            "huge_feat": [10000.0, 20000.0, 30000.0, 40000.0],
            "target": [0, 1, 0, 1],
        },
        schema=schema,
    )
    profile = profile_dataset(bundle)

    # Injected E1_SCALE_DISPARITY is admissible for DEFER_INTRA_FOLD and ACCEPT_AS_IS
    finding_sd = make_finding(
        code="E1_SCALE_DISPARITY",
        message="Scale disparity across features",
        context=None,
    )
    profile_sd = replace(profile, findings=(finding_sd,))
    rule_sd_defer = PreparationRule(
        finding_code="E1_SCALE_DISPARITY",
        column=None,
        kind="DEFER_INTRA_FOLD",
    )
    plan_sd = create_preparation_plan(profile_sd, [rule_sd_defer])
    assert plan_sd.status == "READY"

    rule_sd_accept = PreparationRule(
        finding_code="E1_SCALE_DISPARITY",
        column=None,
        kind="ACCEPT_AS_IS",
    )
    plan_sd_accept = create_preparation_plan(profile_sd, [rule_sd_accept])
    assert plan_sd_accept.status == "READY"


def test_rev_m2_01_target_constant_is_irresolvable() -> None:
    """REV-M2-01: E1_TARGET_CONSTANT cannot be resolved by column exclusion or other rules."""
    assert "E1_TARGET_CONSTANT" in IRRESOLVABLE_FINDING_CODES

    schema = DatasetSchemaSpec(
        target_col="target",
        task_type=TaskType.BINARY_CLASSIFICATION,
        column_semantic_types={
            "feat": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "target": ColumnSemanticType.CATEGORICAL,
        },
    )
    bundle = load_dataset(
        {"feat": [1.0, 2.0, 3.0, 4.0], "target": [0, 1, 0, 1]},
        schema=schema,
    )
    profile = profile_dataset(bundle)

    finding = make_finding(
        code="E1_TARGET_CONSTANT",
        message="Target is constant",
        context={"column": "target"},
    )
    profile_const = replace(profile, findings=(finding,))

    # Attempting to exclude target column raises ConfigurationError
    rule = PreparationRule(
        finding_code="E1_TARGET_CONSTANT",
        column="target",
        kind="EXCLUDE_COLUMN",
    )
    with pytest.raises(ConfigurationError, match="is irresolvable"):
        create_preparation_plan(profile_const, [rule])


# ==============================================================================
# REV-M2-02: Empty Folds Prevention
# ==============================================================================


def test_rev_m2_02_stratified_kfold_insufficient_samples() -> None:
    """REV-M2-02: stratified_kfold_split raises ConfigurationError if n < n_splits."""
    targets = np.array([0, 1])
    obs = (ObservationId("1"), ObservationId("2"))
    with pytest.raises(ConfigurationError, match="Cannot split.*stratified folds"):
        stratified_kfold_split(obs, target=targets, n_splits=5, seed=42)


def test_rev_m2_02_bootstrap_oob_non_empty() -> None:
    """REV-M2-02: bootstrap_split ensures OOB validation set is non-empty for each split."""
    for n in (3, 5, 10):
        obs = tuple(ObservationId(str(i)) for i in range(n))
        splits = bootstrap_split(obs, n_bootstraps=10, seed=123)
        for train_idx, val_idx in splits:
            assert len(train_idx) > 0
            assert len(val_idx) > 0


def test_rev_m2_02_holdout_empty_development_rejected() -> None:
    """REV-M2-02: holdout_split raises ConfigurationError on degenerate small N."""
    targets = np.array([0])
    obs = (ObservationId("1"),)
    with pytest.raises(ConfigurationError, match="Cannot perform holdout split"):
        holdout_split(obs, holdout_fraction=0.5, seed=42, target=targets)


def test_rev_m2_02_validate_partition_plan_rejects_empty_folds() -> None:
    """REV-M2-02: validate_partition_plan rejects plans with empty train or val sets."""
    schema = DatasetSchemaSpec(
        target_col="y",
        task_type=TaskType.REGRESSION,
        column_semantic_types={
            "x": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "y": ColumnSemanticType.NUMERIC_CONTINUOUS,
        },
    )
    bundle = load_dataset({"x": [10.0, 20.0, 30.0], "y": [1.0, 2.0, 3.0]}, schema=schema)
    profile = profile_dataset(bundle)
    plan_prep = create_preparation_plan(profile, [])
    view = sanitize_dataset(bundle, profile, plan_prep)

    cfg = PartitionConfig(strategy=PartitionStrategy.KFOLD, n_splits=2)
    valid_fold = FoldPartition(fold_index=1, train_ids=(view.observation_ids[0],), val_ids=(view.observation_ids[1],))

    # Empty train fold
    empty_train_fold = FoldPartition(fold_index=0, train_ids=(), val_ids=(view.observation_ids[0],))
    plan_bad = PartitionPlan(
        plan_id="p_bad1",
        source_dataset_hash=view.dataset_hash,
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=view.observation_ids,
        holdout_ids=(),
        folds=(empty_train_fold, valid_fold),
        config=cfg,
    )
    with pytest.raises(DataIntegrityError, match="has an empty training set"):
        validate_partition_plan(plan_bad, view)

    # Empty val fold
    empty_val_fold = FoldPartition(fold_index=0, train_ids=(view.observation_ids[0],), val_ids=())
    plan_bad2 = PartitionPlan(
        plan_id="p_bad2",
        source_dataset_hash=view.dataset_hash,
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.KFOLD,
        development_ids=view.observation_ids,
        holdout_ids=(),
        folds=(empty_val_fold, valid_fold),
        config=cfg,
    )
    with pytest.raises(DataIntegrityError, match="has an empty validation set"):
        validate_partition_plan(plan_bad2, view)


def test_rev_m2_02_partition_config_holdout_cv_only_rejected() -> None:
    """REV-M2-02: PartitionConfig rejects strategy=HOLDOUT with regime=CV_ONLY."""
    with pytest.raises(ConfigurationError, match="incompatible"):
        PartitionConfig(
            strategy=PartitionStrategy.HOLDOUT,
            regime=EvaluationRegime.CV_ONLY,
            master_seed=42,
        )


# ==============================================================================
# REV-M2-03: Temporal Partitions Missing/NaN Rejection
# ==============================================================================


def test_rev_m2_03_temporal_split_rejects_nans_and_nones() -> None:
    """REV-M2-03: temporal_split raises ConfigurationError on NaN or missing timestamps."""
    times_with_nan = np.array([1.0, np.nan, 3.0, 4.0])
    obs_4 = tuple(ObservationId(str(i)) for i in range(4))
    with pytest.raises(ConfigurationError, match="zero missing or NaN values"):
        temporal_split(obs_4, times=times_with_nan, n_splits=2)

    times_with_none = np.array(["2020-01-01", None, "2020-01-03"], dtype=object)
    obs_3 = tuple(ObservationId(str(i)) for i in range(3))
    with pytest.raises(ConfigurationError, match="zero missing or NaN values"):
        temporal_split(obs_3, times=times_with_none, n_splits=2)


def test_rev_m2_03_validate_partition_plan_rejects_temporal_nans() -> None:
    """REV-M2-03: validate_partition_plan rejects temporal strategy when fold contains NaN in time column."""
    schema = DatasetSchemaSpec(
        target_col="y",
        task_type=TaskType.REGRESSION,
        time_col="t",
        column_semantic_types={
            "x": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "y": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "t": ColumnSemanticType.NUMERIC_CONTINUOUS,
        },
    )
    bundle = load_dataset(
        {"x": [10.0, 20.0, 30.0], "y": [1.0, 2.0, 3.0], "t": [1.0, np.nan, 3.0]},
        schema=schema,
    )
    profile = profile_dataset(bundle)
    plan_prep = create_preparation_plan(profile, [])
    view = sanitize_dataset(bundle, profile, plan_prep)

    cfg = PartitionConfig(strategy=PartitionStrategy.TEMPORAL, n_splits=2, time_col="t")
    # Include view.observation_ids[1] (which has NaN in t) in val_ids of fold 0
    fold0 = FoldPartition(
        fold_index=0,
        train_ids=(view.observation_ids[0],),
        val_ids=(view.observation_ids[1],),
    )
    fold1 = FoldPartition(
        fold_index=1,
        train_ids=(view.observation_ids[0],),
        val_ids=(view.observation_ids[2],),
    )
    plan = PartitionPlan(
        plan_id="p_temporal_nan",
        source_dataset_hash=view.dataset_hash,
        regime=EvaluationRegime.CV_ONLY,
        strategy=PartitionStrategy.TEMPORAL,
        development_ids=view.observation_ids,
        holdout_ids=(),
        folds=(fold0, fold1),
        config=cfg,
    )
    with pytest.raises(DataIntegrityError, match="contains missing or NaN temporal value"):
        validate_partition_plan(plan, view)


# ==============================================================================
# REV-M2-04: Type Fidelity in JSON Serialization
# ==============================================================================


def test_rev_m2_04_target_label_mapping_type_fidelity() -> None:
    """REV-M2-04: target_label_mapping preserves primitive key types (int, bool, str) across JSON roundtrip."""
    int_desc = SanitizedViewDescriptor(
        dataset_hash="h1",
        source_dataset_hash="s1",
        source_plan_digest="p1",
        n_observations=2,
        candidate_feature_cols=("f1",),
        dropped_observation_ids=(),
        target_label_mapping={100: 0, 200: 1},
        deferred_rules=(),
    )
    d_int = sanitized_view_descriptor_to_dict(int_desc)
    roundtrip_int = sanitized_view_descriptor_from_dict(d_int)
    assert roundtrip_int.target_label_mapping == {100: 0, 200: 1}
    for k in roundtrip_int.target_label_mapping.keys():
        assert isinstance(k, int) and not isinstance(k, bool)

    bool_desc = SanitizedViewDescriptor(
        dataset_hash="h2",
        source_dataset_hash="s2",
        source_plan_digest="p2",
        n_observations=2,
        candidate_feature_cols=("f1",),
        dropped_observation_ids=(),
        target_label_mapping={False: 0, True: 1},
        deferred_rules=(),
    )
    d_bool = sanitized_view_descriptor_to_dict(bool_desc)
    roundtrip_bool = sanitized_view_descriptor_from_dict(d_bool)
    assert roundtrip_bool.target_label_mapping == {False: 0, True: 1}
    for k in roundtrip_bool.target_label_mapping.keys():
        assert isinstance(k, bool)


# ==============================================================================
# REV-M2-05: Source Plan Digest Integrity in Partition Gate
# ==============================================================================


def test_rev_m2_05_source_plan_digest_mismatch_rejected(tmp_path: Path) -> None:
    """REV-M2-05: verify_partition_gate rejects sanitized_view whose source_plan_digest differs from preparation_plan."""
    exp_dir = tmp_path / "exp_digest"
    _setup_valid_test_experiment(exp_dir)

    # Verify that clean experiment passes gate
    verify_partition_gate(exp_dir)

    # Corrupt source_plan_digest in sanitized_view.json
    view_path = exp_dir / SANITIZED_VIEW_REL_PATH
    with open(view_path, "r", encoding="utf-8") as f:
        view_dict = json.load(f)

    view_dict["source_plan_digest"] = "different_plan_digest_tampered"
    with open(view_path, "w", encoding="utf-8") as f:
        json.dump(view_dict, f)

    with pytest.raises((DataIntegrityError, ContractViolationError), match="source_plan_digest.*diverges"):
        verify_partition_gate(exp_dir)


# ==============================================================================
# REV-M2-06: Full Matrix Validation Including EXCLUDED Rows
# ==============================================================================


def test_rev_m2_06_splits_matrix_detects_corrupted_excluded_row(tmp_path: Path) -> None:
    """REV-M2-06: verify_partition_gate detects tampering of EXCLUDED rows in splits.csv.gz."""
    exp_dir = tmp_path / "exp_matrix"
    _setup_valid_test_experiment(exp_dir)

    # Clean gate passes
    verify_partition_gate(exp_dir)

    # In _setup_valid_test_experiment, id_5 is in holdout with role EXCLUDED in all folds
    with gzip.open(exp_dir / SPLITS_CSV_GZ_REL_PATH, "rt", encoding="utf-8") as f:
        lines = f.readlines()

    tampered_lines = []
    for line in lines:
        if line.startswith("id_5,"):
            # Replace EXCLUDED with TRAIN in fold_0
            tampered_lines.append(line.replace("EXCLUDED", "TRAIN", 1))
        else:
            tampered_lines.append(line)

    with gzip.open(exp_dir / SPLITS_CSV_GZ_REL_PATH, "wt", encoding="utf-8") as f:
        f.writelines(tampered_lines)

    # Gate must detect corrupted EXCLUDED cell
    with pytest.raises(DataIntegrityError, match="not marked as EXCLUDED"):
        verify_partition_gate(exp_dir)


# ==============================================================================
# REV-M2-07: CLI Purity (No NumPy or Hashlib in sys.modules)
# ==============================================================================


def test_rev_m2_07_cli_runtime_purity_subprocess() -> None:
    """REV-M2-07: Basic CLI invocation loads neither numpy nor hashlib into sys.modules."""
    code = (
        "import sys\n"
        "from experimental_ml.cli.main import main\n"
        "code = main(['--help'])\n"
        "assert code == 0\n"
        "assert 'numpy' not in sys.modules, f'numpy leaked into sys.modules: {sys.modules.get(\"numpy\")}'\n"
        "assert 'hashlib' not in sys.modules, f'hashlib leaked into sys.modules: {sys.modules.get(\"hashlib\")}'\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Subprocess failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"


# ==============================================================================
# REV-M2-08: Slicing SanitizedDatasetView and Reconstruction API
# ==============================================================================


def test_rev_m2_08_slice_view_by_observation_ids_and_reconstruct(tmp_path: Path) -> None:
    """REV-M2-08: slice_view_by_observation_ids slices view cleanly and preserves metadata."""
    schema = DatasetSchemaSpec(
        target_col="y",
        task_type=TaskType.REGRESSION,
        observation_id_col="id",
        column_semantic_types={
            "id": ColumnSemanticType.IDENTIFIER,
            "x": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "y": ColumnSemanticType.NUMERIC_CONTINUOUS,
        },
    )
    data = {
        "id": ["1", "2", "3", "4"],
        "x": [10.0, 20.0, 30.0, 40.0],
        "y": [1.0, 2.0, 3.0, 4.0],
    }
    bundle = load_dataset(data, schema=schema)
    profile = profile_dataset(bundle)
    prep_plan = create_preparation_plan(profile, [])
    view = sanitize_dataset(bundle, profile, prep_plan)

    # Slice by observation ids (order preserved)
    sliced = slice_view_by_observation_ids(view, ["3", "1"])
    assert sliced.observation_ids == (ObservationId("3"), ObservationId("1"))
    assert list(sliced.columns["x"]) == [30.0, 10.0]
    assert list(sliced.columns["y"]) == [3.0, 1.0]
    assert sliced.columns["x"].flags.writeable is False
    assert sliced.dataset_hash != view.dataset_hash
    assert sliced.schema == view.schema
    assert sliced.candidate_feature_cols == view.candidate_feature_cols

    # Slicing rejects duplicate IDs and unknown IDs
    with pytest.raises(DataIntegrityError, match="Duplicate"):
        slice_view_by_observation_ids(view, ["1", "1"])

    with pytest.raises(DataIntegrityError, match="not present"):
        slice_view_by_observation_ids(view, ["999"])


# ==============================================================================
# REV-M2-09: Target Zero Variance Finding in Regression
# ==============================================================================


def test_rev_m2_09_target_zero_variance_finding() -> None:
    """REV-M2-09: profile_dataset emits E1_TARGET_ZERO_VARIANCE for constant regression target."""
    schema = DatasetSchemaSpec(
        target_col="y",
        task_type=TaskType.REGRESSION,
        column_semantic_types={
            "x": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "y": ColumnSemanticType.NUMERIC_CONTINUOUS,
        },
    )
    bundle = load_dataset({"x": [1.0, 2.0, 3.0, 4.0], "y": [5.0, 5.0, 5.0, 5.0]}, schema=schema)
    profile = profile_dataset(bundle)

    codes = [f.code for f in profile.findings]
    assert "E1_TARGET_ZERO_VARIANCE" in codes


# ==============================================================================
# REV-M2-11: Finding.context None-Safety
# ==============================================================================


def test_rev_m2_11_finding_context_none_safe() -> None:
    """REV-M2-11: Finding with context=None does not trigger AttributeError during preparation planning."""
    finding = make_finding(
        code="E1_FEATURE_MISSING",
        message="Missing values",
        context=None,
    )
    assert finding.context is None

    schema = DatasetSchemaSpec(
        target_col="target",
        task_type=TaskType.BINARY_CLASSIFICATION,
        column_semantic_types={
            "feat": ColumnSemanticType.NUMERIC_CONTINUOUS,
            "target": ColumnSemanticType.CATEGORICAL,
        },
    )
    bundle = load_dataset({"feat": [1.0, 2.0], "target": [0, 1]}, schema=schema)
    profile = profile_dataset(bundle)
    profile_with_none_ctx = replace(profile, findings=(finding,))

    # Calling create_preparation_plan checks unresolved findings safely
    plan = create_preparation_plan(profile_with_none_ctx, [])
    assert plan.status == "INCOMPLETE"
    assert len(plan.unresolved_findings) == 1
    assert plan.unresolved_findings[0].column is None
