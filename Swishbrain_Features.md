# Résumé des Fonctionnalités : Swishbrain (NBA AI Predictor)

Ce document décrit en détail l'ensemble des fonctionnalités intégrées à la plateforme Swishbrain, qui allie prédictions sportives via Intelligence Artificielle et divertissement (mini-jeux).

---

## 1. Moteur d'Intelligence Artificielle & Prédictions
C'est le cœur de la plateforme. Swishbrain permet de simuler et de prédire le résultat de n'importe quel match NBA.
*   **Modèles de Machine Learning :** L'algorithme utilise un modèle "Ensemble" combinant XGBoost, LightGBM et Régression Logistique pour garantir une précision maximale sur la prédiction du vainqueur et du score exact (ex: 110-104).
*   **Analyses et Alertes :** Pour chaque prédiction, le système génère un niveau de confiance en pourcentage, un conseil de pari (Sécurisé / Risqué), et une tendance "Over/Under" (Plus ou Moins de X points dans le match).
*   **Algorithme Avancé des Blessures :** Avant de simuler un match, le robot télécharge instantanément le rapport médical officiel (ESPN). **Il calibre le score final en fonction de 3 paramètres très réalistes :**
    *   Le tirage du statut médical ("Day-to-day", a 50% de chance de jouer).
    *   L'absorption des tirs : le modèle sait qu'un titulaire absent verra environ 65% de ses tirs récupérés par ses remplaçants (l'impact réel de l'absence est de 35% de la moyenne de ses points purs).
    *   Un plafond d'impact maximum (Cap) empêche toute aberration mathématique (une équipe ne perdra jamais plus de 35 points à cause de blessures cumulées).
*   **Mise en Cache Intelligente :** Les prédictions sont gardées en mémoire pendant 24 heures pour charger instantanément les pages et économiser les requêtes serveurs.

## 2. Système d'Abonnement et Économie de Jetons (Tokens)
Une monétisation et gamification est intégrée au site :
*   **Transactions par Jeton :** Chaque analyse IA coûte 1 jeton (Token). Lors de son inscription, l'utilisateur se voit attribuer un solde initial de base (ex: 10 jetons).
*   **Tiers d'Abonnements :** Les joueurs classés **Premium** ou **VIP** (par l'Admin) ont un accès illimité. Les utilisateurs 'Free' doivent utiliser et économiser leurs jetons.
*   **Gestion depuis le Panel :** Un administrateur peut recréditer le compte d'un utilisateur à n'importe quel moment s'il arrive à sec.

## 3. Sécurité et Modération des Comptes Administrateurs
Swishbrain possède une forte couche de sécurité gérée par rôle (`role: user | admin`) et jetons cryptographiques (`JWT`).
*   **Salle d'Attente Interactive :** Un nouvel inscrit ne peut pas directement accéder aux outils cardiaques du site. Son compte est créé avec le statut "En attente". 
*   **Validation Manuelle :** L'administrateur exclusif du site possède un tableau de bord où il peut valider/rejeter les inscriptions en cochant une case ("Approuver").
*   **Protection des Routes :** Sans l'approbation, toutes les tentatives de piratages vers l'API IA sont bloquées (Erreur 403).
*   **Le Tableau de Bord Admin :** Interface complète listant tous les utilisateurs, leurs formulaires (Email, Date d'inscription), leur solde de tokens, et un accès rapide pour élever un User en VIP ou le supprimer.

## 4. Mini-Jeux : Simulateur de Blackjack
Une section indépendante est développée pour divertir le joueur voulant parier virtuellement dans une interface ultra-moderne.
*   **Simulation Authentique Casino :** Jeu de tirage de cartes jouable contre un "Croupier IA".
*   **Bankroll & Tracking :** Gestion d'un portefeuille virtuel pour s'entrainer aux paris (Mises fixes/variables).
*   **Adaptation au Thème :** L'interface Blackjack respecte le Dark/Light mode principal de Swishbrain.

## 5. Actualités (News) & Scores en Direct
Pour proposer un carrefour tout-en-un aux fans de la NBA :
*   **Scores Daily :** Un bandeau (Carousel) remonte les scores mondiaux de la nuit passée issus des APIs officielles avec prise en charge du fuseau horaire.
*   **Agenda & News :** Détection automatique des matchs programmés et centralisation des flux de nouvelles ("News") autour de la ligue NBA, avec des liens vers les articles ESPN complets.

## 6. Historiques Personnels
* Chaque prédiction générée avec des jetons est sauvegardée ("Historique") dans l'espace membre, permettant à l'utilisateur de confronter ses résultats passés et de suivre ses performances !
