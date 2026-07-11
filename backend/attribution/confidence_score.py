"""Confidence scoring: trained model when available, hand-tuned fallback always.

The hand-tuned scorer is the demo's safety net — transparent, dependency-free,
and it must never be removed (plan §6: fifth cut is the MODEL, never the
fallback). score() returns (confidence 0..1, method_used).

Confidence here means "confidence that this plume is consistent with this
facility as its source, pending verification" — it is never a statement that
the operator is violating any rule.
"""
from __future__ import annotations

import logging
from pathlib import Path

from .features import FEATURE_NAMES

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent / "model.pkl"

_model = None
_model_load_failed = False


def _get_model():
    """Load model.pkl once; on any failure, log and fall back permanently."""
    global _model, _model_load_failed
    if _model is not None or _model_load_failed:
        return _model
    try:
        import joblib
        _model = joblib.load(MODEL_PATH)
        logger.info("confidence model loaded from %s", MODEL_PATH)
    except Exception as e:  # missing file, version mismatch, bad pickle — all fall back
        _model_load_failed = True
        logger.warning("confidence model unavailable (%s); using hand-tuned scorer", e)
    return _model


def hand_tuned_score(features: dict) -> float:
    """Transparent weighted score. Distance dominates; wind nudges; a plume in
    the wrong state is disqualified. Weights hand-picked to give ~0.9 at 200 m
    aligned-wind and ~0.35 at the 2 km threshold."""
    if not features.get("state_match", 1):
        return 0.05
    d = features["distance_m"]
    # distance kernel: 1.0 at 0 m -> ~0.37 at 2000 m
    dist_term = 2.718281828 ** (-d / 2000.0)
    wind_term = features.get("wind_consistency", 0.5)  # 0..1, 0.5 neutral
    # 80% distance, 20% wind: wind can help or hurt but never rescue a far pair
    conf = dist_term * (0.8 + 0.4 * wind_term)
    return round(max(0.0, min(1.0, conf)), 3)


def score(features: dict) -> tuple[float, str]:
    """Confidence for one (plume, facility) feature dict -> (0..1, method)."""
    model = _get_model()
    if model is not None:
        try:
            import pandas as pd
            x = pd.DataFrame([features], columns=FEATURE_NAMES)
            conf = float(model.predict_proba(x)[0, 1])
            return round(conf, 3), "trained_model"
        except Exception as e:
            logger.warning("model inference failed (%s); using hand-tuned scorer", e)
    return hand_tuned_score(features), "hand_tuned_fallback"
