"""Validation layer for experimental ML framework (Stage 1 / Step 4A).

Exposes immutable partition data models, partitioning algorithms, and mathematical validation.
Complies with CA-E4A-01, CA-E4A-02, ADR-002, ADR-007, and ADR-008.
"""

from __future__ import annotations

from experimental_ml.validation.engine import build_partition_plan
from experimental_ml.validation.types import (
    EvaluationRegime,
    FoldPartition,
    PartitionConfig,
    PartitionPlan,
    PartitionStrategy,
)
from experimental_ml.validation.validators import validate_partition_plan

__all__ = [
    "EvaluationRegime",
    "FoldPartition",
    "PartitionConfig",
    "PartitionPlan",
    "PartitionStrategy",
    "build_partition_plan",
    "validate_partition_plan",
]
