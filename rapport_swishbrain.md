# Rapport Technique : Swishbrain (NBA AI Predictor)

## 1. Présentation du Projet
**Swishbrain** est une application web full-stack permettant de prédire les résultats des matchs de NBA à l'aide d'un modèle d'intelligence artificielle interne. Le système allie analyse de données sportives en temps réel, apprentissage automatique, divertissement et modération des utilisateurs.

## 2. Architecture Technique
Le projet suit une architecture client-serveur classique séparant le front-end du back-end :
- **Front-end :** Développé avec **React** (TypeScript, Vite), **Tailwind CSS** pour le design responsif et **Lucide React** pour l'iconographie. L'interface propose un thème dynamique (Clair / Sombre).
- **Back-end :** Serveur API développé avec **Python 3** et le micro-framework **Flask**. L'API gère la récupération de données (scrapping/API externes), l'authentification et les prédictions du modèle d'IA.
- **Base de Données :** Système relationnel **SQLite** (`database.py`) assurant le stockage local et performant des membres, de l'historique et la mise en cache.

## 3. Fonctionnalités Principales

### 3.1 Authentification et Sécurité
Le système de gestion d'utilisateurs intègre les aspects suivants :
- **Inscription & Connexion** : Protégé par **JWT** (JSON Web Tokens) et mots de passe hashés avec un sel cryptographique (`pbkdf2:sha256:100000`).
- **Validation Administrateur** : Chaque nouveau compte créé passe par un statut « En attente ». Un administrateur doit l'approuver manuellement avant que la personne puisse se connecter, assurant ainsi un contrôle strict d'accès (VIP/Premium).
- **Gestion de Profil** : Les utilisateurs peuvent modifier leurs informations ou se déconnecter à tout moment.

### 3.2 Modèle de Prédiction IA (NBA)
C'est le cœur de l'application.
- Les données des matchs à venir sont agrégées via l'API **ESPN** (avec l'API `nba_api` en solution de repli).
- Un modèle de Machine Learning entraîné préalablement évalue les probabilités de victoire (en pourcentage) et estime le score final (ex: 110-104) entre deux équipes.
- Un système de **mise en cache intelligente** de 24 heures évite une surcharge computationnelle pour les matchs identiques analysés plusieurs fois. Les utilisateurs peuvent enregistrer leurs prédictions (maximum 50 prédictions par utilisateur) dans leur historique personnel.

### 3.3 Dashboard Administrateur
Un panneau de contrôle centralisé exclusif aux administrateurs offrant :
- Une vue d'ensemble des statistiques : nombres d'utilisateurs, nombres d'administrateurs, prédictions totales du site.
- La gestion dynamique des utilisateurs : validation des comptes en attente ou suppression des utilisateurs frauduleux.
- Un audit de l'historique des prédictions de chaque membre pour suivre l'activité sur le site.

### 3.4 Fonctionnalités Annexes et Divertissement
L'application ne s'arrête pas aux prédictions brutes :
- **Scores en direct et Classements (Standings) :** Données en temps réel (ou avec un faible décalage) sur les scores de la journée et le classement général de la ligue NBA (Équipes et Joueurs).
- **Actualités NBA :** Module intégré récupérant à chaud les dernières informations Basket depuis des flux RSS.
- **Divertissement - Simulateur Blackjack :** Une authentique application de Blackjack développée en JavaScript Vanilla a été encapsulée (Iframe) de manière transparente. Elle est protégée et exclusivement accessible aux utilisateurs connectés. Elle synchronise son propre design avec le thème Clair/Sombre du portail React parent.

## 4. Outils et Dépendances Logiciels
- **Interface & Expérience Utilisateur :**
  - **React Router DOM :** Pour une navigation fluide sans rechargement (SPA).
  - **Contexts React :** Utilisation de `AuthContext` (pour garder la session) et `ThemeContext` (pour la personnalisation visuelle).
- **Serveur & Traitement des Données :**
  - **Flask-JWT-Extended :** Simplifie la création et validation des jetons JWT.
  - **Pandas :** Agilité dans la manipulation et transformation des DataFrame pour l'IA.
  - **BeautifulSoup4 & Requests :** Extraction d'actualités et fallback Web-Scraping si nécéssaire.

## 5. Résumé
**Swishbrain (NBA AI Predictor)** dresse un pont complet entre analyse prédictive et architecture logicielle robuste. Les toutes dernières améliorations structurelles, comprenant une surcouche de protection administrative pour valider les membres et une intégration de fonctionnalités de Gamification externe (Blackjack), dotent Swishbrain d'un niveau d'application de production aboutie et Premium.
