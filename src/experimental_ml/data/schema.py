"""Dataset schema specification and semantic typing.

Defines DatasetSchemaSpec, ColumnSemanticType and schema syntactic validation,
enforcing column role disjunction, Unicode NFC normalization, and strict
isolation against Wave 2 features during Wave 1 MVP.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping
import unicodedata

from experimental_ml.core.enums import StrEnum, TaskType
from experimental_ml.core.findings import ConfigurationError
from experimental_ml.core.storage import read_json


class ColumnSemanticType(StrEnum):
    """Canonical semantic types for tabular dataset columns."""

    NUMERIC_CONTINUOUS = "NUMERIC_CONTINUOUS"
    NUMERIC_DISCRETE = "NUMERIC_DISCRETE"
    CATEGORICAL = "CATEGORICAL"
    BOOLEAN = "BOOLEAN"
    TEMPORAL = "TEMPORAL"
    IDENTIFIER = "IDENTIFIER"


def _validate_and_normalize_col_name(name: Any, role_label: str) -> str:
    """Validate and normalize a column name with Unicode NFC."""
    if not isinstance(name, str):
        raise ConfigurationError(
            f"{role_label} must be a string, got {type(name).__name__}"
        )
    if not name or not name.strip():
        raise ConfigurationError(
            f"{role_label} cannot be empty or whitespace-only"
        )
    for forbidden in ("\n", "\r", "\t", "\x00"):
        if forbidden in name:
            raise ConfigurationError(
                f"{role_label} contains forbidden control or newline characters: {repr(name)}"
            )
    return unicodedata.normalize("NFC", name)


@dataclass(frozen=True, slots=True)
class DatasetSchemaSpec:
    """Immutable schema specification defining variable roles and semantic types.

    Complies with ADR-007, ADR-008, RF1.1 and CA-E1-01:
    - Immutable frozen dataclass with slots.
    - Strict disjunction across variable roles (target, group, observation_id, time, ignore).
    - Unicode NFC normalization for all column names.
    - Protection against Wave 2 feature leakage during Wave 1 MVP.
    """

    target_col: str
    task_type: TaskType
    group_col: str | None = None
    observation_id_col: str | None = None
    time_col: str | None = None
    ignore_cols: tuple[str, ...] = ()
    column_semantic_types: Mapping[str, ColumnSemanticType] = field(default_factory=dict)
    target_transform_spec: Any | None = None

    def __post_init__(self) -> None:
        # 1. Target column validation
        target_norm = _validate_and_normalize_col_name(self.target_col, "target_col")
        object.__setattr__(self, "target_col", target_norm)

        # 2. Task type validation & Wave 2 guard
        if not isinstance(self.task_type, TaskType):
            try:
                task_norm = TaskType(self.task_type)
            except Exception as err:
                raise ConfigurationError(
                    f"Invalid task_type: {self.task_type}"
                ) from err
        else:
            task_norm = self.task_type

        if task_norm == TaskType.MULTI_TARGET_REGRESSION:
            raise ConfigurationError(
                "TaskType.MULTI_TARGET_REGRESSION is a Wave 2 feature not supported in Wave 1 MVP"
            )
        object.__setattr__(self, "task_type", task_norm)

        # 3. Wave 2 target_transform_spec guard
        if self.target_transform_spec is not None:
            raise ConfigurationError(
                "target_transform_spec is a Wave 2 feature not supported in Wave 1 MVP"
            )

        # 4. Optional column roles validation & normalization
        if self.group_col is not None:
            group_norm = _validate_and_normalize_col_name(self.group_col, "group_col")
            object.__setattr__(self, "group_col", group_norm)

        if self.observation_id_col is not None:
            obs_norm = _validate_and_normalize_col_name(
                self.observation_id_col, "observation_id_col"
            )
            object.__setattr__(self, "observation_id_col", obs_norm)

        if self.time_col is not None:
            time_norm = _validate_and_normalize_col_name(self.time_col, "time_col")
            object.__setattr__(self, "time_col", time_norm)

        # 5. ignore_cols validation, NFC normalization and deduplication preserving order
        if self.ignore_cols:
            normalized_ignore: list[str] = []
            for item in self.ignore_cols:
                norm_item = _validate_and_normalize_col_name(item, "ignore_cols element")
                if norm_item not in normalized_ignore:
                    normalized_ignore.append(norm_item)
            object.__setattr__(self, "ignore_cols", tuple(normalized_ignore))
        else:
            object.__setattr__(self, "ignore_cols", ())

        # 6. column_semantic_types validation, NFC keys, and MappingProxyType encapsulation
        if self.column_semantic_types:
            normalized_sem: dict[str, ColumnSemanticType] = {}
            for k, v in self.column_semantic_types.items():
                k_norm = _validate_and_normalize_col_name(k, "column_semantic_types key")
                if not isinstance(v, ColumnSemanticType):
                    try:
                        v_norm = ColumnSemanticType(v)
                    except Exception as err:
                        raise ConfigurationError(
                            f"Invalid ColumnSemanticType for '{k}': {v}"
                        ) from err
                else:
                    v_norm = v
                normalized_sem[k_norm] = v_norm
            object.__setattr__(self, "column_semantic_types", MappingProxyType(normalized_sem))
        else:
            object.__setattr__(self, "column_semantic_types", MappingProxyType({}))

        # 7. Strict pairwise disjunction of structural roles (DATA-05)
        role_occurrences: list[tuple[str, str]] = [("target_col", self.target_col)]
        if self.group_col is not None:
            role_occurrences.append(("group_col", self.group_col))
        if self.observation_id_col is not None:
            role_occurrences.append(("observation_id_col", self.observation_id_col))
        if self.time_col is not None:
            role_occurrences.append(("time_col", self.time_col))
        for item in self.ignore_cols:
            role_occurrences.append(("ignore_cols", item))

        seen_roles: dict[str, str] = {}
        for role_name, col_name in role_occurrences:
            if col_name in seen_roles:
                raise ConfigurationError(
                    f"Column '{col_name}' cannot be assigned to multiple roles: "
                    f"'{seen_roles[col_name]}' and '{role_name}'"
                )
            seen_roles[col_name] = role_name


def validate_schema_spec(schema: Any) -> None:
    """Validate that the provided schema is an instance of DatasetSchemaSpec.

    Raises:
        ConfigurationError: If schema is not a DatasetSchemaSpec.
    """
    if not isinstance(schema, DatasetSchemaSpec):
        raise ConfigurationError(
            f"Expected DatasetSchemaSpec instance, got {type(schema).__name__}"
        )


def load_schema_spec(schema_path: Path | str) -> DatasetSchemaSpec:
    """Load and parse DatasetSchemaSpec from a JSON file.

    Raises:
        ConfigurationError: If schema file is not found or has invalid syntax/content.
    """
    p = Path(schema_path).resolve()
    if not p.exists():
        raise ConfigurationError(f"Schema file not found at '{p}'")
    try:
        data = read_json(p)
    except Exception as err:
        raise ConfigurationError(f"Failed to read schema file '{p}': {err}") from err

    task_type = None
    if data.get("task_type"):
        try:
            task_type = TaskType(data["task_type"])
        except ValueError as err:
            raise ConfigurationError(f"Invalid task_type in schema: {err}") from err

    semantic_types = None
    if data.get("column_semantic_types"):
        try:
            semantic_types = {
                col: ColumnSemanticType(st) for col, st in data["column_semantic_types"].items()
            }
        except ValueError as err:
            raise ConfigurationError(f"Invalid column_semantic_types in schema: {err}") from err

    return DatasetSchemaSpec(
        target_col=data.get("target_col"),
        task_type=task_type,
        column_semantic_types=semantic_types,
        group_col=data.get("group_col"),
        time_col=data.get("time_col"),
        observation_id_col=data.get("observation_id_col"),
        ignore_cols=tuple(data.get("ignore_cols", ())),
    )
