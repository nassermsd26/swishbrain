import pandas as pd
import ast
import re
import os

NBA_TEAM_IDS = {
    "ATL": 1610612737, "BOS": 1610612738, "BKN": 1610612751, "CHA": 1610612766,
    "CHI": 1610612741, "CLE": 1610612739, "DAL": 1610612742, "DEN": 1610612743,
    "DET": 1610612765, "GSW": 1610612744, "HOU": 1610612745, "IND": 1610612754,
    "LAC": 1610612746, "LAL": 1610612747, "MEM": 1610612763, "MIA": 1610612748,
    "MIL": 1610612749, "MIN": 1610612750, "NOP": 1610612740, "NYK": 1610612752,
    "OKC": 1610612760, "ORL": 1610612753, "PHI": 1610612755, "PHX": 1610612756,
    "POR": 1610612757, "SAC": 1610612758, "SAS": 1610612759, "TOR": 1610612761,
    "UTA": 1610612762, "WAS": 1610612764
}

def parse_starter(entry):
    entry = entry.replace("\n", " ").strip()
    parts = entry.split()
    if len(parts) >= 2:
        parts = parts[1:]
    name = " ".join(parts)
    name = re.sub(r"(Ques|Out|Doubt|Prob|OFS)", "", name)
    return name.strip()

def parse_maynot(entry):
    m = re.match(r"(.*) \((.*), (.*)\)", entry)
    if not m:
        return None, None
    name, _pos, status = m.groups()
    return name.strip(), status.strip()

def update_player_mapping(lineups_df, mapping_path="data/clean/players_mapping_local.csv", start_id=100):

    player_cols = [c for c in lineups_df.columns if "starter" in c or "mnp" in c]

    players = set()
    for col in player_cols:
        players.update(lineups_df[col].dropna().unique())

    players = sorted(list(players))

    if os.path.exists(mapping_path):
        mapping_df = pd.read_csv(mapping_path)
    else:
        mapping_df = pd.DataFrame(columns=["player_local_id", "player_name"])

    existing_players = set(mapping_df["player_name"])
    new_players = [p for p in players if p not in existing_players]

    if mapping_df.empty:
        next_id = start_id
    else:
        next_id = mapping_df["player_local_id"].max() + 1

    new_rows = []
    for p in new_players:
        new_rows.append({"player_local_id": next_id, "player_name": p})
        next_id += 1

    if new_rows:
        mapping_df = pd.concat([mapping_df, pd.DataFrame(new_rows)], ignore_index=True)

    os.makedirs(os.path.dirname(mapping_path), exist_ok=True)
    mapping_df.to_csv(mapping_path, index=False)

    return mapping_df

def clean_lineups(
        input_path="data/raw/lineups_full.csv",
        output_path="data/clean/lineups_ml.csv",
        output_ids_path="data/clean/lineups_ml_ids.csv"
):

    try:
        df = pd.read_csv(input_path)

        df["starters"] = df["starters"].apply(lambda x: ast.literal_eval(x))
        df["may_not_play"] = df["may_not_play"].apply(lambda x: ast.literal_eval(x))

        df["team_id"] = df["team"].apply(lambda x: NBA_TEAM_IDS.get(x, None))
        df["opponent_id"] = df["opponent"].apply(lambda x: NBA_TEAM_IDS.get(x, None))

        for i in range(5):
            df[f"starter{i+1}_name"] = None

        for idx, row in df.iterrows():
            for i, entry in enumerate(row["starters"]):
                if i >= 5:
                    break
                df.at[idx, f"starter{i+1}_name"] = parse_starter(entry)

        max_mnp = df["may_not_play"].apply(len).max()

        for i in range(max_mnp):
            df[f"mnp{i+1}_name"] = None
            df[f"mnp{i+1}_status"] = None

        for idx, row in df.iterrows():
            for i, entry in enumerate(row["may_not_play"]):
                name, status = parse_maynot(entry)
                df.at[idx, f"mnp{i+1}_name"] = name
                df.at[idx, f"mnp{i+1}_status"] = status

        df = df.drop(columns=[
            "team", "opponent",
            "starters", "may_not_play",
            "nb_out", "nb_ques", "nb_doubt", "nb_starters_inj"
        ], errors="ignore")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)

        mapping_df = update_player_mapping(df)

        name_to_id = dict(zip(mapping_df["player_name"], mapping_df["player_local_id"]))
        id_df = df.copy()

        player_cols = [c for c in id_df.columns if "_name" in c]
        for col in player_cols:
            id_df[col] = id_df[col].map(name_to_id)

        cols_to_remove = [c for c in id_df.columns if c.endswith("_status")]
        id_df = id_df.drop(columns=cols_to_remove)

        rename_cols = {}
        for col in id_df.columns:
            if col.endswith("_name"):
                rename_cols[col] = col.replace("_name", "_id")
        id_df = id_df.rename(columns=rename_cols)

        id_df = id_df.fillna(0)

        id_df.to_csv(output_ids_path, index=False)

        if os.path.exists(output_path):
            os.remove(output_path)

        print("Succès : cleaning terminé.")

    except Exception as e:
        print("Échec : erreur pendant le cleaning.")
        print(e)
