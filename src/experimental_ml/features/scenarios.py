"""Declarative feature scenarios and catalog management.

Complies with SCN-01 to SCN-08, RF2.2, RF2.3, CA-E2-02, ADR-002, and ADR-008.
Provides immutable FeatureScenario, ScenariosCatalog, and strict anti-leakage validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from experimental_ml.core.enums import StrEnum
from experimental_ml.core.findings import (
    ConfigurationError,
    ContractViolationError,
    DataIntegrityError,
)

_VALID_SLUG_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


class ScenarioMode(StrEnum):
    """Operation mode for a feature scenario."""

    FIXED = "FIXED"
    DYNAMIC = "DYNAMIC"


def _coerce_scenario_mode(val: Any) -> ScenarioMode:
    """Coerce string or ScenarioMode to canonical ScenarioMode."""
    if isinstance(val, ScenarioMode):
        return val
    if isinstance(val, str):
        normalized = val.strip().upper()
        try:
            return ScenarioMode(normalized)
        except ValueError:
            pass
    raise ConfigurationError(
        f"Invalid scenario mode: {val!r}. Allowed modes: {[m.value for m in ScenarioMode]}"
    )


@dataclass(frozen=True, slots=True)
class FeatureScenario:
    """Immutable declarative specification of an experimental feature scenario."""

    scenario_id: str
    name: str
    description: str
    scientific_justification: str
    mode: ScenarioMode | str
    selected_features: tuple[str, ...] = ()
    strategy_name: str | None = None
    strategy_params: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    preprocessing_config: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not isinstance(self.scenario_id, str) or not self.scenario_id.strip():
            raise ConfigurationError(
                f"scenario_id must be a non-empty string, got {self.scenario_id!r}"
            )
        clean_id = self.scenario_id.strip()
        if not _VALID_SLUG_PATTERN.match(clean_id):
            raise ConfigurationError(
                f"scenario_id must consist only of alphanumeric characters, hyphens, and underscores: {clean_id!r}"
            )
        object.__setattr__(self, "scenario_id", clean_id)

        if not isinstance(self.name, str) or not self.name.strip():
            raise ConfigurationError(f"name must be a non-empty string, got {self.name!r}")
        object.__setattr__(self, "name", self.name.strip())

        if not isinstance(self.description, str) or not self.description.strip():
            raise ConfigurationError(f"description must be a non-empty string, got {self.description!r}")
        object.__setattr__(self, "description", self.description.strip())

        if not isinstance(self.scientific_justification, str) or not self.scientific_justification.strip():
            raise ConfigurationError(
                f"scientific_justification must be a non-empty string, got {self.scientific_justification!r}"
            )
        object.__setattr__(self, "scientific_justification", self.scientific_justification.strip())

        coerced_mode = _coerce_scenario_mode(self.mode)
        object.__setattr__(self, "mode", coerced_mode)

        # Enforce mode constraints (SCN-02, SCN-03)
        if coerced_mode == ScenarioMode.FIXED:
            if not self.selected_features:
                raise ConfigurationError(
                    f"Fixed scenario '{clean_id}' requires a non-empty sequence of 'selected_features'."
                )
            # Ensure elements are clean strings and check for duplicates
            feature_tuple = tuple(str(f).strip() for f in self.selected_features)
            if any(not f for f in feature_tuple):
                raise ConfigurationError(
                    f"Fixed scenario '{clean_id}' contains empty feature name in 'selected_features'."
                )
            if len(set(feature_tuple)) != len(feature_tuple):
                raise ConfigurationError(
                    f"Fixed scenario '{clean_id}' contains duplicate features in 'selected_features'."
                )
            object.__setattr__(self, "selected_features", feature_tuple)

            if self.strategy_name is not None and self.strategy_name.strip():
                raise ConfigurationError(
                    f"Fixed scenario '{clean_id}' cannot specify 'strategy_name': {self.strategy_name!r}"
                )
            object.__setattr__(self, "strategy_name", None)

            if bool(self.strategy_params):
                raise ConfigurationError(
                    f"Fixed scenario '{clean_id}' cannot specify non-empty 'strategy_params'."
                )
            object.__setattr__(self, "strategy_params", MappingProxyType({}))

        else:  # ScenarioMode.DYNAMIC
            if not self.strategy_name or not isinstance(self.strategy_name, str) or not self.strategy_name.strip():
                raise ConfigurationError(
                    f"Dynamic scenario '{clean_id}' requires a non-empty 'strategy_name'."
                )
            object.__setattr__(self, "strategy_name", self.strategy_name.strip())

            # Anti-leakage guard: dynamic scenarios must NEVER declare pre-calculated selected_features (SCN-03)
            if bool(self.selected_features):
                raise ContractViolationError(
                    f"Dynamic scenario '{clean_id}' cannot specify 'selected_features'. "
                    "Features must be determined exclusively inside each fold to prevent data leakage (RF2.4, ADR-002)."
                )
            object.__setattr__(self, "selected_features", ())

            if not isinstance(self.strategy_params, MappingProxyType):
                object.__setattr__(self, "strategy_params", MappingProxyType(dict(self.strategy_params)))

        if not isinstance(self.preprocessing_config, MappingProxyType):
            object.__setattr__(self, "preprocessing_config", MappingProxyType(dict(self.preprocessing_config)))

    def to_dict(self) -> dict[str, Any]:
        """Serialize scenario to a JSON-compliant primitive dictionary."""
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "description": self.description,
            "scientific_justification": self.scientific_justification,
            "mode": self.mode.value,
            "selected_features": list(self.selected_features),
            "strategy_name": self.strategy_name,
            "strategy_params": dict(self.strategy_params),
            "preprocessing_config": dict(self.preprocessing_config),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> FeatureScenario:
        """Reconstruct scenario from dictionary representation."""
        return cls(
            scenario_id=data["scenario_id"],
            name=data["name"],
            description=data["description"],
            scientific_justification=data["scientific_justification"],
            mode=data["mode"],
            selected_features=tuple(data.get("selected_features", ())),
            strategy_name=data.get("strategy_name"),
            strategy_params=MappingProxyType(dict(data.get("strategy_params", {}))),
            preprocessing_config=MappingProxyType(dict(data.get("preprocessing_config", {}))),
        )


@dataclass(frozen=True, slots=True)
class ScenariosCatalog:
    """Immutable catalog of validated feature scenarios bound to a sanitized dataset hash."""

    scenarios: tuple[FeatureScenario, ...]
    dataset_hash: str
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not isinstance(self.dataset_hash, str) or not self.dataset_hash.strip():
            raise ConfigurationError("dataset_hash must be a non-empty string.")

        if not isinstance(self.scenarios, tuple):
            object.__setattr__(self, "scenarios", tuple(self.scenarios))

        if not isinstance(self.metadata, MappingProxyType):
            object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, Any]:
        """Serialize catalog to a JSON-compliant primitive dictionary."""
        return {
            "dataset_hash": self.dataset_hash,
            "scenarios": [s.to_dict() for s in self.scenarios],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ScenariosCatalog:
        """Reconstruct catalog from dictionary representation."""
        scenarios = tuple(FeatureScenario.from_dict(item) for item in data.get("scenarios", []))
        return cls(
            scenarios=scenarios,
            dataset_hash=data["dataset_hash"],
            metadata=MappingProxyType(dict(data.get("metadata", {}))),
        )


def validate_scenarios(
    scenarios: Sequence[FeatureScenario],
    view: Any,
) -> ScenariosCatalog:
    """Validate a collection of feature scenarios against a SanitizedDatasetView.

    Verifies scenario_id uniqueness, candidate feature membership, protected column
    disjunction, and binds the resulting catalog to view.dataset_hash (SCN-04, SCN-05).

    Args:
        scenarios: Sequence of FeatureScenario instances to validate.
        view: Validated SanitizedDatasetView from Stage 1 (M2.2).

    Returns:
        Immutable ScenariosCatalog bound to view.dataset_hash.

    Raises:
        ContractViolationError: If view is not a SanitizedDatasetView, or if any scenario
            violates candidate membership or protected column rules.
        ConfigurationError: If scenarios sequence is empty or has duplicate scenario_ids.
    """
    # Duck-typing / type check for SanitizedDatasetView without hard circular imports
    if not hasattr(view, "candidate_feature_cols") or not hasattr(view, "schema") or not hasattr(view, "dataset_hash"):
        raise ContractViolationError(
            f"validate_scenarios requires a SanitizedDatasetView, got {type(view).__name__}"
        )

    if not scenarios:
        raise ConfigurationError("At least one FeatureScenario must be provided.")

    seen_ids: set[str] = set()
    for s in scenarios:
        if not isinstance(s, FeatureScenario):
            raise ContractViolationError(
                f"All elements in scenarios must be FeatureScenario instances, got {type(s).__name__}"
            )
        if s.scenario_id in seen_ids:
            raise ConfigurationError(
                f"Duplicate scenario_id detected: '{s.scenario_id}'"
            )
        seen_ids.add(s.scenario_id)

    schema = view.schema
    candidate_cols = set(view.candidate_feature_cols)

    # Protected columns that must never be used as predictor features
    target_cols = {schema.target_col} if isinstance(schema.target_col, str) else set(schema.target_col)
    group_cols = {schema.group_col} if schema.group_col else set()
    id_cols = {schema.observation_id_col} if schema.observation_id_col else set()
    time_cols = {schema.time_col} if schema.time_col else set()
    ignore_cols = set(schema.ignore_cols) if schema.ignore_cols else set()

    protected_cols = target_cols | group_cols | id_cols | time_cols | ignore_cols

    for s in scenarios:
        if s.mode == ScenarioMode.FIXED:
            for feat in s.selected_features:
                if feat in protected_cols:
                    raise ContractViolationError(
                        f"Fixed scenario '{s.scenario_id}' includes protected column '{feat}' "
                        f"(intersecting with target, group, observation_id, time, or ignore columns)."
                    )
                if feat not in candidate_cols:
                    raise ContractViolationError(
                        f"Fixed scenario '{s.scenario_id}' includes column '{feat}' which is not in candidate_feature_cols."
                    )

    return ScenariosCatalog(
        scenarios=tuple(scenarios),
        dataset_hash=view.dataset_hash,
        metadata=MappingProxyType({"n_scenarios": len(scenarios)}),
    )


__all__ = [
    "ScenarioMode",
    "FeatureScenario",
    "ScenariosCatalog",
    "validate_scenarios",
]
