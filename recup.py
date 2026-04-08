import os
import time
import json
import urllib.request
import urllib.error
import pandas as pd
from datetime import datetime, timedelta

# ============================================================
# ESPN-BASED DATA FETCHER — replaces nba_api (stats.nba.com)
# ESPN never blocks, never times out, always fast (~200ms/call)
# ============================================================

SEASONS_FULL = ["2024-25", "2025-26"]
CURRENT_SEASON = "2025-26"
OLD_SEASON = "2024-25"

OUTPUT_DIR = "data/raw/games"
os.makedirs(OUTPUT_DIR, exist_ok=True)

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
ESPN_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

# ⚡ LE CACHE MAGIQUE QUI ACCÉLÈRE TOUT ⚡
# Il garde en mémoire les jours déjà téléchargés pour ne pas les redemander à ESPN.
_SCOREBOARD_CACHE = {}

# NBA official TEAM_IDs (used in CSVs)
NBA_TEAM_IDS = {
    "ATL": 1610612737, "BOS": 1610612738, "BKN": 1610612751, "CHA": 1610612766,
    "CHI": 1610612741, "CLE": 1610612739, "DAL": 1610612742, "DEN": 1610612743,
    "DET": 1610612765, "GSW": 1610612744, "HOU": 1610612745, "IND": 1610612754,
    "LAC": 1610612746, "LAL": 1610612747, "MEM": 1610612763, "MIA": 1610612748,
    "MIL": 1610612749, "MIN": 1610612750, "NOP": 1610612740, "NYK": 1610612752,
    "OKC": 1610612760, "ORL": 1610612753, "PHI": 1610612755, "PHX": 1610612756,
    "POR": 1610612757, "SAC": 1610612758, "SAS": 1610612759, "TOR": 1610612761,
    "UTA": 1610612762, "WAS": 1610612764,
}

NBA_TEAM_NAMES = {
    "ATL": "Atlanta Hawks", "BOS": "Boston Celtics", "BKN": "Brooklyn Nets",
    "CHA": "Charlotte Hornets", "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets", "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors", "HOU": "Houston Rockets", "IND": "Indiana Pacers",
    "LAC": "LA Clippers", "LAL": "Los Angeles Lakers", "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat", "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans", "NYK": "New York Knicks", "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic", "PHI": "Philadelphia 76ers", "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings", "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors", "UTA": "Utah Jazz", "WAS": "Washington Wizards",
}

# ESPN abbreviation normalization
ESPN_ABBR_MAP = {
    "GS": "GSW", "NO": "NOP", "NY": "NYK", "SA": "SAS",
    "WSH": "WAS", "PHO": "PHX", "UTAH": "UTA",
}


def _normalize_abbr(abbr):
    """Normalize ESPN team abbreviation to our standard."""
    return ESPN_ABBR_MAP.get(abbr, abbr)


def _season_dates(season_str):
    """Get start/end dates for a season string like '2025-26'."""
    start_year = int(season_str.split("-")[0])
    # Regular season ~Oct to Apr
    return (
        datetime(start_year, 10, 1),
        datetime(start_year + 1, 4, 30),
    )


def _season_id(season_str):
    """Convert '2025-26' to SEASON_ID format '22025'."""
    year = int(season_str.split("-")[0])
    return f"2{year}"


def _fetch_scoreboard(date_str):
    """Fetch ESPN scoreboard for a date (YYYYMMDD). Returns list of games."""
    # ⚡ VÉRIFICATION DU CACHE ICI ⚡
    if date_str in _SCOREBOARD_CACHE:
        return _SCOREBOARD_CACHE[date_str]

    try:
        url = f"{ESPN_BASE}?dates={date_str}"
        req = urllib.request.Request(url, headers=ESPN_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            events = data.get("events", [])
            # On enregistre dans le cache pour la prochaine équipe
            _SCOREBOARD_CACHE[date_str] = events
            return events
    except Exception as e:
        print(f"    ⚠️ ESPN error for {date_str}: {e}")
    return []


def _parse_game_for_team(event, team_abbr, season_str):
    """Extract a game row from an ESPN event for a specific team."""
    comp = event.get("competitions", [{}])[0]
    competitors = comp.get("competitors", [])
    status = comp.get("status", {}).get("type", {})

    # Only completed games
    if not (status.get("completed", False) or status.get("name") == "STATUS_FINAL"):
        return None

    if len(competitors) < 2:
        return None

    # Find our team and opponent
    our_team = None
    opp_team = None
    for c in competitors:
        abbr = _normalize_abbr(c.get("team", {}).get("abbreviation", ""))
        if abbr == team_abbr:
            our_team = c
        else:
            opp_team = c

    if our_team is None or opp_team is None:
        return None

    # Extract stats from ESPN
    stats = {}
    for s in our_team.get("statistics", []):
        stats[s["name"]] = s.get("displayValue", "0")

    our_score = int(our_team.get("score", 0))
    opp_score = int(opp_team.get("score", 0))
    opp_abbr = _normalize_abbr(opp_team.get("team", {}).get("abbreviation", ""))
    is_home = our_team.get("homeAway") == "home"
    won = our_score > opp_score

    # Build matchup string (same format as nba_api)
    if is_home:
        matchup = f"{team_abbr} vs. {opp_abbr}"
    else:
        matchup = f"{team_abbr} @ {opp_abbr}"

    # Parse date
    game_date = event.get("date", "")[:10]  # "2025-02-20T..."

    # Build row matching nba_api CSV format
    row = {
        "SEASON_ID": _season_id(season_str),
        "TEAM_ID": NBA_TEAM_IDS.get(team_abbr, 0),
        "TEAM_ABBREVIATION": team_abbr,
        "TEAM_NAME": NBA_TEAM_NAMES.get(team_abbr, team_abbr),
        "GAME_ID": event.get("id", ""),
        "GAME_DATE": game_date,
        "MATCHUP": matchup,
        "WL": "W" if won else "L",
        "MIN": 240,
        "FGM": int(float(stats.get("fieldGoalsMade", 0))),
        "FGA": int(float(stats.get("fieldGoalsAttempted", 0))),
        "FG_PCT": round(float(stats.get("fieldGoalPct", 0)) / 100, 3),
        "FG3M": int(float(stats.get("threePointFieldGoalsMade", 0))),
        "FG3A": int(float(stats.get("threePointFieldGoalsAttempted", 0))),
        "FG3_PCT": round(float(stats.get("threePointFieldGoalPct", stats.get("threePointPct", 0))) / 100, 3),
        "FTM": int(float(stats.get("freeThrowsMade", 0))),
        "FTA": int(float(stats.get("freeThrowsAttempted", 0))),
        "FT_PCT": round(float(stats.get("freeThrowPct", 0)) / 100, 3),
        "OREB": 0,  # Not in scoreboard — not used by model
        "DREB": 0,
        "REB": int(float(stats.get("rebounds", 0))),
        "AST": int(float(stats.get("assists", 0))),
        "STL": 0,
        "BLK": 0,
        "TOV": 0,
        "PF": 0,
        "PTS": our_score,
        "PLUS_MINUS": our_score - opp_score,
        "VIDEO_AVAILABLE": 1,
    }
    return row


def _existing_game_ids(team, season):
    """Load existing CSV and return set of GAME_IDs already saved."""
    filename = f"{team}_{season.replace('-', '')}_Regular.csv"
    path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            return set(df["GAME_ID"].astype(str))
        except Exception:
            pass
    return set()


def _latest_game_date(team, season):
    """Get the latest game date from existing CSV."""
    filename = f"{team}_{season.replace('-', '')}_Regular.csv"
    path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            if not df.empty and "GAME_DATE" in df.columns:
                dates = pd.to_datetime(df["GAME_DATE"])
                return dates.max()
        except Exception:
            pass
    return None


def scrape_season_espn(team, season):
    """Fetch a season using ESPN scoreboard — day by day.
    Only fetches new games not already saved."""
    start_date, end_date = _season_dates(season)
    today = datetime.now()
    end_date = min(end_date, today)

    existing_ids = _existing_game_ids(team, season)
    latest = _latest_game_date(team, season)

    # If we have existing data, only fetch from the day after the latest game
    if latest is not None:
        start_date = latest - timedelta(days=1)  # small overlap for safety
        print(f"  📅 Incremental: fetching from {start_date.strftime('%Y-%m-%d')}")
    else:
        print(f"  📅 Full fetch: {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}")

    new_rows = []
    current = start_date
    total_days = (end_date - start_date).days + 1
    fetched = 0

    while current <= end_date:
        date_str = current.strftime("%Y%m%d")
        events = _fetch_scoreboard(date_str)

        for event in events:
            row = _parse_game_for_team(event, team, season)
            if row and str(row["GAME_ID"]) not in existing_ids:
                new_rows.append(row)

        fetched += 1
        current += timedelta(days=1)

        # ⚡ OPTIMISATION DU TIME.SLEEP ⚡
        # On ne patiente que si on a réellement fait une requête HTTP (et pas si on a utilisé le cache)
        if date_str not in _SCOREBOARD_CACHE:
            time.sleep(0.05)

    if new_rows:
        print(f"  ✔ Found {len(new_rows)} new games")
        _append_games(team, season, new_rows)
    else:
        print(f"  ✔ Already up to date")


def _append_games(team, season, new_rows):
    """Append new games to existing CSV (or create new one)."""
    filename = f"{team}_{season.replace('-', '')}_Regular.csv"
    path = os.path.join(OUTPUT_DIR, filename)

    new_df = pd.DataFrame(new_rows)

    if os.path.exists(path):
        existing = pd.read_csv(path)
        # Remove duplicates by GAME_ID
        existing_ids = set(existing["GAME_ID"].astype(str))
        new_df = new_df[~new_df["GAME_ID"].astype(str).isin(existing_ids)]
        if not new_df.empty:
            combined = pd.concat([existing, new_df], ignore_index=True)
            combined.to_csv(path, index=False)
            print(f"    ✔ {path} → {len(combined)} total games (+{len(new_df)} new)")
        else:
            print(f"    ✔ {path} already has all games")
    else:
        new_df.to_csv(path, index=False)
        print(f"    ✔ Created {path} ({len(new_df)} games)")


def _ensure_empty_files(team, season):
    """Create empty Preseason/Playoffs files if they don't exist."""
    cols = "SEASON_ID,TEAM_ID,TEAM_ABBREVIATION,TEAM_NAME,GAME_ID,GAME_DATE,MATCHUP,WL,MIN,FGM,FGA,FG_PCT,FG3M,FG3A,FG3_PCT,FTM,FTA,FT_PCT,OREB,DREB,REB,AST,STL,BLK,TOV,PF,PTS,PLUS_MINUS,VIDEO_AVAILABLE"
    for stype in ["Preseason", "Playoffs"]:
        filename = f"{team}_{season.replace('-', '')}_{stype}.csv"
        path = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write(cols + "\n")


def season_files_exist(team, season):
    """Check if Regular season file exists with data."""
    filename = f"{team}_{season.replace('-', '')}_Regular.csv"
    path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            return len(df) > 0
        except Exception:
            return False
    return False


def fetch_team_data(team, full_if_missing=True):
    """Fetch team data from ESPN (fast, reliable).
    Skips scraping if data is already fresh (updated recently)."""
    from data_cache import is_team_data_fresh

    print(f"\n📊 {team}...")

    # ⚡ Check si les données sont déjà fraîches → skip tout
    if is_team_data_fresh(team):
        return

    old_exists = season_files_exist(team, OLD_SEASON)

    if not old_exists:
        print(f"  Saison {OLD_SEASON} manquante → fetching from ESPN...")
        scrape_season_espn(team, OLD_SEASON)
        _ensure_empty_files(team, OLD_SEASON)
    else:
        print(f"  Saison {OLD_SEASON} ✔ (cached)")

    # Update current season incrementally
    print(f"  Saison {CURRENT_SEASON} → updating...")
    scrape_season_espn(team, CURRENT_SEASON)
    _ensure_empty_files(team, CURRENT_SEASON)


def fetch_all_teams(teams_list):
    """Fetch all teams from ESPN — incremental, fast."""
    print(f"\n{'=' * 50}")
    print(f"📡 Fetching data for {len(teams_list)} teams via ESPN")
    print(f"{'=' * 50}")

    for team in teams_list:
        fetch_team_data(team)

    print(f"\n{'=' * 50}")
    print(f"✔ Done! All {len(teams_list)} teams updated.")
    print(f"{'=' * 50}")