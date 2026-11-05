"""Probe script for Dimension B (Cross-Module Integration) of M1 Integrity Review.

Checks INT-01 through INT-08 empirically without modifying any repository files.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

from experimental_ml.core import (
    ConfigurationError,
    DataIntegrityError,
    ExperimentalMLError,
    ObservationId,
    TaskType,
    config_hash,
    dataset_hash,
    derive_seeds,
)
from experimental_ml.data import (
    DatasetSchemaSpec,
    get_column_array,
    load_dataset,
    slice_bundle_by_observation_ids,
)
from experimental_ml.metrics import (
    METRICS_CATALOG,
    aggregate_fold_metrics,
    compute_metric,
    rank_configurations,
)


def probe_int_01_e2e_flow() -> dict[str, Any]:
    """INT-01: End-to-end flow load_dataset -> get_column_array -> compute_metric -> aggregate -> rank."""
    data = {
        "x1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "x2": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "y": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0],
    }
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    bundle = load_dataset(data, schema)

    fold1_ids = [ObservationId("obs_000000"), ObservationId("obs_000001"), ObservationId("obs_000002")]
    fold2_ids = [ObservationId("obs_000003"), ObservationId("obs_000004"), ObservationId("obs_000005")]

    b1 = slice_bundle_by_observation_ids(bundle, fold1_ids)
    b2 = slice_bundle_by_observation_ids(bundle, fold2_ids)

    y1 = get_column_array(b1, "y", copy=False)
    y2 = get_column_array(b2, "y", copy=False)

    # Candidate A (exact), Candidate B (shifted)
    m_a1 = compute_metric("rmse", y1, y1)
    m_a2 = compute_metric("rmse", y2, y2)
    agg_a = aggregate_fold_metrics([m_a1, m_a2])

    m_b1 = compute_metric("rmse", y1, y1 + 0.5)
    m_b2 = compute_metric("rmse", y2, y2 + 0.5)
    agg_b = aggregate_fold_metrics([m_b1, m_b2])

    ranked = rank_configurations([("model_b", agg_b), ("model_a", agg_a)])
    return {
        "bundle_n_rows": bundle.n_rows,
        "agg_a_mean": agg_a.mean,
        "agg_b_mean": agg_b.mean,
        "ranked_order": [(r.candidate_id, r.rank, r.status.value) for r in ranked],
    }


def probe_int_02_identifiers_and_enums() -> dict[str, Any]:
    """INT-02: ObservationId and TaskType identity across core, data, metrics."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    bundle = load_dataset({"x": [1.0, 2.0], "y": [3.0, 4.0]}, schema)

    initial_types = [type(oid).__name__ for oid in bundle.observation_ids]
    initial_is_obs_id = all(isinstance(oid, ObservationId) for oid in bundle.observation_ids)

    # Test slicing with plain str vs ObservationId
    sliced_with_str = slice_bundle_by_observation_ids(bundle, ["obs_000001", "obs_000000"])
    sliced_str_types = [type(oid).__name__ for oid in sliced_with_str.observation_ids]
    sliced_str_is_obs_id = all(isinstance(oid, ObservationId) for oid in sliced_with_str.observation_ids)

    # TaskType identity between schema and METRICS_CATALOG
    rmse_spec = METRICS_CATALOG["rmse"]
    task_type_in_supported = bundle.schema.task_type in rmse_spec.supported_tasks

    return {
        "initial_types": initial_types,
        "initial_is_obs_id": initial_is_obs_id,
        "sliced_with_plain_str_types": sliced_str_types,
        "sliced_with_plain_str_is_obs_id": sliced_str_is_obs_id,
        "task_type_in_supported": task_type_in_supported,
    }


def probe_int_03_exceptions() -> dict[str, Any]:
    """INT-03: Check whether invalid inputs across core, metrics, data raise ExperimentalMLError."""
    results = []

    def check_call(label: str, fn):
        try:
            fn()
            results.append({"case": label, "raised": None, "is_expml_error": False})
        except Exception as exc:
            results.append({
                "case": label,
                "raised": type(exc).__name__,
                "mro": [c.__name__ for c in type(exc).__mro__],
                "is_expml_error": isinstance(exc, ExperimentalMLError),
                "message": str(exc)[:120],
            })

    check_call("core.ObservationId('')", lambda: ObservationId(""))
    check_call("core.ObservationId('a\\nb')", lambda: ObservationId("a\nb"))
    check_call("core.derive_seeds(42, 0)", lambda: derive_seeds(42, 0))
    check_call("core.derive_seeds('bad', 2)", lambda: derive_seeds("bad", 2))  # type: ignore[arg-type]
    check_call("core.config_hash(object())", lambda: config_hash(object()))
    check_call("metrics.compute_metric('unknown', [1], [1])", lambda: compute_metric("unknown", [1.0], [1.0]))
    check_call("metrics.compute_metric('rmse', [], [])", lambda: compute_metric("rmse", [], []))
    check_call(
        "data.DatasetSchemaSpec(target_col='', task_type=TaskType.REGRESSION)",
        lambda: DatasetSchemaSpec(target_col="", task_type=TaskType.REGRESSION),
    )
    check_call(
        "data.load_dataset(int64 overflow 2**63)",
        lambda: load_dataset(
            {"x": [2**63], "y": [1.0]},
            DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION),
        ),
    )

    return {"exception_checks": results}


def probe_int_04_cross_format_hashes() -> dict[str, Any]:
    """INT-04: Compare dataset_hash, raw_source_hash, schema_hash across CSV LF, CSV CRLF, TSV, and dict."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    csv_lf = b"x,y\n1.0,2.0\n3.0,4.0\n"
    csv_crlf = b"x,y\r\n1.0,2.0\r\n3.0,4.0\r\n"
    tsv_lf = b"x\ty\n1.0\t2.0\n3.0\t4.0\n"
    mem_dict_xy = {"x": [1.0, 3.0], "y": [2.0, 4.0]}
    mem_dict_yx = {"y": [2.0, 4.0], "x": [1.0, 3.0]}

    with tempfile.TemporaryDirectory(prefix="m1-audit-int04-") as tmpdir:
        p_lf = Path(tmpdir) / "data_lf.csv"
        p_crlf = Path(tmpdir) / "data_crlf.csv"
        p_tsv = Path(tmpdir) / "data.tsv"
        p_lf.write_bytes(csv_lf)
        p_crlf.write_bytes(csv_crlf)
        p_tsv.write_bytes(tsv_lf)

        b_lf = load_dataset(p_lf, schema)
        b_crlf = load_dataset(p_crlf, schema)
        b_tsv = load_dataset(p_tsv, schema)
        b_dict_xy = load_dataset(mem_dict_xy, schema)
        b_dict_yx = load_dataset(mem_dict_yx, schema)

    return {
        "dataset_hash_lf": b_lf.dataset_hash,
        "dataset_hash_crlf": b_crlf.dataset_hash,
        "dataset_hash_tsv": b_tsv.dataset_hash,
        "dataset_hash_dict_xy": b_dict_xy.dataset_hash,
        "dataset_hash_dict_yx": b_dict_yx.dataset_hash,
        "lf_crlf_tsv_dict_xy_all_equal": (
            b_lf.dataset_hash == b_crlf.dataset_hash == b_tsv.dataset_hash == b_dict_xy.dataset_hash
        ),
        "dict_xy_equals_dict_yx": b_dict_xy.dataset_hash == b_dict_yx.dataset_hash,
        "raw_source_hash_lf": b_lf.raw_source_hash,
        "raw_source_hash_crlf": b_crlf.raw_source_hash,
        "raw_source_hash_lf_differs_crlf": b_lf.raw_source_hash != b_crlf.raw_source_hash,
        "schema_hash": b_lf.schema_hash,
    }


def probe_int_05_subprocess_determinism() -> dict[str, Any]:
    """INT-05: Determinism across PYTHONHASHSEED=0 and PYTHONHASHSEED=12345."""
    code = """
import json
from experimental_ml.core import TaskType, config_hash, derive_seeds, spawn_child_seeds
from experimental_ml.data import DatasetSchemaSpec, load_dataset, slice_bundle_by_observation_ids

schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION, ignore_cols=("ig2", "ig1"))
bundle = load_dataset({"b": [1.0, 2.0, 3.0], "a": [4, 5, 6], "ig1": ["x", "y", "z"], "ig2": [True, False, True], "y": [10.0, 20.0, 30.0]}, schema)
sliced = slice_bundle_by_observation_ids(bundle, ["obs_000002", "obs_000000"])
s1 = derive_seeds(42, 3)
s2 = spawn_child_seeds(42, 2)
print(json.dumps({
    "config_hash": config_hash({"z": 1, "a": [1.0, -0.0], "s": {"b", "a"}}),
    "bundle_dataset_hash": bundle.dataset_hash,
    "bundle_raw_source_hash": bundle.raw_source_hash,
    "bundle_schema_hash": bundle.schema_hash,
    "sliced_dataset_hash": sliced.dataset_hash,
    "s1": s1,
    "s2": s2,
}))
"""
    outputs = {}
    for seed in ("0", "12345"):
        env = os.environ.copy()
        env["PYTHONHASHSEED"] = seed
        res = subprocess.run(
            [sys.executable, "-c", code],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        outputs[seed] = json.loads(res.stdout.strip())

    return {
        "hashseed_0": outputs["0"],
        "hashseed_12345": outputs["12345"],
        "identical": outputs["0"] == outputs["12345"],
    }


def probe_int_06_readonly_boundary() -> dict[str, Any]:
    """INT-06: Pass get_column_array(copy=False) to all 15 metrics and verify writeable=False & bytes unchanged."""
    reg_schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    reg_bundle = load_dataset(
        {
            "y": [1.5, 2.5, 3.5, 4.5, 5.5],
            "pred": [1.4, 2.6, 3.4, 4.6, 5.4],
        },
        reg_schema,
    )
    clf_schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.BINARY_CLASSIFICATION)
    clf_bundle = load_dataset(
        {
            "y": [0, 1, 0, 1, 1],
            "pred": [0, 1, 0, 0, 1],
            "prob": [0.1, 0.9, 0.2, 0.4, 0.8],
        },
        clf_schema,
    )

    y_reg = get_column_array(reg_bundle, "y", copy=False)
    p_reg = get_column_array(reg_bundle, "pred", copy=False)
    y_clf = get_column_array(clf_bundle, "y", copy=False)
    p_clf = get_column_array(clf_bundle, "pred", copy=False)
    prob_clf = get_column_array(clf_bundle, "prob", copy=False)

    digest_before = {
        "y_reg": hashlib.sha256(y_reg.tobytes()).hexdigest(),
        "p_reg": hashlib.sha256(p_reg.tobytes()).hexdigest(),
        "y_clf": hashlib.sha256(y_clf.tobytes()).hexdigest(),
        "p_clf": hashlib.sha256(p_clf.tobytes()).hexdigest(),
        "prob_clf": hashlib.sha256(prob_clf.tobytes()).hexdigest(),
    }

    metrics_checked = []
    for m_id, spec in METRICS_CATALOG.items():
        if TaskType.REGRESSION in spec.supported_tasks:
            mv = compute_metric(m_id, y_reg, p_reg)
        elif spec.requires_probabilities:
            mv = compute_metric(m_id, y_clf, prob_clf)
        else:
            mv = compute_metric(m_id, y_clf, p_clf)
        metrics_checked.append({"metric_id": m_id, "value": mv.value, "status": mv.status.value})

    digest_after = {
        "y_reg": hashlib.sha256(y_reg.tobytes()).hexdigest(),
        "p_reg": hashlib.sha256(p_reg.tobytes()).hexdigest(),
        "y_clf": hashlib.sha256(y_clf.tobytes()).hexdigest(),
        "p_clf": hashlib.sha256(p_clf.tobytes()).hexdigest(),
        "prob_clf": hashlib.sha256(prob_clf.tobytes()).hexdigest(),
    }

    writeable_after = any(arr.flags.writeable for arr in (y_reg, p_reg, y_clf, p_clf, prob_clf))

    return {
        "metrics_count": len(metrics_checked),
        "metrics_checked": metrics_checked,
        "digests_unchanged": digest_before == digest_after,
        "any_writeable_after": writeable_after,
    }


def probe_int_07_hash_contracts() -> dict[str, Any]:
    """INT-07: Check relationship between bundle.dataset_hash, raw_source_hash, schema_hash and core functions."""
    schema = DatasetSchemaSpec(target_col="y", task_type=TaskType.REGRESSION)
    with tempfile.TemporaryDirectory(prefix="m1-audit-int07-") as tmpdir:
        csv_path = Path(tmpdir) / "sample.csv"
        raw_bytes = b"x,y\n1.0,2.0\n3.0,4.0\n"
        csv_path.write_bytes(raw_bytes)
        bundle_disk = load_dataset(csv_path, schema)
        core_path_hash = dataset_hash(csv_path, schema)

    core_cols_hash = dataset_hash(bundle_disk.columns, bundle_disk.schema)
    core_schema_hash = config_hash(schema)
    raw_file_sha256 = hashlib.sha256(raw_bytes).hexdigest()

    # Check if observation_ids affect bundle.dataset_hash when observation_id_col is None
    sliced = slice_bundle_by_observation_ids(bundle_disk, [ObservationId("obs_000001")])
    fresh_1row = load_dataset({"x": [3.0], "y": [4.0]}, schema)

    return {
        "bundle_dataset_hash_equals_core_columns_hash": bundle_disk.dataset_hash == core_cols_hash,
        "bundle_schema_hash_equals_core_config_hash": bundle_disk.schema_hash == core_schema_hash,
        "bundle_raw_source_hash_equals_file_sha256": bundle_disk.raw_source_hash == raw_file_sha256,
        "core_dataset_hash_on_path_equals_bundle_dataset_hash": core_path_hash == bundle_disk.dataset_hash,
        "core_dataset_hash_on_path_equals_bundle_raw_source_hash": core_path_hash == bundle_disk.raw_source_hash,
        "sliced_obs_ids": [str(x) for x in sliced.observation_ids],
        "fresh_1row_obs_ids": [str(x) for x in fresh_1row.observation_ids],
        "sliced_and_fresh_have_different_obs_ids_but_same_dataset_hash": (
            sliced.observation_ids != fresh_1row.observation_ids
            and sliced.dataset_hash == fresh_1row.dataset_hash
        ),
    }


def probe_int_08_int64_and_bool_columns() -> dict[str, Any]:
    """INT-08: Pass int64 and bool columns from DatasetBundle into regression and classification metrics."""
    # Case 1: bool target in BINARY_CLASSIFICATION
    schema_bool = DatasetSchemaSpec(target_col="y", task_type=TaskType.BINARY_CLASSIFICATION)
    bundle_bool = load_dataset(
        {
            "x_int": [10, 20, 30, 40],
            "y": [False, True, False, True],
        },
        schema_bool,
    )
    y_bool = get_column_array(bundle_bool, "y", copy=False)
    x_int = get_column_array(bundle_bool, "x_int", copy=False)

    # Test regression metric with int64 array
    reg_on_int64 = compute_metric("rmse", x_int, x_int)

    # Test classification metrics with bool target and bool predictions
    acc_bool = compute_metric("accuracy", y_bool, y_bool)
    bacc_bool = compute_metric("balanced_accuracy", y_bool, y_bool)
    prec_bool_default = compute_metric("precision", y_bool, y_bool)  # default pos_label=1
    rec_bool_default = compute_metric("recall", y_bool, y_bool)
    f1_bool_default = compute_metric("f1", y_bool, y_bool)
    roc_bool = compute_metric("roc_auc", y_bool, [0.1, 0.9, 0.2, 0.8])
    logloss_bool = compute_metric("log_loss", y_bool, [0.1, 0.9, 0.2, 0.8])

    # What if y_true is bool [False, True] and y_pred is int64 [0, 1]?
    y_int01 = np.array([0, 1, 0, 1], dtype=np.int64)
    bacc_bool_vs_int01 = compute_metric("balanced_accuracy", y_bool, y_int01)
    prec_macro_bool_vs_int01 = compute_metric("precision", y_bool, y_int01, average="macro")

    # What if y_true is string labels ["no", "yes"] and pos_label is default 1?
    schema_str = DatasetSchemaSpec(target_col="y", task_type=TaskType.BINARY_CLASSIFICATION)
    bundle_str = load_dataset({"x": [1.0, 2.0, 3.0, 4.0], "y": ["no", "yes", "no", "yes"]}, schema_str)
    y_str = get_column_array(bundle_str, "y", copy=False)
    prec_str_default = compute_metric("precision", y_str, y_str)

    return {
        "y_bool_dtype": str(y_bool.dtype),
        "x_int_dtype": str(x_int.dtype),
        "reg_on_int64": {"value": reg_on_int64.value, "status": reg_on_int64.status.value},
        "acc_bool": {"value": acc_bool.value, "status": acc_bool.status.value},
        "bacc_bool": {"value": bacc_bool.value, "status": bacc_bool.status.value},
        "prec_bool_default": {"value": prec_bool_default.value, "status": prec_bool_default.status.value},
        "rec_bool_default": {"value": rec_bool_default.value, "status": rec_bool_default.status.value},
        "f1_bool_default": {"value": f1_bool_default.value, "status": f1_bool_default.status.value},
        "roc_bool": {"value": roc_bool.value, "status": roc_bool.status.value},
        "logloss_bool": {"value": logloss_bool.value, "status": logloss_bool.status.value},
        "bacc_bool_vs_int01": {"value": bacc_bool_vs_int01.value, "status": bacc_bool_vs_int01.status.value},
        "prec_macro_bool_vs_int01": {
            "value": prec_macro_bool_vs_int01.value,
            "status": prec_macro_bool_vs_int01.status.value,
        },
        "prec_str_default_pos_label_1": {
            "value": prec_str_default.value,
            "status": prec_str_default.status.value,
            "warnings": [w.code for w in prec_str_default.warnings],
        },
    }


def main() -> None:
    report = {
        "INT-01": probe_int_01_e2e_flow(),
        "INT-02": probe_int_02_identifiers_and_enums(),
        "INT-03": probe_int_03_exceptions(),
        "INT-04": probe_int_04_cross_format_hashes(),
        "INT-05": probe_int_05_subprocess_determinism(),
        "INT-06": probe_int_06_readonly_boundary(),
        "INT-07": probe_int_07_hash_contracts(),
        "INT-08": probe_int_08_int64_and_bool_columns(),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
