"""Pure functional query and ordered slicing utilities for DatasetBundle.

Provides get_column_array and slice_bundle_by_observation_ids, guaranteeing
pure functional transformations and hash recalculation per ADR-007 and ADR-008.
"""

from __future__ import annotations

import math
from types import MappingProxyType
from typing import Sequence
import unicodedata
import numpy as np

from experimental_ml.core.findings import DataIntegrityError
from experimental_ml.core.hashing import (
    dataset_hash as core_dataset_hash,
    is_missing_scalar,
)
from experimental_ml.core.types import ObservationId
from experimental_ml.data.types import ColumnDescriptor, DatasetBundle


def get_column_array(
    bundle: DatasetBundle,
    col_name: str,
    *,
    copy: bool = False,
) -> np.ndarray:
    """Extract a 1D column array from DatasetBundle.

    Args:
        bundle: Immutable dataset bundle.
        col_name: Name of column to retrieve.
        copy: If False, returns read-only array; if True, returns writeable independent copy.

    Returns:
        1D NumPy ndarray.

    Raises:
        DataIntegrityError: If col_name does not exist in bundle.
    """
    if col_name not in bundle.columns:
        raise DataIntegrityError(
            f"Column '{col_name}' does not exist in DatasetBundle columns: {bundle.column_names}"
        )

    arr = bundle.columns[col_name]
    if copy:
        return arr.copy()
    return arr


def slice_bundle_by_observation_ids(
    bundle: DatasetBundle,
    observation_ids: Sequence[ObservationId | str],
) -> DatasetBundle:
    """Slice DatasetBundle by a sequence of ObservationIds, strictly preserving caller's order.

    Recalculates n_rows, descriptors, and in-memory dataset_hash.

    Args:
        bundle: Source dataset bundle to slice.
        observation_ids: Non-empty sequence of valid ObservationIds or non-empty strings.

    Returns:
        New immutable DatasetBundle containing sliced observations.

    Raises:
        DataIntegrityError: If observation_ids is bare string/bytes, empty, contains invalid
            identifiers, duplicates, or unknown IDs.
    """
    if isinstance(observation_ids, (str, bytes, bytearray, memoryview)) or not isinstance(
        observation_ids, Sequence
    ):
        raise DataIntegrityError(
            f"observation_ids must be a non-string Sequence, got {type(observation_ids).__name__}"
        )

    if len(observation_ids) == 0:
        raise DataIntegrityError("observation_ids sequence cannot be empty")

    # Validate, convert elements and check duplicates
    validated_ids: list[ObservationId] = []
    seen: set[ObservationId] = set()
    bundle_obs_index: dict[ObservationId, int] = {
        obs: idx for idx, obs in enumerate(bundle.observation_ids)
    }
    indices: list[int] = []

    for item in observation_ids:
        if isinstance(item, ObservationId):
            obs_id = item
        elif isinstance(item, str):
            norm_str = unicodedata.normalize("NFC", item.strip())
            try:
                obs_id = ObservationId(norm_str)
            except ValueError as err:
                raise DataIntegrityError(
                    f"Invalid ObservationId string format '{item}': {err}"
                ) from err
        else:
            raise DataIntegrityError(
                f"Invalid observation_id element type '{type(item).__name__}': expected ObservationId or str"
            )

        if obs_id in seen:
            raise DataIntegrityError(
                f"Duplicate ObservationId '{obs_id}' encountered in requested slicing sequence"
            )
        seen.add(obs_id)

        if obs_id not in bundle_obs_index:
            raise DataIntegrityError(
                f"ObservationId '{obs_id}' not present in DatasetBundle observation_ids"
            )
        indices.append(bundle_obs_index[obs_id])
        validated_ids.append(obs_id)

    idx_arr = np.array(indices, dtype=np.intp)
    new_n_rows = len(indices)
    sliced_obs_ids = tuple(validated_ids)

    new_columns: dict[str, np.ndarray] = {}
    new_descriptors: dict[str, ColumnDescriptor] = {}
    total_memory_bytes = 0

    for col_name in bundle.column_names:
        old_arr = bundle.columns[col_name]
        sliced_arr = old_arr[idx_arr]

        if sliced_arr.dtype == object:
            sliced_arr.flags.writeable = False
            col_immutable = sliced_arr
            n_missing = sum(1 for v in col_immutable if is_missing_scalar(v))
        else:
            raw_bytes = sliced_arr.tobytes()
            col_immutable = np.frombuffer(raw_bytes, dtype=sliced_arr.dtype)
            if col_immutable.dtype == np.float64:
                n_missing = int(np.isnan(col_immutable).sum())
            else:
                n_missing = 0

        new_columns[col_name] = col_immutable
        col_bytes = col_immutable.nbytes
        total_memory_bytes += col_bytes

        old_desc = bundle.descriptors[col_name]
        new_descriptors[col_name] = ColumnDescriptor(
            name=old_desc.name,
            index=old_desc.index,
            role=old_desc.role,
            physical_type=old_desc.physical_type,
            semantic_type=old_desc.semantic_type,
            is_semantic_declared=old_desc.is_semantic_declared,
            n_missing=n_missing,
            memory_bytes=col_bytes,
        )

    # Recalculate canonical in-memory dataset_hash (HARD-04)
    new_dataset_hash = core_dataset_hash(
        new_columns,
        bundle.schema,
        observation_ids=sliced_obs_ids,
    )

    return DatasetBundle(
        schema=bundle.schema,
        n_rows=new_n_rows,
        n_cols=bundle.n_cols,
        column_names=bundle.column_names,
        feature_cols=bundle.feature_cols,
        columns=MappingProxyType(new_columns),
        descriptors=MappingProxyType(new_descriptors),
        observation_ids=sliced_obs_ids,
        dataset_hash=new_dataset_hash,
        raw_source_hash=bundle.raw_source_hash,
        schema_hash=bundle.schema_hash,
        memory_bytes=total_memory_bytes,
        source_path=bundle.source_path,
    )
