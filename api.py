# -*- coding: utf-8 -*-
"""
Backend API Flask pour le frontend NBA AI Predictor
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import secrets
import os
import pandas as pd
import json
from datetime import date, datetime, timedelta

# Database module (SQLite)
import database as db

# Imports des modules existants
from schedule import get_today_tomorrow
from training1 import (
    predict_current_match,
    to_real_id,
    from_real_id,
    compute_team_injury_impact
)
from lineup import scrape_lineups_full
from cleaning3 import clean_lineups
from recup import fetch_team_data
from cleaning import merge_two_teams_games
from cleaning2 import get_training_teams, clean_training_teams
from injury_player_stats import scrape_injured_players_stats
from cleaning4 import clean_injuries_stats
from analyse import analyse_automatique

import re

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3001",
    "http://localhost:5173",
    re.compile(r"https://.*\.vercel\.app"),
    re.compile(r"https://.*\.onrender\.com"),
])  # Permet les requêtes depuis le frontend (local + production)

# Configuration JWT
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
jwt = JWTManager(app)

# Initialise la base de données SQLite
db.init_db()

# Seed admin user if not exists
_admin_email = 'nassermsd26@gmail.com'
_admin_password = '123456'
_admin_user = db.find_user_by_email(_admin_email)
if _admin_user:
    # Ensure existing user has admin role
    if _admin_user.get('role') != 'admin':
        db.set_user_role(_admin_user['id'], 'admin')
        print('🔑 Updated nassermsd26@gmail.com to admin role')
    # Re-hash the admin password to ensure it matches the expected password
    _salt = secrets.token_hex(16)
    _pw_hash = f"pbkdf2:sha256:100000${_salt}${hashlib.pbkdf2_hmac('sha256', _admin_password.encode('utf-8'), _salt.encode('utf-8'), 100000).hex()}"
    db.update_user_password(_admin_user['id'], _pw_hash)
    print('🔑 Admin password re-synced')
    # S"assurer que l'admin est approuvé
    if _admin_user.get('approved') != 1:
        db.approve_user(_admin_user['id'])
        print('🔑 Admin account auto-approved')
else:
    _salt = secrets.token_hex(16)
    _pw_hash = f"pbkdf2:sha256:100000${_salt}${hashlib.pbkdf2_hmac('sha256', _admin_password.encode('utf-8'), _salt.encode('utf-8'), 100000).hex()}"
    _admin = db.create_user(_admin_email, _pw_hash, 'nassermsd')
    if _admin:
        db.set_user_role(_admin['id'], 'admin')
        db.approve_user(_admin['id'])
        print('🔑 Created admin user nassermsd26@gmail.com')


def hash_password(password):
    """Hash un mot de passe avec pbkdf2 (compatible Python 3.9)"""
    salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"pbkdf2:sha256:100000${salt}${pwdhash.hex()}"

def verify_password(password_hash, password):
    """Vérifie un mot de passe"""
    try:
        method, salt, stored_hash = password_hash.split('$')
        if method != 'pbkdf2:sha256:100000':
            # Fallback pour les anciens mots de passe
            return check_password_hash(password_hash, password)
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return pwdhash.hex() == stored_hash
    except:
        # Fallback pour les anciens mots de passe
        return check_password_hash(password_hash, password)

# Mapping des IDs NBA pour les logos officiels
NBA_TEAM_IDS = {
    "ATL": "1610612737", "BOS": "1610612738", "BKN": "1610612751", "CHA": "1610612766",
    "CHI": "1610612741", "CLE": "1610612739", "DAL": "1610612742", "DEN": "1610612743",
    "DET": "1610612765", "GSW": "1610612744", "HOU": "1610612745", "IND": "1610612754",
    "LAC": "1610612746", "LAL": "1610612747", "MEM": "1610612763", "MIA": "1610612748",
    "MIL": "1610612749", "MIN": "1610612750", "NOP": "1610612740", "NYK": "1610612752",
    "OKC": "1610612760", "ORL": "1610612753", "PHI": "1610612755", "PHX": "1610612756",
    "POR": "1610612757", "SAC": "1610612758", "SAS": "1610612759", "TOR": "1610612761",
    "UTA": "1610612762", "WAS": "1610612764"
}

def get_nba_logo(abbr: str) -> str:
    """Retourne l'URL du logo NBA officiel"""
    team_id = NBA_TEAM_IDS.get(abbr)
    if team_id:
        return f"https://cdn.nba.com/logos/nba/{team_id}/primary/L/logo.svg"
    return ""

# Mapping des abréviations alternatives vers nos abréviations
ESPN_TO_OUR_ABBR = {
    "NO": "NOP",  # ESPN utilise "NO" pour New Orleans Pelicans
    "PHX": "PHX",  # Parfois ESPN utilise PHX, parfois PHO
    "PHO": "PHX",
    "GS": "GSW",   # Golden State Warriors
    "NY": "NYK",   # New York Knicks
    "WSH": "WAS",  # Washington Wizards
    "UTAH": "UTA", # Utah Jazz
    "SA": "SAS",   # San Antonio Spurs
}

# Mapping des équipes pour le frontend (avec logos)
TEAMS_MAPPING = {
    "ATL": {"id": "1", "name": "Atlanta Hawks", "abbr": "ATL", "color": "#E03A3E", "logo": get_nba_logo("ATL")},
    "BOS": {"id": "2", "name": "Boston Celtics", "abbr": "BOS", "color": "#007A33", "logo": get_nba_logo("BOS")},
    "BKN": {"id": "3", "name": "Brooklyn Nets", "abbr": "BKN", "color": "#000000", "logo": get_nba_logo("BKN")},
    "CHA": {"id": "4", "name": "Charlotte Hornets", "abbr": "CHA", "color": "#1D1160", "logo": get_nba_logo("CHA")},
    "CHI": {"id": "5", "name": "Chicago Bulls", "abbr": "CHI", "color": "#CE1141", "logo": get_nba_logo("CHI")},
    "CLE": {"id": "6", "name": "Cleveland Cavaliers", "abbr": "CLE", "color": "#860038", "logo": get_nba_logo("CLE")},
    "DAL": {"id": "7", "name": "Dallas Mavericks", "abbr": "DAL", "color": "#00538C", "logo": get_nba_logo("DAL")},
    "DEN": {"id": "8", "name": "Denver Nuggets", "abbr": "DEN", "color": "#0E2240", "logo": get_nba_logo("DEN")},
    "DET": {"id": "9", "name": "Detroit Pistons", "abbr": "DET", "color": "#C8102E", "logo": get_nba_logo("DET")},
    "GSW": {"id": "10", "name": "Golden State Warriors", "abbr": "GSW", "color": "#1D428A", "logo": get_nba_logo("GSW")},
    "HOU": {"id": "11", "name": "Houston Rockets", "abbr": "HOU", "color": "#CE1141", "logo": get_nba_logo("HOU")},
    "IND": {"id": "12", "name": "Indiana Pacers", "abbr": "IND", "color": "#002D62", "logo": get_nba_logo("IND")},
    "LAC": {"id": "13", "name": "LA Clippers", "abbr": "LAC", "color": "#C8102E", "logo": get_nba_logo("LAC")},
    "LAL": {"id": "14", "name": "Los Angeles Lakers", "abbr": "LAL", "color": "#552583", "logo": get_nba_logo("LAL")},
    "MEM": {"id": "15", "name": "Memphis Grizzlies", "abbr": "MEM", "color": "#5D76A9", "logo": get_nba_logo("MEM")},
    "MIA": {"id": "16", "name": "Miami Heat", "abbr": "MIA", "color": "#98002E", "logo": get_nba_logo("MIA")},
    "MIL": {"id": "17", "name": "Milwaukee Bucks", "abbr": "MIL", "color": "#00471B", "logo": get_nba_logo("MIL")},
    "MIN": {"id": "18", "name": "Minnesota Timberwolves", "abbr": "MIN", "color": "#0C2340", "logo": get_nba_logo("MIN")},
    "NOP": {"id": "19", "name": "New Orleans Pelicans", "abbr": "NOP", "color": "#0C2340", "logo": get_nba_logo("NOP")},
    "NYK": {"id": "20", "name": "New York Knicks", "abbr": "NYK", "color": "#006BB6", "logo": get_nba_logo("NYK")},
    "OKC": {"id": "21", "name": "Oklahoma City Thunder", "abbr": "OKC", "color": "#007AC1", "logo": get_nba_logo("OKC")},
    "ORL": {"id": "22", "name": "Orlando Magic", "abbr": "ORL", "color": "#0077C0", "logo": get_nba_logo("ORL")},
    "PHI": {"id": "23", "name": "Philadelphia 76ers", "abbr": "PHI", "color": "#006BB6", "logo": get_nba_logo("PHI")},
    "PHX": {"id": "24", "name": "Phoenix Suns", "abbr": "PHX", "color": "#1D1160", "logo": get_nba_logo("PHX")},
    "POR": {"id": "25", "name": "Portland Trail Blazers", "abbr": "POR", "color": "#E03A3E", "logo": get_nba_logo("POR")},
    "SAC": {"id": "26", "name": "Sacramento Kings", "abbr": "SAC", "color": "#5A2D81", "logo": get_nba_logo("SAC")},
    "SAS": {"id": "27", "name": "San Antonio Spurs", "abbr": "SAS", "color": "#C4CED4", "logo": get_nba_logo("SAS")},
    "TOR": {"id": "28", "name": "Toronto Raptors", "abbr": "TOR", "color": "#CE1141", "logo": get_nba_logo("TOR")},
    "UTA": {"id": "29", "name": "Utah Jazz", "abbr": "UTA", "color": "#002B5C", "logo": get_nba_logo("UTA")},
    "WAS": {"id": "30", "name": "Washington Wizards", "abbr": "WAS", "color": "#002B5C", "logo": get_nba_logo("WAS")},
}


def get_team_id_from_raw(team_abbr: str):
    """Récupère le TEAM_ID depuis les fichiers raw"""
    folder = "data/raw/games"
    if not os.path.exists(folder):
        return None

    for f in os.listdir(folder):
        if f.startswith(team_abbr):
            df = pd.read_csv(os.path.join(folder, f))
            if "TEAM_ID" in df.columns and not df["TEAM_ID"].empty:
                return int(df["TEAM_ID"].iloc[0])
    return None


def get_injured_players(team_abbr: str):
    """Récupère la liste des joueurs blessés pour une équipe"""
    team_id = to_real_id(team_abbr)
    if team_id is None:
        return []

    # Charger les blessures (injuries_clean.csv = source ESPN, prioritaire)
    injuries_path = "data/clean/injuries_clean.csv"
    if not os.path.exists(injuries_path):
        # Fallback vers l'ancien fichier
        injuries_path = "data/clean/injuries_players_stats_clean.csv"
        if not os.path.exists(injuries_path):
            return []

    try:
        df_injuries = pd.read_csv(injuries_path)
        df_team_injuries = df_injuries[df_injuries["TEAM_ID"] == team_id]
        
        if df_team_injuries.empty:
            return []

        # Charger le mapping pour avoir les noms
        mapping_path = "data/clean/players_mapping_local.csv"
        if not os.path.exists(mapping_path):
            return []

        df_mapping = pd.read_csv(mapping_path)
        mapping = df_mapping.set_index("player_local_id")["player_name"].to_dict()

        players = []
        for _, row in df_team_injuries.iterrows():
            player_id = row["player_local_id"]
            player_name = mapping.get(player_id, f"Player {player_id}")
            pts_avg = row.get("PTS", 0)
            # Lire le vrai statut depuis ESPN (Out, Day-To-Day, etc.)
            status = row.get("status", "Out")
            if pd.isna(status):
                status = "Out"
            
            players.append({
                "id": int(player_id),
                "name": player_name,
                "status": str(status),
                "pts_avg": float(pts_avg) if pd.notna(pts_avg) else 0
            })

        return players
    except Exception as e:
        print(f"Erreur lors de la récupération des blessures: {e}")
        return []


def get_team_stats(team_abbr: str):
    """Récupère les stats moyennes d'une équipe depuis matchup_clean.csv"""
    matchup_path = "data/clean/matchup_clean.csv"
    if not os.path.exists(matchup_path):
        return None

    try:
        df = pd.read_csv(matchup_path)
        team_id = to_real_id(team_abbr)
        if team_id is None:
            return None

        df_team = df[df["TEAM_ID"] == team_id]
        if df_team.empty:
            return None

        # Prendre la dernière ligne (stats les plus récentes)
        row = df_team.iloc[-1]

        return {
            "pts": float(row.get("PTS", 0)),
            "reb": float(row.get("REB", 0)),
            "ast": float(row.get("AST", 0)),
            "fg_pct": float(row.get("FG_PCT", 0)) * 100,  # Convertir en pourcentage
            "fg3_pct": float(row.get("FG3_PCT", 0)) * 100,
            "plus_minus": float(row.get("PLUS_MINUS", 0))
        }
    except Exception as e:
        print(f"Erreur lors de la récupération des stats: {e}")
        return None


def normalize_team_abbr(abbr: str) -> str:
    """Normalise les abréviations d'équipes (ESPN -> nos abréviations)"""
    abbr = abbr.upper().strip()
    # Vérifier d'abord le mapping ESPN
    if abbr in ESPN_TO_OUR_ABBR:
        return ESPN_TO_OUR_ABBR[abbr]
    # Si déjà dans notre format, retourner tel quel
    if abbr in TEAMS_MAPPING:
        return abbr
    # Sinon retourner l'abréviation originale (sera géré par le frontend)
    return abbr


@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    """Récupère les matchs d'aujourd'hui et de demain"""
    try:
        df_today, df_tomorrow = get_today_tomorrow()
        
        games = []
        
        # Matchs d'aujourd'hui
        for _, row in df_today.iterrows():
            home_abbr = normalize_team_abbr(row["home"])
            away_abbr = normalize_team_abbr(row["away"])
            games.append({
                "id": str(row.get("gameId", len(games) + 1)),
                "home": home_abbr,
                "away": away_abbr,
                "time": row.get("start", ""),
                "isToday": True
            })
        
        # Matchs de demain
        for _, row in df_tomorrow.iterrows():
            home_abbr = normalize_team_abbr(row["home"])
            away_abbr = normalize_team_abbr(row["away"])
            games.append({
                "id": str(row.get("gameId", len(games) + 1)),
                "home": home_abbr,
                "away": away_abbr,
                "time": row.get("start", ""),
                "isToday": False
            })
        
        return jsonify({"games": games})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/predict', methods=['POST'])
def predict():
    """Fait une prédiction pour un match entre deux équipes"""
    try:
        data = request.json
        teamA_abbr = data.get("teamA")
        teamB_abbr = data.get("teamB")
        
        if not teamA_abbr or not teamB_abbr:
            return jsonify({"error": "teamA et teamB sont requis"}), 400

        # Normaliser les abréviations d'équipes AVANT la vérification
        teamA_abbr = normalize_team_abbr(teamA_abbr)
        teamB_abbr = normalize_team_abbr(teamB_abbr)

        # Vérifier que les équipes existent (après normalisation)
        if teamA_abbr not in TEAMS_MAPPING or teamB_abbr not in TEAMS_MAPPING:
            return jsonify({"error": f"Équipes invalides: {data.get('teamA')} -> {teamA_abbr}, {data.get('teamB')} -> {teamB_abbr}"}), 400
        
        # (Cache verification moved down after token deduction)
        
        # Require authentication for predictions
        user_id = None
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Connexion requise pour faire une prédiction."}), 401
        
        token = auth_header.split(' ')[1]
        from flask_jwt_extended import decode_token
        try:
            decoded = decode_token(token)
            user_id = decoded.get('sub')
            if not user_id:
                return jsonify({"error": "Token invalide"}), 401
            user_id = str(user_id)
        except Exception as e:
            return jsonify({"error": "Token invalide: " + str(e)}), 401
            
        # Fetch user and check tokens
        user = db.find_user_by_id(user_id)
        if not user:
            return jsonify({"error": "Utilisateur introuvable"}), 404
            
        role = user.get("role", "user")
        
        # Vérifier l'approbation du compte
        if user.get("approved", 0) != 1 and role != "admin":
            return jsonify({"error": "Votre compte est en attente de validation. Vous ne pouvez pas encore faire de prédictions."}), 403

        subscription = user.get("subscription_tier", "free")
        tokens_remaining = user.get("tokens", 10)
        
        # Admins and Premium have unlimited access. VIPs use their tokens (initialized/upgraded to 70).
        if role != "admin" and subscription != "premium":
            if tokens_remaining <= 0:
                return jsonify({"error": "Vous n'avez plus de jetons. Veuillez passer à un abonnement Premium ou VIP pour faire des prédictions."}), 403
            
            # Decrement tokens (assuming success for the request flow)
            success = db.decrement_user_tokens(user_id)
            if not success:
                return jsonify({"error": "Erreur lors de la déduction du jeton"}), 500
            tokens_remaining -= 1
        elif role == "admin" or subscription == "premium":
            # Make sure we don't return an outdated tokens count to frontend for unlimited users
            # Or just return their current tokens without changing them
            pass

        # Vérifier le cache APRÈS la déduction des jetons
        cached_result = db.get_cached_prediction(teamA_abbr, teamB_abbr)
        if cached_result:
            print("✅ Utilisation de la prédiction en cache - pas besoin de recalculer")
            # Mettre à jour les jetons restants dans le résultat
            cached_result["tokens_remaining"] = tokens_remaining
            # Sauvegarder dans l'historique
            db.save_prediction_to_history(user_id, cached_result)
            return jsonify(cached_result)

        # Préparer les données pour la prédiction (avec cache intelligent)
        from data_cache import is_clean_data_fresh, is_training_data_fresh, is_model_fresh

        # 1. Scraper les lineups (toujours frais car quotidiens)
        print("Scraping lineups...")
        scrape_lineups_full()
        
        # 2. Nettoyer les lineups
        clean_lineups()
        
        # 3. Récupérer les données des équipes (skip si fraîches — check interne)
        print("Fetching team data...")
        fetch_team_data(teamA_abbr)
        fetch_team_data(teamB_abbr)
        
        # 4. Nettoyer le matchup (skip si matchup_clean.csv > raw)
        if is_clean_data_fresh(teamA_abbr, teamB_abbr):
            print("⚡ matchup_clean.csv à jour, skip cleaning matchup")
        else:
            print("Merging teams games...")
            merge_two_teams_games(teamA_abbr, teamB_abbr)
        
        # 5. Préparer le training (skip si training > raw)
        if is_training_data_fresh():
            print("⚡ Training data à jour, skip cleaning training")
        else:
            print("Preparing training data...")
            random_teams = get_training_teams(teamA_abbr, teamB_abbr)
            clean_training_teams(random_teams)
        
        # 6. Vérifier si c'est un match d'aujourd'hui (pour les blessures)
        df_today, _ = get_today_tomorrow()
        is_today = False
        for _, row in df_today.iterrows():
            if (row["home"] == teamA_abbr and row["away"] == teamB_abbr) or \
               (row["home"] == teamB_abbr and row["away"] == teamA_abbr):
                is_today = True
                break
        
        # 7. Gérer les blessures (toujours, pas seulement les matchs d'aujourd'hui)
        print("Processing injuries...")
        teamA_id = get_team_id_from_raw(teamA_abbr)
        teamB_id = get_team_id_from_raw(teamB_abbr)
        
        if teamA_id and teamB_id:
            from new_injury_scraper import update_injuries_clean
            update_injuries_clean(teamA_abbr, teamA_id, teamB_abbr, teamB_id)
        
        # 8. Faire la prédiction (réutiliser les modèles existants si à jour)
        if not is_model_fresh():
            print("Training models...")
            from training1 import train_winner_model, train_score_model
            train_winner_model()
            train_score_model()
        else:
            print("⚡ Modèles à jour, skip training ML")

        print("Making prediction...")
        prediction = predict_current_match(user_team1=teamA_abbr, user_team2=teamB_abbr)
        
        if not prediction:
            return jsonify({"error": "Impossible de faire la prédiction"}), 500

        # 9. Récupérer les données supplémentaires
        teamA_info = TEAMS_MAPPING[teamA_abbr]
        teamB_info = TEAMS_MAPPING[teamB_abbr]
        
        # Stats des équipes
        statsA = get_team_stats(teamA_abbr) or {
            "pts": 0, "reb": 0, "ast": 0, "fg_pct": 0, "fg3_pct": 0, "plus_minus": 0
        }
        statsB = get_team_stats(teamB_abbr) or {
            "pts": 0, "reb": 0, "ast": 0, "fg_pct": 0, "fg3_pct": 0, "plus_minus": 0
        }
        
        # Blessures
        injuriesA = get_injured_players(teamA_abbr)
        injuriesB = get_injured_players(teamB_abbr)
        
        # Impact des blessures
        teamA_id = to_real_id(teamA_abbr)
        teamB_id = to_real_id(teamB_abbr)
        impactA = compute_team_injury_impact(teamA_id, teamB_id) if teamA_id and teamB_id else 0
        impactB = compute_team_injury_impact(teamB_id, teamA_id) if teamA_id and teamB_id else 0
        
        # Calculer le niveau de risque
        confidence = prediction["confidence"]
        if confidence < 55:
            risk_level = "Very Risky"
        elif confidence < 65:
            risk_level = "Risky"
        else:
            risk_level = "Secure"
        
        # Calculer Over/Under
        total = prediction["predicted_total_points"]
        if total < 210:
            over_under = "Lean UNDER"
        elif total < 225:
            over_under = "Neutral"
        else:
            over_under = "Lean OVER"
        
        # Vérifier si c'est un match du programme (aujourd'hui ou demain)
        df_today, df_tomorrow = get_today_tomorrow()
        is_scheduled = False
        for _, row in df_today.iterrows():
            if (row["home"] == teamA_abbr and row["away"] == teamB_abbr) or \
               (row["home"] == teamB_abbr and row["away"] == teamA_abbr):
                is_scheduled = True
                break
        if not is_scheduled:
            for _, row in df_tomorrow.iterrows():
                if (row["home"] == teamA_abbr and row["away"] == teamB_abbr) or \
                   (row["home"] == teamB_abbr and row["away"] == teamA_abbr):
                    is_scheduled = True
                    break
        
        # Construire la réponse
        match_id = f"{teamA_abbr}-{teamB_abbr}-{pd.Timestamp.now().value}"
        result = {
            "matchId": match_id,
            "teamA": {
                "id": teamA_info["id"],
                "name": teamA_info["name"],
                "abbr": teamA_abbr,
                "logo": teamA_info["logo"],
                "color": teamA_info["color"]
            },
            "teamB": {
                "id": teamB_info["id"],
                "name": teamB_info["name"],
                "abbr": teamB_abbr,
                "logo": teamB_info["logo"],
                "color": teamB_info["color"]
            },
            "winner": prediction["winner"],
            "confidence": round(prediction["confidence"], 1),
            "scoreA": round(prediction["pred_teamA"]),
            "scoreB": round(prediction["pred_teamB"]),
            "totalPoints": round(prediction["predicted_total_points"], 1),
            "bettingAnalysis": {
                "riskLevel": risk_level,
                "overUnder": over_under
            },
            "statsA": statsA,
            "statsB": statsB,
            "injuries": {
                "teamA": injuriesA,
                "teamB": injuriesB
            },
            "impactA": round(impactA, 2),
            "impactB": round(impactB, 2),
            "timestamp": datetime.now().isoformat(),
            "isOffSchedule": not is_scheduled,  # True si le match n'est pas dans le programme
            "tokens_remaining": tokens_remaining
        }
        
        # Sauvegarder dans le cache
        db.save_prediction_to_cache(teamA_abbr, teamB_abbr, result)
        
        # Sauvegarder dans l'historique si l'utilisateur est connecté
        if user_id:
            print(f"💾 Sauvegarde de la prédiction dans l'historique pour user_id={user_id}")
            db.save_prediction_to_history(user_id, result)
            print(f"✅ Prédiction sauvegardée avec succès")
        else:
            print("⚠️ Aucun utilisateur connecté - prédiction non sauvegardée dans l'historique")
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        print(f"Erreur lors de la prédiction: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route('/api/news/content', methods=['GET'])
def get_news_content():
    """Scrape le contenu complet d'un article depuis son URL"""
    try:
        import requests
        from bs4 import BeautifulSoup
        
        url = request.args.get('url', '')
        if not url:
            return jsonify({"error": "URL manquante"}), 400
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Chercher le contenu principal de l'article
        # ESPN utilise généralement des classes comme 'article-body', 'StoryBody', etc.
        content = ""
        
        # Essayer différentes méthodes pour trouver le contenu
        article_body = soup.find('div', class_=lambda x: x and ('article-body' in x.lower() or 'story-body' in x.lower() or 'article-content' in x.lower()))
        if article_body:
            # Supprimer les scripts et styles
            for script in article_body(["script", "style", "iframe", "aside"]):
                script.decompose()
            content = article_body.get_text(separator='\n', strip=True)
        else:
            # Fallback: chercher tous les paragraphes dans l'article
            paragraphs = soup.find_all('p')
            content_parts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 50:  # Filtrer les paragraphes trop courts
                    content_parts.append(text)
            content = '\n\n'.join(content_parts[:20])  # Limiter à 20 paragraphes
        
        if not content or len(content) < 100:
            # Si pas de contenu trouvé, retourner un message
            content = "Le contenu complet de l'article n'a pas pu être récupéré. Veuillez consulter l'article original."
        
        return jsonify({"content": content[:5000]})  # Limiter à 5000 caractères
        
    except Exception as e:
        print(f"Erreur scraping contenu article: {e}")
        return jsonify({"error": str(e), "content": ""}), 500


@app.route('/api/news', methods=['GET'])
def get_news():
    """Récupère les dernières actualités NBA depuis ESPN"""
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # Scraper ESPN NBA News
        url = "https://www.espn.com/nba/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []
        
        # Chercher les articles dans les sections ESPN
        articles = soup.find_all(['article', 'div'], class_=lambda x: x and ('story' in x.lower() or 'headline' in x.lower() or 'article' in x.lower()))[:10]
        
        for idx, article in enumerate(articles):
            try:
                title_elem = article.find(['h1', 'h2', 'h3', 'a'], class_=lambda x: x and ('headline' in x.lower() or 'title' in x.lower()))
                if not title_elem:
                    title_elem = article.find('a')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '') if title_elem.name == 'a' else article.find('a', href=True)
                    
                    if link and isinstance(link, dict):
                        link = link.get('href', '')
                    elif hasattr(link, 'get'):
                        link = link.get('href', '')
                    else:
                        link = str(link) if link else ''
                    
                    if not link.startswith('http'):
                        link = f"https://www.espn.com{link}" if link.startswith('/') else f"https://www.espn.com/nba/{link}"
                    
                    desc_elem = article.find('p') or article.find('span', class_=lambda x: x and 'summary' in x.lower())
                    description = desc_elem.get_text(strip=True) if desc_elem else "Lire l'article complet sur ESPN."
                    
                    if title and len(title) > 10:
                        news_items.append({
                            "id": str(idx + 1),
                            "title": title[:150],
                            "description": description[:200] if description else "Lire l'article complet sur ESPN.",
                            "source": "ESPN",
                            "url": link,
                            "publishedAt": datetime.now().isoformat(),
                            "category": "News"
                        })
            except Exception as e:
                print(f"Erreur parsing article: {e}")
                continue
        
        # Si pas assez d'articles, utiliser l'API ESPN
        if len(news_items) < 5:
            try:
                api_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/news"
                api_response = requests.get(api_url, headers=headers, timeout=10)
                if api_response.status_code == 200:
                    data = api_response.json()
                    for item in data.get('articles', [])[:10]:
                        news_items.append({
                            "id": item.get('dataSourceIdentifier', str(len(news_items) + 1)),
                            "title": item.get('headline', '')[:150],
                            "description": item.get('description', 'Lire l\'article complet sur ESPN.')[:200],
                            "source": "ESPN",
                            "url": item.get('links', {}).get('web', {}).get('href', 'https://www.espn.com/nba/'),
                            "publishedAt": item.get('published', datetime.now().isoformat()),
                            "category": "News"
                        })
            except Exception as e:
                print(f"Erreur API ESPN: {e}")
        
        return jsonify({"news": news_items[:10]})
        
    except Exception as e:
        print(f"Erreur scraping news: {e}")
        return jsonify({"news": [], "error": str(e)}), 500


@app.route('/api/recent-scores', methods=['GET'])
def get_recent_scores():
    """Récupère les derniers scores de matchs NBA"""
    try:
        # Vérifier le cache d'abord
        cached_scores = db.get_cached_scores()
        if cached_scores:
            # Vérifier que les scores ne sont pas trop anciens (vérifier la date du dernier match)
            if cached_scores:
                # Le dernier score devrait être d'aujourd'hui ou hier
                today = date.today()
                yesterday = today - timedelta(days=1)
                
                # Vérifier si on a des scores récents (des 7 derniers jours)
                has_recent_scores = False
                seven_days_ago = today - timedelta(days=7)
                
                for score in cached_scores:
                    score_date_str = score.get("date", "")
                    score_date_full = score.get("dateFull")
                    
                    # Utiliser dateFull si disponible (plus fiable)
                    if score_date_full:
                        try:
                            score_date = datetime.fromisoformat(score_date_full).date()
                            if score_date >= seven_days_ago:
                                has_recent_scores = True
                                break
                        except:
                            pass
                    else:
                        # Fallback sur le format "DD MMM"
                        try:
                            score_date = datetime.strptime(f"{score_date_str} {today.year}", "%d %b %Y").date()
                            if score_date >= seven_days_ago:
                                has_recent_scores = True
                                break
                        except:
                            pass
                
                if has_recent_scores:
                    # Filtrer pour ne garder que les scores des 7 derniers jours
                    filtered_scores = []
                    for score in cached_scores:
                        score_date_full = score.get("dateFull")
                        if score_date_full:
                            try:
                                score_date = datetime.fromisoformat(score_date_full).date()
                                if score_date >= seven_days_ago:
                                    filtered_scores.append(score)
                            except:
                                filtered_scores.append(score)  # Garder si erreur de parsing
                        else:
                            filtered_scores.append(score)  # Garder si pas de dateFull
                    
                    if filtered_scores:
                        return jsonify({"scores": filtered_scores})
        
        import requests
        
        # Récupérer les scores récents depuis ESPN
        today = date.today()
        scores = []
        
        # Récupérer les scores des 7 derniers jours
        for i in range(7):
            target_date = today - timedelta(days=i)
            url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
            params = {"dates": target_date.strftime("%Y%m%d")}
            
            try:
                response = requests.get(url, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    events = data.get("events", [])
                    
                    for event in events:
                        comp = event.get("competitions", [{}])[0]
                        competitors = comp.get("competitors", [])
                        
                        if len(competitors) >= 2:
                            home = competitors[0]
                            away = competitors[1]
                            
                            # Vérifier si le match est terminé
                            status = comp.get("status", {}).get("type", {})
                            if status.get("completed", False) or status.get("name", "") == "STATUS_FINAL":
                                home_abbr = home.get("team", {}).get("abbreviation", "")
                                away_abbr = away.get("team", {}).get("abbreviation", "")
                                home_score = int(home.get("score", 0))
                                away_score = int(away.get("score", 0))
                                
                                # Normaliser les abréviations
                                home_abbr = normalize_team_abbr(home_abbr)
                                away_abbr = normalize_team_abbr(away_abbr)
                                
                                if home_abbr and away_abbr:
                                    scores.append({
                                        "id": event.get("id", ""),
                                        "homeTeam": home_abbr,
                                        "awayTeam": away_abbr,
                                        "homeScore": home_score,
                                        "awayScore": away_score,
                                        "date": target_date.strftime("%d %b"),
                                        "dateFull": target_date.isoformat(),  # Date complète pour vérification
                                        "winner": home_abbr if home_score > away_score else away_abbr
                                    })
            except Exception as e:
                print(f"Erreur récupération scores pour {target_date}: {e}")
                continue
        
        # Ne pas limiter - retourner tous les scores des 7 derniers jours
        # Les scores sont déjà triés par date (du plus récent au plus ancien)
        
        # Sauvegarder dans le cache
        if scores:
            db.save_scores_to_cache(scores)
        
        return jsonify({"scores": scores})
        
    except Exception as e:
        print(f"Erreur récupération scores: {e}")
        return jsonify({"scores": []}), 500


@app.route('/api/standings/teams', methods=['GET'])
def get_team_standings():
    """Récupère les classements des équipes NBA pour la saison 2025-26"""
    try:
        import requests
        standings = []
        
        # Méthode 1: ESPN API (fast, reliable)
        print("Tentative avec l'API ESPN...")
        headers_espn = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        
        endpoints = [
            "https://site.api.espn.com/apis/v2/sports/basketball/nba/standings",
            "https://site.web.api.espn.com/apis/v2/sports/basketball/nba/standings"
        ]
        
        for api_url in endpoints:
            try:
                params = {"seasontype": "2", "season": "2026"}
                response = requests.get(api_url, headers=headers_espn, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'children' in data:
                        for conference in data['children']:
                            conf_name = conference.get('name', '').upper()
                            conference_type = "east" if "EAST" in conf_name else "west" if "WEST" in conf_name else None
                            
                            if not conference_type:
                                continue
                            
                            entries = conference.get('standings', {}).get('entries', [])
                            
                            for idx, entry in enumerate(entries, 1):
                                team = entry.get('team', {})
                                stats = entry.get('stats', [])
                                
                                wins = 0
                                losses = 0
                                win_pct = 0.0
                                games_behind = 0.0
                                streak = "-"
                                
                                for stat in stats:
                                    stat_type = stat.get('type', '')
                                    if stat_type == 'wins':
                                        wins = int(stat.get('value', 0))
                                    elif stat_type == 'losses':
                                        losses = int(stat.get('value', 0))
                                    elif stat_type == 'winPercent':
                                        win_pct = float(stat.get('value', 0)) * 100
                                    elif stat_type == 'gamesBehind':
                                        games_behind = float(stat.get('value', 0))
                                    elif stat_type == 'streak':
                                        streak = stat.get('displayValue', '-')
                                
                                team_abbr = normalize_team_abbr(team.get('abbreviation', '') or team.get('abbrev', ''))
                                
                                if team_abbr:
                                    standings.append({
                                        "rank": idx,
                                        "team": team_abbr,
                                        "wins": wins,
                                        "losses": losses,
                                        "winPct": round(win_pct, 1),
                                        "gamesBehind": games_behind,
                                        "streak": streak,
                                        "conference": conference_type
                                    })
                    
                    if len(standings) >= 30:
                        standings.sort(key=lambda x: (x["conference"], x["rank"]))
                        return jsonify({"standings": standings})
            except Exception as e:
                print(f"Erreur API ESPN {api_url}: {e}")
                continue
        
        # Méthode 2 (fallback): Utiliser nba_api si ESPN a échoué
        if not standings:
            try:
                from nba_api.stats.endpoints import LeagueStandings
                print("ESPN échoué → fallback nba_api...")
                
                for season_format in ['2025-26', '2025', '2026']:
                    try:
                        standings_data = LeagueStandings(season=season_format, timeout=60, headers={"Host": "stats.nba.com", "User-Agent": "Mozilla/5.0", "Referer": "https://www.nba.com/", "x-nba-stats-origin": "stats", "x-nba-stats-token": "true"})
                        df = standings_data.get_data_frames()[0]
                        
                        if len(df) > 0:
                            print(f"✅ Données récupérées avec nba_api (saison: {season_format})")
                            
                            east_teams = ["ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DET", "IND", "MIA", "MIL", "NYK", "ORL", "PHI", "TOR", "WAS"]
                            
                            for idx, row in df.iterrows():
                                try:
                                    team_id = int(row.get('TeamID', 0))
                                    team_abbr = from_real_id(team_id)
                                    
                                    if not team_abbr:
                                        team_name_map = {
                                            'Oklahoma City': 'OKC', 'Detroit': 'DET', 'Denver': 'DEN',
                                            'New York': 'NYK', 'Boston': 'BOS', 'Houston': 'HOU',
                                            'Orlando': 'ORL', 'Los Angeles': 'LAL', 'Toronto': 'TOR',
                                            'San Antonio': 'SAS', 'Minnesota': 'MIN', 'Philadelphia': 'PHI',
                                            'Cleveland': 'CLE', 'Phoenix': 'PHX', 'Miami': 'MIA',
                                            'Golden State': 'GSW', 'Memphis': 'MEM', 'Atlanta': 'ATL',
                                            'Dallas': 'DAL', 'Milwaukee': 'MIL', 'Portland': 'POR',
                                            'Chicago': 'CHI', 'Utah': 'UTA', 'Charlotte': 'CHA',
                                            'Sacramento': 'SAC', 'Brooklyn': 'BKN', 'Indiana': 'IND',
                                            'LA': 'LAC', 'New Orleans': 'NOP', 'Washington': 'WAS'
                                        }
                                        full_name = f"{row.get('TeamCity', '')} {row.get('TeamName', '')}"
                                        for key, abbr in team_name_map.items():
                                            if key in full_name:
                                                team_abbr = abbr
                                                break
                                    
                                    if team_abbr:
                                        conference = "east" if team_abbr in east_teams else "west"
                                        wins = int(row.get('WINS', 0))
                                        losses = int(row.get('LOSSES', 0))
                                        win_pct = float(row.get('WinPCT', 0)) * 100
                                        games_behind = float(row.get('ConferenceGamesBack', 0))
                                        streak = str(row.get('Streak', '-'))
                                        
                                        standings.append({
                                            "rank": int(row.get('PlayoffRank', idx + 1)),
                                            "team": team_abbr,
                                            "wins": wins,
                                            "losses": losses,
                                            "winPct": round(win_pct, 1),
                                            "gamesBehind": games_behind,
                                            "streak": streak,
                                            "conference": conference
                                        })
                                except Exception as e:
                                    continue
                            
                            if len(standings) >= 30:
                                standings.sort(key=lambda x: (x["conference"], x["rank"]))
                                return jsonify({"standings": standings})
                    except Exception as e:
                        print(f"Erreur nba_api avec saison {season_format}: {e}")
                        continue
            except ImportError:
                print("nba_api non disponible")
            except Exception as e:
                print(f"Erreur nba_api: {e}")
        
        # Méthode 3: Scraper depuis ESPN.com avec parsing amélioré
        if not standings:
            print("Tentative avec scraping ESPN.com...")
            url = "https://www.espn.com/nba/standings/_/season/2026"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                html_content = response.text
                import re
                from bs4 import BeautifulSoup
                
                # Chercher les données dans les scripts
                soup = BeautifulSoup(html_content, 'html.parser')
                
                for script in soup.find_all('script'):
                    if not script.string:
                        continue
                    
                    script_text = script.string
                    
                    # Chercher le pattern avec les données de standings
                    # Format: "standings":{"groups":[{"name":"Eastern Conference","standings":[...]}]}
                    if '"standings"' in script_text and '"groups"' in script_text:
                        try:
                            # Extraire le JSON depuis le script
                            # Chercher window.__espnfitt__ ou directement les données
                            json_match = re.search(r'window\.__espnfitt__\s*=\s*({.*?});', script_text, re.DOTALL)
                            
                            if json_match:
                                import json as json_lib
                                data = json_lib.loads(json_match.group(1))
                                
                                if 'page' in data and 'content' in data['page']:
                                    content = data['page']['content']
                                    if 'standings' in content and 'groups' in content['standings']:
                                        groups = content['standings']['groups']
                                        
                                        for group in groups:
                                            conf_name = group.get('name', '').upper()
                                            conference = "east" if "EAST" in conf_name else "west" if "WEST" in conf_name else None
                                            
                                            if not conference:
                                                continue
                                            
                                            entries = group.get('standings', [])
                                            
                                            for idx, entry in enumerate(entries, 1):
                                                team = entry.get('team', {})
                                                stats = entry.get('stats', [])
                                                
                                                wins = 0
                                                losses = 0
                                                win_pct = 0.0
                                                games_behind = 0.0
                                                streak = "-"
                                                
                                                # Les stats sont dans un tableau
                                                if len(stats) > 15:
                                                    wl_str = str(stats[15])
                                                    if '-' in wl_str:
                                                        parts = wl_str.split('-')
                                                        wins = int(parts[0].strip())
                                                        losses = int(parts[1].strip())
                                                        win_pct = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0.0
                                                
                                                if len(stats) > 9:
                                                    gb_str = str(stats[9])
                                                    if gb_str and gb_str != '-' and gb_str != '':
                                                        try:
                                                            games_behind = float(gb_str)
                                                        except:
                                                            games_behind = 0.0
                                                
                                                if len(stats) > 12:
                                                    streak = str(stats[12]) if stats[12] else "-"
                                                
                                                if len(stats) > 13:
                                                    try:
                                                        win_pct = float(stats[13]) * 100
                                                    except:
                                                        pass
                                                
                                                team_abbr = normalize_team_abbr(team.get('abbrev', '') or team.get('abbreviation', ''))
                                                
                                                if team_abbr:
                                                    standings.append({
                                                        "rank": idx,
                                                        "team": team_abbr,
                                                        "wins": wins,
                                                        "losses": losses,
                                                        "winPct": round(win_pct, 1),
                                                        "gamesBehind": games_behind,
                                                        "streak": streak,
                                                        "conference": conference
                                                    })
                                        
                                        if len(standings) >= 30:
                                            standings.sort(key=lambda x: (x["conference"], x["rank"]))
                                            return jsonify({"standings": standings})
                        except Exception as e:
                            print(f"Erreur parsing script: {e}")
                            continue
        
        # D'après la réponse HTML précédente, les données sont dans un script avec une structure JSON
        # Chercher directement le pattern avec les données de standings
        # Les données sont dans: "standings":{"groups":[{"name":"Eastern Conference",...}]}
        
        # Essayer d'extraire les données depuis le HTML brut
        # Pattern pour trouver les groupes de standings
        groups_pattern = r'"name":"(Eastern|Western) Conference"[^}]*"standings":\[(.*?)\]'
        groups_matches = re.finditer(groups_pattern, html_content, re.DOTALL)
        
        for group_match in groups_matches:
            conf_name = group_match.group(1).upper()
            conference = "east" if "EAST" in conf_name else "west"
            standings_text = group_match.group(2)
            
            # Parser chaque équipe dans le groupe
            # Format: {"team":{"id":"25","abbrev":"OKC",...},"stats":["106.2","123.6",...]}
            team_pattern = r'\{"team":\{[^}]*"abbrev":"([^"]+)"[^}]*\}[^}]*"stats":\[([^\]]+)\]'
            teams = re.finditer(team_pattern, standings_text)
            
            for idx, team_match in enumerate(teams, 1):
                abbrev = team_match.group(1)
                stats_str = team_match.group(2)
                
                # Parser les stats - format: "106.2","123.6","+17.4","0.833","-","0.952","1","1","+437","11.5","2654","3091","W16",".960","24","24-1",...
                # Les stats sont: [PPG, OPP PPG, DIFF, DPCT, GB, LPCT, POS, PTS, DIFF, GB, PTS, PA, PF, STRK, PCT, W, W-L, HOME, AWAY, DIV, CONF, L10]
                stats = []
                current = ""
                in_quotes = False
                escape_next = False
                
                for char in stats_str:
                    if escape_next:
                        current += char
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        current += char
                        continue
                    
                    if char == '"' and not escape_next:
                        in_quotes = not in_quotes
                    elif char == ',' and not in_quotes:
                        stats.append(current.strip().strip('"'))
                        current = ""
                    else:
                        current += char
                
                if current:
                    stats.append(current.strip().strip('"'))
                
                wins = 0
                losses = 0
                win_pct = 0.0
                games_behind = 0.0
                streak = "-"
                
                # Le record W-L est dans stats[15] (format "24-1")
                if len(stats) > 15:
                    wl = stats[15]
                    if '-' in wl:
                        parts = wl.split('-')
                        try:
                            wins = int(parts[0].strip())
                            losses = int(parts[1].strip())
                            win_pct = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0.0
                        except:
                            pass
                
                # Games Behind dans stats[4] ou stats[9]
                if len(stats) > 9:
                    gb = stats[9]
                    if gb and gb != '-' and gb != '':
                        try:
                            games_behind = float(gb)
                        except:
                            games_behind = 0.0
                
                # Streak dans stats[12]
                if len(stats) > 12:
                    streak = stats[12] if stats[12] else "-"
                
                # Win percentage dans stats[13] (format décimal 0.960)
                if len(stats) > 13:
                    try:
                        win_pct = float(stats[13]) * 100
                    except:
                        pass
                
                team_abbr = normalize_team_abbr(abbrev)
                if team_abbr:
                    standings.append({
                        "rank": idx,
                        "team": team_abbr,
                        "wins": wins,
                        "losses": losses,
                        "winPct": round(win_pct, 1),
                        "gamesBehind": games_behind,
                        "streak": streak,
                        "conference": conference
                    })
        
        # Si toujours vide, essayer avec BeautifulSoup
        if not standings:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Chercher dans tous les scripts
            for script in soup.find_all('script'):
                if not script.string:
                    continue
                
                script_text = script.string
                
                # Chercher la structure avec "standings" et "groups"
                if '"standings"' in script_text and '"groups"' in script_text:
                    try:
                        # Chercher le début de l'objet standings
                        # Format: "standings":{"groups":[{"name":"Eastern Conference","abbreviation":"East","standings":[...]}]}
                        standings_match = re.search(r'"standings":\s*\{[^}]*"groups":\s*\[(.*?)\]', script_text, re.DOTALL)
                        
                        if standings_match:
                            groups_text = standings_match.group(1)
                            
                            # Parser chaque groupe (Eastern et Western)
                            # Chercher chaque groupe: {"name":"...","standings":[...]}
                            group_pattern = r'\{"name":"([^"]+)","abbreviation":"([^"]+)","standings":\[(.*?)\]\}'
                            groups = re.finditer(group_pattern, groups_text, re.DOTALL)
                            
                            for group_match in groups:
                                conf_name = group_match.group(1).upper()
                                conference = "east" if "EAST" in conf_name else "west" if "WEST" in conf_name else None
                                
                                if not conference:
                                    continue
                                
                                standings_text = group_match.group(3)
                                
                                # Parser chaque équipe dans le groupe
                                # Format: {"team":{"id":"25","abbrev":"OKC",...},"stats":["113.3","118.7",...]}
                                team_pattern = r'\{"team":\{[^}]*"abbrev":"([^"]+)"[^}]*\}[^}]*"stats":\[([^\]]+)\]'
                                teams = re.finditer(team_pattern, standings_text)
                                
                                for idx, team_match in enumerate(teams, 1):
                                    abbrev = team_match.group(1)
                                    stats_str = team_match.group(2)
                                    
                                    # Parser les stats - format: "113.3","118.7","+5.4","0.625","-","0.737",...
                                    # Les stats sont: [PPG, OPP PPG, DIFF, DPCT, GB, LPCT, POS, PTS, DIFF, GB, PTS, PA, PF, STRK, PCT, W, W-L, HOME, AWAY, DIV, CONF, L10]
                                    stats = []
                                    current = ""
                                    in_quotes = False
                                    for char in stats_str:
                                        if char == '"' and (not current or current[-1] != '\\'):
                                            in_quotes = not in_quotes
                                        elif char == ',' and not in_quotes:
                                            stats.append(current.strip().strip('"'))
                                            current = ""
                                        else:
                                            current += char
                                    if current:
                                        stats.append(current.strip().strip('"'))
                                    
                                    wins = 0
                                    losses = 0
                                    win_pct = 0.0
                                    games_behind = 0.0
                                    streak = "-"
                                    
                                    # Le record W-L est dans stats[15] (format "24-1")
                                    if len(stats) > 15:
                                        wl = stats[15]
                                        if '-' in wl:
                                            parts = wl.split('-')
                                            try:
                                                wins = int(parts[0].strip())
                                                losses = int(parts[1].strip())
                                                win_pct = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0.0
                                            except:
                                                pass
                                    
                                    # Games Behind dans stats[4] ou stats[9]
                                    if len(stats) > 9:
                                        gb = stats[9]
                                        if gb and gb != '-' and gb != '':
                                            try:
                                                games_behind = float(gb)
                                            except:
                                                games_behind = 0.0
                                    
                                    # Streak dans stats[12]
                                    if len(stats) > 12:
                                        streak = stats[12] if stats[12] else "-"
                                    
                                    # Win percentage dans stats[13] (format décimal 0.960)
                                    if len(stats) > 13:
                                        try:
                                            win_pct = float(stats[13]) * 100
                                        except:
                                            pass
                                    
                                    team_abbr = normalize_team_abbr(abbrev)
                                    if team_abbr:
                                        standings.append({
                                            "rank": idx,
                                            "team": team_abbr,
                                            "wins": wins,
                                            "losses": losses,
                                            "winPct": round(win_pct, 1),
                                            "gamesBehind": games_behind,
                                            "streak": streak,
                                            "conference": conference
                                        })
                        
                        if standings:
                            break
                    except Exception as e:
                        print(f"Erreur parsing script: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
        
        # Si toujours vide, utiliser l'API JSON directe d'ESPN avec la structure correcte
        if not standings:
            print("Tentative avec l'API JSON directe d'ESPN...")
            # Utiliser l'endpoint qui retourne les données de classement
            api_url = "https://site.api.espn.com/apis/v2/sports/basketball/nba/standings"
            params = {"seasontype": "2", "season": "2026"}  # 2 = Regular Season, 2026 = saison 2025-26
            api_response = requests.get(api_url, headers=headers, params=params, timeout=10)
            
            if api_response.status_code == 200:
                try:
                    data = api_response.json()
                    
                    # D'après la structure vue précédemment, les données sont dans page.content.standings.groups
                    if 'page' in data and 'content' in data['page']:
                        content = data['page']['content']
                        if 'standings' in content and 'groups' in content['standings']:
                            groups = content['standings']['groups']
                            
                            for group in groups:
                                conf_name = group.get('name', '').upper()
                                conference = "east" if "EAST" in conf_name else "west" if "WEST" in conf_name else None
                                
                                if not conference:
                                    continue
                                
                                entries = group.get('standings', [])
                                
                                for idx, entry in enumerate(entries, 1):
                                    team = entry.get('team', {})
                                    stats = entry.get('stats', [])
                                    
                                    wins = 0
                                    losses = 0
                                    win_pct = 0.0
                                    games_behind = 0.0
                                    streak = "-"
                                    
                                    # Les stats sont dans un tableau: ["PPG", "OPP PPG", "DIFF", "DPCT", "GB", "LPCT", "POS", "PTS", "DIFF", "GB", "PTS", "PA", "PF", "STRK", "PCT", "W", "W-L", "HOME", "AWAY", "DIV", "CONF", "L10"]
                                    if len(stats) > 15:
                                        # W-L record dans stats[15] (format "24-1")
                                        wl_str = str(stats[15])
                                        if '-' in wl_str:
                                            parts = wl_str.split('-')
                                            wins = int(parts[0].strip())
                                            losses = int(parts[1].strip())
                                            win_pct = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0.0
                                    
                                    if len(stats) > 9:
                                        # Games Behind dans stats[9]
                                        gb_str = str(stats[9])
                                        if gb_str and gb_str != '-' and gb_str != '':
                                            try:
                                                games_behind = float(gb_str)
                                            except:
                                                games_behind = 0.0
                                    
                                    if len(stats) > 12:
                                        # Streak dans stats[12]
                                        streak = str(stats[12]) if stats[12] else "-"
                                    
                                    if len(stats) > 13:
                                        # Win percentage dans stats[13] (format décimal 0.960)
                                        try:
                                            win_pct = float(stats[13]) * 100
                                        except:
                                            pass
                                    
                                    team_abbr = normalize_team_abbr(team.get('abbrev', '') or team.get('abbreviation', ''))
                                    
                                    if team_abbr:
                                        standings.append({
                                            "rank": idx,
                                            "team": team_abbr,
                                            "wins": wins,
                                            "losses": losses,
                                            "winPct": round(win_pct, 1),
                                            "gamesBehind": games_behind,
                                            "streak": streak,
                                            "conference": conference
                                        })
                except Exception as e:
                    print(f"Erreur parsing API JSON: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Trier par conférence puis par rang
        standings.sort(key=lambda x: (x["conference"], x["rank"]))
        
        # Vérifier qu'on a toutes les équipes (30)
        if len(standings) < 30:
            print(f"⚠️ Attention: seulement {len(standings)} équipes trouvées sur 30")
        else:
            print(f"✅ {len(standings)} équipes récupérées avec succès")
        
        return jsonify({"standings": standings})
        
    except Exception as e:
        import traceback
        print(f"Erreur récupération standings équipes: {e}")
        print(traceback.format_exc())
        return jsonify({"standings": [], "error": str(e)}), 500


@app.route('/api/standings/players', methods=['GET'])
def get_player_standings():
    """Récupère les classements des joueurs NBA (points, rebonds, passes décisives)"""
    try:
        import requests
        
        # Récupérer le paramètre de catégorie (points, rebounds, assists)
        category = request.args.get('category', 'points')  # 'points', 'rebounds', 'assists'
        # Récupérer le paramètre pour moyennes (PPG/RPG/APG) vs totaux
        averages = request.args.get('averages', 'true').lower() == 'true'
        
        standings = []
        
        # Méthode 1: ESPN API (fast, reliable)
        try:
            print(f"Tentative ESPN pour les stats joueurs (catégorie: {category})...")
            headers_espn = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/statistics"
            if category == 'points':
                params = {"contentorigin": "espn", "limit": "50", "statType": "scoring"}
            elif category == 'rebounds':
                params = {"contentorigin": "espn", "limit": "50", "statType": "rebounding"}
            elif category == 'assists':
                params = {"contentorigin": "espn", "limit": "50", "statType": "assists"}
            else:
                params = {"contentorigin": "espn", "limit": "50", "statType": "scoring"}
            
            response = requests.get(url, headers=headers_espn, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                athletes = data.get('athletes', [])
                
                for idx, athlete_data in enumerate(athletes[:50], 1):
                    athlete = athlete_data.get('athlete', {})
                    stats_list = athlete_data.get('stats', [])
                    
                    name = athlete.get('displayName', '')
                    team_info = athlete.get('team', {})
                    team_abbr = normalize_team_abbr(team_info.get('abbreviation', ''))
                    position = athlete.get('position', {}).get('abbreviation', '')
                    
                    # ESPN stats vary by category, but typically include pts, reb, ast
                    pts = 0.0
                    reb = 0.0
                    ast = 0.0
                    
                    # Try to get stats from the categories
                    categories = data.get('categories', [])
                    if stats_list and categories:
                        stat_map = {}
                        for i, cat in enumerate(categories):
                            cat_name = cat.get('name', '').lower()
                            if i < len(stats_list):
                                try:
                                    stat_map[cat_name] = float(stats_list[i])
                                except (ValueError, TypeError):
                                    pass
                        
                        pts = stat_map.get('points', stat_map.get('pts', 0.0))
                        reb = stat_map.get('rebounds', stat_map.get('reb', 0.0))
                        ast = stat_map.get('assists', stat_map.get('ast', 0.0))
                    
                    if name:
                        standings.append({
                            "rank": idx,
                            "name": name,
                            "team": team_abbr or "",
                            "points": round(pts, 1),
                            "rebounds": round(reb, 1),
                            "assists": round(ast, 1),
                            "position": position
                        })
                
                if len(standings) > 0:
                    return jsonify({"standings": standings})
        except Exception as e:
            print(f"Erreur API ESPN stats: {e}")
        
        # Méthode 2 (fallback): nba_api — slower but comprehensive
        if not standings:
            try:
                from nba_api.stats.endpoints import LeagueLeaders
                print(f"ESPN échoué → fallback nba_api (catégorie: {category})...")
                
                for season_format in ['2025-26', '2025', '2026']:
                    try:
                        nba_headers = {"Host": "stats.nba.com", "User-Agent": "Mozilla/5.0", "Referer": "https://www.nba.com/", "x-nba-stats-origin": "stats", "x-nba-stats-token": "true"}
                        if category == 'points':
                            leaders = LeagueLeaders(season=season_format, stat_category_abbreviation='PTS', timeout=60, headers=nba_headers)
                        elif category == 'rebounds':
                            leaders = LeagueLeaders(season=season_format, stat_category_abbreviation='REB', timeout=60, headers=nba_headers)
                        elif category == 'assists':
                            leaders = LeagueLeaders(season=season_format, stat_category_abbreviation='AST', timeout=60, headers=nba_headers)
                        else:
                            leaders = LeagueLeaders(season=season_format, stat_category_abbreviation='PTS', timeout=60, headers=nba_headers)
                        
                        df = leaders.get_data_frames()[0]
                        
                        if len(df) > 0:
                            print(f"✅ Données récupérées avec nba_api (saison: {season_format}, catégorie: {category})")
                            
                            all_stats = LeagueLeaders(season=season_format, stat_category_abbreviation='PTS', timeout=60, headers=nba_headers)
                            all_df = all_stats.get_data_frames()[0]
                            
                            stats_dict = {}
                            for idx, row in all_df.iterrows():
                                player_id = int(row.get('PLAYER_ID', 0))
                                games_played = float(row.get('GP', 0))
                                pts_total = float(row.get('PTS', 0))
                                reb_total = float(row.get('REB', 0))
                                ast_total = float(row.get('AST', 0))
                                
                                if games_played > 0 and averages:
                                    pts = pts_total / games_played
                                    reb = reb_total / games_played
                                    ast = ast_total / games_played
                                else:
                                    pts = pts_total
                                    reb = reb_total
                                    ast = ast_total
                                
                                stats_dict[player_id] = {
                                    'PTS': pts, 'REB': reb, 'AST': ast,
                                    'TEAM_ABBREVIATION': str(row.get('TEAM_ABBREVIATION', '')),
                                    'PLAYER': str(row.get('PLAYER', '')),
                                    'POSITION': str(row.get('POSITION', ''))
                                }
                            
                            if category == 'points':
                                df = df.sort_values('PTS', ascending=False)
                            elif category == 'rebounds':
                                df = df.sort_values('REB', ascending=False)
                            elif category == 'assists':
                                df = df.sort_values('AST', ascending=False)
                            
                            for idx, row in df.head(50).iterrows():
                                player_id = int(row.get('PLAYER_ID', 0))
                                if player_id in stats_dict:
                                    player_stats = stats_dict[player_id]
                                    team_abbr = normalize_team_abbr(player_stats['TEAM_ABBREVIATION'])
                                    standings.append({
                                        "rank": len(standings) + 1,
                                        "name": player_stats['PLAYER'],
                                        "team": team_abbr or player_stats['TEAM_ABBREVIATION'],
                                        "points": round(player_stats['PTS'], 1),
                                        "rebounds": round(player_stats['REB'], 1),
                                        "assists": round(player_stats['AST'], 1),
                                        "position": player_stats['POSITION']
                                    })
                            
                            if len(standings) > 0:
                                return jsonify({"standings": standings})
                                
                    except Exception as e:
                        print(f"Erreur nba_api avec saison {season_format}: {e}")
                        continue
                        
            except ImportError:
                print("nba_api non disponible")
            except Exception as e:
                print(f"Erreur nba_api: {e}")
        
        # Fallback: Données mockées basées sur des stats réelles de la saison 2025-26
        if len(standings) == 0:
            print("Utilisation de données mockées...")
            # Données en moyennes par match (PPG, RPG, APG) pour la saison 2025-26
            mock_players_data = [
                {"name": "Shai Gilgeous-Alexander", "team": "OKC", "points_avg": 31.2, "rebounds_avg": 5.8, "assists_avg": 6.4, "position": "PG", "games": 25},
                {"name": "Luka Dončić", "team": "DAL", "points_avg": 30.5, "rebounds_avg": 9.1, "assists_avg": 9.8, "position": "PG", "games": 24},
                {"name": "Giannis Antetokounmpo", "team": "MIL", "points_avg": 30.1, "rebounds_avg": 11.2, "assists_avg": 6.2, "position": "PF", "games": 23},
                {"name": "Joel Embiid", "team": "PHI", "points_avg": 29.8, "rebounds_avg": 11.0, "assists_avg": 5.1, "position": "C", "games": 22},
                {"name": "Jayson Tatum", "team": "BOS", "points_avg": 28.5, "rebounds_avg": 8.7, "assists_avg": 4.9, "position": "SF", "games": 25},
                {"name": "Stephen Curry", "team": "GSW", "points_avg": 27.8, "rebounds_avg": 4.5, "assists_avg": 5.2, "position": "PG", "games": 24},
                {"name": "Kevin Durant", "team": "PHX", "points_avg": 27.3, "rebounds_avg": 6.7, "assists_avg": 5.0, "position": "PF", "games": 23},
                {"name": "Devin Booker", "team": "PHX", "points_avg": 26.8, "rebounds_avg": 4.6, "assists_avg": 6.9, "position": "SG", "games": 24},
                {"name": "Anthony Edwards", "team": "MIN", "points_avg": 26.5, "rebounds_avg": 5.2, "assists_avg": 5.1, "position": "SG", "games": 24},
                {"name": "LeBron James", "team": "LAL", "points_avg": 25.8, "rebounds_avg": 7.3, "assists_avg": 8.2, "position": "SF", "games": 23},
            ]
            
            # Calculer les valeurs selon le mode (moyennes ou totaux)
            for player in mock_players_data:
                if averages:
                    # Mode moyennes: utiliser les moyennes par match de la saison 2025-26
                    player['points'] = player['points_avg']
                    player['rebounds'] = player['rebounds_avg']
                    player['assists'] = player['assists_avg']
                else:
                    # Mode totaux: calculer les totaux de la saison 2025-26 (moyenne × matchs joués)
                    player['points'] = round(player['points_avg'] * player['games'], 1)
                    player['rebounds'] = round(player['rebounds_avg'] * player['games'], 1)
                    player['assists'] = round(player['assists_avg'] * player['games'], 1)
            
            # Trier selon la catégorie
            if category == 'points':
                mock_players_data.sort(key=lambda x: x['points'], reverse=True)
            elif category == 'rebounds':
                mock_players_data.sort(key=lambda x: x['rebounds'], reverse=True)
            elif category == 'assists':
                mock_players_data.sort(key=lambda x: x['assists'], reverse=True)
            
            for idx, player in enumerate(mock_players_data[:50], 1):
                standings.append({
                    "rank": idx,
                    "name": player["name"],
                    "team": player["team"],
                    "points": round(player["points"], 1),
                    "rebounds": round(player["rebounds"], 1),
                    "assists": round(player["assists"], 1),
                    "position": player["position"]
                })
        
        return jsonify({"standings": standings})
        
    except Exception as e:
        import traceback
        print(f"Erreur récupération standings joueurs: {e}")
        traceback.print_exc()
        return jsonify({"standings": []}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Endpoint de santé"""
    return jsonify({"status": "ok"})


# ============================================================
# ENDPOINTS D'AUTHENTIFICATION
# ============================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Inscription d'un nouvel utilisateur"""
    try:
        data = request.json
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        username = data.get("username", "").strip()
        plan = data.get("plan", "free").strip().lower()
        referral_code_input = data.get("referralCode", "").strip()

        valid_plans = ["free", "basic", "premium", "vip"]
        if plan not in valid_plans:
            plan = "free"

        # Validation
        if not email or "@" not in email:
            return jsonify({"error": "Email invalide"}), 400
        
        if not password or len(password) < 6:
            return jsonify({"error": "Le mot de passe doit contenir au moins 6 caractères"}), 400

        # Vérifier si l'utilisateur existe déjà
        if db.find_user_by_email(email):
            return jsonify({"error": "Cet email est déjà utilisé"}), 400

        # Créer l'utilisateur
        password_hashed = hash_password(password)
        user = db.create_user(email, password_hashed, username, subscription_tier=plan, referral_code_input=referral_code_input)
        if not user:
            return jsonify({"error": "Erreur lors de la création du compte"}), 500

        # Créer un token JWT pour que le frontend puisse afficher la page d'attente
        access_token = create_access_token(identity=str(user["id"]))

        return jsonify({
            "message": "Compte créé avec succès. En attente de validation par un administrateur.",
            "token": access_token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "username": user["username"],
                "role": user.get("role", "user"),
                "subscription_tier": user.get("subscription_tier", "free"),
                "tokens": user.get("tokens", 10),
                "diamonds": user.get("diamonds", 0),
                "referral_code": user.get("referral_code", ""),
                "approved": user.get("approved", 0)
            }
        }), 201

    except Exception as e:
        print(f"Erreur lors de l'inscription: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Connexion d'un utilisateur"""
    try:
        data = request.json
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"error": "Email et mot de passe requis"}), 400

        # Trouver l'utilisateur
        user = db.find_user_by_email(email)
        if not user:
            return jsonify({"error": "Email ou mot de passe incorrect"}), 401

        # Vérifier le mot de passe
        if not verify_password(user["password_hash"], password):
            return jsonify({"error": "Email ou mot de passe incorrect"}), 401

        # Vérifier si le compte est approuvé
        # On autorise la connexion même en attente pour accéder à la messagerie
        # Le frontend bloquera l'accès grâce à user.approved == 0
        # if user.get("approved", 0) != 1:
        #     return jsonify({"error": "Compte en attente de validation par un administrateur."}), 403

        # Créer le token JWT (l'identity doit être une string)
        access_token = create_access_token(identity=str(user["id"]))

        return jsonify({
            "message": "Connexion réussie",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "username": user["username"],
                "role": user.get("role", "user"),
                "subscription_tier": user.get("subscription_tier", "free"),
                "tokens": user.get("tokens", 10),
                "diamonds": user.get("diamonds", 0),
                "referral_code": user.get("referral_code", ""),
                "approved": user.get("approved", 0)
            },
            "token": access_token
        }), 200

    except Exception as e:
        print(f"Erreur lors de la connexion: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Récupère les informations de l'utilisateur connecté"""
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Token manquant"}), 401
        
        token = auth_header.split(' ')[1]
        from flask_jwt_extended import decode_token
        try:
            decoded = decode_token(token)
            user_id = decoded.get('sub')
            if not user_id:
                return jsonify({"error": "ID utilisateur manquant dans le token"}), 401
            # S'assurer que user_id est une string pour la comparaison
            user_id = str(user_id)
        except Exception as e:
            print(f"Erreur décodage token /me: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"Token invalide: {str(e)}"}), 401
        
        user = db.find_user_by_id(user_id)
        if not user:
            return jsonify({"error": "Utilisateur non trouvé"}), 404

        return jsonify({
            "user": {
                "id": user["id"],
                "email": user["email"],
                "username": user["username"],
                "role": user.get("role", "user"),
                "subscription_tier": user.get("subscription_tier", "free"),
                "tokens": user.get("tokens", 10),
                "diamonds": user.get("diamonds", 0),
                "referral_code": user.get("referral_code", ""),
                "approved": user.get("approved", 0)
            }
        }), 200

    except Exception as e:
        print(f"Erreur lors de la récupération de l'utilisateur: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Déconnexion (côté client, on supprime juste le token)"""
    return jsonify({"message": "Déconnexion réussie"}), 200


@app.route('/api/auth/profile', methods=['PUT'])
def update_profile():
    """Met à jour le profil de l'utilisateur (username, email)"""
    try:
        # Récupérer le token depuis les headers
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Token manquant"}), 401
        
        token = auth_header.split(' ')[1]
        if not token:
            return jsonify({"error": "Token vide"}), 401
        
        from flask_jwt_extended import decode_token
        try:
            decoded = decode_token(token)
            user_id = decoded.get('sub')
            if not user_id:
                return jsonify({"error": "ID utilisateur manquant dans le token"}), 401
            user_id = str(user_id)
        except Exception as e:
            return jsonify({"error": f"Token invalide: {str(e)}"}), 401
        
        # Trouver l'utilisateur
        user = db.find_user_by_id(user_id)
        if not user:
            return jsonify({"error": "Utilisateur non trouvé"}), 404
        
        data = request.json
        new_username = data.get("username", "").strip()
        new_email = data.get("email", "").strip().lower()
        
        # Validation
        if not new_username:
            return jsonify({"error": "Le nom d'utilisateur est requis"}), 400
        
        if not new_email or "@" not in new_email:
            return jsonify({"error": "Email invalide"}), 400
        
        # Vérifier si l'email est déjà utilisé par un autre utilisateur
        existing_user = db.find_user_by_email(new_email)
        if existing_user and existing_user["id"] != user["id"]:
            return jsonify({"error": "Cet email est déjà utilisé"}), 400
        
        # Mettre à jour l'utilisateur
        db.update_user_profile(user_id, new_email, new_username)
        
        return jsonify({
            "message": "Profil mis à jour avec succès",
            "user": {
                "id": user["id"],
                "email": new_email,
                "username": new_username,
                "role": user.get("role", "user"),
                "subscription_tier": user.get("subscription_tier", "free"),
                "tokens": user.get("tokens", 10),
                "diamonds": user.get("diamonds", 0),
                "referral_code": user.get("referral_code", "")
            }
        }), 200
    except Exception as e:
        import traceback
        print(f"Erreur mise à jour profil: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/auth/change-password', methods=['PUT'])
def change_password():
    """Change le mot de passe de l'utilisateur"""
    try:
        # Récupérer le token depuis les headers
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Token manquant"}), 401
        
        token = auth_header.split(' ')[1]
        if not token:
            return jsonify({"error": "Token vide"}), 401
        
        from flask_jwt_extended import decode_token
        try:
            decoded = decode_token(token)
            user_id = decoded.get('sub')
            if not user_id:
                return jsonify({"error": "ID utilisateur manquant dans le token"}), 401
            user_id = str(user_id)
        except Exception as e:
            return jsonify({"error": f"Token invalide: {str(e)}"}), 401
        
        # Trouver l'utilisateur
        user = db.find_user_by_id(user_id)
        if not user:
            return jsonify({"error": "Utilisateur non trouvé"}), 404
        
        data = request.json
        current_password = data.get("currentPassword", "")
        new_password = data.get("newPassword", "")
        
        # Validation
        if not current_password:
            return jsonify({"error": "Le mot de passe actuel est requis"}), 400
        
        if not new_password or len(new_password) < 6:
            return jsonify({"error": "Le nouveau mot de passe doit contenir au moins 6 caractères"}), 400
        
        # Vérifier le mot de passe actuel
        if not verify_password(user["password_hash"], current_password):
            return jsonify({"error": "Mot de passe actuel incorrect"}), 401
        
        # Mettre à jour le mot de passe
        db.update_user_password(user_id, hash_password(new_password))
        
        return jsonify({
            "message": "Mot de passe modifié avec succès"
        }), 200
    except Exception as e:
        import traceback
        print(f"Erreur changement mot de passe: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/game-result', methods=['GET'])
def get_game_result():
    """Récupère le résultat réel d'un match spécifique"""
    try:
        teamA = request.args.get('teamA', '')
        teamB = request.args.get('teamB', '')
        match_date = request.args.get('date', '')  # Date du match en ISO format
        
        if not teamA or not teamB:
            return jsonify({"error": "teamA et teamB sont requis"}), 400
        
        # Normaliser les abréviations
        teamA = normalize_team_abbr(teamA)
        teamB = normalize_team_abbr(teamB)
        
        # Si une date est fournie, chercher ce jour-là, sinon chercher dans les 7 derniers jours
        import requests
        from datetime import date, timedelta
        
        search_dates = []
        if match_date:
            try:
                target_date = datetime.fromisoformat(match_date).date()
                search_dates = [target_date]
            except:
                pass
        
        # Si pas de date ou erreur, chercher dans les 7 derniers jours
        if not search_dates:
            today = date.today()
            search_dates = [today - timedelta(days=i) for i in range(7)]
        
        # Chercher le match dans les scores récents
        for target_date in search_dates:
            url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
            params = {"dates": target_date.strftime("%Y%m%d")}
            
            try:
                response = requests.get(url, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    events = data.get("events", [])
                    
                    for event in events:
                        comp = event.get("competitions", [{}])[0]
                        competitors = comp.get("competitors", [])
                        
                        if len(competitors) >= 2:
                            home = competitors[0]
                            away = competitors[1]
                            
                            home_abbr = normalize_team_abbr(home.get("team", {}).get("abbreviation", ""))
                            away_abbr = normalize_team_abbr(away.get("team", {}).get("abbreviation", ""))
                            
                            # Vérifier si c'est le match recherché (peu importe l'ordre)
                            if ((home_abbr == teamA and away_abbr == teamB) or 
                                (home_abbr == teamB and away_abbr == teamA)):
                                
                                # Vérifier si le match est terminé
                                status = comp.get("status", {}).get("type", {})
                                is_completed = status.get("completed", False) or status.get("name", "") == "STATUS_FINAL"
                                
                                if is_completed:
                                    home_score = int(home.get("score", 0))
                                    away_score = int(away.get("score", 0))
                                    actual_winner = home_abbr if home_score > away_score else away_abbr
                                    
                                    # Déterminer quel équipe correspond à teamA et teamB de la prédiction
                                    # L'ordre peut être différent, donc on retourne les deux possibilités
                                    return jsonify({
                                        "completed": True,
                                        "homeTeam": home_abbr,
                                        "awayTeam": away_abbr,
                                        "homeScore": home_score,
                                        "awayScore": away_score,
                                        "actualWinner": actual_winner,
                                        "date": target_date.isoformat(),
                                        # Ajouter les scores par équipe pour faciliter la correspondance
                                        "scores": {
                                            home_abbr: home_score,
                                            away_abbr: away_score
                                        }
                                    })
                                else:
                                    return jsonify({
                                        "completed": False,
                                        "date": target_date.isoformat()
                                    })
            except Exception as e:
                print(f"Erreur récupération résultat pour {target_date}: {e}")
                continue
        
        # Match non trouvé ou pas encore joué
        return jsonify({
            "completed": False,
            "message": "Match non trouvé ou pas encore joué"
        })
        
    except Exception as e:
        print(f"Erreur récupération résultat match: {e}")
        return jsonify({"error": str(e), "completed": False}), 500


@app.route('/api/history/<match_id>', methods=['DELETE'])
def delete_prediction(match_id):
    """Supprime une prédiction de l'historique de l'utilisateur"""
    try:
        # Récupérer le token depuis les headers
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Token manquant"}), 401
        
        token = auth_header.split(' ')[1]
        if not token:
            return jsonify({"error": "Token vide"}), 401
        
        from flask_jwt_extended import decode_token
        try:
            decoded = decode_token(token)
            user_id = decoded.get('sub')
            if not user_id:
                return jsonify({"error": "ID utilisateur manquant dans le token"}), 401
            user_id = str(user_id)
        except Exception as e:
            return jsonify({"error": f"Token invalide: {str(e)}"}), 401
        
        # Trouver l'utilisateur
        user = db.find_user_by_id(user_id)
        if not user:
            return jsonify({"error": "Utilisateur non trouvé"}), 404
        
        # Supprimer la prédiction de l'historique
        deleted = db.delete_prediction_from_history(user_id, match_id)
        if deleted:
            return jsonify({"message": "Prédiction supprimée avec succès"}), 200
        
        return jsonify({"error": "Prédiction non trouvée"}), 404
        
    except Exception as e:
        print(f"Erreur suppression prédiction: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Récupère l'historique des prédictions de l'utilisateur connecté"""
    try:
        # Récupérer le token depuis les headers
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Token manquant", "history": []}), 401
        
        token = auth_header.split(' ')[1]
        if not token:
            return jsonify({"error": "Token vide", "history": []}), 401
        
        from flask_jwt_extended import decode_token
        try:
            # decode_token nécessite le contexte de l'application Flask
            decoded = decode_token(token)
            user_id = decoded.get('sub')
            if not user_id:
                return jsonify({"error": "ID utilisateur manquant dans le token", "history": []}), 401
            # S'assurer que user_id est une string pour la comparaison
            user_id = str(user_id)
        except Exception as e:
            print(f"Erreur décodage token: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"Token invalide: {str(e)}", "history": []}), 401
        
        print(f"Récupération historique pour user_id: {user_id}")
        history = db.get_user_history(user_id)
        print(f"Historique trouvé: {len(history)} prédictions")
        return jsonify({"history": history}), 200
    except Exception as e:
        print(f"Erreur récupération historique: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "history": []}), 500


# ============================================================
# ADMIN ENDPOINTS
# ============================================================

def get_admin_user_from_token():
    """Helper: extract user from Authorization header and verify admin role. Returns (user, error_response)."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, (jsonify({"error": "Token manquant"}), 401)
    token = auth_header.split(' ')[1]
    from flask_jwt_extended import decode_token
    try:
        decoded = decode_token(token)
        user_id = decoded.get('sub')
        if not user_id:
            return None, (jsonify({"error": "Token invalide"}), 401)
    except Exception:
        return None, (jsonify({"error": "Token invalide"}), 401)
    user = db.find_user_by_id(user_id)
    if not user:
        return None, (jsonify({"error": "Utilisateur non trouvé"}), 404)
    if user.get('role') != 'admin':
        return None, (jsonify({"error": "Accès refusé — admin uniquement"}), 403)
    return user, None


@app.route('/api/admin/users', methods=['GET'])
def admin_get_users():
    """Admin: list all users with their prediction counts and history."""
    try:
        admin, err = get_admin_user_from_token()
        if err:
            return err
        users = db.get_all_users_with_history()
        return jsonify({"users": users}), 200
    except Exception as e:
        print(f"Erreur admin get users: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/users/<int:user_id>/history', methods=['GET'])
def admin_get_user_history(user_id):
    """Admin: get prediction history for a specific user."""
    try:
        admin, err = get_admin_user_from_token()
        if err:
            return err
        target = db.find_user_by_id(user_id)
        if not target:
            return jsonify({"error": "Utilisateur non trouvé"}), 404
        history = db.get_user_history(user_id)
        return jsonify({
            "user": {
                "id": target["id"],
                "email": target["email"],
                "username": target["username"],
                "role": target.get("role", "user")
            },
            "history": history
        }), 200
    except Exception as e:
        print(f"Erreur admin get user history: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def admin_delete_user(user_id):
    """Admin: delete a user and their data."""
    try:
        admin, err = get_admin_user_from_token()
        if err:
            return err
        # Prevent admin from deleting themselves
        if admin["id"] == user_id:
            return jsonify({"error": "Impossible de supprimer votre propre compte"}), 400
        deleted = db.delete_user(user_id)
        if deleted:
            return jsonify({"message": "Utilisateur supprimé avec succès"}), 200
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    except Exception as e:
        print(f"Erreur admin delete user: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/users/<int:user_id>/approve', methods=['PUT'])
def admin_approve_user(user_id):
    """Admin: approve a user."""
    try:
        admin, err = get_admin_user_from_token()
        if err:
            return err
        target = db.find_user_by_id(user_id)
        if not target:
            return jsonify({"error": "Utilisateur non trouvé"}), 404
        if db.approve_user(user_id):
            return jsonify({"message": "Utilisateur approuvé avec succès"}), 200
        return jsonify({"error": "Impossible d'approuver l'utilisateur"}), 500
    except Exception as e:
        print(f"Erreur admin approve user: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/users/<int:user_id>/suspend', methods=['PUT'])
def admin_suspend_user(user_id):
    """Admin: suspend an approved user (put back to pending)."""
    try:
        admin, err = get_admin_user_from_token()
        if err:
            return err
        target = db.find_user_by_id(user_id)
        if not target:
            return jsonify({"error": "Utilisateur non trouvé"}), 404
        if db.suspend_user(user_id):
            return jsonify({"message": "Utilisateur remis en attente"}), 200
        return jsonify({"error": "Impossible de mettre en attente"}), 500
    except Exception as e:
        print(f"Erreur admin suspend user: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/users/<int:user_id>/role', methods=['PUT'])
def admin_set_user_role(user_id):
    """Admin: toggle a user's role between 'user' and 'admin'."""
    try:
        admin, err = get_admin_user_from_token()
        if err:
            return err
        if admin["id"] == user_id:
            return jsonify({"error": "Impossible de modifier votre propre rôle"}), 400
        target = db.find_user_by_id(user_id)
        if not target:
            return jsonify({"error": "Utilisateur non trouvé"}), 404
        data = request.json
        new_role = data.get("role", "user")
        if new_role not in ("user", "admin"):
            return jsonify({"error": "Rôle invalide"}), 400
        db.set_user_role(user_id, new_role)
        return jsonify({"message": f"Rôle mis à jour : {new_role}", "role": new_role}), 200
    except Exception as e:
        print(f"Erreur admin set role: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/users/<int:user_id>/subscription', methods=['PUT'])
@jwt_required()
def admin_update_subscription(user_id):
    """Admin: update a user's subscription tier."""
    try:
        admin, err = get_admin_user_from_token()
        if err:
            return err
        target = db.find_user_by_id(user_id)
        if not target:
            return jsonify({"error": "Utilisateur non trouvé"}), 404
            
        data = request.json
        tier = data.get("tier", "free")
        if tier not in ["free", "basic", "premium", "vip"]:
            return jsonify({"error": "Forfait invalide"}), 400
            
        if db.update_user_subscription(user_id, tier):
            return jsonify({"message": f"Abonnement mis à jour vers {tier}"}), 200
        return jsonify({"error": "Impossible de mettre à jour l'abonnement"}), 500
    except Exception as e:
        print(f"Erreur admin update subscription: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/users/<int:user_id>/tokens/add', methods=['POST'])
@jwt_required()
def admin_add_tokens(user_id):
    """Admin: add tokens to a user's account."""
    try:
        admin, err = get_admin_user_from_token()
        if err:
            return err
        target = db.find_user_by_id(user_id)
        if not target:
            return jsonify({"error": "Utilisateur non trouvé"}), 404

        data = request.json
        amount = int(data.get("amount", 0))
        if amount <= 0 or amount > 10000:
            return jsonify({"error": "Montant invalide (1–10000)"}), 400

        if db.add_user_tokens(user_id, amount):
            updated = db.find_user_by_id(user_id)
            new_tokens = updated.get("tokens", 0) if updated else target.get("tokens", 0) + amount
            return jsonify({"message": f"{amount} jetons ajoutés", "new_tokens": new_tokens}), 200
        return jsonify({"error": "Impossible d'ajouter les jetons"}), 500
    except Exception as e:
        print(f"Erreur admin add tokens: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# ENDPOINTS MESSAGERIE
# ============================================================

@app.route('/api/messages/<user_id>', methods=['GET'])
@jwt_required()
def get_user_messages(user_id):
    """Récupère les messages d'un utilisateur (pour l'admin ou lui-même)"""
    try:
        current_user_id = str(get_jwt_identity())
        user = db.find_user_by_id(current_user_id)
        if not user:
            return jsonify({"error": "Non autorisé"}), 401
            
        if user.get("role") != "admin" and str(current_user_id) != str(user_id):
            return jsonify({"error": "Accès refusé"}), 403
            
        messages = db.get_user_messages(user_id)
        return jsonify({"messages": messages}), 200
    except Exception as e:
        print(f"Erreur get_user_messages: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/messages/<user_id>', methods=['POST'])
@jwt_required()
def send_user_message(user_id):
    """Envoie un message via la plateforme"""
    try:
        current_user_id = str(get_jwt_identity())
        user = db.find_user_by_id(current_user_id)
        if not user:
            return jsonify({"error": "Non autorisé"}), 401
            
        if user.get("role") != "admin" and str(current_user_id) != str(user_id):
            return jsonify({"error": "Accès refusé"}), 403
            
        data = request.json
        content = data.get("content", "").strip()
        if not content:
            return jsonify({"error": "Message vide"}), 400
            
        sender = "admin" if user.get("role") == "admin" else "user"
        message = db.add_message(user_id, sender, content)
        
        return jsonify(message), 201
    except Exception as e:
        print(f"Erreur send_user_message: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# ENDPOINTS DEMANDES DE RETRAIT
# ============================================================

@app.route('/api/withdrawals', methods=['POST'])
@jwt_required()
def create_withdrawal():
    """User: submit a withdrawal request with their crypto address."""
    try:
        user_id = str(get_jwt_identity())
        user = db.find_user_by_id(user_id)
        if not user:
            return jsonify({"error": "Utilisateur non trouvé"}), 404

        diamonds = user.get("diamonds", 0)
        if diamonds < 3:
            return jsonify({"error": "Pas assez de diamonds (minimum 3 requis)"}), 400

        data = request.json
        crypto_addr = (data.get("crypto_addr") or "").strip()
        if not crypto_addr:
            return jsonify({"error": "Adresse crypto requise"}), 400

        amount = 50 if diamonds >= 5 else 20

        req = db.create_withdrawal_request(
            user_id=user_id,
            username=user.get("username", ""),
            email=user.get("email", ""),
            diamonds=diamonds,
            amount=amount,
            crypto_addr=crypto_addr
        )
        print(f"💸 Demande de retrait créée : user={user.get('username')} montant={amount}€ addr={crypto_addr}")
        return jsonify({"message": "Demande de retrait enregistrée", "request": req}), 201

    except Exception as e:
        print(f"Erreur create_withdrawal: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/withdrawals', methods=['GET'])
def admin_get_withdrawals():
    """Admin: list all withdrawal requests."""
    try:
        admin, err = get_admin_user_from_token()
        if err:
            return err
        requests_list = db.get_all_withdrawal_requests()
        return jsonify({"withdrawals": requests_list}), 200
    except Exception as e:
        print(f"Erreur admin_get_withdrawals: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/withdrawals/<int:req_id>/status', methods=['PUT'])
def admin_update_withdrawal(req_id):
    """Admin: approve or reject a withdrawal request."""
    try:
        admin, err = get_admin_user_from_token()
        if err:
            return err
        data = request.json
        status = data.get("status", "")
        if status not in ("approved", "rejected"):
            return jsonify({"error": "Statut invalide (approved / rejected)"}), 400
        if db.update_withdrawal_status(req_id, status):
            return jsonify({"message": f"Demande #{req_id} mise à jour : {status}"}), 200
        return jsonify({"error": "Demande non trouvée"}), 404
    except Exception as e:
        print(f"Erreur admin_update_withdrawal: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5002, host='0.0.0.0')
