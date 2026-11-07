"""Experimental stages management and stage gates verification.

Complies with STORE-03, STORE-05, STORE-06, and CA-GER-01.
"""

from __future__ import annotations

from experimental_ml.stages.stage_gates import (
    DATASET_DESCRIPTOR_REL_PATH,
    DATASET_PROFILE_REL_PATH,
    PARTITION_PLAN_REL_PATH,
    PREPARATION_PLAN_REL_PATH,
    SANITIZED_VIEW_REL_PATH,
    SPLITS_CSV_GZ_REL_PATH,
    SPLITS_SCHEMA_REL_PATH,
    verify_partition_gate,
    verify_preparation_gate,
)

__all__ = [
    "DATASET_DESCRIPTOR_REL_PATH",
    "DATASET_PROFILE_REL_PATH",
    "PREPARATION_PLAN_REL_PATH",
    "SANITIZED_VIEW_REL_PATH",
    "PARTITION_PLAN_REL_PATH",
    "SPLITS_CSV_GZ_REL_PATH",
    "SPLITS_SCHEMA_REL_PATH",
    "verify_preparation_gate",
    "verify_partition_gate",
]
