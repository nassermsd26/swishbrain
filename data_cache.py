# -*- coding: utf-8 -*-
"""
Smart Data Cache — vérifie la fraîcheur des données à chaque étape du pipeline.
Évite de relancer scraping / cleaning / training quand rien n'a changé.
"""
import os
import glob
from datetime import datetime, timedelta

# ──────────────────────────────────────────────────────────
# CONFIG PATHS
# ──────────────────────────────────────────────────────────
RAW_GAMES_DIR = "data/raw/games"
CLEAN_DIR = "data/clean"
MODELS_DIR = "models"

MATCHUP_CLEAN = os.path.join(CLEAN_DIR, "matchup_clean.csv")
TRAINING_TRAIN = os.path.join(CLEAN_DIR, "training_train.csv")
TRAINING_TEST = os.path.join(CLEAN_DIR, "training_test.csv")
TRAINING_FULL = os.path.join(CLEAN_DIR, "training_full.csv")

# Fichiers modèle principaux
MODEL_FILES = [
    os.path.join(MODELS_DIR, "xgb_winner.pkl"),
    os.path.join(MODELS_DIR, "xgb_score.pkl"),
]


def _mtime(path):
    """Retourne le timestamp de modification d'un fichier, ou 0 si inexistant."""
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0


def _raw_files_for_team(team_abbr):
    """Retourne la liste des fichiers raw CSV pour une équipe."""
    if not os.path.exists(RAW_GAMES_DIR):
        return []
    return [
        os.path.join(RAW_GAMES_DIR, f)
        for f in os.listdir(RAW_GAMES_DIR)
        if f.startswith(team_abbr) and f.endswith(".csv")
    ]


def _latest_raw_mtime(*team_abbrs):
    """Retourne le mtime le plus récent parmi tous les fichiers raw des équipes données."""
    latest = 0
    for team in team_abbrs:
        for fp in _raw_files_for_team(team):
            mt = _mtime(fp)
            if mt > latest:
                latest = mt
    return latest


def _all_raw_mtime():
    """Retourne le mtime le plus récent de TOUS les fichiers dans data/raw/games."""
    pattern = os.path.join(RAW_GAMES_DIR, "*.csv")
    latest = 0
    for fp in glob.glob(pattern):
        mt = _mtime(fp)
        if mt > latest:
            latest = mt
    return latest


# ──────────────────────────────────────────────────────────
# CHECKS DE FRAÎCHEUR
# ──────────────────────────────────────────────────────────

def is_team_data_fresh(team_abbr, max_age_hours=2):
    """
    Vérifie si les fichiers raw d'une équipe sont assez récents.
    Retourne True si les données ont été mises à jour il y a moins de max_age_hours.
    """
    files = _raw_files_for_team(team_abbr)
    if not files:
        return False  # pas de données → il faut fetcher

    # Vérifier le fichier Regular de la saison courante
    current_season_files = [f for f in files if "202526" in f and "Regular" in f]
    if not current_season_files:
        return False

    latest_mtime = max(_mtime(f) for f in current_season_files)
    age_seconds = datetime.now().timestamp() - latest_mtime
    age_hours = age_seconds / 3600

    if age_hours < max_age_hours:
        print(f"  ⚡ {team_abbr} — données fraîches ({age_hours:.1f}h), skip scraping")
        return True

    return False


def is_clean_data_fresh(teamA, teamB):
    """
    Vérifie si matchup_clean.csv est plus récent que les fichiers raw
    des deux équipes ET contient bien les données de ces équipes.
    """
    if not os.path.exists(MATCHUP_CLEAN):
        return False

    clean_mtime = _mtime(MATCHUP_CLEAN)
    raw_mtime = _latest_raw_mtime(teamA, teamB)

    if raw_mtime == 0:
        return False  # pas de raw → on ne peut pas skip

    if clean_mtime <= raw_mtime:
        return False  # raw plus récent → refaire le cleaning

    # Vérifier que matchup_clean.csv contient bien les TEAM_IDs des 2 équipes
    try:
        import csv
        # Mapping rapide abbr → TEAM_ID
        _ABBR_TO_ID = {
            "ATL": 1610612737, "BOS": 1610612738, "BKN": 1610612751, "CHA": 1610612766,
            "CHI": 1610612741, "CLE": 1610612739, "DAL": 1610612742, "DEN": 1610612743,
            "DET": 1610612765, "GSW": 1610612744, "HOU": 1610612745, "IND": 1610612754,
            "LAC": 1610612746, "LAL": 1610612747, "MEM": 1610612763, "MIA": 1610612748,
            "MIL": 1610612749, "MIN": 1610612750, "NOP": 1610612740, "NYK": 1610612752,
            "OKC": 1610612760, "ORL": 1610612753, "PHI": 1610612755, "PHX": 1610612756,
            "POR": 1610612757, "SAC": 1610612758, "SAS": 1610612759, "TOR": 1610612761,
            "UTA": 1610612762, "WAS": 1610612764,
        }
        needed_ids = {str(_ABBR_TO_ID.get(teamA, "")), str(_ABBR_TO_ID.get(teamB, ""))}

        found_ids = set()
        with open(MATCHUP_CLEAN, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tid = row.get("TEAM_ID", "")
                # Normaliser (enlever .0 si présent)
                tid = tid.split(".")[0] if "." in tid else tid
                found_ids.add(tid)
                if needed_ids.issubset(found_ids):
                    break

        if not needed_ids.issubset(found_ids):
            print(f"  ⚠️ matchup_clean.csv ne contient pas {teamA}/{teamB}, re-merge nécessaire")
            return False

    except Exception as e:
        print(f"  ⚠️ Erreur vérification matchup_clean.csv: {e}")
        return False

    print(f"  ⚡ matchup_clean.csv à jour (clean > raw) et contient {teamA}/{teamB}, skip cleaning matchup")
    return True


def is_training_data_fresh():
    """
    Vérifie si les fichiers de training sont plus récents que
    TOUS les fichiers raw. Si oui → pas besoin de re-cleaner le training.
    """
    for f in [TRAINING_TRAIN, TRAINING_TEST]:
        if not os.path.exists(f):
            return False

    training_mtime = min(_mtime(TRAINING_TRAIN), _mtime(TRAINING_TEST))
    raw_mtime = _all_raw_mtime()

    if raw_mtime == 0:
        return False

    if training_mtime > raw_mtime:
        print(f"  ⚡ training data à jour, skip cleaning training")
        return True

    return False


def is_model_fresh():
    """
    Vérifie si les modèles entraînés sont plus récents que les données
    de training. Si oui → pas besoin de re-entraîner.
    """
    for mf in MODEL_FILES:
        if not os.path.exists(mf):
            return False

    model_mtime = min(_mtime(mf) for mf in MODEL_FILES)

    # Les modèles doivent être plus récents que les données de training
    training_mtime = 0
    for tf in [TRAINING_TRAIN, TRAINING_FULL]:
        if os.path.exists(tf):
            mt = _mtime(tf)
            if mt > training_mtime:
                training_mtime = mt

    if training_mtime == 0:
        return False

    if model_mtime > training_mtime:
        print(f"  ⚡ modèles à jour, skip training ML")
        return True

    return False


def get_cache_status():
    """Retourne un dict résumant l'état de fraîcheur de tout le pipeline."""
    status = {}

    # Raw data freshness
    if os.path.exists(RAW_GAMES_DIR):
        raw_latest = _all_raw_mtime()
        if raw_latest > 0:
            age = (datetime.now().timestamp() - raw_latest) / 3600
            status["raw_data_age_hours"] = round(age, 1)
        else:
            status["raw_data_age_hours"] = None
    else:
        status["raw_data_age_hours"] = None

    # Clean data freshness
    status["matchup_clean_exists"] = os.path.exists(MATCHUP_CLEAN)
    status["training_data_exists"] = all(
        os.path.exists(f) for f in [TRAINING_TRAIN, TRAINING_TEST]
    )

    # Models freshness
    status["models_exist"] = all(os.path.exists(mf) for mf in MODEL_FILES)
    status["model_fresh"] = is_model_fresh() if status["models_exist"] else False

    return status
