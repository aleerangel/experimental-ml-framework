"""Tabular dataset ingestion, schemas and immutable data bundles.

Exports DatasetSchemaSpec, ColumnSemanticType, DatasetBundle, load_dataset,
and pure functional query/slicing utilities.
"""

from experimental_ml.data.loader import load_dataset
from experimental_ml.data.parsing import (
    SUPPORTED_DELIMITERS,
    detect_delimiter,
    parse_tabular_text,
)
from experimental_ml.data.profiling import (
    ColumnProfile,
    DatasetProfile,
    ProfileConfig,
    profile_dataset,
)
from experimental_ml.data.query import (
    get_column_array,
    slice_bundle_by_observation_ids,
)
from experimental_ml.data.schema import (
    ColumnSemanticType,
    DatasetSchemaSpec,
    validate_schema_spec,
)
from experimental_ml.data.types import (
    ColumnDescriptor,
    DatasetBundle,
)
from experimental_ml.data.validation import (
    assign_or_validate_observation_ids,
    validate_dataset_schema,
)

__all__ = [
    "ColumnSemanticType",
    "DatasetSchemaSpec",
    "validate_schema_spec",
    "ColumnDescriptor",
    "DatasetBundle",
    "ColumnProfile",
    "DatasetProfile",
    "ProfileConfig",
    "profile_dataset",
    "SUPPORTED_DELIMITERS",
    "detect_delimiter",
    "parse_tabular_text",
    "assign_or_validate_observation_ids",
    "validate_dataset_schema",
    "load_dataset",
    "get_column_array",
    "slice_bundle_by_observation_ids",
]
