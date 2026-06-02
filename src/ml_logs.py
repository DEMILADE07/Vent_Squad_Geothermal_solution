"""Bonus AI track (WS5.1): ML prediction of missing well-log curves.

Only BLT-01 carries the full curve suite; the other three wells are missing
curves the petrophysics would like to have (NPHI on EVD-01/JUT-01, a dense RHOB
on EVD-01).  The idea is the obvious one: train a regressor on the wells that
*do* have a curve and predict it on the wells that don't.

The honesty is in the validation.  In-sample R^2 on a well the model trained on
is vanity — the only number that matters is whether the model predicts a curve in
a well it has *never seen*.  So every curve is scored by **leave-one-well-out**
cross-validation: hold out one donor well, train on the rest, score on the held-
out well, rotate.  The pooled cross-well R^2 is the headline.

Fallback rule (locked into the project): where the cross-well R^2 for a curve is
below ``R2_FALLBACK_THRESHOLD`` the prediction is *not* trusted downstream — the
petrophysics/resource calc falls back to the ThermoGIS deterministic value and the
report says so.  This keeps a weak model from quietly poisoning Challenge 1.

Everything is deterministic (fixed seeds) so the pipeline and the notebook agree.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, r2_score

from src.wells_io import WELLS, load_all

log = logging.getLogger(__name__)

# Curves we attempt to predict where a well lacks them.  DTC is present on all
# four wells, so it has no recipient to fill — we keep it as a pure cross-well
# validation curve (can sonic be reconstructed from GR + depth?), which is a
# useful, honest benchmark for how far log-prediction can be trusted here.
TARGET_CURVES = ("NPHI", "RHOB", "DTC")

# Curves eligible to act as predictors (minus the target itself each time).  We
# deliberately use only raw measured curves + depth, never derived quantities
# (vsh, phi_d) — those are functions of GR/RHOB and would leak the target.
FEATURE_POOL = ("GR", "DTC", "RHOB", "NPHI", "DTS", "PE")
ALWAYS_FEATURES = ("tvd_m",)

# A well "has" a curve (is a donor / training well for it) above this coverage;
# below it the well is a recipient we predict onto.  0.25 keeps PKP-01's partial
# NPHI (~33%) as a usable second donor so NPHI can be cross-validated at all.
DONOR_MIN_COVERAGE = 0.25
# A curve may only be a *feature* if it is this well-covered in every well we need
# to train on and predict onto — otherwise predictions would be full of holes.
FEATURE_MIN_COVERAGE = 0.50

R2_FALLBACK_THRESHOLD = 0.50

_LGBM_DEFAULTS = dict(
    n_estimators=400,
    learning_rate=0.03,
    num_leaves=31,
    max_depth=6,
    min_child_samples=80,
    subsample=0.8,
    subsample_freq=1,
    colsample_bytree=0.9,
    reg_lambda=1.0,
    random_state=42,
    n_jobs=1,
    verbose=-1,
)


def curve_coverage(logs: pd.DataFrame) -> pd.DataFrame:
    """Per-well non-null fraction for every candidate curve (well x curve)."""
    curves = [c for c in (*FEATURE_POOL, *TARGET_CURVES) if c in logs.columns]
    rows = {}
    for well, g in logs.groupby("well", sort=False):
        rows[well] = {c: float(g[c].notna().mean()) for c in dict.fromkeys(curves)}
    return pd.DataFrame(rows).T.reindex(WELLS)


def _wells_with(cov: pd.DataFrame, curve: str, thr: float) -> list[str]:
    return [w for w in cov.index if cov.loc[w, curve] >= thr]


def select_features(cov: pd.DataFrame, target: str, feature_wells: list[str],
                    pool=FEATURE_POOL, thr=FEATURE_MIN_COVERAGE) -> list[str]:
    """Feature curves well-covered across every well we train on *and* predict onto.

    ``tvd_m`` is always included (depth is the cheapest, most portable predictor);
    the target curve and any curve absent/sparse in any ``feature_wells`` well are
    excluded so the resulting model can actually be evaluated and applied there.
    """
    feats = []
    for c in pool:
        if c == target or c not in cov.columns:
            continue
        if all(cov.loc[w, c] >= thr for w in feature_wells):
            feats.append(c)
    return [*ALWAYS_FEATURES, *feats]


def _fit_predict(train: pd.DataFrame, test: pd.DataFrame, features: list[str],
                 target: str, params: dict | None):
    model = LGBMRegressor(**{**_LGBM_DEFAULTS, **(params or {})})
    model.fit(train[features], train[target])
    return model, model.predict(test[features])


def loo_cv(logs: pd.DataFrame, target: str, features: list[str] | None = None,
           params: dict | None = None) -> dict:
    """Leave-one-well-out cross-validation for one target curve.

    Returns a dict with a per-fold frame (``folds``), the pooled cross-well R^2
    over all held-out predictions (``cross_well_r2``), the chosen ``features``,
    the donor wells, and the fallback verdict for this curve.
    """
    cov = curve_coverage(logs)
    donors = _wells_with(cov, target, DONOR_MIN_COVERAGE)
    recipients = [w for w in cov.index if w not in donors]
    if features is None:
        features = select_features(cov, target, donors + recipients)

    if len(donors) < 2:
        return {"target": target, "donors": donors, "recipients": recipients,
                "features": features, "folds": pd.DataFrame(),
                "cross_well_r2": float("nan"), "n_test_total": 0,
                "use_ml": False,
                "note": f"only {len(donors)} donor well(s); cannot cross-validate"}

    cols = [target, *features]
    fold_rows, pooled_true, pooled_pred = [], [], []
    for held in donors:
        train = logs[logs["well"].isin([w for w in donors if w != held])][cols].dropna()
        test = logs[logs["well"] == held][cols].dropna()
        if train.empty or test.empty:
            continue
        _, yhat = _fit_predict(train, test, features, target, params)
        y = test[target].to_numpy()
        fold_rows.append({
            "target": target, "held_out_well": held, "train_wells": "+".join(
                w for w in donors if w != held),
            "n_train": len(train), "n_test": len(test),
            "r2": round(float(r2_score(y, yhat)), 3),
            "mae": round(float(mean_absolute_error(y, yhat)), 4),
            "rmse": round(float(np.sqrt(np.mean((y - yhat) ** 2))), 4),
        })
        pooled_true.append(y)
        pooled_pred.append(yhat)

    pooled_r2 = (round(float(r2_score(np.concatenate(pooled_true),
                                      np.concatenate(pooled_pred))), 3)
                 if pooled_true else float("nan"))
    n_test_total = int(sum(r["n_test"] for r in fold_rows))
    return {
        "target": target, "donors": donors, "recipients": recipients,
        "features": features, "folds": pd.DataFrame(fold_rows),
        "cross_well_r2": pooled_r2, "n_test_total": n_test_total,
        "use_ml": bool(np.isfinite(pooled_r2) and pooled_r2 >= R2_FALLBACK_THRESHOLD),
    }


def holdout_prediction(logs: pd.DataFrame, target: str, held_out_well: str,
                       features: list[str] | None = None,
                       params: dict | None = None) -> dict:
    """One LOO fold exposed for plotting: train on the other donors, predict the
    held-out donor well, and return the per-sample actual vs predicted curve.

    This is the single fold *behind* the ``loo_cv`` cross-well R^2 — handy for a
    predicted-vs-actual scatter without re-deriving the split in the notebook.
    """
    cov = curve_coverage(logs)
    donors = _wells_with(cov, target, DONOR_MIN_COVERAGE)
    recipients = [w for w in cov.index if w not in donors]
    if features is None:
        features = select_features(cov, target, donors + recipients)
    if held_out_well not in donors:
        raise ValueError(f"{held_out_well} is not a donor well for {target}")

    cols = [target, *features]  # tvd_m is always in features
    train = logs[logs["well"].isin([w for w in donors if w != held_out_well])][cols].dropna()
    test = logs[logs["well"] == held_out_well][cols].dropna()
    _, yhat = _fit_predict(train, test, features, target, params)
    return {
        "target": target, "held_out_well": held_out_well, "features": features,
        "tvd_m": test["tvd_m"].to_numpy(), "y_true": test[target].to_numpy(),
        "y_pred": yhat, "r2": round(float(r2_score(test[target], yhat)), 3),
    }


def predict_missing(logs: pd.DataFrame, target: str, features: list[str] | None = None,
                    params: dict | None = None) -> pd.DataFrame:
    """Train on all donor wells and predict ``target`` on the recipient wells.

    Returns a long frame ``well, md_m, tvd_m, curve, value_pred`` (empty if the
    curve is present everywhere, i.e. nothing to fill).
    """
    cov = curve_coverage(logs)
    donors = _wells_with(cov, target, DONOR_MIN_COVERAGE)
    recipients = [w for w in cov.index if w not in donors]
    if not recipients or len(donors) < 1:
        return pd.DataFrame(columns=["well", "md_m", "tvd_m", "curve", "value_pred"])
    if features is None:
        features = select_features(cov, target, donors + recipients)

    train = logs[logs["well"].isin(donors)][[target, *features]].dropna()
    model = LGBMRegressor(**{**_LGBM_DEFAULTS, **(params or {})})
    model.fit(train[features], train[target])

    out = []
    for w in recipients:
        g = logs[logs["well"] == w]
        usable = g[features].dropna()
        if usable.empty:
            continue
        pred = model.predict(usable)
        out.append(pd.DataFrame({
            "well": w, "md_m": g.loc[usable.index, "md_m"].to_numpy(),
            "tvd_m": g.loc[usable.index, "tvd_m"].to_numpy(),
            "curve": target, "value_pred": pred,
        }))
    return (pd.concat(out, ignore_index=True) if out
            else pd.DataFrame(columns=["well", "md_m", "tvd_m", "curve", "value_pred"]))


def run_all(logs: pd.DataFrame | None = None, params: dict | None = None) -> dict:
    """Cross-validate and predict every target curve.

    Returns ``{"cv": DataFrame, "summary": DataFrame, "predictions": DataFrame}``:
      * ``cv``       — per-fold cross-well scores (every target x held-out well).
      * ``summary``  — one row per target: pooled cross-well R^2 + fallback verdict.
      * ``predictions`` — long frame of filled values on the recipient wells.
    """
    if logs is None:
        from src.petrophysics import add_petrophysics
        logs = add_petrophysics(load_all())

    cv_frames, summary_rows, pred_frames = [], [], []
    for target in TARGET_CURVES:
        res = loo_cv(logs, target, params=params)
        if not res["folds"].empty:
            cv_frames.append(res["folds"])
        summary_rows.append({
            "target": target,
            "donor_wells": "+".join(res["donors"]),
            "recipient_wells": "+".join(res["recipients"]) or "(none)",
            "features": ",".join(res["features"]),
            "n_folds": len(res["folds"]),
            "n_test_total": res["n_test_total"],
            "cross_well_r2": res["cross_well_r2"],
            "decision": "ML" if res["use_ml"] else "ThermoGIS fallback",
        })
        pred_frames.append(predict_missing(logs, target, features=res["features"],
                                            params=params))

    cv = pd.concat(cv_frames, ignore_index=True) if cv_frames else pd.DataFrame()
    summary = pd.DataFrame(summary_rows)
    predictions = (pd.concat([p for p in pred_frames if not p.empty], ignore_index=True)
                   if any(not p.empty for p in pred_frames) else pd.DataFrame(
                       columns=["well", "md_m", "tvd_m", "curve", "value_pred"]))
    return {"cv": cv, "summary": summary, "predictions": predictions}


if __name__ == "__main__":  # smoke check
    import warnings

    warnings.filterwarnings("ignore")
    logging.basicConfig(level=logging.WARNING)
    out = run_all()
    pd.set_option("display.width", 160, "display.max_columns", 20)
    print(out["summary"].to_string(index=False))
