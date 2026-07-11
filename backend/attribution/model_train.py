"""Train the attribution-confidence classifier (offline, run once, commit model.pkl).

Trains on backend/attribution/training_data.csv (from synthetic_data.py).
Grouped cross-validation by anchor plume_id so jittered copies of the same
plume never leak across the train/validation split — the honest way to
evaluate augmented data. Reports AUC + accuracy, then fits on all data and
saves model.pkl for confidence_score.py. Appends one row per run to
accuracy_log.csv so AUC/accuracy trend is visible across data versions.
"""
from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
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
ACCURACY_LOG_PATH = HERE / "accuracy_log.csv"
_LOG_FIELDS = ["timestamp_utc", "data_version", "n_training_rows", "n_positives",
               "n_negatives", "n_community_confirmed", "model_name",
               "auc_mean", "auc_std", "acc_mean", "acc_std"]

CANDIDATES = {
    "logistic_regression": lambda: make_pipeline(
        StandardScaler(), LogisticRegression(max_iter=1000)),
    "gradient_boosting": lambda: GradientBoostingClassifier(random_state=42),
}


def evaluate(df: pd.DataFrame) -> tuple[str, dict[str, dict]]:
    """Grouped 5-fold CV per candidate; returns (winning model name, per-candidate metrics)."""
    x, y = df[FEATURE_NAMES], df["label"]
    groups = df["plume_id"]
    gkf = GroupKFold(n_splits=5)
    best_name, best_auc = None, -1.0
    results: dict[str, dict] = {}
    for name, make in CANDIDATES.items():
        aucs, accs = [], []
        for tr, va in gkf.split(x, y, groups):
            m = make()
            m.fit(x.iloc[tr], y.iloc[tr])
            proba = m.predict_proba(x.iloc[va])[:, 1]
            aucs.append(roc_auc_score(y.iloc[va], proba))
            accs.append(accuracy_score(y.iloc[va], proba >= 0.5))
        results[name] = {
            "auc_mean": float(np.mean(aucs)), "auc_std": float(np.std(aucs)),
            "acc_mean": float(np.mean(accs)), "acc_std": float(np.std(accs)),
        }
        print(f"{name}: AUC {np.mean(aucs):.3f} ± {np.std(aucs):.3f} | "
              f"acc {np.mean(accs):.3f} (grouped 5-fold by plume)")
        if np.mean(aucs) > best_auc:
            best_name, best_auc = name, float(np.mean(aucs))
    return best_name, results


def _data_version(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()[:8]


def _append_accuracy_log(data_version: str, df: pd.DataFrame, best_name: str,
                         metrics: dict) -> None:
    is_new = not ACCURACY_LOG_PATH.exists()
    n_community = int((df.get("pair_kind") == "community_confirmed").sum()) \
        if "pair_kind" in df.columns else 0
    row = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "data_version": data_version,
        "n_training_rows": len(df),
        "n_positives": int(df["label"].sum()),
        "n_negatives": int((1 - df["label"]).sum()),
        "n_community_confirmed": n_community,
        "model_name": best_name,
        "auc_mean": round(metrics["auc_mean"], 4),
        "auc_std": round(metrics["auc_std"], 4),
        "acc_mean": round(metrics["acc_mean"], 4),
        "acc_std": round(metrics["acc_std"], 4),
    }
    with open(ACCURACY_LOG_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_LOG_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    print(f"training pairs: {len(df)} (pos {int(df.label.sum())} / "
          f"neg {int((1 - df.label).sum())})")
    best, results = evaluate(df)
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

    data_version = _data_version(DATA_PATH)
    _append_accuracy_log(data_version, df, best, results[best])
    print(f"logged accuracy for data_version={data_version} -> {ACCURACY_LOG_PATH.name}")


if __name__ == "__main__":
    main()
