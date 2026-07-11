"""Train the attribution-confidence classifier (offline, run once, commit model.pkl).

Trains on backend/attribution/training_data.csv (from synthetic_data.py).
Grouped cross-validation by anchor plume_id so jittered copies of the same
plume never leak across the train/validation split — the honest way to
evaluate augmented data. Reports AUC + accuracy, then fits on all data and
saves model.pkl for confidence_score.py.
"""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .features import FEATURE_NAMES

HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / "training_data.csv"
MODEL_PATH = HERE / "model.pkl"

CANDIDATES = {
    "logistic_regression": lambda: make_pipeline(
        StandardScaler(), LogisticRegression(max_iter=1000)),
    "gradient_boosting": lambda: GradientBoostingClassifier(random_state=42),
}


def evaluate(df: pd.DataFrame) -> str:
    """Grouped 5-fold CV per candidate; returns the winning model name."""
    x, y = df[FEATURE_NAMES], df["label"]
    groups = df["plume_id"]
    gkf = GroupKFold(n_splits=5)
    best_name, best_auc = None, -1.0
    for name, make in CANDIDATES.items():
        aucs, accs = [], []
        for tr, va in gkf.split(x, y, groups):
            m = make()
            m.fit(x.iloc[tr], y.iloc[tr])
            proba = m.predict_proba(x.iloc[va])[:, 1]
            aucs.append(roc_auc_score(y.iloc[va], proba))
            accs.append(accuracy_score(y.iloc[va], proba >= 0.5))
        print(f"{name}: AUC {np.mean(aucs):.3f} ± {np.std(aucs):.3f} | "
              f"acc {np.mean(accs):.3f} (grouped 5-fold by plume)")
        if np.mean(aucs) > best_auc:
            best_name, best_auc = name, float(np.mean(aucs))
    return best_name


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    print(f"training pairs: {len(df)} (pos {int(df.label.sum())} / "
          f"neg {int((1 - df.label).sum())})")
    best = evaluate(df)
    model = CANDIDATES[best]()
    model.fit(df[FEATURE_NAMES], df["label"])
    joblib.dump(model, MODEL_PATH)
    print(f"winner: {best} -> saved {MODEL_PATH.name}")

    # feature importances / coefficients for judge Q&A
    if best == "gradient_boosting":
        imp = dict(zip(FEATURE_NAMES, model.feature_importances_.round(3)))
    else:
        lr = model.named_steps["logisticregression"]
        imp = dict(zip(FEATURE_NAMES, lr.coef_[0].round(3)))
    print("feature weights:", imp)


if __name__ == "__main__":
    main()
