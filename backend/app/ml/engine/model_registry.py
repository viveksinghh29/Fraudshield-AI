"""Manages versioned model artifacts, metadata, thresholds, scalers, and SHAP data for consistent inference."""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.preprocessing import RobustScaler
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.pipeline.feature_engineering import get_model_feature_columns
from app.repositories.model_version_repository import ModelVersionRepository

BACKGROUND_SAMPLE_SIZE = 100


def save_model_artifact(
    *,
    model: Any,
    optimal_threshold: float,
    scaler: RobustScaler,
    background_sample: pd.DataFrame,
    artifact_dir: str | Path,
    version_tag: str,
) -> str:
    """
    Serializes {model, feature_columns, optimal_threshold, scaler,
    background_sample} as one joblib artifact. Returns the artifact's
    path as a string, ready to store in the `model_versions.artifact_path`
    column.

    Args:
        scaler: the RobustScaler fit on this training run's train
            split (Phase 5/6) -- must be reused unchanged at inference,
            never refit on incoming transactions.
        background_sample: a small reference sample of training-feature
            rows, used by FraudExplainer (Phase 7) as SHAP's baseline.
            Capped at BACKGROUND_SAMPLE_SIZE rows here so the artifact
            stays small; the explainer itself doesn't need more than
            that to produce stable attributions.
    """
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / f"{version_tag}.joblib"

    if len(background_sample) > BACKGROUND_SAMPLE_SIZE:
        background_sample = background_sample.sample(n=BACKGROUND_SAMPLE_SIZE, random_state=42)

    bundle = {
        "model": model,
        "feature_columns": get_model_feature_columns(),
        "optimal_threshold": optimal_threshold,
        "scaler": scaler,
        "background_sample": background_sample.reset_index(drop=True),
    }
    joblib.dump(bundle, artifact_path)

    return str(artifact_path)


def load_model_artifact(artifact_path: str | Path) -> dict[str, Any]:
    """Loads a previously-saved bundle back into {model, feature_columns, optimal_threshold}."""
    path = Path(artifact_path)
    if not path.exists():
        raise FileNotFoundError(f"Model artifact not found at: {path}")
    return joblib.load(path)


async def register_model_version(
    session: AsyncSession,
    *,
    version_tag: str,
    algorithm: str,
    metrics: dict[str, Any],
    artifact_path: str,
    activate: bool = True,
) -> uuid.UUID:
    """
    Inserts a new row into `model_versions` and, if `activate=True`,
    atomically deactivates every other version so exactly one model
    is ever active (ModelVersionRepository.activate() handles the
    "exactly one" invariant; see also the partial unique index from
    Phase 3's second migration for a DB-level backstop).
    """
    repo = ModelVersionRepository(session)

    existing = await repo.get_by_tag(version_tag)
    if existing is not None:
        raise ValueError(
            f"A model version with tag '{version_tag}' already exists "
            f"(id={existing.id}). Use a unique version_tag per training run."
        )

    model_version = await repo.create(
        version_tag=version_tag,
        algorithm=algorithm,
        metrics=metrics,
        artifact_path=artifact_path,
        is_active=False,  # set via activate() below so the invariant holds even on first insert
        trained_at=datetime.now(timezone.utc),
    )

    if activate:
        await repo.activate(model_version.id)

    return model_version.id
