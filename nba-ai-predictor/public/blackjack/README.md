# Blackjack Card Counter (Python)

Application web **Python** (Streamlit) de comptage de cartes Blackjack (Hi‑Lo) avec choix du nombre de joueurs à chaque manche.

## Lancer l'application

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Utilisation

- Choisir **nombre de decks** (1–8), puis **Nouvelle manche** (1–7 joueurs).
- Cliquer sur les cartes pour les ajouter à une main (joueur ou dealer).
- Le **Running Count** et le **True Count** se mettent à jour en temps réel (Hi‑Lo).
- Le conseil (Hit / Stand / Double / Split) est basé sur **basic strategy** + quelques ajustements au **true count**.

## Notes

- Le **count persiste** entre les manches tant que vous ne cliquez pas sur **Nouveau shoe / Reset**.
- Le True Count est calculé comme \(TC = RC / decks\_restants\), avec decks\_restants basé sur les cartes déjà vues.
