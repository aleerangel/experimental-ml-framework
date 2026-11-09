"""Bidirectional lossless codecs for data layer objects.

Complies with STORE-02, STORE-03, RFC 8259, and ADR-008.
"""

from __future__ import annotations

import math
from types import MappingProxyType
from typing import Any

import numpy as np

from experimental_ml.core.enums import FindingSeverity, TaskType
from experimental_ml.core.findings import Finding
from experimental_ml.core.types import ObservationId
from experimental_ml.data.descriptors import DatasetDescriptor, SanitizedViewDescriptor
from experimental_ml.data.preparation import (
    PreparationPlan,
    PreparationRule,
    UnresolvedFinding,
)
from experimental_ml.data.profiling import (
    CategoricalDistributionStats,
    CategoryFrequency,
    ColumnProfile,
    DatasetProfile,
    DuplicateRowsProfile,
    GroupProfile,
    NumericDistributionStats,
    TargetProfile,
)
from experimental_ml.data.schema import ColumnSemanticType


def _sanitize_float(val: float | None) -> float | None:
    """Ensure float value contains no NaN or Infinity (STORE-02, RFC 8259)."""
    if val is None:
        return None
    fval = float(val)
    if math.isnan(fval) or math.isinf(fval):
        return None
    return fval


def _to_json_primitive(val: Any) -> Any:
    """Recursively convert NumPy scalars and framework objects to pure JSON primitives."""
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, np.integer)):
        return int(val)
    if isinstance(val, (float, np.floating)):
        fval = float(val)
        return None if (math.isnan(fval) or math.isinf(fval)) else fval
    if hasattr(val, "value"):  # Enum
        return val.value
    if isinstance(val, (list, tuple, np.ndarray)):
        return [_to_json_primitive(x) for x in val]
    if isinstance(val, (dict, MappingProxyType)):
        return {str(k): _to_json_primitive(v) for k, v in val.items()}
    return str(val)


# --- DatasetDescriptor Codecs ---


def dataset_descriptor_to_dict(desc: DatasetDescriptor) -> dict[str, Any]:
    """Serialize DatasetDescriptor to standard JSON-compatible dict."""
    return {
        "dataset_hash": desc.dataset_hash,
        "raw_source_hash": desc.raw_source_hash,
        "raw_source_path": desc.raw_source_path,
        "n_observations": desc.n_observations,
        "n_columns": desc.n_columns,
        "column_names": list(desc.column_names),
        "column_types": dict(desc.column_types),
        "target_col": desc.target_col,
        "task_type": desc.task_type,
        "group_col": desc.group_col,
        "time_col": desc.time_col,
        "schema_path": desc.schema_path,
    }


def dataset_descriptor_from_dict(d: dict[str, Any]) -> DatasetDescriptor:
    """Reconstruct DatasetDescriptor from dict."""
    return DatasetDescriptor(
        dataset_hash=d["dataset_hash"],
        raw_source_hash=d.get("raw_source_hash"),
        raw_source_path=d.get("raw_source_path"),
        n_observations=int(d["n_observations"]),
        n_columns=int(d["n_columns"]),
        column_names=tuple(d["column_names"]),
        column_types=MappingProxyType(dict(d["column_types"])),
        target_col=d.get("target_col"),
        task_type=d.get("task_type"),
        group_col=d.get("group_col"),
        time_col=d.get("time_col"),
        schema_path=d.get("schema_path"),
    )


# --- SanitizedViewDescriptor Codecs ---


def sanitized_view_descriptor_to_dict(desc: SanitizedViewDescriptor) -> dict[str, Any]:
    """Serialize SanitizedViewDescriptor to dict."""
    deferred_rules_list = [
        {
            "finding_code": r.finding_code,
            "column": r.column,
            "kind": r.kind,
            "parameters": dict(r.parameters),
        }
        for r in desc.deferred_rules
    ]
    target_mapping_serialized: list[dict[str, Any]] | None = None
    if desc.target_label_mapping is not None:
        target_mapping_serialized = [
            {"key": k, "key_type": type(k).__name__, "value": v}
            for k, v in desc.target_label_mapping.items()
        ]
    return {
        "dataset_hash": desc.dataset_hash,
        "source_dataset_hash": desc.source_dataset_hash,
        "source_plan_digest": desc.source_plan_digest,
        "n_observations": desc.n_observations,
        "candidate_feature_cols": list(desc.candidate_feature_cols),
        "dropped_observation_ids": [str(oid) for oid in desc.dropped_observation_ids],
        "target_label_mapping": target_mapping_serialized,
        "deferred_rules": deferred_rules_list,
    }


def sanitized_view_descriptor_from_dict(d: dict[str, Any]) -> SanitizedViewDescriptor:
    """Reconstruct SanitizedViewDescriptor from dict."""
    deferred_rules = tuple(
        PreparationRule(
            finding_code=r["finding_code"],
            column=r["column"],
            kind=r["kind"],
            parameters=MappingProxyType(dict(r.get("parameters", {}))),
        )
        for r in d.get("deferred_rules", [])
    )
    raw_mapping = d.get("target_label_mapping")
    target_mapping: MappingProxyType[Any, int] | None = None
    if raw_mapping is not None:
        if isinstance(raw_mapping, list):
            coerced_map: dict[Any, int] = {}
            for item in raw_mapping:
                k = item["key"]
                k_type = item.get("key_type")
                if k_type == "int":
                    k = int(k)
                elif k_type == "float":
                    k = float(k)
                elif k_type == "bool":
                    k = bool(k)
                elif k_type == "str":
                    k = str(k)
                coerced_map[k] = int(item["value"])
            target_mapping = MappingProxyType(coerced_map)
        elif isinstance(raw_mapping, dict):
            target_mapping = MappingProxyType(dict(raw_mapping))
    return SanitizedViewDescriptor(
        dataset_hash=d["dataset_hash"],
        source_dataset_hash=d["source_dataset_hash"],
        source_plan_digest=d["source_plan_digest"],
        n_observations=int(d["n_observations"]),
        candidate_feature_cols=tuple(d["candidate_feature_cols"]),
        dropped_observation_ids=tuple(ObservationId(oid) for oid in d["dropped_observation_ids"]),
        target_label_mapping=target_mapping,
        deferred_rules=deferred_rules,
    )


# --- DatasetProfile Codecs ---


def _numeric_stats_to_dict(stats: NumericDistributionStats | None) -> dict[str, Any] | None:
    if stats is None:
        return None
    return {
        "mean": _sanitize_float(stats.mean),
        "std": _sanitize_float(stats.std),
        "min": _sanitize_float(stats.min),
        "q1": _sanitize_float(stats.q1),
        "median": _sanitize_float(stats.median),
        "q3": _sanitize_float(stats.q3),
        "max": _sanitize_float(stats.max),
        "range": _sanitize_float(stats.range),
        "iqr": _sanitize_float(stats.iqr),
    }


def _numeric_stats_from_dict(d: dict[str, Any] | None) -> NumericDistributionStats | None:
    if d is None:
        return None
    return NumericDistributionStats(
        mean=d["mean"],
        std=d["std"],
        min=d["min"],
        q1=d["q1"],
        median=d["median"],
        q3=d["q3"],
        max=d["max"],
        range=d["range"],
        iqr=d["iqr"],
    )


def _categorical_stats_to_dict(stats: CategoricalDistributionStats | None) -> dict[str, Any] | None:
    if stats is None:
        return None
    return {
        "cardinality": stats.cardinality,
        "frequencies": [
            {
                "value": _to_json_primitive(freq.value),
                "count": freq.count,
                "proportion": _sanitize_float(freq.proportion),
            }
            for freq in stats.frequencies
        ],
        "remainder_count": stats.remainder_count,
        "remainder_proportion": _sanitize_float(stats.remainder_proportion) or 0.0,
    }


def _categorical_stats_from_dict(d: dict[str, Any] | None) -> CategoricalDistributionStats | None:
    if d is None:
        return None
    frequencies = tuple(
        CategoryFrequency(
            value=f["value"],
            count=int(f["count"]),
            proportion=float(f["proportion"]),
        )
        for f in d["frequencies"]
    )
    return CategoricalDistributionStats(
        cardinality=int(d["cardinality"]),
        frequencies=frequencies,
        remainder_count=int(d["remainder_count"]),
        remainder_proportion=float(d["remainder_proportion"]),
    )


def dataset_profile_to_dict(profile: DatasetProfile) -> dict[str, Any]:
    """Serialize DatasetProfile to dict."""
    columns_dict = {}
    for name, col in profile.columns.items():
        columns_dict[name] = {
            "name": col.name,
            "physical_type": col.physical_type,
            "semantic_type": col.semantic_type.value,
            "role": col.role,
            "n_missing": col.n_missing,
            "missing_proportion": _sanitize_float(col.missing_proportion) or 0.0,
            "n_unique": col.n_unique,
            "numeric_stats": _numeric_stats_to_dict(col.numeric_stats),
            "categorical_stats": _categorical_stats_to_dict(col.categorical_stats),
        }

    target_dict = {
        "column_name": profile.target.column_name,
        "task_type": profile.target.task_type.value,
        "numeric_stats": _numeric_stats_to_dict(profile.target.numeric_stats),
        "skewness": _sanitize_float(profile.target.skewness),
        "outliers_count_iqr_fences": profile.target.outliers_count_iqr_fences,
        "class_frequencies": (
            [
                {
                    "value": _to_json_primitive(cf.value),
                    "count": cf.count,
                    "proportion": _sanitize_float(cf.proportion),
                }
                for cf in profile.target.class_frequencies
            ]
            if profile.target.class_frequencies
            else None
        ),
        "majority_minority_ratio": _sanitize_float(profile.target.majority_minority_ratio),
    }

    groups_dict = None
    if profile.groups:
        groups_dict = {
            "group_col": profile.groups.group_col,
            "n_groups": profile.groups.n_groups,
            "min_group_size": profile.groups.min_group_size,
            "median_group_size": _sanitize_float(profile.groups.median_group_size) or 0.0,
            "max_group_size": profile.groups.max_group_size,
        }

    duplicate_rows_dict = {
        "n_duplicate_rows": profile.duplicate_rows.n_duplicate_rows,
        "duplicate_observation_ids": [str(oid) for oid in profile.duplicate_rows.duplicate_observation_ids],
        "is_truncated": profile.duplicate_rows.is_truncated,
    }

    findings_list = [
        {
            "severity": f.severity.value,
            "code": f.code,
            "message": f.message,
            "context": {k: _to_json_primitive(v) for k, v in f.context.items()} if f.context else None,
        }
        for f in profile.findings
    ]

    return {
        "source_dataset_hash": profile.source_dataset_hash,
        "n_rows": profile.n_rows,
        "n_cols": profile.n_cols,
        "memory_bytes": profile.memory_bytes,
        "columns": columns_dict,
        "duplicate_rows": duplicate_rows_dict,
        "target": target_dict,
        "groups": groups_dict,
        "findings": findings_list,
    }


def dataset_profile_from_dict(d: dict[str, Any]) -> DatasetProfile:
    """Reconstruct DatasetProfile from dict."""
    columns_map = {}
    for name, cdict in d["columns"].items():
        columns_map[name] = ColumnProfile(
            name=cdict["name"],
            physical_type=cdict["physical_type"],
            semantic_type=ColumnSemanticType(cdict["semantic_type"]),
            role=cdict["role"],
            n_missing=int(cdict["n_missing"]),
            missing_proportion=float(cdict["missing_proportion"]),
            n_unique=int(cdict["n_unique"]),
            numeric_stats=_numeric_stats_from_dict(cdict.get("numeric_stats")),
            categorical_stats=_categorical_stats_from_dict(cdict.get("categorical_stats")),
        )

    t_dict = d["target"]
    target_class_freqs = None
    if t_dict.get("class_frequencies") is not None:
        target_class_freqs = tuple(
            CategoryFrequency(
                value=cf["value"],
                count=int(cf["count"]),
                proportion=float(cf["proportion"]),
            )
            for cf in t_dict["class_frequencies"]
        )

    target_profile = TargetProfile(
        column_name=t_dict["column_name"],
        task_type=TaskType(t_dict["task_type"]),
        numeric_stats=_numeric_stats_from_dict(t_dict.get("numeric_stats")),
        skewness=t_dict.get("skewness"),
        outliers_count_iqr_fences=t_dict.get("outliers_count_iqr_fences"),
        class_frequencies=target_class_freqs,
        majority_minority_ratio=t_dict.get("majority_minority_ratio"),
    )

    group_profile = None
    if d.get("groups"):
        g_dict = d["groups"]
        group_profile = GroupProfile(
            group_col=g_dict["group_col"],
            n_groups=int(g_dict["n_groups"]),
            min_group_size=int(g_dict["min_group_size"]),
            median_group_size=float(g_dict["median_group_size"]),
            max_group_size=int(g_dict["max_group_size"]),
        )

    dup_dict = d["duplicate_rows"]
    dup_profile = DuplicateRowsProfile(
        n_duplicate_rows=int(dup_dict["n_duplicate_rows"]),
        duplicate_observation_ids=tuple(
            ObservationId(oid) for oid in dup_dict["duplicate_observation_ids"]
        ),
        is_truncated=bool(dup_dict["is_truncated"]),
    )

    findings = tuple(
        Finding(
            severity=FindingSeverity(f["severity"]),
            code=f["code"],
            message=f["message"],
            context=MappingProxyType(dict(f["context"])) if f.get("context") else None,
        )
        for f in d["findings"]
    )

    return DatasetProfile(
        source_dataset_hash=d["source_dataset_hash"],
        n_rows=int(d["n_rows"]),
        n_cols=int(d["n_cols"]),
        memory_bytes=int(d["memory_bytes"]),
        columns=MappingProxyType(columns_map),
        duplicate_rows=dup_profile,
        target=target_profile,
        groups=group_profile,
        findings=findings,
    )


# --- PreparationPlan Codecs ---


def preparation_plan_to_dict(plan: PreparationPlan) -> dict[str, Any]:
    """Serialize PreparationPlan to dict."""
    rules_list = [
        {
            "finding_code": r.finding_code,
            "column": r.column,
            "kind": r.kind,
            "parameters": dict(r.parameters),
        }
        for r in plan.rules
    ]
    unresolved_list = [
        {
            "finding_code": u.finding_code,
            "column": u.column,
            "reason": u.reason,
        }
        for u in plan.unresolved_findings
    ]
    return {
        "status": plan.status,
        "source_dataset_hash": plan.source_dataset_hash,
        "source_profile_digest": plan.source_profile_digest,
        "plan_digest": plan.plan_digest,
        "rules": rules_list,
        "unresolved_findings": unresolved_list,
    }


def preparation_plan_from_dict(d: dict[str, Any]) -> PreparationPlan:
    """Reconstruct PreparationPlan from dict."""
    rules = tuple(
        PreparationRule(
            finding_code=r["finding_code"],
            column=r["column"],
            kind=r["kind"],
            parameters=MappingProxyType(dict(r.get("parameters", {}))),
        )
        for r in d.get("rules", [])
    )
    unresolved = tuple(
        UnresolvedFinding(
            finding_code=u["finding_code"],
            column=u["column"],
            reason=u["reason"],
        )
        for u in d.get("unresolved_findings", [])
    )
    return PreparationPlan(
        status=d["status"],
        source_dataset_hash=d["source_dataset_hash"],
        source_profile_digest=d["source_profile_digest"],
        plan_digest=d.get("plan_digest", ""),
        rules=rules,
        unresolved_findings=unresolved,
    )
