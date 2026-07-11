"""One-shot retrain pipeline: regenerate training data, retrain, log accuracy.

Run whenever new data lands (more facilities, more plumes, new community
reports): python -m backend.attribution.retrain

Equivalent to running synthetic_data.generate() then model_train.main() in
sequence, in-process (no subprocess), so failures surface with full tracebacks.
"""
from __future__ import annotations


def main() -> None:
    from . import model_train, synthetic_data

    synthetic_data.generate()
    model_train.main()


if __name__ == "__main__":
    main()
