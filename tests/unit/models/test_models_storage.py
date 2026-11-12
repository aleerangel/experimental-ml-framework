"""Unit tests for ModelsCatalog atomic storage and loading (MPC-03)."""

from pathlib import Path
import pytest

from experimental_ml.core.findings import ConfigurationError
from experimental_ml.models.baselines import DummyBaselineModel
from experimental_ml.models.catalog import ModelsCatalog
from experimental_ml.models.spec import ModelSpec
from experimental_ml.models.storage import load_models_catalog, save_models_catalog
from experimental_ml.models.types import ModelCapabilities, ModelFamily


def _create_sample_catalog() -> ModelsCatalog:
    spec = ModelSpec(
        model_id="dummy_mean",
        display_name="Dummy Mean Regressor",
        family=ModelFamily.BASELINE,
        estimator_factory=lambda seed: DummyBaselineModel(strategy="mean"),
        capabilities=ModelCapabilities(requires_fit=True),
        description="Predicts y_train mean",
        scientific_justification="Minimal baseline reference",
    )
    return ModelsCatalog(models=[spec], metadata={"test": "sample"})


def test_m44_03_01_save_and_load_roundtrip(tmp_path: Path) -> None:
    """C7: save_models_catalog writes catalog atomically and load_models_catalog restores it."""
    catalog = _create_sample_catalog()
    dest = tmp_path / "models.json"

    saved_path = save_models_catalog(catalog, dest)
    assert saved_path == dest.resolve()
    assert dest.exists()

    loaded = load_models_catalog(dest)
    assert len(loaded.models) == 1
    assert loaded.models[0].model_id == "dummy_mean"
    assert loaded.metadata["test"] == "sample"
    assert loaded.catalog_hash == catalog.catalog_hash


def test_m44_03_02_save_overwrite_guard(tmp_path: Path) -> None:
    """C8: save_models_catalog raises ConfigurationError on existing file when overwrite=False."""
    catalog = _create_sample_catalog()
    dest = tmp_path / "models.json"

    # First write succeeds
    save_models_catalog(catalog, dest)
    assert dest.exists()

    # Second write without overwrite fails
    with pytest.raises(ConfigurationError, match="already exists"):
        save_models_catalog(catalog, dest, overwrite=False)

    # Second write with overwrite=True succeeds
    save_models_catalog(catalog, dest, overwrite=True)
    assert dest.exists()


def test_m44_03_03_load_missing_or_corrupt(tmp_path: Path) -> None:
    """C9: load_models_catalog raises ConfigurationError on missing or corrupt file."""
    # 1. Missing file
    missing_file = tmp_path / "non_existent.json"
    with pytest.raises(ConfigurationError, match="file not found"):
        load_models_catalog(missing_file)

    # 2. Corrupt / invalid JSON structure
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("{\"not_models\": 123}", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="must contain a 'models' list"):
        load_models_catalog(corrupt_file)
