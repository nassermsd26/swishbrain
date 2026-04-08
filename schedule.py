# espn_schedule.py

import requests
import pandas as pd
from datetime import date, timedelta, datetime


def get_espn_schedule(target_date: date):
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    params = {"dates": target_date.strftime("%Y%m%d")}
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return pd.DataFrame()

    data = r.json()
    games = data.get("events", [])
    rows = []

    for g in games:
        comp = g["competitions"][0]
        home = comp["competitors"][0]["team"]["abbreviation"]
        away = comp["competitors"][1]["team"]["abbreviation"]
        start_raw = comp.get("date")
        game_id = g.get("id")
        
        # Formater l'heure depuis la date ISO
        start_formatted = ""
        if start_raw:
            try:
                # Parser la date ISO (format: "2025-01-15T19:00:00Z" ou similaire)
                if isinstance(start_raw, str):
                    # Enlever le Z à la fin si présent et ajouter le timezone
                    start_clean = start_raw.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(start_clean)
                    # Formater en heure 12h (ex: "7:00 PM")
                    # Utiliser %I (avec zéro) puis enlever le zéro de tête si nécessaire
                    hour_str = dt.strftime("%I:%M %p")
                    # Enlever le zéro de tête pour l'heure (ex: "07:00 PM" -> "7:00 PM")
                    if hour_str.startswith("0"):
                        hour_str = hour_str[1:]
                    start_formatted = hour_str
                else:
                    start_formatted = str(start_raw)
            except Exception as e:
                # Si erreur de parsing, utiliser la valeur brute
                start_formatted = str(start_raw) if start_raw else "TBD"

        rows.append({
            "gameId": game_id,
            "date": target_date,
            "home": home,
            "away": away,
            "start": start_formatted
        })

    return pd.DataFrame(rows)



def get_today_tomorrow():
    today = date.today()
    tomorrow = today + timedelta(days=1)

    df_today = get_espn_schedule(today)
    df_tomorrow = get_espn_schedule(tomorrow)

    return df_today, df_tomorrow