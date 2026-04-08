# -*- coding: utf-8 -*-
import os
import ast
import pandas as pd
from fuzzywuzzy import process

# MODULE LINEUP (scraping + cleaning3 déjà intégré)
from lineup import scrape_lineups_full
from cleaning3 import clean_lineups

from cleaning import merge_two_teams_games
from cleaning2 import get_training_teams, clean_training_teams
from schedule import get_today_tomorrow
from recup import fetch_team_data
from analyse import analyse_automatique, generate_graphs
from injury_player_stats import scrape_injured_players_stats
from cleaning4 import clean_injuries_stats   # nettoyage des stats blessés
from data_cache import is_team_data_fresh, is_clean_data_fresh, is_training_data_fresh, is_model_fresh

from training1 import (
    train_winner_model,
    train_score_model,
    predict_current_match
)

# ------------------------------------------------------
# Liste officielle des équipes NBA
# ------------------------------------------------------
NBA_TEAMS = [
    "ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DAL", "DEN", "DET", "GSW",
    "HOU", "IND", "LAC", "LAL", "MEM", "MIA", "MIL", "MIN", "NOP", "NYK",
    "OKC", "ORL", "PHI", "PHX", "POR", "SAC", "SAS", "TOR", "UTA", "WAS"
]


# ------------------------------------------------------
# Correction fuzzy des équipes
# ------------------------------------------------------
def correction_equipe(user_input: str):
    if not user_input:
        return None

    user_input = user_input.strip().upper()

    # Déjà une abréviation officielle
    if user_input in NBA_TEAMS:
        return user_input

    # Fuzzy matching
    best, score = process.extractOne(user_input, NBA_TEAMS)
    if score >= 70:
        return best

    # Ambigu → proposer des choix
    matches = process.extract(user_input, NBA_TEAMS, limit=3)
    print("\nSaisie ambiguë :")
    for i, (abbr, sc) in enumerate(matches, 1):
        print(f"{i} - {abbr} ({sc}%)")

    choice = input("Choisissez (1/2/3) : ")
    if choice.isdigit() and 1 <= int(choice) <= len(matches):
        return matches[int(choice) - 1][0]

    return None


# ------------------------------------------------------
# Récupérer TEAM_ID réel depuis RAW
# ------------------------------------------------------
def get_team_id_from_raw(team_abbr: str):
    folder = "data/raw/games"
    if not os.path.exists(folder):
        return None

    for f in os.listdir(folder):
        if f.startswith(team_abbr):
            df = pd.read_csv(os.path.join(folder, f))
            if "TEAM_ID" in df.columns and not df["TEAM_ID"].empty:
                return df["TEAM_ID"].iloc[0]
    return None


# ------------------------------------------------------
# Afficher les lineups à partir de lineups_full.csv
# ------------------------------------------------------
def display_lineups_for_match(teamA_abbr: str,
                              teamB_abbr: str,
                              path="data/raw/lineups_full.csv"):
    """
    Affiche les lineups (starters + may_not_play) pour teamA et teamB
    à partir de lineups_full.csv produit par scrape_lineups_full().
    """
    if not os.path.exists(path):
        print(f"[WARN] {path} introuvable, impossible d'afficher les lineups.")
        return

    df = pd.read_csv(path)

    def parse_list(val):
        if isinstance(val, str):
            try:
                return ast.literal_eval(val)
            except Exception:
                # fallback : split simple
                return [x.strip() for x in val.split(",") if x.strip()]
        return val

    print("\n===== LINEUPS (Rotowire) =====\n")

    for abbr in [teamA_abbr, teamB_abbr]:
        df_team = df[df["team"] == abbr]

        if df_team.empty:
            print(f"→ {abbr}: aucun lineup trouvé dans lineups_full.csv")
            continue

        row = df_team.iloc[0]

        starters = parse_list(row.get("starters", []))
        mnp = parse_list(row.get("may_not_play", []))

        print(f"Équipe : {abbr}")
        print("  Starters :")
        for s in starters:
            print(f"    - {s}")

        if mnp:
            print("  May Not Play / OUT :")
            for p in mnp:
                print(f"    - {p}")
        else:
            print("  May Not Play / OUT : aucun signalé.")

        print("")


# ======================================================
# MAIN
# ======================================================
def main():
    print("\n==================== NBA MATCH SELECTION ====================\n")

    # 1) Charger le calendrier
    df_today, df_tomorrow = get_today_tomorrow()
    today_games = df_today.to_dict("records")
    tomorrow_games = df_tomorrow.to_dict("records")

    print("=== MATCHS NBA AUJOURD'HUI ===")
    for i, g in enumerate(today_games, 1):
        print(f"{i}. {g['away']} @ {g['home']} ({g['start']})")

    print("\n=== MATCHS NBA DEMAIN ===")
    offset = len(today_games)
    for i, g in enumerate(tomorrow_games, 1):
        print(f"{offset + i}. {g['away']} @ {g['home']} ({g['start']})")

    total = len(today_games) + len(tomorrow_games)

    # 2) Choix du match
    while True:
        try:
            choice = int(input(f"\nChoisissez un match (1-{total}) : "))
            if 1 <= choice <= total:
                break
        except Exception:
            pass
        print("Choix invalide.")

    # Match choisi + info "aujourd'hui / demain"
    is_today = choice <= len(today_games)

    selected = (
        today_games[choice - 1]
        if is_today
        else tomorrow_games[choice - len(today_games) - 1]
    )

    raw_home = selected["home"]
    raw_away = selected["away"]

    teamA = correction_equipe(raw_home)
    teamB = correction_equipe(raw_away)

    if teamA is None or teamB is None:
        print("❌ Impossible de corriger les équipes sélectionnées.")
        print(f"  home brut: {raw_home} → {teamA}")
        print(f"  away brut: {raw_away} → {teamB}")
        return

    jour_txt = "AUJOURD'HUI" if is_today else "DEMAIN"
    print(f"\n→ Match sélectionné ({jour_txt}) : {raw_home} vs {raw_away} → {teamA} vs {teamB}\n")

    # ======================================================
    # LINEUPS (toujours, avant la prédiction)
    # ======================================================
    print("\n==================== LINEUPS (SCRAP + DISPLAY) ====================\n")

    # Scraping lineups bruts → data/raw/lineups_full.csv
    scrape_lineups_full()

    # Affichage lisible pour l'utilisateur
    display_lineups_for_match(teamA, teamB)

    # ======================================================
    # SI MATCH D'AUJOURD'HUI → ANALYSE COMPLÈTE (LINEUPS + BLESSURES)
    # SI MATCH DE DEMAIN → ANALYSE SANS BLESSURES
    # ======================================================
    if is_today:
        print("\n=== MATCH D'AUJOURD'HUI → analyse complète (lineups + blessures) ===\n")

        # Nettoyage lineups → data/clean/lineups_ml_ids.csv
        clean_lineups()

        # ID des équipes (pour filtrer dans les lineups + blessures)
        teamA_id = get_team_id_from_raw(teamA)
        teamB_id = get_team_id_from_raw(teamB)

        if teamA_id is None or teamB_id is None:
            print("❌ Impossible de retrouver les TEAM_ID pour les lineups/blessures.")
        else:
            # Stats des joueurs blessés (injury_player_stats.py)
            print("\nJoueurs blessés détectés → récupération des stats…")
            scrape_injured_players_stats(teamA_id, teamB_id)

            # Nettoyage des stats blessés (cleaning4.py → injuries_clean.csv)
            print("\n==================== CLEANING INJURIES ====================\n")
            clean_injuries_stats()
    else:
        print("\n=== MATCH DE DEMAIN → analyse standard (SANS blessures) ===\n")
        print("(Lineups affichés, mais pas de pipeline blessures pour ne pas biaiser la prédiction.)")

    # ======================================================
    # SCRAPING ÉQUIPES (skip si données fraîches)
    # ======================================================
    print("\n==================== SCRAPING EQUIPES ====================\n")
    fetch_team_data(teamA)  # skip interne si is_team_data_fresh()
    fetch_team_data(teamB)

    # ======================================================
    # CLEAN MATCHUP (skip si matchup_clean.csv > raw)
    # ======================================================
    print("\n==================== CLEANING MATCHUP ====================\n")
    if is_clean_data_fresh(teamA, teamB):
        print("⚡ Matchup clean déjà à jour, skip.")
    else:
        merge_two_teams_games(teamA, teamB)

    # ======================================================
    # CLEAN TRAINING (skip si training files > raw)
    # ======================================================
    print("\n==================== CLEANING TRAINING ====================\n")
    if is_training_data_fresh():
        print("⚡ Training data déjà à jour, skip.")
    else:
        random_teams = get_training_teams(teamA, teamB)
        clean_training_teams(random_teams)

    # ======================================================
    # MACHINE LEARNING (skip si modèles > training data)
    # ======================================================
    print("\n==================== MACHINE LEARNING ====================\n")
    if is_model_fresh():
        print("⚡ Modèles déjà à jour, skip training.")
    else:
        train_winner_model()
        train_score_model()

    # La fonction predict_current_match utilise injuries_clean.csv
    # → pour aujourd'hui : impact blessures pris en compte
    # → pour demain : injuries_clean.csv n'a pas été mis à jour, donc effet neutre
    prediction = predict_current_match(user_team1=teamA, user_team2=teamB)

    if prediction:
        print("\n===== PREDICTION XGBOOST =====")
        print(f"Winner: {prediction['winner']}")
        print(f"Confidence: {prediction['confidence']:.1f}%")
        print(f"Score estimé: {prediction['pred_teamA']:.0f} - {prediction['pred_teamB']:.0f}")
        print(f"Total estimé: {prediction['predicted_total_points']:.1f}\n")

    # ======================================================
    # ANALYSE COMPLÈTE
    # ======================================================
    print("\n==================== ANALYSE ====================\n")

    df_match = pd.read_csv("data/clean/matchup_clean.csv")

    teamA_id = get_team_id_from_raw(teamA)
    teamB_id = get_team_id_from_raw(teamB)

    if teamA_id is None or teamB_id is None:
        print("❌ Impossible de retrouver les TEAM_ID pour l'analyse.")
        return

    dfA = df_match[df_match["TEAM_ID"] == teamA_id]
    dfB = df_match[df_match["TEAM_ID"] == teamB_id]

    if dfA.empty or dfB.empty:
        print("❌ Données insuffisantes pour l'analyse.")
        print(f"  Lignes pour {teamA} : {len(dfA)}")
        print(f"  Lignes pour {teamB} : {len(dfB)}")
        return

    analyse_automatique(teamA, teamB)

    def stats(df):
        return {
            "PTS": df["PTS"].mean(),
            "REB": df["REB"].mean(),
            "AST": df["AST"].mean(),
            "STL": df["STL"].mean(),
            "BLK": df["BLK"].mean(),
            "DIFF": df["PLUS_MINUS"].mean(),
            "FG_PCT": df["FG_PCT"].mean(),
            "FG3_PCT": df["FG3_PCT"].mean(),
        }

    generate_graphs(teamA, teamB, dfA, dfB, stats(dfA), stats(dfB))

    print("\n==================== FIN ====================\n")


if __name__ == "__main__":
    main()