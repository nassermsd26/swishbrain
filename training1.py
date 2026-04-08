# -*- coding: utf-8 -*-
import os
import warnings
import joblib
import pandas as pd
import numpy as np

from sklearn.metrics import accuracy_score, mean_absolute_error
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBClassifier, XGBRegressor
from lightgbm import LGBMClassifier, LGBMRegressor
import optuna

optuna.logging.set_verbosity(optuna.logging.WARNING)
warnings.filterwarnings("ignore", category=UserWarning)

# ============================================================
# CONFIG
# ============================================================
OPTUNA_TRIALS = 5        # Réduit de 60 à 5 pour un entraînement presque immédiat (on-the-fly)
OPTUNA_CV_SPLITS = 3     # TimeSeriesSplit folds

# ============================================================
# PATHS
# ============================================================
TRAIN_TRAIN_PATH = "data/clean/training_train.csv"
TRAIN_TEST_PATH  = "data/clean/training_test.csv"
MATCHUP_PATH     = "data/clean/matchup_clean.csv"

LINEUPS_PATH     = "data/clean/lineups_ml_ids.csv"
INJURIES_PATH    = "data/clean/injuries_clean.csv"
PLAYERS_PATH     = "data/clean/clean_players.csv"

# Ensemble model paths
MODEL_CLF_PATH   = "models/xgb_winner.pkl"
MODEL_LGBM_CLF   = "models/lgbm_winner.pkl"
MODEL_LR_CLF     = "models/lr_winner.pkl"
MODEL_META_CLF   = "models/meta_winner.pkl"

MODEL_SCORE_PATH = "models/xgb_score.pkl"
MODEL_LGBM_SCORE = "models/lgbm_score.pkl"
MODEL_LR_SCORE   = "models/lr_score.pkl"
MODEL_META_SCORE = "models/meta_score.pkl"

SCALER_CLF_PATH   = "models/scaler_clf.pkl"
SCALER_SCORE_PATH = "models/scaler_score.pkl"

FEATURES_CLF_PATH   = "models/features_clf.pkl"
FEATURES_SCORE_PATH = "models/features_score.pkl"


# ============================================================
# NBA ID → ABBR
# ============================================================
NBA_TEAMS = {
    1610612737: "ATL", 1610612738: "BOS", 1610612739: "CLE",
    1610612740: "NOP", 1610612741: "CHI", 1610612742: "DAL",
    1610612743: "DEN", 1610612744: "GSW", 1610612745: "HOU",
    1610612746: "LAC", 1610612747: "LAL", 1610612748: "MIA",
    1610612749: "MIL", 1610612750: "MIN", 1610612751: "BKN",
    1610612752: "NYK", 1610612753: "ORL", 1610612754: "IND",
    1610612755: "PHI", 1610612756: "PHX", 1610612757: "POR",
    1610612758: "SAC", 1610612759: "SAS", 1610612760: "OKC",
    1610612761: "TOR", 1610612762: "UTA", 1610612763: "MEM",
    1610612764: "WAS", 1610612765: "DET", 1610612766: "CHA"
}


def from_real_id(real_id):
    """Convertit TEAM_ID numérique → abbr (ex: 1610612750 → MIN)."""
    try:
        rid = int(real_id)
    except Exception:
        return None
    return NBA_TEAMS.get(rid, None)


def to_real_id(abbr):
    """Convertit abbr → TEAM_ID numérique (ex: MIN → 1610612750)."""
    for team_id, team_abbr in NBA_TEAMS.items():
        if team_abbr == abbr:
            return team_id
    return None


# ============================================================
# LOAD DATA POUR LE TRAINING
# ============================================================
def load_training_data():
    df = pd.read_csv(TRAIN_TRAIN_PATH)

    drop_cols = ["GAME_ID", "GAME_DATE", "TEAM_ID"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")

    # Remove ALL in-game box score stats — these are data leakage
    leak_cols = [
        "PTS", "POINT_DIFF", "PLUS_MINUS",
        "MIN", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT",
        "FTM", "FTA", "FT_PCT", "OREB", "DREB", "REB", "AST",
        "STL", "BLK", "TOV", "PF",
    ]
    df = df.drop(columns=[c for c in leak_cols if c in df.columns], errors="ignore")

    y = df["VICTORY"]
    X = df.drop(columns=["VICTORY"], errors="ignore")

    return X, y


def load_test_data():
    df = pd.read_csv(TRAIN_TEST_PATH)

    drop_cols = ["GAME_ID", "GAME_DATE", "TEAM_ID"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")

    # Remove ALL in-game box score stats — these are data leakage
    leak_cols = [
        "PTS", "POINT_DIFF", "PLUS_MINUS",
        "MIN", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT",
        "FTM", "FTA", "FT_PCT", "OREB", "DREB", "REB", "AST",
        "STL", "BLK", "TOV", "PF",
    ]
    df = df.drop(columns=[c for c in leak_cols if c in df.columns], errors="ignore")

    y = df["VICTORY"]
    X = df.drop(columns=["VICTORY"], errors="ignore")

    return X, y


# ============================================================
# WINNER MODEL — ENSEMBLE + OPTUNA
# ============================================================
def _fill_nan(X_train, X_test):
    """Fill NaN with training median — safe for temporal splits."""
    medians = X_train.median()
    return X_train.fillna(medians), X_test.fillna(medians), medians


def _optuna_xgb(X, y, n_trials=OPTUNA_TRIALS):
    """Bayesian hyperparameter search for XGBClassifier."""
    tscv = TimeSeriesSplit(n_splits=OPTUNA_CV_SPLITS)

    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 800),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "max_depth": trial.suggest_int("max_depth", 3, 8),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "gamma": trial.suggest_float("gamma", 0.0, 0.5),
            "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 1.0),
            "reg_lambda": trial.suggest_float("reg_lambda", 0.5, 3.0),
            "eval_metric": "logloss",
        }
        scores = []
        for train_idx, val_idx in tscv.split(X):
            X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
            m = XGBClassifier(**params, verbosity=0)
            m.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
            scores.append(accuracy_score(y_val, m.predict(X_val)))
        return np.mean(scores)

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    print(f"  XGB best CV acc: {study.best_value*100:.1f}%  params: { {k: round(v, 4) if isinstance(v, float) else v for k, v in study.best_params.items()} }")
    return study.best_params


def _optuna_lgbm(X, y, n_trials=OPTUNA_TRIALS):
    """Bayesian hyperparameter search for LGBMClassifier."""
    tscv = TimeSeriesSplit(n_splits=OPTUNA_CV_SPLITS)

    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 800),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "max_depth": trial.suggest_int("max_depth", 3, 8),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "min_child_weight": trial.suggest_float("min_child_weight", 0.1, 10.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 1.0),
            "reg_lambda": trial.suggest_float("reg_lambda", 0.5, 3.0),
            "num_leaves": trial.suggest_int("num_leaves", 15, 63),
            "verbose": -1,
        }
        scores = []
        for train_idx, val_idx in tscv.split(X):
            X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
            m = LGBMClassifier(**params)
            m.fit(X_tr, y_tr, eval_set=[(X_val, y_val)])
            scores.append(accuracy_score(y_val, m.predict(X_val)))
        return np.mean(scores)

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    print(f"  LGBM best CV acc: {study.best_value*100:.1f}%  params: { {k: round(v, 4) if isinstance(v, float) else v for k, v in study.best_params.items()} }")
    return study.best_params


def _generate_oof_predictions(models, X, y):
    """Generate out-of-fold predictions for stacking (prevents leakage)."""
    tscv = TimeSeriesSplit(n_splits=OPTUNA_CV_SPLITS)
    n = len(X)
    oof = np.zeros((n, len(models)))
    counts = np.zeros(n)

    for train_idx, val_idx in tscv.split(X):
        for i, (name, model_cls, params) in enumerate(models):
            X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_tr = y.iloc[train_idx]

            m = model_cls(**params)
            m.fit(X_tr, y_tr)
            oof[val_idx, i] = m.predict_proba(X_val)[:, 1]
        counts[val_idx] += 1

    # Keep only rows that were in at least one validation fold
    mask = counts > 0
    return oof[mask], y.values[mask]


def train_winner_model():
    print("\n===== TRAINING ENSEMBLE WINNER MODEL =====\n")

    X_train, y_train = load_training_data()
    X_test, y_test   = load_test_data()

    # Fill NaN with median
    X_train, X_test, medians = _fill_nan(X_train, X_test)

    os.makedirs("models", exist_ok=True)
    joblib.dump(X_train.columns.tolist(), FEATURES_CLF_PATH)
    joblib.dump(medians.to_dict(), SCALER_CLF_PATH)  # store medians for prediction

    print(f"Features ({len(X_train.columns)}): {X_train.columns.tolist()}\n")

    # --- Step 1: Optuna tuning ---
    print("Step 1/3: Optuna hyperparameter tuning...")
    xgb_params = _optuna_xgb(X_train, y_train)
    lgbm_params = _optuna_lgbm(X_train, y_train)

    # --- Step 2: Train base models on full training set ---
    print("\nStep 2/3: Training base models...")

    xgb_params["eval_metric"] = "logloss"
    xgb_model = XGBClassifier(**xgb_params, verbosity=0)
    xgb_model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    lgbm_params["verbose"] = -1
    lgbm_model = LGBMClassifier(**lgbm_params)
    lgbm_model.fit(X_train, y_train, eval_set=[(X_test, y_test)])

    lr_model = LogisticRegression(max_iter=1000, C=1.0)
    lr_model.fit(X_train, y_train)

    # Individual accuracies
    acc_xgb  = accuracy_score(y_test, xgb_model.predict(X_test))
    acc_lgbm = accuracy_score(y_test, lgbm_model.predict(X_test))
    acc_lr   = accuracy_score(y_test, lr_model.predict(X_test))
    print(f"  XGBoost:  {acc_xgb*100:.1f}%")
    print(f"  LightGBM: {acc_lgbm*100:.1f}%")
    print(f"  LogReg:   {acc_lr*100:.1f}%")

    # --- Step 3: Stacking meta-learner ---
    print("\nStep 3/3: Training stacking meta-learner...")

    base_models = [
        ("xgb",  XGBClassifier,  {**xgb_params, "verbosity": 0}),
        ("lgbm", LGBMClassifier, {**lgbm_params, "verbose": -1}),
        ("lr",   LogisticRegression, {"max_iter": 1000, "C": 1.0}),
    ]
    oof_preds, oof_y = _generate_oof_predictions(base_models, X_train, y_train)

    meta_model = LogisticRegression(max_iter=1000)
    meta_model.fit(oof_preds, oof_y)

    # Stacked prediction on test set
    test_stack = np.column_stack([
        xgb_model.predict_proba(X_test)[:, 1],
        lgbm_model.predict_proba(X_test)[:, 1],
        lr_model.predict_proba(X_test)[:, 1],
    ])
    preds_ensemble = meta_model.predict(test_stack)
    acc_ensemble = accuracy_score(y_test, preds_ensemble)

    # Save all models
    joblib.dump(xgb_model,  MODEL_CLF_PATH)
    joblib.dump(lgbm_model, MODEL_LGBM_CLF)
    joblib.dump(lr_model,   MODEL_LR_CLF)
    joblib.dump(meta_model, MODEL_META_CLF)

    print(f"\n✔ ENSEMBLE Accuracy: {acc_ensemble*100:.2f}%")
    print(f"  (XGB: {acc_xgb*100:.1f}%, LGBM: {acc_lgbm*100:.1f}%, LR: {acc_lr*100:.1f}%)\n")

    return meta_model, None, acc_ensemble


# ============================================================
# SCORE MODEL
# ============================================================
def train_score_model():

    df_train = pd.read_csv(TRAIN_TRAIN_PATH)
    df_test  = pd.read_csv(TRAIN_TEST_PATH)

    drop_cols = ["GAME_DATE", "MATCHUP", "OPP", "TEAM",
                 "TEAM_NAME", "GAME_ID", "VICTORY", "TEAM_ID"]

    df_train = df_train.drop(columns=[c for c in drop_cols if c in df_train.columns], errors="ignore")
    df_test  = df_test.drop(columns=[c for c in drop_cols if c in df_test.columns], errors="ignore")

    # Remove in-game stats that leak the result (except PTS which is the target)
    score_leak_cols = [
        "POINT_DIFF", "PLUS_MINUS",
        "MIN", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT",
        "FTM", "FTA", "FT_PCT", "OREB", "DREB", "REB", "AST",
        "STL", "BLK", "TOV", "PF",
    ]
    df_train = df_train.drop(columns=[c for c in score_leak_cols if c in df_train.columns], errors="ignore")
    df_test  = df_test.drop(columns=[c for c in score_leak_cols if c in df_test.columns], errors="ignore")

    y_train = df_train["PTS"]
    X_train = df_train.drop(columns=["PTS"]).select_dtypes(include=["number"])

    y_test = df_test["PTS"]
    X_test = df_test.drop(columns=["PTS"]).select_dtypes(include=["number"])

    os.makedirs("models", exist_ok=True)
    joblib.dump(X_train.columns.tolist(), FEATURES_SCORE_PATH)

    # No scaler needed — XGBoost is tree-based

    model = XGBRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        reg_alpha=0.1,
        reg_lambda=1.0,
    )

    model.fit(X_train, y_train)

    # Evaluation
    preds = model.predict(X_test)
    mae = np.mean(np.abs(preds - y_test))

    joblib.dump(model, MODEL_SCORE_PATH)
    joblib.dump(None, SCALER_SCORE_PATH)  # backward compat

    print("\n===== SCORE MODEL =====")
    print(f"Features used: {X_train.columns.tolist()}")
    print(f"✔ MAE match par match : {mae:.2f}\n")

    return model, None


# ============================================================
#  IMPACT BLESSURES : TITULAIRE - REMPLAÇANT
# ============================================================
def _load_players_df(players_path=PLAYERS_PATH):
    if not os.path.exists(players_path):
        print(f"[INFO] {players_path} introuvable → pas d'impact blessures.")
        return None

    df = pd.read_csv(players_path)

    # on s'assure des noms de colonnes
    if "player_local_id" not in df.columns:
        raise ValueError("[ERROR] clean_players.csv doit contenir 'player_local_id'.")

    if "TEAM_ID" not in df.columns:
        raise ValueError("[ERROR] clean_players.csv doit contenir 'TEAM_ID'.")

    if "PTS" not in df.columns:
        raise ValueError("[ERROR] clean_players.csv doit contenir 'PTS' (points par match).")

    return df


def _load_lineups_df(lineups_path=LINEUPS_PATH):
    if not os.path.exists(lineups_path):
        print(f"[INFO] {lineups_path} introuvable → pas d'impact blessures.")
        return None

    return pd.read_csv(lineups_path)


def _load_injuries_df(injuries_path=INJURIES_PATH):
    if not os.path.exists(injuries_path):
        print(f"[INFO] {injuries_path} introuvable → pas d'impact blessures.")
        return None

    df = pd.read_csv(injuries_path)
    if df.empty:
        print("[INFO] injuries_clean.csv vide → pas d'impact blessures.")
        return None

    # On tolère plusieurs noms pour la colonne ID joueur
    if "player_local_id" not in df.columns:
        raise ValueError("[ERROR] injuries_clean.csv doit contenir 'player_local_id'.")

    if "TEAM_ID" not in df.columns:
        raise ValueError("[ERROR] injuries_clean.csv doit contenir 'TEAM_ID'.")

    return df


def compute_team_injury_impact(team_id,
                               opp_id,
                               lineups_path=LINEUPS_PATH,
                               injuries_path=INJURIES_PATH,
                               players_path=PLAYERS_PATH):
    """
    Impact équipe = somme(max(PTS_blessé - PTS_remplaçant, 0))
    - PTS_blessé vient de clean_players.csv
    - PTS_remplaçant = PTS du starter le plus faible du lineup du jour
    """
    players_df  = _load_players_df(players_path)
    lineups_df  = _load_lineups_df(lineups_path)
    injuries_df = _load_injuries_df(injuries_path)

    if players_df is None or lineups_df is None or injuries_df is None:
        return 0.0

    # --- 1) lineup du jour pour cette équipe ---
    df_line = lineups_df[
        (lineups_df["team_id"] == team_id) &
        ((lineups_df["opponent_id"] == opp_id) | ~lineups_df["opponent_id"].notna())
    ]

    if df_line.empty:
        # fallback : n'importe quel lineup pour cette team
        df_line = lineups_df[lineups_df["team_id"] == team_id]

    if df_line.empty:
        print(f"[INFO] Aucun lineup trouvé pour team_id={team_id} → pas d'impact blessures.")
        return 0.0

    row_lineup = df_line.iloc[-1]

    starter_cols = [c for c in lineups_df.columns if c.startswith("starter") and c.endswith("_id")]
    starter_ids = []

    for col in starter_cols:
        val = row_lineup.get(col, np.nan)
        if pd.notna(val):
            try:
                starter_ids.append(int(val))
            except Exception:
                pass

    if not starter_ids:
        print(f"[INFO] Aucun starter_id pour team_id={team_id} → impact=0.")
        return 0.0

    # PTS des starters (depuis clean_players.csv)
    starters_stats = players_df[players_df["player_local_id"].isin(starter_ids)]
    if starters_stats.empty or "PTS" not in starters_stats.columns:
        print(f"[INFO] Impossible de récupérer PTS des starters pour team_id={team_id}.")
        return 0.0

    # Remplaçant = starter le moins scoreur
    replacement_pts = starters_stats["PTS"].min()
    if pd.isna(replacement_pts):
        replacement_pts = 0.0

    # --- 2) blessés de cette équipe ---
    inj_team = injuries_df[injuries_df["TEAM_ID"] == team_id]
    if inj_team.empty:
        return 0.0

    total_impact = 0.0

    for _, inj_row in inj_team.iterrows():
        player_id = inj_row["player_local_id"]
        status = str(inj_row.get("status", "Out")).strip()

        p_stats = players_df[players_df["player_local_id"] == player_id]
        if not p_stats.empty:
            pts_inj = p_stats["PTS"].iloc[0]
        elif "PTS" in injuries_df.columns:
            # Fallback : utiliser les PTS stockés dans injuries_clean.csv (from BR)
            pts_inj = inj_row.get("PTS", None)
        else:
            pts_inj = None

        if pts_inj is None or pd.isna(pts_inj):
            continue

        pts_inj = float(pts_inj)
        
        # Un joueur Day-To-Day a ~50% de chance de jouer, on réduit l'impact
        weight = 0.5 if "Day-To-Day" in status else 1.0
        
        # Coefficient d'absorption : les autres joueurs prennent les tirs,
        # la perte sèche n'est donc que d'environ 35% de la différence de points.
        absorption_factor = 0.35 

        impact = max(0.0, (pts_inj - float(replacement_pts)) * weight * absorption_factor)
        total_impact += impact

    # Plafond maximum réaliste : une équipe entière blessée ne la fera pas descendre à 20 points dans le match
    total_impact = min(35.0, total_impact)

    return float(total_impact)


# ============================================================
#   AFFICHAGE FINAL
# ============================================================
def final_matrix(teamA, teamB, winner, confidence, predA, predB):
    """Construit la matrice finale d'analyse du match avec feu tricolore."""

    # ----- Niveau de confiance -----
    if confidence < 55:
        conf_label = "Faible"
        risk_color = "🔴 Très risqué"
    elif confidence < 65:
        conf_label = "Moyenne"
        risk_color = "🟡 Risqué"
    else:
        conf_label = "Élevée"
        risk_color = "🟢 Sécurisé"

    # ----- Total estimé -----
    total = predA + predB

    # ----- Recommandation Over/Under -----
    if total < 210:
        ou = "Lean UNDER"
    elif total < 225:
        ou = "Neutre / 50-50"
    else:
        ou = "Lean OVER"

    print("\n===== MATRICE FINALE =====")
    print(f"Match: {teamA} vs {teamB}")
    print(f"Winner: {winner} ({confidence:.1f}% confiance) → Niveau : {conf_label}")
    print(f"Score estimé: {int(predA)} - {int(predB)}")
    print(f"Total estimé: {total:.1f}")

    print("\nAnalyse betting:")
    print(f"- Sécurité du pick : {risk_color}")
    print(f"- Pick gagnant : {conf_label}")
    print(f"- Over/Under : {ou}")
    print("- Attention : les prédictions NBA ont une variance naturelle.\n")


# ============================================================
#   PREDICTION (HEAD-TO-HEAD + WINNER + SCORES + BLESSURES)
# ============================================================
def predict_current_match(user_team1=None, user_team2=None):
    # Les équipes choisies par l'utilisateur (abréviations, ex: TOR, POR)
    selected_pair = None
    if user_team1 and user_team2:
        selected_pair = {user_team1, user_team2}

    # 1) Charger le matchup
    df = pd.read_csv(MATCHUP_PATH)

    if len(df) < 2:
        print("❌ matchup_clean.csv doit contenir au moins 2 lignes.")
        return None

    # 2) Charger les modèles ensemble + features
    clf_xgb  = joblib.load(MODEL_CLF_PATH)
    clf_lgbm = joblib.load(MODEL_LGBM_CLF)
    clf_lr   = joblib.load(MODEL_LR_CLF)
    meta_clf = joblib.load(MODEL_META_CLF)
    features_clf = joblib.load(FEATURES_CLF_PATH)
    medians_clf  = joblib.load(SCALER_CLF_PATH)

    score_model   = joblib.load(MODEL_SCORE_PATH)
    features_score = joblib.load(FEATURES_SCORE_PATH)
    medians_score  = joblib.load(SCALER_SCORE_PATH)

    # 3) Préparer les features pour le modèle winner
    df_clf = df.drop(columns=["PTS", "VICTORY", "GAME_DATE"], errors="ignore")
    for col in features_clf:
        if col not in df_clf.columns:
            df_clf[col] = 0
    df_clf = df_clf[features_clf]
    # Fill NaN with stored medians
    if isinstance(medians_clf, dict):
        df_clf = df_clf.fillna(medians_clf)
    df_clf_ready = df_clf.values

    # 4) Préparer les features pour le modèle score
    df_score = df.drop(columns=["VICTORY", "GAME_DATE"], errors="ignore")
    df_score = df_score.select_dtypes(include=["number"])
    for col in features_score:
        if col not in df_score.columns:
            df_score[col] = 0
    df_score = df_score[features_score]
    if isinstance(medians_score, dict):
        df_score = df_score.fillna(medians_score)
    df_score_ready = df_score.values

    def _ensemble_proba(X_one):
        """Get ensemble probability for a single row."""
        p_xgb  = clf_xgb.predict_proba(X_one)[0][1]
        p_lgbm = clf_lgbm.predict_proba(X_one)[0][1]
        p_lr   = clf_lr.predict_proba(X_one)[0][1]
        stack  = np.array([[p_xgb, p_lgbm, p_lr]])
        return meta_clf.predict_proba(stack)[0][1]

    print("\n===== HEAD-TO-HEAD PREDICTIONS =====\n")
    if selected_pair is None:
        print("⚠️ Aucune paire d'équipes reçue. Aucun filtrage possible pour le head-to-head.\n")
    else:
        print(f"Affichage UNIQUEMENT des matchs : {selected_pair}\n")

    # =====================================================
    # HEAD-TO-HEAD (sur les matchs passés entre ces 2 équipes)
    # =====================================================
    if selected_pair is not None:
        for i in range(len(df) - 1):
            real_teamA = df.iloc[i]["TEAM_ID"]
            real_teamB = df.iloc[i]["OPP_ID"]

            teamA = from_real_id(real_teamA)
            teamB = from_real_id(real_teamB)

            if teamA is None or teamB is None:
                continue

            if {teamA, teamB} != selected_pair:
                continue

            X_one = df_clf_ready[i:i + 1]
            y_true = int(df.iloc[i]["VICTORY"])

            proba = _ensemble_proba(X_one)
            pred = 1 if proba > 0.5 else 0

            print(f"Match {i + 1}: {teamA} vs {teamB} → Pred: {pred}, Real: {y_true}, Proba: {proba:.3f}")

    # =====================================================
    # MATCH FINAL : WINNER + SCORES PRÉDITS
    # =====================================================
    if user_team1 and user_team2:
        teamA = user_team1
        teamB = user_team2
        real_teamA = to_real_id(teamA)
        real_teamB = to_real_id(teamB)

        if real_teamA is None or real_teamB is None:
            print(f"Impossible de trouver les TEAM_ID pour {teamA} ou {teamB}")
            return None

        df_teamA = df[df["TEAM_ID"] == real_teamA]
        df_teamB = df[df["TEAM_ID"] == real_teamB]

        if df_teamA.empty or df_teamB.empty:
            print(f"Aucune donnée trouvée pour {teamA} ou {teamB}")
            return None

        idxA = int(df_teamA.index.max())
        idxB = int(df_teamB.index.max())

        df_matchup = df[(df["TEAM_ID"] == real_teamA) & (df["OPP_ID"] == real_teamB)]
        if not df_matchup.empty:
            idx_match = int(df_matchup.index.max())
        else:
            idx_match = idxA

    else:
        last = len(df) - 1
        idx_match = last
        real_teamA = df.iloc[last]["TEAM_ID"]
        real_teamB = df.iloc[last]["OPP_ID"]
        teamA = from_real_id(real_teamA)
        teamB = from_real_id(real_teamB)

        idxA = int(df[df["TEAM_ID"] == real_teamA].index.max())
        idxB = int(df[df["TEAM_ID"] == real_teamB].index.max())

    # ----------- WINNER (ensemble, sans blessures) -----------
    X_last = df_clf_ready[idx_match:idx_match + 1]
    proba1_last = _ensemble_proba(X_last)

    winner_pred = 1 if proba1_last > 0.5 else 0
    base_winner = teamA if winner_pred == 1 else teamB
    base_confidence = max(proba1_last, 1 - proba1_last) * 100

    # ----------- SCORE MODEL (sans blessures) -----------
    X_score_A = df_score_ready[idxA:idxA + 1]
    X_score_B = df_score_ready[idxB:idxB + 1]

    predA = float(score_model.predict(X_score_A)[0])
    predB = float(score_model.predict(X_score_B)[0])

    predA = max(0.0, predA)
    predB = max(0.0, predB)

    # ============================================================
    #  AJUSTEMENT AVEC BLESSURES (clean_players + lineups + injuries)
    # ============================================================
    impactA = compute_team_injury_impact(real_teamA, real_teamB)
    impactB = compute_team_injury_impact(real_teamB, real_teamA)

    if impactA > 0 or impactB > 0:
        print("\n===== IMPACT BLESSURES =====")
        print(f"Impact {teamA}: -{impactA:.2f} pts théoriques")
        print(f"Impact {teamB}: -{impactB:.2f} pts théoriques")

    predA_adj = max(0.0, predA - impactA)
    predB_adj = max(0.0, predB - impactB)

    # Ajustement confiance en fonction du différentiel d'impact
    diff_impact = abs(impactA - impactB)
    confidence_adj = base_confidence

    if diff_impact > 0:
        delta_conf = min(10.0, diff_impact)  # max +/-10 pts de confiance
        if impactA > impactB:
            # TeamA plus touchée → on baisse la confiance sur base_winner si c'est A
            if base_winner == teamA:
                confidence_adj -= delta_conf
            else:
                confidence_adj += delta_conf
        elif impactB > impactA:
            if base_winner == teamB:
                confidence_adj -= delta_conf
            else:
                confidence_adj += delta_conf

    confidence_adj = float(max(1.0, min(confidence_adj, 99.0)))

    # Recalcul winner final basé sur scores ajustés
    # Éviter les égalités en forçant une différence minimale de 1.0 point
    score_diff = abs(predA_adj - predB_adj)
    if score_diff < 1.0:
        # Si les scores sont trop proches, utiliser plusieurs facteurs pour trancher
        # 1. Probabilité du modèle winner (poids 60%)
        # 2. Différentiel d'impact des blessures (poids 30%)
        # 3. Score brut avant ajustement (poids 10%)

        proba_weight = 0.6
        impact_weight = 0.3
        raw_score_weight = 0.1

        # Calculer un score composite
        proba_score = proba1_last if proba1_last > 0.5 else (1 - proba1_last)
        impact_score = 1.0 if (impactA < impactB) else 0.0  # Moins de blessures = mieux
        raw_score_diff = abs(predA - predB)
        raw_score_norm = min(1.0, raw_score_diff / 5.0)  # Normaliser sur 5 points

        composite_A = (proba_score * proba_weight) + (impact_score * impact_weight) + (raw_score_norm * raw_score_weight)
        composite_B = ((1 - proba_score) * proba_weight) + ((1 - impact_score) * impact_weight) + ((1 - raw_score_norm) * raw_score_weight)

        # Forcer une différence minimale de 1.0 point
        if composite_A > composite_B:
            predA_adj = predB_adj + 1.0
        else:
            predB_adj = predA_adj + 1.0

    winner_final = teamA if predA_adj > predB_adj else teamB

    # ===== MATRICE FINALE =====
    final_matrix(
        teamA=teamA,
        teamB=teamB,
        winner=winner_final,
        confidence=confidence_adj,
        predA=predA_adj,
        predB=predB_adj
    )

    return {
        "winner": winner_final,
        "teamA": teamA,
        "teamB": teamB,
        "pred_teamA": predA_adj,
        "pred_teamB": predB_adj,
        "predicted_total_points": predA_adj + predB_adj,
        "confidence": confidence_adj
    }