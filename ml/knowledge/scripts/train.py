"""Train the Model A candidates on ASSISTments and select by validation AUC."""

import argparse
import json
import logging
import pickle
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import sklearn
import yaml
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from ml_core.knowledge.features import FEATURES, build_feature_frame

LOGGER = logging.getLogger(__name__)
SPLITS = ("train", "val")
ATTEMPT_COLUMNS = ["user_id", "topic_id", "question_id", "attempt_order", "is_correct", "split"]
MODEL_TYPES = {
    "logistic_regression": LogisticRegression,
    "hist_gradient_boosting": HistGradientBoostingClassifier,
}


@dataclass(frozen=True)
class TrainingResult:
    model: LogisticRegression | HistGradientBoostingClassifier
    model_name: str
    features: list[str]
    validation_auc: dict[str, float]
    train_rows: int
    validation_rows: int


def prepare_splits(attempts: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build earlier-answer features separately for train and validation students."""
    train = attempts.loc[attempts["split"] == "train"]
    validation = attempts.loc[attempts["split"] == "val"]
    if not set(train["user_id"]).isdisjoint(validation["user_id"]):
        raise ValueError("Train and validation share student IDs.")
    for name, rows in zip(SPLITS, (train, validation), strict=True):
        if rows["is_correct"].isna().any() or set(rows["is_correct"].unique()) != {False, True}:
            raise ValueError(f"{name} needs both correct and incorrect answers and no missing labels.")
        if rows[["user_id", "topic_id", "question_id", "attempt_order"]].isna().any().any():
            raise ValueError(f"{name} contains missing student, topic, question or attempt IDs.")
        if rows.duplicated(subset=["user_id", "attempt_order"]).any():
            raise ValueError(f"{name} must have a unique attempt order for each student.")
    return build_feature_frame(train), build_feature_frame(validation)


def train_candidates(attempts: pd.DataFrame, config: dict) -> TrainingResult:
    """Fit both models on train rows and select the one with the higher validation AUC."""
    train, validation = prepare_splits(attempts)
    fitted = {}
    validation_auc = {}
    candidate_features = {}
    for name, model_type in MODEL_TYPES.items():
        candidate = config["models"][name]
        features = list(candidate["features"])
        if not features or len(features) != len(set(features)) or not set(features) <= set(FEATURES):
            raise ValueError(f"{name} features must be unique names from the knowledge feature list.")
        model = model_type(random_state=config["seed"], **candidate["params"])
        model.fit(train[features], train["is_correct"].astype(int))
        scores = model.predict_proba(validation[features])[:, 1]
        validation_auc[name] = float(roc_auc_score(validation["is_correct"], scores))
        fitted[name] = model
        candidate_features[name] = features
        LOGGER.info("%s validation AUC: %.6f", name, validation_auc[name])

    # In a tie, keep the simpler logistic regression candidate.
    winner = max(validation_auc, key=validation_auc.__getitem__)
    return TrainingResult(
        model=fitted[winner],
        model_name=winner,
        features=candidate_features[winner],
        validation_auc=validation_auc,
        train_rows=len(train),
        validation_rows=len(validation),
    )


def save_artifacts(result: TrainingResult, config_bytes: bytes, dataset: Path, output_dir: Path) -> None:
    """Save the winner, the exact config, its input order and validation results."""
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics = {
        "dataset": dataset.as_posix(),
        "selected_model": result.model_name,
        "validation_auc": result.validation_auc,
        "train_rows": result.train_rows,
        "validation_rows": result.validation_rows,
        "scikit_learn_version": sklearn.__version__,
    }
    (output_dir / "model.pkl").write_bytes(pickle.dumps(result.model, protocol=pickle.HIGHEST_PROTOCOL))
    (output_dir / "train.yaml").write_bytes(config_bytes)
    (output_dir / "features.json").write_text(json.dumps(result.features, indent=2) + "\n", encoding="utf-8")
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    auc_rows = "\n".join(f"| {name} | {auc:.6f} |" for name, auc in result.validation_auc.items())
    model_card = (
        "# Knowledge model v1\n\n"
        f"- Training data: `{dataset.as_posix()}` (ASSISTments).\n"
        f"- Selected model: `{result.model_name}`.\n"
        f"- Rows: {result.train_rows:,} train and {result.validation_rows:,} validation.\n"
        f"- Ordered inputs: {', '.join(f'`{feature}`' for feature in result.features)}.\n"
        "- Experiment settings: `train.yaml`.\n\n"
        "| Candidate | Validation ROC AUC |\n"
        "| --- | ---: |\n"
        f"{auc_rows}\n\n"
        "Held-out ASSISTments and EdNet evaluation, calibration and serving speed are tracked separately.\n"
    )
    (output_dir / "model_card.md").write_text(model_card, encoding="utf-8")


def run_training(config_path: Path) -> TrainingResult:
    """Load train and validation rows, then write the selected trained model."""
    config_bytes = config_path.read_bytes()
    config = yaml.safe_load(config_bytes)
    dataset = Path(config["dataset_path"])
    attempts = pd.read_parquet(dataset, columns=ATTEMPT_COLUMNS, filters=[("split", "in", SPLITS)])
    result = train_candidates(attempts, config)
    output_dir = Path(config["output_dir"])
    save_artifacts(result, config_bytes, dataset, output_dir)
    LOGGER.info("Selected %s; saved model and validation results to %s", result.model_name, output_dir)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("ml/knowledge/configs/train.yaml"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_training(args.config)


if __name__ == "__main__":
    main()
