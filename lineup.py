import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from datetime import datetime

# Import du cleaning3.py
from cleaning3 import clean_lineups


def scrape_lineups_full(save_path="data/raw/lineups_full.csv"):
    url = "https://www.rotowire.com/basketball/nba-lineups.php"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    games = soup.find_all("div", class_="lineup is-nba")
    all_data = []

    for game in games:

        # ------------------------------
        # TEAMS (home / away)
        # ------------------------------
        teams = game.find_all("div", class_="lineup__abbr")
        if len(teams) < 2:
            continue

        home = teams[0].text.strip()
        away = teams[1].text.strip()

        # ------------------------------
        # STARTERS & MNP
        # ------------------------------
        lineup_blocks = game.find_all("ul", class_="lineup__list")
        if len(lineup_blocks) != 2:
            continue

        home_block = lineup_blocks[0]
        away_block = lineup_blocks[1]

        # Extract starters
        def extract_starters(block):
            starters = []
            for li in block.find_all("li", class_="lineup__player"):
                starters.append(li.text.strip())
            return starters[:5]

        starters_home = extract_starters(home_block)
        starters_away = extract_starters(away_block)

        # Extract MAY NOT PLAY
        def extract_may_not_play(block):
            results = []
            title = block.find("li", class_="lineup__title")
            if not title:
                return results

            for li in title.find_all_next("li", class_="lineup__player"):
                if li.find_parent("ul") != block:
                    break

                pos = li.find("div", class_="lineup__pos").text.strip()
                name = li.find("a").text.strip()
                status = li.find("span", class_="lineup__inj").text.strip()
                results.append(f"{name} ({pos}, {status})")

            return results

        may_not_play_home = extract_may_not_play(home_block)
        may_not_play_away = extract_may_not_play(away_block)

        # ------------------------------
        # STORE EACH TEAM SEPARATELY
        # ------------------------------
        all_data.append({
            "team": home,
            "opponent": away,
            "starters": starters_home,
            "may_not_play": may_not_play_home,
        })

        all_data.append({
            "team": away,
            "opponent": home,
            "starters": starters_away,
            "may_not_play": may_not_play_away,
        })

    df = pd.DataFrame(all_data)

    # ------------------------------
    # SAVE RAW FILE
    # ------------------------------
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    if os.path.exists(save_path):
        os.remove(save_path)

    df.to_csv(save_path, index=False, encoding="utf-8-sig")
    print(" Lineups bruts sauvegardés :", save_path)

    return df


if __name__ == "__main__":
    print(" Scraping des lineups Rotowire…")
    df_raw = scrape_lineups_full()

    print("\n Nettoyage via cleaning3.py…")
    df_ml = clean_lineups()

