# -*- coding: utf-8 -*-
import os
import pandas as pd
import requests
from rapidfuzz import process

# Mapping abréviations → noms complets
TEAMS_MAPPING_NAMES = {
    "ATL": "Atlanta Hawks", "BOS": "Boston Celtics", "BKN": "Brooklyn Nets",
    "CHA": "Charlotte Hornets", "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets", "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors", "HOU": "Houston Rockets", "IND": "Indiana Pacers",
    "LAC": "LA Clippers", "LAL": "Los Angeles Lakers", "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat", "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans", "NYK": "New York Knicks", "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic", "PHI": "Philadelphia 76ers", "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings", "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors", "UTA": "Utah Jazz", "WAS": "Washington Wizards"
}

# Reverse mapping : nom complet → abréviation
TEAM_NAME_TO_ABBR = {v: k for k, v in TEAMS_MAPPING_NAMES.items()}

def normalize_name(name):
    import unicodedata, re
    if not isinstance(name, str): return ""
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r"[^a-zA-Z0-9 ]", "", name)
    return name.lower().strip()


def fetch_espn_injuries():
    """Récupère les blessures depuis l'API ESPN (JSON structuré)."""
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("injuries", [])
    except Exception as e:
        print(f"[ERROR] Impossible de récupérer les blessures ESPN: {e}")
        return []


def _load_br_totals(path="data/raw/nba_totals_2026.csv"):
    """Charge les stats BR per-game pour lookup PTS des blessés."""
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    if "Player" in df.columns:
        df["normalized"] = df["Player"].apply(normalize_name)
    return df


def _find_team_and_pts_from_br(player_name, df_br):
    """Trouve l'équipe et les PTS/match d'un joueur dans les stats BR."""
    if df_br is None or "PTS" not in df_br.columns or "Team" not in df_br.columns:
        return None, None

    norm = normalize_name(player_name)

    # Exact match
    exact = df_br[df_br["normalized"] == norm]
    if not exact.empty:
        pts = exact.iloc[0]["PTS"]
        team = exact.iloc[0]["Team"]
        try:
            return str(team).strip().upper(), float(pts)
        except (ValueError, TypeError):
            return str(team).strip().upper(), None

    # Fuzzy match
    names_list = df_br["normalized"].tolist()
    result = process.extractOne(norm, names_list)
    if result:
        match, score, idx = result
        if score >= 80:
            pts = df_br.iloc[idx]["PTS"]
            team = df_br.iloc[idx]["Team"]
            try:
                return str(team).strip().upper(), float(pts)
            except (ValueError, TypeError):
                return str(team).strip().upper(), None

    return None, None


def update_injuries_clean(teamA_abbr, teamA_id, teamB_abbr, teamB_id,
                          mapping_path="data/clean/players_mapping_local.csv",
                          out_path="data/clean/injuries_clean.csv"):
    """Scrape les blessures ESPN pour les 2 équipes du match et génère injuries_clean.csv."""

    # 1. Récupérer les blessures depuis l'API ESPN
    espn_injuries = fetch_espn_injuries()
    if not espn_injuries:
        print("[WARN] Aucune donnée de blessures récupérée depuis ESPN.")
        return

    # 2. Charger les stats BR pour lookup PTS
    df_br = _load_br_totals()

    # 3. Filtrer les joueurs blessés des deux équipes
    target_teams = {teamA_abbr: teamA_id, teamB_abbr: teamB_id}
    injured_players = []  # list of {name, team_id, status, pts}

    for team_data in espn_injuries:
        espn_team_display_name = team_data.get("displayName", "")
        espn_team_abbr = TEAM_NAME_TO_ABBR.get(espn_team_display_name)

        for inj in team_data.get("injuries", []):
            athlete = inj.get("athlete", {})
            player_name = athlete.get("displayName", "")
            status = inj.get("status", "Out")

            if player_name:
                # Lookup Team and PTS from BR data to avoid ESPN team grouping bugs
                br_team, pts = _find_team_and_pts_from_br(player_name, df_br)
                
                # Determine standard team abbreviation
                final_team_abbr = br_team if br_team else espn_team_abbr
                
                # ESPN bug workaround: if the player is supposedly assigned to Milwaukee but BR says otherwise, believe BR.
                if final_team_abbr in target_teams:
                    team_id = target_teams[final_team_abbr]
                    injured_players.append({
                        "name": player_name,
                        "team_id": team_id,
                        "status": status,
                        "PTS": pts if pts is not None else 0.0
                    })

    print(f"[DEBUG] ESPN injuries found: {len(injured_players)} players for {teamA_abbr}/{teamB_abbr}")

    # 4. Mapper les noms avec players_mapping_local.csv
    if not os.path.exists(mapping_path):
        print("[ERROR] Mapping local introuvable.")
        return

    df_map = pd.read_csv(mapping_path)
    df_map["norm_name"] = df_map["player_name"].apply(normalize_name)
    names_list = df_map["norm_name"].tolist()

    results = []

    for player in injured_players:
        p_name = player["name"]
        norm_p = normalize_name(p_name)

        # Perfect match
        exact = df_map[df_map["norm_name"] == norm_p]
        if not exact.empty:
            local_id = exact.iloc[0]["player_local_id"]
            results.append({
                "player_local_id": local_id,
                "TEAM_ID": player["team_id"],
                "status": player["status"],
                "PTS": player["PTS"]
            })
            print(f"  - {p_name} ➔ Trouvé (Exact) [{player['status']}] PTS={player['PTS']:.1f}")
            continue

        # Fuzzy match
        match_result = process.extractOne(norm_p, names_list)
        if match_result:
            match, score, idx = match_result
            if score >= 80:
                local_id = df_map.iloc[idx]["player_local_id"]
                results.append({
                    "player_local_id": local_id,
                    "TEAM_ID": player["team_id"],
                    "status": player["status"],
                    "PTS": player["PTS"]
                })
                print(f"  - {p_name} ➔ Trouvé (Fuzzy: {match}) [{player['status']}] PTS={player['PTS']:.1f}")
            else:
                print(f"  - {p_name} ➔ Non trouvé dans la base (score={score})")
        else:
            print(f"  - {p_name} ➔ Non trouvé dans la base")

    # 5. Sauvegarder dans injuries_clean.csv
    df_out = pd.DataFrame(results, columns=["player_local_id", "TEAM_ID", "status", "PTS"])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df_out.to_csv(out_path, index=False)
    print(f"[OK] Fichier {out_path} généré avec succès ({len(results)} blessés).")


if __name__ == "__main__":
    # Test avec Lakers vs Warriors
    update_injuries_clean("LAL", 1610612747, "GSW", 1610612744)
