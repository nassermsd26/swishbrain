# -*- coding: utf-8 -*-
import os
import unicodedata
import pandas as pd
import requests
from bs4 import BeautifulSoup


# ============================================================
# 0) REPARATION DES NOMS MAL ENCODÉs (DonÄRiÄESA → Dončić)
# ============================================================
def fix_bad_encoding(name: str) -> str:
    if not isinstance(name, str):
        return name

    # Corrections spécifiques vues dans ton fichier
    replacements = {
        "DonÄRiÄESA": "Dončić",
        "JokiÄESA": "Jokić",
        "JokiÄ‡": "Jokić",
        "Ä‡": "ć",
        "Ä": "č",
        "ÄŒ": "Č",
        "Ä": "Đ",
        "Ä‘": "đ",
        "Ä–": "ė",
        "Å¡": "š",
        "Å½": "Ž",
        "Å¾": "ž"
    }

    for bad, good in replacements.items():
        if bad in name:
            name = name.replace(bad, good)

    return name


# ============================================================
# 1) EXTRACTION IDS DE JOUEURS BLESSÉS
# ============================================================
def load_injured_player_ids(path="data/clean/lineups_ml_ids.csv"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"[ERROR] lineups_ml_ids.csv introuvable : {path}")

    df = pd.read_csv(path)
    mnp_cols = [c for c in df.columns if c.startswith("mnp") and c.endswith("_id")]

    ids = set()
    for col in mnp_cols:
        for val in df[col].dropna().unique():
            try:
                if int(val) != 0:
                    ids.add(int(val))
            except:
                pass

    ids = sorted(list(ids))
    print(f"[INFO] {len(ids)} IDs blessés détectés.")
    return ids


# ============================================================
# 2) MAPPING ID LOCAL → NOM (avec correction d'encodage)
# ============================================================
def map_ids_to_names(ids_list,
                     mapping_path="data/clean/players_mapping_local.csv"):

    if not os.path.exists(mapping_path):
        raise FileNotFoundError("[ERROR] players_mapping_local.csv introuvable.")

    df = pd.read_csv(mapping_path)

    mapping = df.set_index("player_local_id")["player_name"].to_dict()

    names = []
    for pid in ids_list:
        if pid in mapping:
            fixed = fix_bad_encoding(mapping[pid])
            names.append(fixed)
        else:
            print(f"[WARN] Aucun nom trouvé pour ID local {pid}")

    print(f"[INFO] {len(names)} noms obtenus.")
    return names


# ============================================================
# 3) NORMALISATION (sans accents, minuscule)
# ============================================================
def normalize_name(name: str):
    import unicodedata, re
    if not isinstance(name, str):
        return ""

    # Décomposer tous les accents (ex: ö → o + ¨)
    name = unicodedata.normalize("NFKD", name)

    # Enlever tous les accents quels qu'ils soient
    name = "".join(c for c in name if not unicodedata.combining(c))

    # Retirer tout sauf lettres/chiffres/espace
    name = re.sub(r"[^a-zA-Z0-9 ]", "", name)

    # Passer en minuscule
    name = name.lower().strip()

    return name
# ============================================================
# 4) SCRAPING BR PER-GAME 2026 DIRECTEMENT
# ============================================================
def scrape_br_totals_2026(path="data/raw/nba_totals_2026.csv"):
    print("[INFO] Scraping Basketball Reference per-game 2026...")

    url = "https://www.basketball-reference.com/leagues/NBA_2026_per_game.html"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

    if r.status_code != 200:
        raise RuntimeError(f"[ERROR] Impossible de scraper BR : status {r.status_code}")

    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table", id="per_game_stats")

    if table is None:
        raise RuntimeError("[ERROR] Tableau per-game introuvable dans la page.")

    df = pd.read_html(str(table))[0]
    df = df[df["Player"] != "Player"]  # enlever doublons d'entête
    df["Player"] = df["Player"].astype(str).apply(fix_bad_encoding)

    # Ajouter colonne normalisée
    df["normalized"] = df["Player"].apply(normalize_name)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)

    print("[OK] per-game 2026 sauvegardé.")
    return df


# ============================================================
# 5) LOAD BR TOTALS OU SCRAPER SI ABSENT
# ============================================================
def load_br_totals(path="data/raw/nba_totals_2026.csv"):
    if not os.path.exists(path):
        print("[WARN] BR totals introuvable → scraping automatique...")
        return scrape_br_totals_2026(path)
    else:
        df = pd.read_csv(path)
        df["Player"] = df["Player"].apply(fix_bad_encoding)
        df["normalized"] = df["Player"].apply(normalize_name)
        return df


# ============================================================
# 6) Fuzzy match joueur dans BR
# ============================================================
def find_player_in_totals(player_name, df_totals):
    from rapidfuzz import process

    target = normalize_name(player_name)

    exact = df_totals[df_totals["normalized"] == target]
    if len(exact) == 1:
        return exact.iloc[0].to_dict()

    names = df_totals["normalized"].tolist()
    match, score, idx = process.extractOne(target, names)

    if score >= 80:
        return df_totals.iloc[idx].to_dict()

    return None


# ============================================================
# 7) PIPELINE GLOBAL
# ============================================================
def generate_injured_players_stats(out_path="data/raw/injuries_players_stats_raw.csv"):
    ids = load_injured_player_ids()
    names = map_ids_to_names(ids)
    df_totals = load_br_totals()

    results = []
    for name in names:
        print(f"[INFO] Matching {name}...")
        stats = find_player_in_totals(name, df_totals)
        if stats:
            stats["input_name"] = name
            results.append(stats)
            print(f"[OK] Stats trouvées pour {name}")
        else:
            print(f"[WARN] Aucun match pour {name}")

    if results:
        df = pd.DataFrame(results)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        df.to_csv(out_path, index=False)
        print(f"[OK] Stats blessés sauvegardées → {out_path}")
    else:
        print("[INFO] Aucun blessé matché.")


# ============================================================
# 8) VERSION POUR main.py (MATCH UNIQUEMENT)
# ============================================================
def scrape_injured_players_stats(teamA_id,
                                 teamB_id,
                                 lineup_path="data/clean/lineups_ml_ids.csv",
                                 mapping_path="data/clean/players_mapping_local.csv",
                                 out_path="data/raw/injuries_players_stats.csv"):

    if not os.path.exists(lineup_path):
        print("[ERROR] lineups_ml_ids.csv introuvable.")
        return

    df = pd.read_csv(lineup_path)
    df_match = df[df["team_id"].isin([teamA_id, teamB_id])]

    mnp_cols = [c for c in df_match.columns if c.startswith("mnp")]

    injured_ids = []
    for _, row in df_match.iterrows():
        for c in mnp_cols:
            try:
                if int(row[c]) != 0:
                    injured_ids.append(int(row[c]))
            except:
                pass

    injured_ids = sorted(set(injured_ids))
    if not injured_ids:
        print("[INFO] Aucun blessé pour ce match.")
        return

    print("Joueurs blessés détectés → récupération BR per-game...")

    names = map_ids_to_names(injured_ids, mapping_path)
    df_totals = load_br_totals()

    results = []
    for name in names:
        stats = find_player_in_totals(name, df_totals)
        if stats:
            print(f"[OK] {name} trouvé")
            stats["input_name"] = name
            results.append(stats)
        else:
            print(f"[WARN] Aucun match BR pour {name}")

    if results:
        df = pd.DataFrame(results)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        df.to_csv(out_path, index=False)
        print(f"[OK] Stats blessés match → {out_path}")


# ============================================================
# MAIN TEST
# ============================================================
if __name__ == "__main__":
    generate_injured_players_stats()