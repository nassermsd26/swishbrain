# NBA AI Predictor - Backend API

Ce document explique comment lancer le backend Flask et le frontend React pour afficher de vraies prédictions NBA.

## Installation

### 1. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### 2. Installer les dépendances du frontend

```bash
cd nba-ai-predictor
npm install
```

## Lancement

### 1. Démarrer le backend Flask

Dans le répertoire racine du projet :

```bash
python api.py
```

Le serveur Flask sera accessible sur `http://localhost:5000`

### 2. Démarrer le frontend React

Dans un autre terminal, depuis le dossier `nba-ai-predictor` :

```bash
npm run dev
```

Le frontend sera accessible sur `http://localhost:5173` (ou le port indiqué par Vite)

## Utilisation

1. Ouvrez votre navigateur sur l'URL du frontend (généralement `http://localhost:5173`)
2. Vous verrez les matchs d'aujourd'hui récupérés depuis l'API ESPN
3. Cliquez sur un match pour obtenir une prédiction basée sur vos modèles XGBoost
4. Ou utilisez l'onglet "CUSTOM MATCHUP" pour sélectionner deux équipes manuellement

## Endpoints API

### GET `/api/schedule`
Récupère les matchs d'aujourd'hui et de demain depuis ESPN

### POST `/api/predict`
Fait une prédiction pour un match entre deux équipes

**Body:**
```json
{
  "teamA": "LAL",
  "teamB": "GSW"
}
```

**Response:**
```json
{
  "matchId": "...",
  "teamA": {...},
  "teamB": {...},
  "winner": "LAL",
  "confidence": 75.5,
  "scoreA": 112,
  "scoreB": 108,
  "totalPoints": 220,
  "bettingAnalysis": {
    "riskLevel": "Secure",
    "overUnder": "Neutral"
  },
  "statsA": {...},
  "statsB": {...},
  "injuries": {
    "teamA": [...],
    "teamB": [...]
  },
  "impactA": 2.5,
  "impactB": 0.0
}
```

## Notes

- Le backend utilise les modèles XGBoost entraînés dans `models/`
- Les données sont scrapées depuis ESPN et Rotowire
- Les blessures sont prises en compte uniquement pour les matchs d'aujourd'hui
- Le processus de prédiction peut prendre quelques secondes car il inclut le scraping et le traitement des données

