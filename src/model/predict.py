"""
Model prediction functions.

This module provides functions to load trained models and generate predictions.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Union
from pathlib import Path
import joblib


ModelLike = Union[object, Dict[str, Any]]


def load_model_bundle(model_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load a trained model bundle from disk.

    The training pipeline saves a dict containing:
      - model: the trained estimator
      - encoders: fitted encoders for categorical features (e.g., conference)
      - metadata: training seasons, metrics, etc.

    Returns:
        Dict with keys: model, encoders, metadata
    """
    if model_path is None:
        model_path = Path(__file__).parent.parent.parent / "data" / "models" / "cfp_predictor.pkl"

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Train the model first.")

    loaded = joblib.load(model_path)

    if isinstance(loaded, dict) and "model" in loaded:
        return {
            "model": loaded["model"],
            "encoders": loaded.get("encoders", {}) or {},
            "metadata": loaded.get("metadata", {}) or {},
        }

    # Back-compat: older saves may be a raw model object
    return {"model": loaded, "encoders": {}, "metadata": {}}


def load_model(model_path: Optional[Path] = None) -> object:
    """
    Load a trained model from disk.
    
    Args:
        model_path: Path to saved model. If None, uses default location.
        
    Returns:
        Loaded model object
    """
    return load_model_bundle(model_path)["model"]


def _safe_label_encode(values: pd.Series, encoder: object) -> np.ndarray:
    """
    Label-encode values with a fitted sklearn LabelEncoder, safely handling unknowns.
    Unknown labels map to -1.
    """
    classes = getattr(encoder, "classes_", None)
    if classes is None:
        return pd.Series(values).astype(str).factorize()[0]

    mapping = {str(label): int(i) for i, label in enumerate(classes)}
    encoded = pd.Series(values).astype(str).map(mapping).fillna(-1).astype(int)
    return encoded.to_numpy()


def _coerce_model_bundle(model: Optional[ModelLike], model_path: Optional[Path]) -> Dict[str, Any]:
    if model is None:
        return load_model_bundle(model_path)

    if isinstance(model, dict) and "model" in model:
        return {
            "model": model["model"],
            "encoders": model.get("encoders", {}) or {},
            "metadata": model.get("metadata", {}) or {},
        }

    # Model object only. If a path is available, pull encoders/metadata from disk.
    if model_path is not None:
        bundle = load_model_bundle(model_path)
        bundle["model"] = model
        return bundle

    return {"model": model, "encoders": {}, "metadata": {}}


def _prepare_features_for_model(features_df: pd.DataFrame, model_bundle: Dict[str, Any]) -> pd.DataFrame:
    model = model_bundle["model"]
    encoders = model_bundle.get("encoders", {}) or {}

    expected = list(getattr(model, "feature_names_", []))
    if not expected:
        exclude_cols = {"team", "season", "week", "target_rank", "conference"}
        expected = [col for col in features_df.columns if col not in exclude_cols]

    working = features_df.copy()

    # Training encodes conference -> conference_encoded; recreate it for inference.
    if "conference_encoded" in expected and "conference_encoded" not in working.columns:
        if "conference" in working.columns and "conference" in encoders:
            working["conference_encoded"] = _safe_label_encode(working["conference"], encoders["conference"])
        else:
            working["conference_encoded"] = 0

    # Ensure all expected columns exist and are ordered correctly
    for col in expected:
        if col not in working.columns:
            working[col] = 0

    X = working[expected].copy()
    return X.fillna(0)


def predict_rankings(
    features_df: pd.DataFrame,
    model: Optional[ModelLike] = None,
    model_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Predict CFP rankings from team features.
    
    Args:
        features_df: DataFrame with feature columns (one row per team)
        model: Optional pre-loaded model. If None, loads from model_path.
        model_path: Path to saved model (used if model is None)
        
    Returns:
        DataFrame with columns: team, predicted_score, predicted_rank
    """
    bundle = _coerce_model_bundle(model, model_path)
    model_obj = bundle["model"]
    X = _prepare_features_for_model(features_df, bundle)
    
    # Predict scores (lower score = better rank)
    predicted_scores = model_obj.predict(X)
    
    # Create results DataFrame
    results = features_df[["team"]].copy()
    results["predicted_score"] = predicted_scores
    
    # Sort by score to assign ranks (lower = better)
    results = results.sort_values("predicted_score").reset_index(drop=True)
    results["predicted_rank"] = range(1, len(results) + 1)
    
    return results


def predict_top_n(
    features_df: pd.DataFrame,
    n: int = 25,
    model: Optional[object] = None,
    model_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Predict Top N teams.
    
    Args:
        features_df: DataFrame with feature columns
        n: Number of teams to return (default 25)
        model: Optional pre-loaded model
        model_path: Path to saved model
        
    Returns:
        DataFrame with top N teams by predicted rank
    """
    rankings = predict_rankings(features_df, model, model_path)
    return rankings.head(n)
