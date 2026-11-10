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


__all__ = [
    "ScenarioMode",
    "FeatureScenario",
]
