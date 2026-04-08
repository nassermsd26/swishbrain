# -*- coding: utf-8 -*-
import os
import pandas as pd


# ============================================================
# UTILITAIRE : charger ou créer player mapping
# ============================================================
def load_player_mapping(path="data/clean/players_mapping_local.csv"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"[ERROR] players_mapping_local.csv introuvable : {path}")
    df = pd.read_csv(path)
    return df


def save_player_mapping(df, path="data/clean/players_mapping_local.csv"):
    df.to_csv(path, index=False)
    print(f"[OK] players_mapping_local.csv mis à jour.")


# ============================================================
# UTILITAIRE : conversion nom → player_local_id
# ============================================================
def get_or_create_player_id(player_name, mapping_df):
    # 1) Exact match dans player_name
    row = mapping_df[mapping_df["player_name"].str.lower() == player_name.lower()]
    if not row.empty:
        return int(row["player_local_id"].iloc[0]), mapping_df  # ID trouvé

    # 2) Sinon créer un nouvel ID
    new_id = mapping_df["player_local_id"].max() + 1
    new_row = pd.DataFrame([{
        "player_local_id": new_id,
        "player_name": player_name
    }])

    mapping_df = pd.concat([mapping_df, new_row], ignore_index=True)

    print(f"[INFO] Nouveau joueur ajouté : {player_name} → ID {new_id}")
    return new_id, mapping_df


# ============================================================
# UTILITAIRE : Team → Team_ID
# ============================================================
def get_team_id(team_abbr, raw_dir="data/raw/games"):
    if not os.path.exists(raw_dir):
        return None
    for f in os.listdir(raw_dir):
        if f.startswith(team_abbr):
            df = pd.read_csv(os.path.join(raw_dir, f))
            if "TEAM_ID" in df.columns and not df.empty:
                return int(df["TEAM_ID"].iloc[0])
    print(f"[WARN] Aucun TEAM_ID trouvé pour {team_abbr}")
    return None


# ============================================================
#  CLEANING PRINCIPAL
# ============================================================
def clean_injuries_stats(
        input_path="data/raw/injuries_players_stats.csv",
        output_path="data/clean/injuries_players_stats_clean.csv",
        mapping_path="data/clean/players_mapping_local.csv"):

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"[ERROR] injuries_players_stats.csv introuvable : {input_path}")

    df = pd.read_csv(input_path)

    # Colonnes à supprimer si présentes
    cols_to_drop = ["Rk", "Age", "Pos", "Awards", "normalized", "input_name"]
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns], errors="ignore")

    # Charger le mapping joueur
    mapping_df = load_player_mapping(mapping_path)

    # Conversion Player → player_local_id
    player_ids = []
    for name in df["Player"]:
        pid, mapping_df = get_or_create_player_id(name, mapping_df)
        player_ids.append(pid)

    df["player_local_id"] = player_ids

    # Sauvegarder le mapping mis à jour
    save_player_mapping(mapping_df, mapping_path)

    # Convertir Team → TEAM_ID
    team_ids = []
    for abbr in df["Team"]:
        tid = get_team_id(abbr)
        team_ids.append(tid)

    df["TEAM_ID"] = team_ids
    # Assurer que player_local_id et TEAM_ID sont les deux premières colonnes
    first_cols = ["player_local_id", "TEAM_ID"]

    # Vérifier qu'elles existent
    existing_first = [c for c in first_cols if c in df.columns]

    # Colonnes restantes dans l’ordre actuel
    other_cols = [c for c in df.columns if c not in existing_first]

    # Reconstruire le DF avec le bon ordre
    df = df[existing_first + other_cols]
    # On peut maintenant supprimer Player et Team (pas utiles pour ML)
    df = df.drop(columns=["Player", "Team"], errors="ignore")

    # Sauvegarde
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"[OK] injuries_players_stats_clean.csv généré → {output_path}")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    clean_injuries_stats()