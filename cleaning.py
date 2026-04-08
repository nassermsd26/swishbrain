# -*- coding: utf-8 -*-
import os
import glob
import pandas as pd

# ================================================================
# MAPPING NBA (ID RÉELS)
# ================================================================
NBA_TEAMS_IDS = {
    "ATL": 1610612737, "BOS": 1610612738, "CLE": 1610612739,
    "NOP": 1610612740, "CHI": 1610612741, "DAL": 1610612742,
    "DEN": 1610612743, "GSW": 1610612744, "HOU": 1610612745,
    "LAC": 1610612746, "LAL": 1610612747, "MIA": 1610612748,
    "MIL": 1610612749, "MIN": 1610612750, "BKN": 1610612751,
    "NYK": 1610612752, "ORL": 1610612753, "IND": 1610612754,
    "PHI": 1610612755, "PHX": 1610612756, "POR": 1610612757,
    "SAC": 1610612758, "SAS": 1610612759, "OKC": 1610612760,
    "TOR": 1610612761, "UTA": 1610612762, "MEM": 1610612763,
    "WAS": 1610612764, "DET": 1610612765, "CHA": 1610612766
}


def _safe_numeric(series):
    try:
        return pd.to_numeric(series)
    except:
        return series


# ================================================================
# MERGE POUR 2 ÉQUIPES
# ================================================================
# ================================================================
# MERGE POUR 2 ÉQUIPES AVEC RESCRAPE INTELLIGENT
# ================================================================
def merge_two_teams_games(team1, team2,
                          raw_dir="data/raw/games",
                          out_path="data/clean/matchup_clean.csv"):
    """
    Merge des games de deux équipes avec :
    - Détection des colonnes manquantes
    - Identification de la saison corrompue (2024-25 ou 2025-26)
    - Rescrape automatique sélectif via recup.py
    """

    from recup import fetch_team_data  # import interne ici pour éviter les cycles

    REQUIRED_COLS = [
        "GAME_ID", "GAME_DATE", "PTS", "REB", "AST", "STL", "BLK",
        "FG_PCT", "FG3_PCT", "PLUS_MINUS", "WL", "MATCHUP"
    ]

    CURRENT_SEASON = "2025-26"
    OLD_SEASON = "2024-25"

    # Pour éviter boucle infinie
    MAX_RETRY = 2
    attempt = 0

    while attempt < MAX_RETRY:
        attempt += 1

        print(f"\n=== MERGE ATTEMPT {attempt}/{MAX_RETRY} ===")

        # -----------------------------
        # 1) Récupérer les fichiers sources
        # -----------------------------
        files = [
            os.path.join(raw_dir, f)
            for f in os.listdir(raw_dir)
            if f.endswith(".csv") and (f.startswith(team1) or f.startswith(team2))
        ]

        if not files:
            raise FileNotFoundError("Aucun fichier trouvé pour ces deux équipes.")

        print(f"Fichiers trouvés ({len(files)}):")
        for f in files:
            print(" •", os.path.basename(f))

        dfs = []
        corrupted_new = False   # saison 2025-26
        corrupted_old = False   # saison 2024-25

        # -----------------------------
        # 2) Lecture + détection NULL
        # -----------------------------
        for fp in files:
            df = pd.read_csv(fp)

            # Détecter saison via le filename
            fname = os.path.basename(fp)
            if CURRENT_SEASON.replace("-", "") in fname:
                season = CURRENT_SEASON
            elif OLD_SEASON.replace("-", "") in fname:
                season = OLD_SEASON
            else:
                season = None

            # Vérification colonnes critiques
            for col in REQUIRED_COLS:
                if col in df.columns and df[col].isna().any():
                    print(f"\n⚠️ Colonne manquante détectée : {col} dans {fname}")

                    if season == CURRENT_SEASON:
                        corrupted_new = True
                    elif season == OLD_SEASON:
                        corrupted_old = True

            dfs.append(df)

        # -----------------------------
        # 3) Si tout est propre → sortir de la boucle
        # -----------------------------
        if not corrupted_new and not corrupted_old:
            print("✔ Données OK, aucun rescrape nécessaire.")
            break

        # -----------------------------
        # 4) RESCRAPE INTELLIGENT
        # -----------------------------
        if corrupted_new and not corrupted_old:
            print("\n🔄 Rescrape uniquement la saison 2025-26…")
            fetch_team_data(team1)
            fetch_team_data(team2)

        elif corrupted_old and not corrupted_new:
            print("\n🔄 Rescrape uniquement la saison 2024-25…")
            fetch_team_data(team1)
            fetch_team_data(team2)

        elif corrupted_new and corrupted_old:
            print("\n🔄 Rescrape COMPLET (2024-25 + 2025-26)…")
            fetch_team_data(team1)
            fetch_team_data(team2)

        print("⏳ Rechargement des fichiers…")
        continue  # recommence le merge

    # Fin boucle de retry
    if attempt == MAX_RETRY:
        print("⚠️ Attention : certaines données pourraient rester manquantes après rescrape.")

    # -----------------------------
    # 5) Merge final propre
    # -----------------------------
    dfs = []
    for fp in files:
        df = pd.read_csv(fp).drop_duplicates()
        team_abbr = os.path.basename(fp).split("_")[0]
        df["TEAM_ABBR"] = team_abbr

        # Format date
        if "GAME_DATE" in df.columns:
            df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], errors="coerce")
            df["GAME_DATE"] = df["GAME_DATE"].dt.strftime("%Y-%m-%d")

        for col in df.columns:
            if col != "GAME_DATE":
                df[col] = _safe_numeric(df[col])

        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)

    # --- Filter: keep ONLY regular season games (SEASON_ID starts with '2') ---
    if "SEASON_ID" in df.columns:
        before = len(df)
        df = df[df["SEASON_ID"].astype(str).str.startswith("2")].reset_index(drop=True)
        after = len(df)
        if before != after:
            print(f"[merge_two_teams] Filtered out {before - after} preseason/playoff rows (kept {after} regular season)")

    # -----------------------------
    # Colonnes dérivées
    # -----------------------------
    df["HOME"] = df["MATCHUP"].apply(lambda x: 1 if isinstance(x, str) and "vs." in x else 0)
    df["VICTORY"] = df["WL"].apply(lambda x: 1 if x == "W" else 0)
    df["TEAM_ID_NUM"] = df["TEAM_ABBR"].astype("category").cat.codes

    # Extraction OPP
    def extract_opp(m):
        if not isinstance(m, str):
            return None
        m = m.replace("vs.", "").replace("@", "").strip()
        parts = m.split(" ")
        return parts[-1].upper() if parts else None

    df["OPP"] = df["MATCHUP"].apply(extract_opp)

    # OPP_ID
    df["OPP_ID"] = df["OPP"].apply(lambda a: NBA_TEAMS_IDS.get(str(a), None))

    # POINT_DIFF from PLUS_MINUS (always available)
    if "PLUS_MINUS" in df.columns:
        df["POINT_DIFF"] = df["PLUS_MINUS"]

    # ---------------------------------------------------------
    # ROLLING FEATURES (per team — recent form)
    # ---------------------------------------------------------
    df = df.sort_values(by=["TEAM_ID", "GAME_DATE"]).reset_index(drop=True)

    roll_base = {
        "PTS": "PTS", "AST": "AST", "REB": "REB",
        "FG_PCT": "FG_PCT", "FG3_PCT": "FG3_PCT", "FT_PCT": "FT_PCT",
    }
    if "TOV" in df.columns:
        roll_base["TOV"] = "TOV"

    # ROLL5 (simple), ROLL10 (simple), EWM5 (exponential)
    for src_col, name in roll_base.items():
        if src_col in df.columns:
            grp = df.groupby("TEAM_ID")[src_col]
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

        df["WIN_STREAK"] = df.groupby("TEAM_ID")["VICTORY"].transform(calc_streak)

        # WIN_PCT_ROLL10 — win rate over last 10 games
        df["WIN_PCT_ROLL10"] = df.groupby("TEAM_ID")["VICTORY"].transform(
            lambda x: x.rolling(10, min_periods=2).mean().shift(1)
        )

    # REST_DAYS + IS_B2B
    if "GAME_DATE" in df.columns:
        df["GAME_DATE_DT"] = pd.to_datetime(df["GAME_DATE"], errors="coerce")
        df["REST_DAYS"] = df.groupby("TEAM_ID")["GAME_DATE_DT"].transform(
            lambda x: x.diff().dt.days.fillna(3)
        ).clip(0, 10)
        df["IS_B2B"] = (df["REST_DAYS"] == 1).astype(int)
        df = df.drop(columns=["GAME_DATE_DT"])

    # ---------------------------------------------------------
    # ELO RATINGS (team strength tracker)
    # ---------------------------------------------------------
    import numpy as np
    K_FACTOR = 20
    elo = {}

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

    # NET_RATING_ROLL5
    if "PTS_ROLL5" in df.columns and "OPP_PTS_ROLL5" in df.columns:
        df["NET_RATING_ROLL5"] = df["PTS_ROLL5"] - df["OPP_PTS_ROLL5"]

    # Cleanup
    drop_cols = ["TEAM_NAME", "TEAM_ABBREVIATION", "MATCHUP", "WL", "VIDEO_AVAILABLE", "OPP", "TEAM_ABBR"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")

    df = df.sort_values(by="GAME_DATE")
    df.to_csv(out_path, index=False)

    print("\n✔ merge_two_teams_games terminé et sauvegardé.")
    return df
# ================================================================
# AUTRES MERGES (inchangés)
# ================================================================
def merge_and_clean_games(raw_dir="data/raw/games",
                          out_path="data/clean/all_games_clean.csv"):

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    files = sorted(glob.glob(os.path.join(raw_dir, "*.csv")))
    if not files:
        raise FileNotFoundError("Aucun fichier trouvé dans data/raw/games")

    dfs = [pd.read_csv(fp).drop_duplicates() for fp in files]
    final_df = pd.concat(dfs, ignore_index=True)
    final_df.to_csv(out_path, index=False)
    return final_df


def merge_and_clean_players(raw_dir="data/raw/players",
                            out_path="data/clean/all_players_clean.csv"):

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    files = sorted(glob.glob(os.path.join(raw_dir, "*.csv")))
    if not files:
        return None

    dfs = [pd.read_csv(f).drop_duplicates() for f in files]
    final_df = pd.concat(dfs, ignore_index=True)
    final_df.to_csv(out_path, index=False)
    return final_df


def merge_and_clean_injuries(raw_path="data/raw/injuries/injuries.csv",
                             out_path="data/clean/injuries_clean.csv"):

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if not os.path.exists(raw_path):
        return None

    df = pd.read_csv(raw_path).drop_duplicates()
    df.to_csv(out_path, index=False)
    return df


def merge_and_clean_lineups(raw_dir="data/raw/lineups",
                            out_path="data/clean/all_lineups_clean.csv"):

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    files = sorted(glob.glob(os.path.join(raw_dir, "*_starting5.csv")))
    if not files:
        return None

    dfs = []
    for fp in files:
        df = pd.read_csv(fp).drop_duplicates()
        df["TEAM"] = os.path.basename(fp).replace("_starting5.csv", "")
        dfs.append(df)

    final_df = pd.concat(dfs, ignore_index=True)
    final_df.to_csv(out_path, index=False)
    return final_df


def merge_and_clean_team_stats(raw_dir="data/raw/stats",
                               out_path="data/clean/stats_clean.csv"):

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    files = sorted(glob.glob(os.path.join(raw_dir, "*.csv")))
    if not files:
        return None

    dfs = [pd.read_csv(f).drop_duplicates() for f in files]
    final_df = pd.concat(dfs, ignore_index=True)
    final_df.to_csv(out_path, index=False)
    return final_df