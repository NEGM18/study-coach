"""Reference baseline for model A on ASSISTments 2009-2010 skill builder.

Cleans the raw CSV with the data-plan steps, splits by student, and trains two
baselines. On our copy: 525,534 raw rows -> 253,312 clean; PFA AUC 0.717.

Run: python -m ml.knowledge.scripts.baseline_pfa ml/data/raw/knowledge/skill_builder_data.csv

Note: this reference still uses skill IDs as features (classic PFA). The app version
in ml_core/knowledge/features.py must be topic-agnostic.
"""

import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score

SEED = 42


def step(name: str, before: int, after: int) -> None:
    print(f"{name:<40} {before:>8,} -> {after:>8,}  (-{before - after:,})")


def clean(df: pd.DataFrame) -> pd.DataFrame:
    n = len(df)
    df = df[df.original == 1]
    step("1. keep original problems", n, len(df))
    n = len(df)
    df = df[df.skill_id.notna()]
    step("2. drop missing skill_id", n, len(df))
    n = len(df)
    df = df.drop_duplicates("order_id", keep="first")
    step("3. drop duplicate order_id", n, len(df))
    n = len(df)
    df = df[df.ms_first_response > 0].copy()
    step("4. drop response time <= 0", n, len(df))
    df["ms_first_response"] = df.ms_first_response.clip(upper=df.ms_first_response.quantile(0.99))
    n = len(df)
    per_user = df.user_id.value_counts()
    df = df[df.user_id.isin(per_user[per_user >= 10].index)]
    step("5a. drop students with < 10 answers", n, len(df))
    n = len(df)
    per_skill = df.skill_id.value_counts()
    df = df[df.skill_id.isin(per_skill[per_skill >= 20].index)]
    step("5b. drop skills with < 20 answers", n, len(df))
    return df


def add_history(df: pd.DataFrame) -> pd.DataFrame:
    """Counts from each student's EARLIER answers on the same skill only."""
    df = df.sort_values(["user_id", "order_id"]).copy()
    g = df.groupby(["user_id", "skill_id"])
    df["prior_attempts"] = g.cumcount()
    df["prior_correct"] = g.correct.cumsum() - df.correct
    df["prior_wrong"] = df.prior_attempts - df.prior_correct
    return df


def pfa_matrix(d: pd.DataFrame) -> pd.DataFrame:
    skill = d.skill_id.astype(int)
    easiness = pd.get_dummies(skill, prefix="s")
    wins = pd.get_dummies(skill, prefix="c").mul(np.log1p(d.prior_correct), axis=0)
    fails = pd.get_dummies(skill, prefix="w").mul(np.log1p(d.prior_wrong), axis=0)
    return pd.concat([easiness, wins, fails], axis=1)


def report(name: str, y: pd.Series, p: np.ndarray) -> None:
    print(f"{name:<40} AUC {roc_auc_score(y, p):.3f}  acc {accuracy_score(y, p > 0.5):.3f}")


def main(path: str) -> None:
    df = pd.read_csv(path, encoding="latin-1", low_memory=False)
    print(f"raw rows {len(df):,}, students {df.user_id.nunique():,}, skills {df.skill_id.nunique()}")
    df = add_history(clean(df))

    users = df.user_id.unique()
    np.random.default_rng(SEED).shuffle(users)
    train_users = set(users[: int(0.8 * len(users))])
    tr, te = df[df.user_id.isin(train_users)], df[~df.user_id.isin(train_users)]
    print(f"train {len(tr):,} rows, test {len(te):,} rows (split by student)")

    skill_rate = tr.groupby("skill_id").correct.mean()
    report(
        "Baseline: skill difficulty only", te.correct, te.skill_id.map(skill_rate).fillna(tr.correct.mean())
    )

    x_tr = pfa_matrix(tr)
    x_te = pfa_matrix(te).reindex(columns=x_tr.columns, fill_value=0)
    model = LogisticRegression(max_iter=2000).fit(x_tr.values.astype(np.float32), tr.correct.values)
    report(
        "Baseline: PFA logistic regression",
        te.correct,
        model.predict_proba(x_te.values.astype(np.float32))[:, 1],
    )


if __name__ == "__main__":
    main(sys.argv[1])
