# analyse.py

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


# ============================================================
# 🔥 ANALYSE AUTOMATIQUE
# ============================================================

def analyse_automatique(team1, team2):
    """Analyse textuelle du matchup entre deux équipes."""

    clean_path = "data/clean/matchup_clean.csv"
    if not os.path.exists(clean_path):
        print("❌ Fichier matchup_clean.csv introuvable.")
        return

    df = pd.read_csv(clean_path)

    if "TEAM_ID" not in df.columns:
        print("❌ La colonne TEAM_ID est manquante.")
        return


    # On récupère les stats agrégées pour le match
    # Comme merge_two_teams_games() met déjà les deux équipes dans 1 fichier
    # on peut simplement faire :
    df_team1 = df.iloc[0]
    df_team2 = df.iloc[1]

    # Score
    pts1 = df_team1["PTS"]
    pts2 = df_team2["PTS"]



    # Différentiels
    diff1 = df_team1.get("PLUS_MINUS", 0)
    diff2 = df_team2.get("PLUS_MINUS", 0)



    # FG%
    fg1 = df_team1["FG_PCT"] * 100
    fg2 = df_team2["FG_PCT"] * 100



    # 3PT%
    fg31 = df_team1["FG3_PCT"] * 100
    fg32 = df_team2["FG3_PCT"] * 100



    # Reb / Assists

    score_team1 = 0
    score_team2 = 0

    if diff1 > diff2:
        score_team1 += 1
    else:
        score_team2 += 1

    if fg1 > fg2:
        score_team1 += 1
    else:
        score_team2 += 1

    if fg31 > fg32:
        score_team1 += 1
    else:
        score_team2 += 1

    winner = team1 if score_team1 > score_team2 else team2



# ============================================================
# 🔥 GRAPHIQUES
# ============================================================

def generate_graphs(team1, team2, df1, df2, stats1, stats2):
    """Affiche 6 graphiques complets comparant les deux équipes."""

    color1 = "#1d428a"
    color2 = "#c8102e"

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle(f'{team1} vs {team2} - Analyse Comparative', fontsize=15, fontweight='bold')

    # ----------------------------- 1) Points -----------------------------
    ax1 = axes[0, 0]
    ax1.bar([team1, team2], [stats1["PTS"], stats2["PTS"]], color=[color1, color2])
    ax1.set_title("Points moyens")
    for i, v in enumerate([stats1["PTS"], stats2["PTS"]]):
        ax1.text(i, v + 0.5, f"{v:.1f}", ha="center")

    # ---------------------------- 2) FG / 3PT ----------------------------
    ax2 = axes[0, 1]
    labels = ["FG%", "3PT%"]
    x = np.arange(len(labels))
    width = 0.35
    ax2.bar(x - width/2, [stats1["FG_PCT"]*100, stats1["FG3_PCT"]*100], width, label=team1, color=color1)
    ax2.bar(x + width/2, [stats2["FG_PCT"]*100, stats2["FG3_PCT"]*100], width, label=team2, color=color2)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.set_title("Efficacité au tir")
    ax2.legend()

    # ---------------------------- 3) Reb / AST ----------------------------
    ax3 = axes[0, 2]
    labels2 = ["REB", "AST"]
    x2 = np.arange(len(labels2))
    ax3.bar(x2 - width/2, [stats1["REB"], stats1["AST"]], width, color=color1, label=team1)
    ax3.bar(x2 + width/2, [stats2["REB"], stats2["AST"]], width, color=color2, label=team2)
    ax3.set_xticks(x2)
    ax3.set_xticklabels(labels2)
    ax3.set_title("Rebonds & Passes")
    ax3.legend()

    # --------------------------- 4) Derniers points -----------------------
    ax4 = axes[1, 0]
    ax4.plot(df1.tail(15)["PTS"].values, color=color1, marker='o', label=team1)
    ax4.plot(df2.tail(15)["PTS"].values, color=color2, marker='o', label=team2)
    ax4.set_title("Points (derniers matchs)")
    ax4.legend()

    ax5 = axes[1, 1]

    # On calcule le Net Rating pour chaque match
    # Si déjà présent dans PLUS_MINUS (différentiel), on utilise directement
    nr1 = df1["PLUS_MINUS"].dropna().values if "PLUS_MINUS" in df1.columns else []
    nr2 = df2["PLUS_MINUS"].dropna().values if "PLUS_MINUS" in df2.columns else []

    ax5.boxplot(
        [nr1, nr2],
        labels=[team1, team2],
        patch_artist=True,
        boxprops=dict(facecolor="#1d428a", alpha=0.5),
        medianprops=dict(color="yellow", linewidth=2),
    )

    ax5.set_title("Net Rating — Distribution (Boxplot)")
    ax5.set_ylabel("Net Rating (Points Diff.)")
    ax5.axhline(0, color='black', linestyle='--', linewidth=1)

    # ---------------------------- 6) Radar Chart --------------------------
    ax6 = fig.add_subplot(2, 3, 6, projection='polar')

    features = ["PTS", "REB", "AST", "STL", "BLK"]
    maxvals = [max(stats1[f], stats2[f], 1) for f in features]

    t1 = [stats1[f]/maxvals[i] for i, f in enumerate(features)]
    t2 = [stats2[f]/maxvals[i] for i, f in enumerate(features)]

    t1 += [t1[0]]
    t2 += [t2[0]]
    angles = np.linspace(0, 2*np.pi, len(features), endpoint=False)
    angles = np.concatenate((angles, [angles[0]]))

    ax6.plot(angles, t1, color=color1, label=team1)
    ax6.fill(angles, t1, alpha=0.2, color=color1)
    ax6.plot(angles, t2, color=color2, label=team2)
    ax6.fill(angles, t2, alpha=0.2, color=color2)
    ax6.set_xticks(angles[:-1])
    ax6.set_xticklabels(features)
    ax6.set_title("Radar des performances")
    ax6.legend()

    plt.tight_layout()
    plt.show()

    print("\n Graphiques générés.")