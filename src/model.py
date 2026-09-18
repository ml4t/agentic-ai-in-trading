"""Train a LightGBM regressor on the eight features with walk-forward CV.

Why not a random split: the label is a 21-session forward return, so a
training row's label window overlaps the label windows of the 20 sessions on
either side of it. A shuffled split (train_test_split, KFold, cross_val_score
with shuffle=True) would routinely place a training row a few sessions away
from a test row on the other side of the boundary - their labels share most
of their realized price path. The model can then partly "predict" the test
label by having memorized the overlapping training label, which is not
predictive skill. WalkForwardCV keeps all training data strictly before
validation data in time and additionally purges the label_horizon=21 training
rows immediately preceding each validation fold, so no training label's
window reaches into the validation period.
"""

from __future__ import annotations

import lightgbm as lgb
import pandas as pd

from ml4t.diagnostic.splitters import WalkForwardCV
from src.data import load_eligible_panel
from src.features import FEATURE_COLUMNS, build_features
from src.label import LABEL_HORIZON, build_label

N_SPLITS = 5


def build_dataset() -> pd.DataFrame:
    panel = load_eligible_panel()
    panel = build_features(panel)
    panel = build_label(panel)
    panel = panel.sort_values(["timestamp", "symbol"]).reset_index(drop=True)
    return panel


def run_walk_forward(df: pd.DataFrame) -> pd.DataFrame:
    """Fit/predict across walk-forward folds; return out-of-fold predictions."""
    model_df = df.dropna(subset=[*FEATURE_COLUMNS, "fwd_ret_21"]).reset_index(drop=True)
    X = model_df[FEATURE_COLUMNS]
    y = model_df["fwd_ret_21"]
    X_indexed = X.set_index(pd.DatetimeIndex(model_df["timestamp"]).tz_localize("UTC"))

    cv = WalkForwardCV(
        n_splits=N_SPLITS,
        label_horizon=LABEL_HORIZON,
        expanding=True,
        consecutive=True,
    )

    oof_rows = []
    for fold_i, (train_idx, val_idx) in enumerate(cv.split(X_indexed)):
        model = lgb.LGBMRegressor(
            n_estimators=300,
            learning_rate=0.05,
            num_leaves=31,
            random_state=42,
            verbosity=-1,
        )
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        preds = model.predict(X.iloc[val_idx])

        fold_out = model_df.iloc[val_idx][["symbol", "timestamp", "fwd_ret_21"]].copy()
        fold_out["prediction"] = preds
        fold_out["fold"] = fold_i
        oof_rows.append(fold_out)

        train_span = (
            model_df.iloc[train_idx]["timestamp"].min(),
            model_df.iloc[train_idx]["timestamp"].max(),
        )
        val_span = (
            model_df.iloc[val_idx]["timestamp"].min(),
            model_df.iloc[val_idx]["timestamp"].max(),
        )
        print(
            f"fold {fold_i}: train {len(train_idx):,} rows [{train_span[0].date()} .. "
            f"{train_span[1].date()}], val {len(val_idx):,} rows [{val_span[0].date()} .. "
            f"{val_span[1].date()}]"
        )

    return pd.concat(oof_rows, ignore_index=True)


if __name__ == "__main__":
    dataset = build_dataset()
    oof = run_walk_forward(dataset)
    print(oof.head())
    print(f"Total out-of-fold predictions: {len(oof):,}")
