# Structure du Projet NBA AI Predictor

## 📁 Organisation du Projet

```
an-nba 5/
│
├── 📂 Backend/                    # Code Python backend
│   ├── api.py                     # API Flask principale
│   ├── main.py                    # Script principal CLI
│   ├── training1.py               # Modèles ML (XGBoost)
│   ├── schedule.py                # Récupération calendrier ESPN
│   ├── lineup.py                  # Scraping lineups
│   ├── recup.py                   # Récupération données équipes
│   ├── analyse.py                 # Analyses statistiques
│   ├── injury_player_stats.py     # Gestion blessures
│   ├── cleaning.py                # Nettoyage données (matchup)
│   ├── cleaning2.py               # Nettoyage données (training)
│   ├── cleaning3.py               # Nettoyage données (lineups)
│   ├── cleaning4.py               # Nettoyage données (blessures)
│   └── requirements.txt           # Dépendances Python
│
├── 📂 nba-ai-predictor/           # Frontend React/TypeScript
│   ├── 📂 components/            # Composants React
│   │   ├── Header.tsx            # En-tête avec menu
│   │   ├── GameSelector.tsx     # Sélecteur de matchs
│   │   ├── PredictionSummary.tsx # Résumé prédiction
│   │   ├── StatsCharts.tsx        # Graphiques statistiques
│   │   ├── LineupStatus.tsx      # Statut lineups/blessures
│   │   ├── News.tsx              # Page actualités
│   │   ├── PredictionPage.tsx    # Page dédiée prédiction
│   │   ├── BasketballLoader.tsx  # Loader animation basket
│   │   ├── RecentScores.tsx      # Derniers scores
│   │   └── Footer.tsx            # Pied de page
│   │
│   ├── 📂 contexts/              # Contextes React
│   │   └── ThemeContext.tsx      # Gestion thème clair/sombre
│   │
│   ├── 📂 services/              # Services API
│   │   └── mockApi.ts            # Appels API backend
│   │
│   ├── 📂 types/                 # Types TypeScript
│   │   └── types.ts              # Interfaces TypeScript
│   │
│   ├── constants.ts              # Constantes (équipes, etc.)
│   ├── App.tsx                   # Composant principal
│   ├── index.tsx                 # Point d'entrée
│   ├── index.html                # HTML principal
│   ├── package.json              # Dépendances npm
│   └── vite.config.ts            # Configuration Vite
│
├── 📂 data/                      # Données
│   ├── 📂 raw/                   # Données brutes
│   │   ├── 📂 games/             # Fichiers matchs par équipe
│   │   ├── lineups_full.csv      # Lineups bruts
│   │   └── injuries_players_stats.csv
│   │
│   └── 📂 clean/                 # Données nettoyées
│       ├── matchup_clean.csv     # Matchups nettoyés
│       ├── training_train.csv    # Données training
│       ├── training_test.csv     # Données test
│       ├── lineups_ml_ids.csv    # Lineups pour ML
│       ├── injuries_clean.csv    # Blessures nettoyées
│       └── clean_players.csv     # Joueurs nettoyés
│
├── 📂 models/                    # Modèles ML sauvegardés
│   ├── xgb_winner.pkl            # Modèle gagnant
│   ├── xgb_score.pkl             # Modèle score
│   ├── scaler_clf.pkl            # Scaler classification
│   ├── scaler_score.pkl          # Scaler score
│   └── features_*.pkl            # Features utilisées
│
├── README_API.md                 # Documentation API
└── PROJECT_STRUCTURE.md          # Ce fichier
```

## 🔄 Flux de Données

### 1. Prédiction d'un Match
```
Frontend (App.tsx)
  ↓ POST /api/predict
Backend (api.py)
  ↓ Scraping & Cleaning
  ├── scrape_lineups_full()      # Lineups
  ├── fetch_team_data()          # Stats équipes
  ├── merge_two_teams_games()    # Matchup
  ├── clean_training_teams()     # Training data
  └── predict_current_match()    # Prédiction ML
  ↓ Retour JSON
Frontend affiche PredictionPage
```

### 2. Actualités NBA
```
Frontend (News.tsx)
  ↓ GET /api/news
Backend (api.py)
  ↓ Scraping ESPN
  └── BeautifulSoup parsing
  ↓ Retour JSON
Frontend affiche actualités
```

### 3. Derniers Scores
```
Frontend (RecentScores.tsx)
  ↓ GET /api/recent-scores
Backend (api.py)
  ↓ API ESPN Scoreboard
  └── Récupération scores récents
  ↓ Retour JSON
Frontend affiche scores
```

## 🎨 Architecture Frontend

- **ThemeContext** : Gestion thème clair/sombre global
- **Components** : Composants réutilisables
- **Services** : Communication avec backend
- **Types** : Types TypeScript pour type-safety

## 🤖 Modèles ML

- **XGBoost Classifier** : Prédiction gagnant
- **XGBoost Regressor** : Prédiction score
- **Features** : Stats historiques, head-to-head, blessures
- **Ajustements** : Impact blessures sur scores finaux

## 📊 Pipeline de Données

1. **Raw Data** → Scraping ESPN/Rotowire
2. **Cleaning** → Nettoyage et normalisation
3. **Training** → Préparation données ML
4. **Prediction** → Utilisation modèles entraînés
5. **API** → Format JSON pour frontend

