"""Model A evaluation: stub vs PFA vs knowledge_model_v1 on the held-out test split.

Runs strictly on ``split == "test"`` rows from kt_processed_v1.parquet (ASSISTments)
and kt_ednet_processed_v1.parquet (EdNet).  Also measures cross-dataset transfer
(train on ASSISTments, test on EdNet).

Outputs a Markdown report to ml/knowledge/eval_v1.md.

Run:
    python -m ml.knowledge.scripts.evaluate --config ml/knowledge/configs/evaluate.yaml
"""

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.calibration import calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score

from ml_core.knowledge.features import FEATURES, build_feature_frame

LOGGER = logging.getLogger(__name__)

N_CALIBRATION_BINS = 10
STUB_VERSION = "stub"
PFA_VERSION = "pfa"
V1_VERSION = "v1"


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------


def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    """AUC, accuracy (threshold 0.5), log-loss, and 10-bin calibration ECE."""
    y_pred = (y_prob >= 0.5).astype(int)
    fraction_pos, mean_pred = calibration_curve(y_true, y_prob, n_bins=N_CALIBRATION_BINS)
    ece = float(np.mean(np.abs(fraction_pos - mean_pred)))
    return {
        "auc": float(roc_auc_score(y_true, y_prob)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "log_loss": float(log_loss(y_true, y_prob)),
        "ece": ece,
    }


def metrics_row(name: str, metrics: dict[str, float]) -> str:
    return (
        f"| {name} "
        f"| {metrics['auc']:.4f} "
        f"| {metrics['accuracy']:.4f} "
        f"| {metrics['log_loss']:.4f} "
        f"| {metrics['ece']:.4f} |"
    )


# ---------------------------------------------------------------------------
# Stub predictor (vectorised over a feature-frame)
# ---------------------------------------------------------------------------


def predict_stub_frame(frame: pd.DataFrame) -> np.ndarray:
    """Apply the stub (smoothed topic correct rate) to every row in the frame."""
    history_rows: list[float] = []
    for _, row in frame.iterrows():
        # The stub uses only topic_correct_rate, pre-computed by build_feature_frame.
        history_rows.append(float(row["topic_correct_rate"]))
    return np.array(history_rows, dtype=np.float64)


def _stub_probs(frame: pd.DataFrame) -> np.ndarray:
    """Return stub predictions directly from the pre-computed feature column."""
    return frame["topic_correct_rate"].to_numpy(dtype=np.float64)


# ---------------------------------------------------------------------------
# PFA predictor (re-measured on kt_processed_v1 — fixes the W2-09 note)
# ---------------------------------------------------------------------------


def _pfa_matrix(df: pd.DataFrame, skill_columns: list[str] | None = None) -> pd.DataFrame:
    """One-hot skill easiness + log-count wins/fails per skill (classic PFA)."""
    topic = df["topic_id"].astype(int)
    easiness = pd.get_dummies(topic, prefix="s")
    wins = pd.get_dummies(topic, prefix="c").mul(np.log1p(df["prior_correct"]), axis=0)
    fails = pd.get_dummies(topic, prefix="w").mul(np.log1p(df["prior_wrong"]), axis=0)
    matrix = pd.concat([easiness, wins, fails], axis=1)
    if skill_columns is not None:
        matrix = matrix.reindex(columns=skill_columns, fill_value=0.0)
    return matrix


def train_pfa(train_frame: pd.DataFrame) -> tuple[LogisticRegression, list[str]]:
    """Fit PFA logistic regression; return (model, column_names_used)."""
    x = _pfa_matrix(train_frame)
    y = train_frame["is_correct"].astype(int).to_numpy()
    model = LogisticRegression(max_iter=2000, random_state=42)
    model.fit(x.values.astype(np.float32), y)
    return model, list(x.columns)


def predict_pfa(
    model: LogisticRegression,
    skill_columns: list[str],
    frame: pd.DataFrame,
) -> np.ndarray:
    x = _pfa_matrix(frame, skill_columns=skill_columns)
    return model.predict_proba(x.values.astype(np.float32))[:, 1]


# ---------------------------------------------------------------------------
# V1 predictor (placeholder — depends on W2-08 Amr's train.py)
# ---------------------------------------------------------------------------


def predict_v1_frame(frame: pd.DataFrame, model_path: str | None) -> np.ndarray | None:
    """Return v1 probabilities or None when the model is not yet available."""
    if model_path is None or not Path(model_path).exists():
        LOGGER.warning("knowledge_model_v1 not found at %s; skipping v1 evaluation", model_path)
        return None
    try:
        import joblib  # type: ignore[import-untyped]

        model = joblib.load(model_path)
        return model.predict_proba(frame[FEATURES].to_numpy(dtype=np.float32))[:, 1]
    except Exception:
        LOGGER.exception("Failed to load v1 model from %s", model_path)
        return None


# ---------------------------------------------------------------------------
# Data loading and leak verification
# ---------------------------------------------------------------------------


def load_split(parquet_path: str, split: str) -> pd.DataFrame:
    """Load one named split from a processed parquet file and add feature columns."""
    df = pd.read_parquet(parquet_path)
    assert_no_leakage(df)
    subset = df[df["split"] == split].copy()
    n_students = subset["user_id"].nunique()
    LOGGER.info("%s / split=%s: %d rows, %d students", parquet_path, split, len(subset), n_students)
    return subset


def assert_no_leakage(df: pd.DataFrame) -> None:
    """Fail fast if any student appears in more than one split."""
    per_student = df.groupby("user_id")["split"].nunique()
    leakers = per_student[per_student > 1]
    if not leakers.empty:
        raise AssertionError(
            f"Data leakage: {len(leakers)} student(s) appear in multiple splits: {leakers.index.tolist()[:5]}"
        )
    LOGGER.info("Leakage check passed: every student is in exactly one split.")


def build_frames(parquet_path: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (train_frame, val_frame, test_frame) with FEATURES pre-computed."""
    df = pd.read_parquet(parquet_path)
    assert_no_leakage(df)
    # Features are computed on the full dataset (cumulative counts respect ordering)
    # but each row only uses data from earlier rows of the same student.
    featured = build_feature_frame(df)
    train_f = featured[featured["split"] == "train"].copy()
    val_f = featured[featured["split"] == "val"].copy()
    test_f = featured[featured["split"] == "test"].copy()
    return train_f, val_f, test_f


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------


def report_section(
    dataset_name: str,
    test_frame: pd.DataFrame,
    pfa_model: LogisticRegression,
    pfa_cols: list[str],
    model_v1_path: str | None,
) -> list[str]:
    """Return Markdown lines for one dataset's evaluation table."""
    y = test_frame["is_correct"].astype(int).to_numpy()

    rows = []
    rows.append(f"\n### {dataset_name}\n")
    rows.append(f"Test rows: {len(test_frame):,} | Students: {test_frame['user_id'].nunique():,}\n")
    rows.append("")
    rows.append("| Model | AUC | Accuracy | Log-loss | Calibration ECE |")
    rows.append("| --- | ---: | ---: | ---: | ---: |")

    # Stub
    stub_p = _stub_probs(test_frame)
    rows.append(metrics_row(STUB_VERSION, compute_metrics(y, stub_p)))

    # PFA
    pfa_p = predict_pfa(pfa_model, pfa_cols, test_frame)
    rows.append(metrics_row(PFA_VERSION, compute_metrics(y, pfa_p)))

    # V1 (optional)
    v1_p = predict_v1_frame(test_frame, model_v1_path)
    if v1_p is not None:
        rows.append(metrics_row(V1_VERSION, compute_metrics(y, v1_p)))
    else:
        rows.append(f"| {V1_VERSION} | — | — | — | — | *(model not yet built — waiting on W2-08)* |")

    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="ml/knowledge/configs/evaluate.yaml")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    cfg_text = Path(args.config).read_text(encoding="utf-8")
    cfg: dict = yaml.safe_load(cfg_text)

    assistments_path: str = cfg["datasets"]["assistments"]
    ednet_path: str = cfg["datasets"]["ednet"]
    model_v1_path: str | None = cfg.get("model_v1_path")
    output_md: str = cfg.get("output_md", "ml/knowledge/eval_v1.md")

    # --- Build feature frames (train/val/test) for each dataset ---
    LOGGER.info("Building ASSISTments feature frames …")
    ast_train, ast_val, ast_test = build_frames(assistments_path)

    LOGGER.info("Building EdNet feature frames …")
    edn_train, edn_val, edn_test = build_frames(ednet_path)

    # --- Train PFA on each dataset's train split ---
    LOGGER.info("Training PFA on ASSISTments train split …")
    pfa_ast, pfa_ast_cols = train_pfa(ast_train)

    LOGGER.info("Training PFA on EdNet train split …")
    pfa_edn, pfa_edn_cols = train_pfa(edn_train)

    # --- PFA cross-dataset: trained on ASSISTments, tested on EdNet ---
    LOGGER.info("Measuring cross-dataset transfer (ASSISTments → EdNet) …")
    edn_y = edn_test["is_correct"].astype(int).to_numpy()
    cross_p = predict_pfa(pfa_ast, pfa_ast_cols, edn_test)
    cross_metrics = compute_metrics(edn_y, cross_p)

    # --- Assemble markdown report ---
    lines: list[str] = []
    lines.append("# eval_v1 — Model A evaluation report\n")
    lines.append("*Generated by `ml/knowledge/scripts/evaluate.py`.*\n")
    lines.append("\n## Methodology\n")
    lines.append(
        "- Evaluation is **strictly on the `test` split** (held-out by student; no student "
        "appears in both train and test — verified by `assert_no_leakage`).\n"
    )
    lines.append(
        "- Features are built from **earlier answers only** (`build_feature_frame`), "
        "so there is no within-row leakage.\n"
    )
    lines.append(
        "- Metrics: **AUC** (ROC), **accuracy** (threshold 0.5), **log-loss**, "
        f"**calibration ECE** ({N_CALIBRATION_BINS} bins).\n"
    )
    lines.append("- **Stub**: smoothed topic correct rate (`topic_correct_rate` from `features.py`).\n")
    lines.append(
        "- **PFA**: logistic regression with per-skill easiness + log-count wins/fails "
        "(classic Performance Factors Analysis), trained on `split == train`.\n"
    )
    lines.append(
        "- **v1**: `knowledge_model_v1` trained by W2-08 (Amr). "
        "Results shown as `—` until the model weights are available.\n"
    )

    lines.append("\n## Per-dataset results\n")
    lines += report_section("ASSISTments (kt_processed_v1)", ast_test, pfa_ast, pfa_ast_cols, model_v1_path)
    lines += report_section(
        "EdNet KT1 sample (kt_ednet_processed_v1)", edn_test, pfa_edn, pfa_edn_cols, model_v1_path
    )

    lines.append("\n## Cross-dataset transfer: PFA trained on ASSISTments → tested on EdNet\n")
    lines.append("| Model | AUC | Accuracy | Log-loss | Calibration ECE |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    lines.append(metrics_row("PFA (ASSISTments→EdNet)", cross_metrics))
    lines.append("")
    lines.append(
        "> A large drop vs. in-domain PFA indicates topic-ID mismatch: "
        "ASSISTments topic IDs (1–149 encoded from skill_id) are unrelated to EdNet tag IDs.\n"
    )

    lines.append("\n## Leakage verification\n")
    lines.append(
        "- `assert_no_leakage` confirmed no student appears in more than one split "
        "for both ASSISTments and EdNet.\n"
    )
    lines.append("- Feature frame uses cumulative counts up to (not including) the current row.\n")
    lines.append("- The test split is never used for training or for any hyperparameter choice.\n")

    lines.append("\n## Notes\n")
    lines.append(
        "- The old PFA AUC of 0.717 was measured on the original 525,534-row file "
        "(README §7.3, issue #5). This report re-measures PFA on `kt_processed_v1` "
        "(346,860 → 253,278 rows, corrected collapsed file) — that number is the new bar.\n"
    )
    lines.append("- v1 comparison will be filled in once Amr's W2-08 (`train.py`) is merged into `dev`.\n")

    md_path = Path(output_md)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines), encoding="utf-8")
    LOGGER.info("Wrote report to %s", md_path)
    print(f"Report written to {md_path}")


if __name__ == "__main__":
    main()
