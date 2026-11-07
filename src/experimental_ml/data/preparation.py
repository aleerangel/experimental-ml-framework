"""Data preparation plan and sanitized dataset view.

Implements declarative preparation planning and strict pre-partition sanitization,
enforcing ADR-002 (no data leakage) and zero silent mutations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from types import MappingProxyType
from typing import Any, Literal, Mapping, Sequence

import numpy as np

from experimental_ml.core.enums import FindingSeverity
from experimental_ml.core.findings import ConfigurationError, ContractViolationError, DataIntegrityError
from experimental_ml.core.hashing import dataset_hash as core_dataset_hash, is_missing_scalar
from experimental_ml.core.types import ObservationId
from experimental_ml.data.profiling import DatasetProfile
from experimental_ml.data.schema import DatasetSchemaSpec
from experimental_ml.data.types import DatasetBundle

FindingCode = str

RuleKind = Literal[
    "DROP_ROWS",
    "EXCLUDE_COLUMN",
    "MAP_BINARY_TARGET",
    "DEFER_INTRA_FOLD",
    "ACCEPT_AS_IS",
]

PlanStatus = Literal["READY", "INCOMPLETE"]


@dataclass(frozen=True, slots=True)
class PreparationRule:
    """Explicit preparation rule targeting a confirmed diagnostic finding."""

    finding_code: FindingCode
    column: str | None
    kind: RuleKind
    parameters: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not isinstance(self.parameters, MappingProxyType):
            object.__setattr__(
                self,
                "parameters",
                MappingProxyType(dict(self.parameters) if self.parameters else {}),
            )


@dataclass(frozen=True, slots=True)
class UnresolvedFinding:
    """Diagnostic finding that lacks an admissible preparation rule."""

    finding_code: FindingCode
    column: str | None
    reason: str


@dataclass(frozen=True, slots=True)
class PreparationPlan:
    """Deterministic preparation plan binding profile diagnostics to explicit rules."""

    status: PlanStatus
    source_dataset_hash: str
    source_profile_digest: str
    rules: tuple[PreparationRule, ...] = ()
    unresolved_findings: tuple[UnresolvedFinding, ...] = ()
    plan_digest: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.rules, tuple):
            object.__setattr__(self, "rules", tuple(self.rules))
        if not isinstance(self.unresolved_findings, tuple):
            object.__setattr__(self, "unresolved_findings", tuple(self.unresolved_findings))


@dataclass(frozen=True, slots=True)
class SanitizedDatasetView:
    """Immutable view of sanitized dataset post pre-partition structural preparation."""

    columns: Mapping[str, np.ndarray]
    schema: DatasetSchemaSpec
    observation_ids: tuple[ObservationId, ...]
    candidate_feature_cols: tuple[str, ...]
    dropped_observation_ids: tuple[ObservationId, ...]
    target_label_mapping: Mapping[Any, int] | None
    deferred_rules: tuple[PreparationRule, ...]
    source_dataset_hash: str
    source_plan_digest: str
    dataset_hash: str

    def __post_init__(self) -> None:
        if not isinstance(self.columns, MappingProxyType):
            object.__setattr__(self, "columns", MappingProxyType(dict(self.columns)))
        if not isinstance(self.observation_ids, tuple):
            object.__setattr__(self, "observation_ids", tuple(self.observation_ids))
        if not isinstance(self.candidate_feature_cols, tuple):
            object.__setattr__(self, "candidate_feature_cols", tuple(self.candidate_feature_cols))
        if not isinstance(self.dropped_observation_ids, tuple):
            object.__setattr__(self, "dropped_observation_ids", tuple(self.dropped_observation_ids))
        if not isinstance(self.deferred_rules, tuple):
            object.__setattr__(self, "deferred_rules", tuple(self.deferred_rules))
        if self.target_label_mapping is not None and not isinstance(self.target_label_mapping, MappingProxyType):
            object.__setattr__(
                self,
                "target_label_mapping",
                MappingProxyType(dict(self.target_label_mapping)),
            )


IRRESOLVABLE_FINDING_CODES: frozenset[str] = frozenset(
    {
        "E1_TARGET_ALL_MISSING",
        "E1_TARGET_ZERO_VARIANCE",
        "E1_TARGET_CLASS_COUNT_INVALID",
        "E1_TARGET_NOT_NUMERIC",
    }
)

VALID_RULE_KINDS: frozenset[str] = frozenset(
    {
        "DROP_ROWS",
        "EXCLUDE_COLUMN",
        "MAP_BINARY_TARGET",
        "DEFER_INTRA_FOLD",
        "ACCEPT_AS_IS",
    }
)

ADMISSIBLE_RULES_BY_CODE: dict[str, frozenset[str]] = {
    "E1_TARGET_MISSING": frozenset({"DROP_ROWS"}),
    "E1_GROUP_MISSING": frozenset({"DROP_ROWS"}),
    "E1_GROUP_EMPTY_VALUES": frozenset({"DROP_ROWS"}),
    "E1_FEATURE_MISSING": frozenset({"DROP_ROWS", "EXCLUDE_COLUMN", "DEFER_INTRA_FOLD", "ACCEPT_AS_IS"}),
    "E1_CONSTANT_COLUMN": frozenset({"EXCLUDE_COLUMN", "ACCEPT_AS_IS"}),
    "E1_CONSTANT_FEATURE_COLUMN": frozenset({"EXCLUDE_COLUMN", "ACCEPT_AS_IS"}),
    "E1_COLUMN_ALL_MISSING": frozenset({"EXCLUDE_COLUMN", "ACCEPT_AS_IS"}),
    "E1_IDENTIFIER_COLUMN_SUSPECTED": frozenset({"EXCLUDE_COLUMN", "ACCEPT_AS_IS"}),
    "E1_CATEGORICAL_UNENCODED": frozenset({"EXCLUDE_COLUMN", "DEFER_INTRA_FOLD", "ACCEPT_AS_IS"}),
    "E1_TARGET_BINARY_UNMAPPED": frozenset({"MAP_BINARY_TARGET"}),
}


def _validate_rule_admissibility(rule: PreparationRule, profile: DatasetProfile) -> None:
    """Validate a preparation rule against profile findings and the closed catalog.

    Raises:
        ConfigurationError: If the rule targets an invalid, non-confirmed, or irresolvable
            finding, uses an inadmissible rule kind, targets a protected column for exclusion,
            or carries invalid parameters.
    """
    if rule.kind not in VALID_RULE_KINDS:
        raise ConfigurationError(
            f"Invalid rule kind '{rule.kind}'. Allowed kinds: {sorted(VALID_RULE_KINDS)}"
        )

    # 1. Check if finding exists in profile and verify severity
    matching_findings = [
        f for f in profile.findings
        if f.code == rule.finding_code and f.context.get("column") == rule.column
    ]
    if not matching_findings:
        raise ConfigurationError(
            f"Rule targets non-existent finding ({rule.finding_code}, column={rule.column!r}) in profile"
        )

    finding = matching_findings[0]
    if finding.severity != FindingSeverity.CONFIRMED_ISSUE:
        raise ConfigurationError(
            f"Rule targets finding ({rule.finding_code}, column={rule.column!r}) with severity "
            f"'{finding.severity.value}', but only CONFIRMED_ISSUE can be targeted by preparation rules"
        )

    # 2. Check for irresolvable finding codes
    if rule.finding_code in IRRESOLVABLE_FINDING_CODES:
        raise ConfigurationError(
            f"Finding '{rule.finding_code}' is irresolvable and accepts no preparation rules"
        )

    # 3. Check admissibility catalog
    admissible_kinds = ADMISSIBLE_RULES_BY_CODE.get(rule.finding_code)
    if admissible_kinds is None or rule.kind not in admissible_kinds:
        raise ConfigurationError(
            f"Rule kind '{rule.kind}' is not admissible for finding '{rule.finding_code}'. "
            f"Admissible kinds: {sorted(admissible_kinds) if admissible_kinds else 'none'}"
        )

    # 4. EXCLUDE_COLUMN checks on protected columns
    if rule.kind == "EXCLUDE_COLUMN":
        if rule.column == profile.target.column_name:
            raise ConfigurationError("Cannot apply EXCLUDE_COLUMN to target column")
        if profile.groups is not None and rule.column == profile.groups.group_col:
            raise ConfigurationError("Cannot apply EXCLUDE_COLUMN to group column")
        if rule.column is None:
            raise ConfigurationError("EXCLUDE_COLUMN requires a non-None column")

    # 5. MAP_BINARY_TARGET checks
    elif rule.kind == "MAP_BINARY_TARGET":
        if "positive_label" not in rule.parameters:
            raise ConfigurationError("MAP_BINARY_TARGET requires 'positive_label' parameter")
        pos_label = rule.parameters["positive_label"]
        if profile.target.class_frequencies is not None:
            observed_classes = [cf.value for cf in profile.target.class_frequencies]
            if pos_label not in observed_classes:
                raise ConfigurationError(
                    f"positive_label {pos_label!r} not found in target observed classes: {observed_classes}"
                )

    # 6. DEFER_INTRA_FOLD checks
    elif rule.kind == "DEFER_INTRA_FOLD":
        if rule.finding_code == "E1_FEATURE_MISSING":
            strategy = rule.parameters.get("imputation_strategy")
            if strategy not in ("MEAN", "MEDIAN", "MODE"):
                raise ConfigurationError(
                    f"DEFER_INTRA_FOLD for E1_FEATURE_MISSING requires 'imputation_strategy' in "
                    f"('MEAN', 'MEDIAN', 'MODE'), got {strategy!r}"
                )
        elif rule.finding_code == "E1_CATEGORICAL_UNENCODED":
            encoding = rule.parameters.get("encoding_strategy")
            if not isinstance(encoding, str) or not encoding.strip():
                raise ConfigurationError(
                    "DEFER_INTRA_FOLD for E1_CATEGORICAL_UNENCODED requires non-empty string 'encoding_strategy'"
                )


def _compute_profile_digest(profile: DatasetProfile) -> str:
    """Compute canonical SHA-256 digest of DatasetProfile findings and structure."""
    items = [
        f"{f.severity.value}:{f.code}:{f.context.get('column')}:{f.message}"
        for f in sorted(
            profile.findings,
            key=lambda x: (x.severity.value, x.code, str(x.context.get("column") or ""), x.message),
        )
    ]
    content = f"{profile.source_dataset_hash}|{profile.n_rows}|{profile.n_cols}|" + ";".join(items)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _compute_plan_digest(
    source_dataset_hash: str,
    profile_digest: str,
    rules: tuple[PreparationRule, ...],
) -> str:
    """Compute canonical SHA-256 digest of a READY PreparationPlan."""
    rule_strs = [
        f"{r.finding_code}:{r.column}:{r.kind}:{json.dumps(dict(r.parameters), sort_keys=True)}"
        for r in rules
    ]
    content = f"{source_dataset_hash}|{profile_digest}|" + ";".join(rule_strs)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def create_preparation_plan(
    profile: DatasetProfile,
    rules: Sequence[PreparationRule | dict[str, Any]],
) -> PreparationPlan:
    """Create a deterministic preparation plan from profile findings and user rules.

    Audits all confirmed issues against provided rules. If all confirmed issues are
    covered by admissible rules, returns status 'READY' with canonical digest.
    If any confirmed issue is uncovered or irresolvable, returns status 'INCOMPLETE'.

    Args:
        profile: DatasetProfile generated from dataset profiling.
        rules: Sequence of PreparationRule instances or dict specifications.

    Returns:
        Immutable PreparationPlan.

    Raises:
        ConfigurationError: If any rule targets an invalid finding, is duplicate,
            is inadmissible, or contains invalid parameters.
    """
    # 1. Coerce rules
    parsed_rules: list[PreparationRule] = []
    seen_targets: set[tuple[str, str | None]] = set()

    for r in rules:
        if isinstance(r, dict):
            rule_obj = PreparationRule(
                finding_code=r["finding_code"],
                column=r.get("column"),
                kind=r["kind"],
                parameters=r.get("parameters", {}),
            )
        elif isinstance(r, PreparationRule):
            rule_obj = r
        else:
            raise ConfigurationError(
                f"Expected PreparationRule or dict, got {type(r).__name__}"
            )

        target_key = (rule_obj.finding_code, rule_obj.column)
        if target_key in seen_targets:
            raise ConfigurationError(
                f"Duplicate preparation rule targeting finding ({rule_obj.finding_code}, column={rule_obj.column!r})"
            )
        seen_targets.add(target_key)

        # Validate admissibility against profile
        _validate_rule_admissibility(rule_obj, profile)
        parsed_rules.append(rule_obj)

    # 2. Check coverage of all confirmed issues in profile
    confirmed_findings = [
        f for f in profile.findings
        if f.severity == FindingSeverity.CONFIRMED_ISSUE
    ]

    unresolved_list: list[UnresolvedFinding] = []
    covered_keys = { (r.finding_code, r.column) for r in parsed_rules }

    for finding in confirmed_findings:
        col = finding.context.get("column")
        f_key = (finding.code, col)

        if finding.code in IRRESOLVABLE_FINDING_CODES:
            unresolved_list.append(
                UnresolvedFinding(
                    finding_code=finding.code,
                    column=col,
                    reason=f"Finding '{finding.code}' is irresolvable and cannot be fixed by preparation rules.",
                )
            )
        elif f_key not in covered_keys:
            unresolved_list.append(
                UnresolvedFinding(
                    finding_code=finding.code,
                    column=col,
                    reason=f"Confirmed issue '{finding.code}' on column {col!r} has no assigned preparation rule.",
                )
            )

    # 3. Canonical ordering
    sorted_rules = tuple(
        sorted(
            parsed_rules,
            key=lambda r: (r.finding_code, r.column or "", r.kind),
        )
    )
    sorted_unresolved = tuple(
        sorted(
            unresolved_list,
            key=lambda u: (u.finding_code, u.column or ""),
        )
    )

    profile_digest = _compute_profile_digest(profile)

    if sorted_unresolved:
        return PreparationPlan(
            status="INCOMPLETE",
            source_dataset_hash=profile.source_dataset_hash,
            source_profile_digest=profile_digest,
            rules=sorted_rules,
            unresolved_findings=sorted_unresolved,
            plan_digest="",
        )

    plan_digest = _compute_plan_digest(
        source_dataset_hash=profile.source_dataset_hash,
        profile_digest=profile_digest,
        rules=sorted_rules,
    )

    return PreparationPlan(
        status="READY",
        source_dataset_hash=profile.source_dataset_hash,
        source_profile_digest=profile_digest,
        rules=sorted_rules,
        unresolved_findings=(),
        plan_digest=plan_digest,
    )


def _is_missing_array_mask(arr: np.ndarray) -> np.ndarray:
    """Return boolean mask where True indicates a missing value."""
    if arr.dtype.kind == "f":
        return np.isnan(arr)
    return np.array([is_missing_scalar(v) for v in arr], dtype=bool)


def sanitize_dataset(
    bundle: DatasetBundle,
    profile: DatasetProfile,
    plan: PreparationPlan,
) -> SanitizedDatasetView:
    """Execute pre-partition dataset sanitization based on an approved READY plan.

    Applies strictly pre-partition structural rules:
    - DROP_ROWS: filters rows with missing values for specified columns.
    - EXCLUDE_COLUMN: excludes columns from output columns and candidate features.
    - MAP_BINARY_TARGET: encodes unmapped binary target into int64 {0, 1}.

    Preserves 100% bit-identical values for columns with DEFER_INTRA_FOLD and ACCEPT_AS_IS
    (ADR-002: no global imputation or encoding before fold splitting).

    Args:
        bundle: Source immutable DatasetBundle.
        profile: DatasetProfile corresponding to bundle.
        plan: PreparationPlan with status 'READY'.

    Returns:
        Immutable SanitizedDatasetView.

    Raises:
        ContractViolationError: If plan.status != 'READY'.
        DataIntegrityError: If bundle, profile or plan hashes/digests do not match,
            or if sanitization leaves 0 observations or 0 candidate feature columns.
    """
    if plan.status != "READY":
        raise ContractViolationError(
            f"Cannot sanitize dataset with plan status '{plan.status}'; status must be 'READY'"
        )

    if plan.source_dataset_hash != bundle.dataset_hash:
        raise DataIntegrityError(
            f"Plan source_dataset_hash '{plan.source_dataset_hash}' does not match "
            f"bundle.dataset_hash '{bundle.dataset_hash}'"
        )

    if profile.source_dataset_hash != bundle.dataset_hash:
        raise DataIntegrityError(
            f"Profile source_dataset_hash '{profile.source_dataset_hash}' does not match "
            f"bundle.dataset_hash '{bundle.dataset_hash}'"
        )

    current_profile_digest = _compute_profile_digest(profile)
    if plan.source_profile_digest != current_profile_digest:
        raise DataIntegrityError(
            f"Plan source_profile_digest '{plan.source_profile_digest}' does not match "
            f"computed profile digest '{current_profile_digest}'"
        )

    # 1. Identify rules
    drop_rows_cols: list[str] = []
    excluded_cols: set[str] = set()
    map_binary_rule: PreparationRule | None = None
    deferred_rules: list[PreparationRule] = []

    for rule in plan.rules:
        if rule.kind == "DROP_ROWS":
            if rule.column:
                drop_rows_cols.append(rule.column)
        elif rule.kind == "EXCLUDE_COLUMN":
            if rule.column:
                excluded_cols.add(rule.column)
        elif rule.kind == "MAP_BINARY_TARGET":
            map_binary_rule = rule
        elif rule.kind in ("DEFER_INTRA_FOLD", "ACCEPT_AS_IS"):
            deferred_rules.append(rule)

    # 2. Compute keep mask for rows (DROP_ROWS)
    keep_mask = np.ones(bundle.n_rows, dtype=bool)
    for col_name in drop_rows_cols:
        if col_name in bundle.columns:
            missing_mask = _is_missing_array_mask(bundle.columns[col_name])
            keep_mask &= ~missing_mask

    kept_indices = np.where(keep_mask)[0]
    dropped_indices = np.where(~keep_mask)[0]

    if len(kept_indices) == 0:
        raise DataIntegrityError(
            "Sanitization resulted in 0 observations after applying DROP_ROWS"
        )

    # Preserve original relative order
    kept_obs_ids = tuple(bundle.observation_ids[i] for i in kept_indices)
    dropped_obs_ids = tuple(bundle.observation_ids[i] for i in dropped_indices)

    # 3. Process columns
    output_columns: dict[str, np.ndarray] = {}
    target_col = bundle.schema.target_col
    target_label_mapping: dict[Any, int] | None = None

    for col_name, arr in bundle.columns.items():
        if col_name in excluded_cols:
            continue

        sliced = arr[kept_indices]

        if col_name == target_col and map_binary_rule is not None:
            pos_label = map_binary_rule.parameters["positive_label"]
            unique_classes = set(sliced)
            if pos_label not in unique_classes:
                raise DataIntegrityError(
                    f"MAP_BINARY_TARGET positive_label {pos_label!r} not in sliced target classes: {unique_classes}"
                )
            alt_classes = unique_classes - {pos_label}
            if len(alt_classes) != 1:
                raise DataIntegrityError(
                    f"MAP_BINARY_TARGET expected exactly 2 target classes in remaining rows, found: {unique_classes}"
                )
            neg_label = next(iter(alt_classes))

            mapped_arr = np.empty(len(sliced), dtype=np.int64)
            mapped_arr[sliced == pos_label] = 1
            mapped_arr[sliced == neg_label] = 0
            mapped_arr.flags.writeable = False
            output_columns[col_name] = mapped_arr
            target_label_mapping = {pos_label: 1, neg_label: 0}
        else:
            # Preserve bit-identical values (including DEFER_INTRA_FOLD and ACCEPT_AS_IS)
            out_arr = np.copy(sliced)
            out_arr.flags.writeable = False
            output_columns[col_name] = out_arr

    # 4. Compute candidate feature columns and clean schema
    schema = bundle.schema
    clean_semantic_types = {
        col: st for col, st in schema.column_semantic_types.items()
        if col not in excluded_cols
    }
    view_schema = DatasetSchemaSpec(
        target_col=schema.target_col,
        task_type=schema.task_type,
        group_col=schema.group_col,
        observation_id_col=schema.observation_id_col,
        time_col=schema.time_col,
        ignore_cols=schema.ignore_cols,
        column_semantic_types=clean_semantic_types,
    )

    protected_or_non_feature: set[str] = {schema.target_col}
    if schema.group_col:
        protected_or_non_feature.add(schema.group_col)
    if schema.observation_id_col:
        protected_or_non_feature.add(schema.observation_id_col)
    if schema.time_col:
        protected_or_non_feature.add(schema.time_col)
    protected_or_non_feature.update(schema.ignore_cols)
    protected_or_non_feature.update(excluded_cols)

    candidate_features = tuple(
        c for c in bundle.column_names
        if c in output_columns and c not in protected_or_non_feature
    )

    if len(candidate_features) == 0:
        raise DataIntegrityError(
            "Sanitization resulted in 0 candidate feature columns"
        )

    # 5. Compute canonical sanitized dataset hash (PREP-06)
    view_hash = core_dataset_hash(
        output_columns,
        view_schema,
        observation_ids=kept_obs_ids,
    )

    return SanitizedDatasetView(
        columns=output_columns,
        schema=view_schema,
        observation_ids=kept_obs_ids,
        candidate_feature_cols=candidate_features,
        dropped_observation_ids=dropped_obs_ids,
        target_label_mapping=target_label_mapping,
        deferred_rules=tuple(deferred_rules),
        source_dataset_hash=bundle.dataset_hash,
        source_plan_digest=plan.plan_digest,
        dataset_hash=view_hash,
    )
