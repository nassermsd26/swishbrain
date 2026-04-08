# cleaning2.py
# -*- coding: utf-8 -*-

import os
import pandas as pd
from cleaning import _safe_numeric, NBA_TEAMS_IDS
import numpy as np

def get_training_teams(user_team1, user_team2, raw_dir="data/raw/games"):
    """
    Retourne TOUTES les équipes présentes dans data/raw/games
    sauf les deux équipes choisies par l'utilisateur.
    """
    if not os.path.exists(raw_dir):
        print(f"[get_training_teams] Dossier introuvable : {raw_dir}")
        return []

    raw_teams = {
        f.split("_")[0]
        for f in os.listdir(raw_dir)
        if f.endswith(".csv") and len(f.split("_")[0]) == 3
    }

    training_teams = [
        t for t in raw_teams
        if t not in (user_team1, user_team2)
    ]

    training_teams = sorted(list(training_teams))

    print(f"[get_training_teams] Équipes trouvées dans RAW : {sorted(list(raw_teams))}")
    print(f"[get_training_teams] Équipes utilisées pour le training (hors {user_team1}, {user_team2}) : {training_teams}")

    return training_teams


def clean_training_teams(
    teams_list,
    raw_dir="data/raw/games",
    out_path="data/clean/training.csv"
):


    dfs = []

    if not os.path.exists(raw_dir):
        return None

    if not teams_list:
        return None

    for team in teams_list:
        files = [
            os.path.join(raw_dir, f)
            for f in os.listdir(raw_dir)
            if f.startswith(team) and f.endswith(".csv")
        ]

        if not files:
            continue

        for fp in files:
            df = pd.read_csv(fp).drop_duplicates()
            df["TEAM"] = team

            if "GAME_DATE" in df.columns:
                df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], errors="coerce")
                df["GAME_DATE"] = df["GAME_DATE"].dt.strftime("%Y-%m-%d")

            for col in df.columns:
                if col != "GAME_DATE":
                    df[col] = _safe_numeric(df[col])

            dfs.append(df)

    if not dfs:
        return None

    df = pd.concat(dfs, ignore_index=True)

    # --- Filter: keep ONLY regular season games (SEASON_ID starts with '2') ---
    if "SEASON_ID" in df.columns:
        before = len(df)
        df = df[df["SEASON_ID"].astype(str).str.startswith("2")].reset_index(drop=True)
        after = len(df)
        if before != after:
            print(f"[clean_training_teams] Filtered out {before - after} preseason/playoff rows (kept {after} regular season)")

    df["HOME"] = df["MATCHUP"].apply(
        lambda x: 1 if isinstance(x, str) and "vs." in x else 0
    )
    df["VICTORY"] = df["WL"].apply(lambda x: 1 if x == "W" else 0)
    df["TEAM_ID_NUM"] = df["TEAM"].astype("category").cat.codes

    def extract_opp(m):
        if not isinstance(m, str):
            return None
        m = m.replace("vs. ", "").replace("@ ", "")
        parts = m.split(" ")
        return parts[-1].upper() if len(parts) > 1 else None

    df["OPP"] = df["MATCHUP"].apply(extract_opp)
    # Use real NBA IDs (consistent with matchup_clean.csv)
    df["OPP_ID"] = df["OPP"].map(NBA_TEAMS_IDS)

    # Use PLUS_MINUS directly as POINT_DIFF (always available, no broken zeros)
    if "PLUS_MINUS" in df.columns:
        df["POINT_DIFF"] = df["PLUS_MINUS"]

    # ---------------------------------------------------------
    # ROLLING FEATURES (per team — recent form)
    # ---------------------------------------------------------
    group_col = "TEAM" if "TEAM" in df.columns else "TEAM_ID"
    df = df.sort_values(by=[group_col, "GAME_DATE"]).reset_index(drop=True)

    roll_base = {
        "PTS": "PTS", "AST": "AST", "REB": "REB",
        "FG_PCT": "FG_PCT", "FG3_PCT": "FG3_PCT", "FT_PCT": "FT_PCT",
    }
    if "TOV" in df.columns:
        roll_base["TOV"] = "TOV"

    # ROLL5 (simple), ROLL10 (simple), EWM5 (exponential)
    for src_col, name in roll_base.items():
        if src_col in df.columns:
            grp = df.groupby(group_col)[src_col]
            df[f"{name}_ROLL5"] = grp.transform(
                lambda x: x.rolling(5, min_periods=1).mean().shift(1)
            )
            df[f"{name}_ROLL10"] = grp.transform(
                lambda x: x.rolling(10, min_periods=2).mean().shift(1)
            )
            df[f"{name}_EWM5"] = grp.transform(
                lambda x: x.ewm(span=5, min_periods=2).mean().shift(1)
            )

    # WIN_STREAK (positive = wins, negative = losses)
    if "VICTORY" in df.columns:
        def calc_streak(series):
            streak = []
            current = 0
            for v in series:
                if v == 1:
                    current = current + 1 if current > 0 else 1
                else:
                    current = current - 1 if current < 0 else -1
                streak.append(current)
            return [0] + streak[:-1]

        df["WIN_STREAK"] = df.groupby(group_col)["VICTORY"].transform(calc_streak)

        # WIN_PCT_ROLL10 — win rate over last 10 games
        df["WIN_PCT_ROLL10"] = df.groupby(group_col)["VICTORY"].transform(
            lambda x: x.rolling(10, min_periods=2).mean().shift(1)
        )

    # REST_DAYS + IS_B2B (back-to-back flag)
    if "GAME_DATE" in df.columns:
        df["GAME_DATE_DT"] = pd.to_datetime(df["GAME_DATE"], errors="coerce")
        df["REST_DAYS"] = df.groupby(group_col)["GAME_DATE_DT"].transform(
            lambda x: x.diff().dt.days.fillna(3)
        ).clip(0, 10)
        df["IS_B2B"] = (df["REST_DAYS"] == 1).astype(int)
        df = df.drop(columns=["GAME_DATE_DT"])

    # ---------------------------------------------------------
    # ELO RATINGS (team strength tracker)
    # ---------------------------------------------------------
    K_FACTOR = 20
    elo = {}  # team → current elo

    def get_elo(team_id):
        return elo.get(team_id, 1500.0)

    elo_col = []
    opp_elo_col = []

    for idx, row in df.iterrows():
        tid = row.get("TEAM_ID", None)
        oid = row.get("OPP_ID", None)

        team_elo = get_elo(tid)
        opp_elo = get_elo(oid)
        elo_col.append(team_elo)
        opp_elo_col.append(opp_elo)

        # Update Elo after recording pre-game values
        if pd.notna(row.get("VICTORY", None)) and tid is not None and oid is not None:
            expected = 1 / (1 + 10 ** ((opp_elo - team_elo) / 400))
            actual = float(row["VICTORY"])
            delta = K_FACTOR * (actual - expected)
            elo[tid] = team_elo + delta
            elo[oid] = opp_elo - delta

    df["ELO"] = elo_col
    df["OPP_ELO"] = opp_elo_col
    df["ELO_DIFF"] = df["ELO"] - df["OPP_ELO"]

    # ---------------------------------------------------------
    # OPPONENT ROLLING FEATURES (merge opponent's recent form)
    # ---------------------------------------------------------
    opp_roll_src = {
        "PTS_ROLL5": "OPP_PTS_ROLL5",
        "AST_ROLL5": "OPP_AST_ROLL5",
        "REB_ROLL5": "OPP_REB_ROLL5",
        "FG_PCT_ROLL5": "OPP_FG_PCT_ROLL5",
    }
    if "OPP_ID" in df.columns and "TEAM_ID" in df.columns:
        opp_cols_available = [c for c in opp_roll_src.keys() if c in df.columns]
        if opp_cols_available:
            opp_lookup = df[["TEAM_ID", "GAME_DATE"] + opp_cols_available].copy()
            opp_rename = {c: opp_roll_src[c] for c in opp_cols_available}
            opp_rename["TEAM_ID"] = "OPP_ID"
            opp_lookup = opp_lookup.rename(columns=opp_rename)
            df = df.merge(opp_lookup, on=["OPP_ID", "GAME_DATE"], how="left")

    # NET_RATING_ROLL5 = team's scoring - opponent's scoring trend
    if "PTS_ROLL5" in df.columns and "OPP_PTS_ROLL5" in df.columns:
        df["NET_RATING_ROLL5"] = df["PTS_ROLL5"] - df["OPP_PTS_ROLL5"]

    drop_cols = [
        "TEAM_NAME",
        "TEAM_ABBREVIATION",
        "MATCHUP",
        "OPP",
        "TEAM",
        "WL",
        "VIDEO_AVAILABLE",
    ]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")

    if "GAME_DATE" in df.columns:
        df = df.sort_values("GAME_DATE")

    base_dir = os.path.dirname(out_path)
    os.makedirs(base_dir, exist_ok=True)

    base_cols = []
    if "SEASON_ID" in df.columns:
        base_cols.append("SEASON_ID")
    if "TEAM_ID" in df.columns:
        base_cols.append("TEAM_ID")
    if "OPP_TEAM_ID" in df.columns:
        base_cols.append("OPP_TEAM_ID")
    elif "OPP_ID" in df.columns:
        base_cols.append("OPP_ID")
    if "GAME_DATE" in df.columns:
        base_cols.append("GAME_DATE")
    if "VICTORY" in df.columns:
        base_cols.append("VICTORY")

    training_base = df[base_cols].copy()
    training_base.to_csv(os.path.join(base_dir, "training_base.csv"), index=False)

    training_full = df.copy()
    training_full.to_csv(os.path.join(base_dir, "training_full.csv"), index=False)

    # Temporal split: train on past, test on recent (no future leakage)
    training_full = training_full.sort_values("GAME_DATE").reset_index(drop=True)
    split_idx = int(len(training_full) * 0.8)
    train_df = training_full.iloc[:split_idx]
    test_df = training_full.iloc[split_idx:]

    train_df.to_csv(os.path.join(base_dir, "training_train.csv"), index=False)
    test_df.to_csv(os.path.join(base_dir, "training_test.csv"), index=False)

    test_ids_cols = [c for c in base_cols if c in test_df.columns]
    training_test_ids = test_df[test_ids_cols].copy()
    training_test_ids.to_csv(os.path.join(base_dir, "training_test_ids.csv"), index=False)

    return train_df, test_df