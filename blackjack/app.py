import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

import streamlit as st


RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
SUITS = ["♠", "♥", "♦", "♣"]


def hilo_value(rank: str) -> int:
    if rank in {"2", "3", "4", "5", "6"}:
        return 1
    if rank in {"7", "8", "9"}:
        return 0
    return -1  # 10, J, Q, K, A


def card_points(rank: str) -> int:
    if rank in {"J", "Q", "K", "10"}:
        return 10
    if rank == "A":
        return 11
    return int(rank)


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str

    @property
    def label(self) -> str:
        return f"{self.rank}{self.suit}"


def hand_value(cards: List[Card]) -> Tuple[int, bool]:
    """
    Returns (best_total, is_soft).
    Soft means at least one Ace is counted as 11 in the best_total.
    """
    total = 0
    aces = 0
    for c in cards:
        total += card_points(c.rank)
        if c.rank == "A":
            aces += 1

    # Reduce Aces from 11 -> 1 as needed
    soft = aces > 0
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    soft = soft and (aces > 0)  # at least one Ace still counted as 11
    return total, soft


def is_pair(cards: List[Card]) -> bool:
    if len(cards) != 2:
        return False
    r1, r2 = cards[0].rank, cards[1].rank
    # Treat 10/J/Q/K as same pair for strategy purposes
    tens = {"10", "J", "Q", "K"}
    if r1 in tens and r2 in tens:
        return True
    return r1 == r2


def dealer_up_rank(dealer_cards: List[Card]) -> Optional[str]:
    return dealer_cards[0].rank if dealer_cards else None


def rank_to_up_value(rank: str) -> int:
    if rank == "A":
        return 11
    if rank in {"10", "J", "Q", "K"}:
        return 10
    return int(rank)


def basic_strategy_action(
    player_cards: List[Card], dealer_up: str, can_double: bool = True, can_split: bool = True
) -> str:
    """
    Multi-deck, S17 baseline (common casino rules).
    Returns one of: "Split", "Double", "Hit", "Stand".
    """
    if not dealer_up:
        return "—"

    up = rank_to_up_value(dealer_up)
    total, soft = hand_value(player_cards)

    # Splits
    if can_split and is_pair(player_cards):
        r = player_cards[0].rank
        if r in {"A", "8"}:
            return "Split"
        if r in {"2", "3"}:
            return "Split" if 2 <= up <= 7 else "Hit"
        if r == "4":
            return "Split" if 5 <= up <= 6 else "Hit"
        if r == "5":
            # treat as hard 10
            pass
        if r == "6":
            return "Split" if 2 <= up <= 6 else "Hit"
        if r == "7":
            return "Split" if 2 <= up <= 7 else "Hit"
        if r == "9":
            return "Split" if up in {2, 3, 4, 5, 6, 8, 9} else "Stand"
        if r in {"10", "J", "Q", "K"}:
            return "Stand"

    # Soft totals (A counted as 11)
    if soft and total <= 21:
        if total <= 17:  # A,2..A,6
            if can_double and up in {4, 5, 6} and total in {15, 16, 17}:
                return "Double"
            if can_double and up in {5, 6} and total in {13, 14}:
                return "Double"
            return "Hit"
        if total == 18:  # A,7
            if can_double and up in {3, 4, 5, 6}:
                return "Double"
            return "Stand" if up in {2, 7, 8} else "Hit"
        if total in {19, 20, 21}:
            return "Stand"

    # Hard totals
    if total <= 8:
        return "Hit"
    if total == 9:
        if can_double and 3 <= up <= 6:
            return "Double"
        return "Hit"
    if total == 10:
        if can_double and 2 <= up <= 9:
            return "Double"
        return "Hit"
    if total == 11:
        if can_double and up != 11:
            return "Double"
        return "Hit"
    if total == 12:
        return "Stand" if up in {4, 5, 6} else "Hit"
    if 13 <= total <= 16:
        return "Stand" if 2 <= up <= 6 else "Hit"
    return "Stand"  # 17+


def apply_count_deviations(
    action: str, player_cards: List[Card], dealer_up: str, true_count: float
) -> str:
    """
    Small, high-signal set of common Hi-Lo indices.
    Only tweaks Hit/Stand/Double in a few spots.
    """
    if not dealer_up or len(player_cards) == 0:
        return action

    up = rank_to_up_value(dealer_up)
    total, soft = hand_value(player_cards)

    # Only consider deviations on hard totals (most common indices)
    if soft:
        # Example: 11 vs A double at TC>=1 (treat as hard 11 if no soft? keep simple)
        pass

    # 16 vs 10: Stand at TC>=0 (otherwise Hit)
    if total == 16 and up == 10 and not soft:
        return "Stand" if true_count >= 0 else "Hit"

    # 15 vs 10: Stand at TC>=4
    if total == 15 and up == 10 and not soft:
        return "Stand" if true_count >= 4 else "Hit"

    # 12 vs 3: Stand at TC>=2
    if total == 12 and up == 3 and not soft:
        return "Stand" if true_count >= 2 else "Hit"

    # 12 vs 2: Stand at TC>=3
    if total == 12 and up == 2 and not soft:
        return "Stand" if true_count >= 3 else "Hit"

    # 11 vs A: Double at TC>=1 (otherwise Hit)
    if total == 11 and up == 11 and not soft:
        return "Double" if true_count >= 1 else "Hit"

    # 10 vs 10: Double at TC>=4
    if total == 10 and up == 10 and not soft:
        return "Double" if true_count >= 4 else action

    # 9 vs 2: Double at TC>=1
    if total == 9 and up == 2 and not soft:
        return "Double" if true_count >= 1 else action

    # 9 vs 7: Double at TC>=3
    if total == 9 and up == 7 and not soft:
        return "Double" if true_count >= 3 else action

    return action


def ensure_state():
    st.session_state.setdefault("shoe_decks", 6)
    st.session_state.setdefault("running_count", 0)
    st.session_state.setdefault("seen_cards", [])  # list[Card]
    st.session_state.setdefault("round_players", 1)
    st.session_state.setdefault("player_hands", [[]])  # list[list[Card]]
    st.session_state.setdefault("dealer_hand", [])  # list[Card]
    st.session_state.setdefault("selected_target", "Dealer")


def reset_shoe(decks: int):
    st.session_state["shoe_decks"] = decks
    st.session_state["running_count"] = 0
    st.session_state["seen_cards"] = []
    new_round(players=st.session_state.get("round_players", 1))


def new_round(players: int):
    st.session_state["round_players"] = players
    st.session_state["player_hands"] = [[] for _ in range(players)]
    st.session_state["dealer_hand"] = []
    st.session_state["selected_target"] = "Dealer"


def decks_remaining() -> float:
    total_cards = st.session_state["shoe_decks"] * 52
    seen = len(st.session_state["seen_cards"])
    remaining = max(total_cards - seen, 0)
    return max(remaining / 52.0, 0.25)  # prevent blow-ups late shoe


def true_count() -> float:
    return st.session_state["running_count"] / decks_remaining()


def add_card_to(target: str, rank: str, suit: str):
    c = Card(rank=rank, suit=suit)
    st.session_state["seen_cards"].append(c)
    st.session_state["running_count"] += hilo_value(rank)

    if target == "Dealer":
        st.session_state["dealer_hand"].append(c)
        return

    if target.startswith("Joueur "):
        idx = int(target.split(" ")[1]) - 1
        st.session_state["player_hands"][idx].append(c)


def undo_last():
    if not st.session_state["seen_cards"]:
        return
    last = st.session_state["seen_cards"].pop()
    st.session_state["running_count"] -= hilo_value(last.rank)

    # remove from any hand (search dealer then players)
    if st.session_state["dealer_hand"] and st.session_state["dealer_hand"][-1] == last:
        st.session_state["dealer_hand"].pop()
        return
    for h in st.session_state["player_hands"]:
        if h and h[-1] == last:
            h.pop()
            return


def card_chip_html(text: str, tone: str = "neutral") -> str:
    tone_class = {
        "neutral": "chip",
        "positive": "chip chip--pos",
        "negative": "chip chip--neg",
        "gold": "chip chip--gold",
    }.get(tone, "chip")
    return f"<span class='{tone_class}'>{text}</span>"


st.set_page_config(page_title="Blackjack Card Counter (Hi‑Lo)", page_icon="🂡", layout="wide")
ensure_state()

st.markdown(
    """
<style>
  :root{
    --felt:#0b2a21;
    --felt2:#071f19;
    --gold:#d9b65d;
    --gold2:#b8902e;
    --text:#e8eef0;
    --muted:#b7c4c9;
    --panel: rgba(255,255,255,.06);
    --stroke: rgba(255,255,255,.12);
    --shadow: 0 18px 50px rgba(0,0,0,.45);
  }
  .stApp{
    background: radial-gradient(1200px 600px at 15% 10%, rgba(217,182,93,.15), transparent 60%),
                radial-gradient(900px 500px at 85% 15%, rgba(185,144,46,.14), transparent 60%),
                linear-gradient(180deg, var(--felt) 0%, var(--felt2) 100%);
    color: var(--text);
  }
  h1,h2,h3{ letter-spacing:.4px; }
  .panel{
    background: var(--panel);
    border: 1px solid var(--stroke);
    border-radius: 18px;
    padding: 16px 18px;
    box-shadow: var(--shadow);
  }
  .metricRow{
    display:flex; gap:12px; flex-wrap:wrap;
  }
  .metric{
    flex: 1 1 220px;
    background: rgba(0,0,0,.18);
    border: 1px solid var(--stroke);
    border-radius: 16px;
    padding: 12px 14px;
  }
  .metric .k{ color: var(--muted); font-size: 12px; }
  .metric .v{ font-size: 26px; font-weight: 700; margin-top: 4px; }
  .metric .s{ color: var(--muted); font-size: 12px; margin-top: 2px; }
  .chip{
    display:inline-flex; align-items:center; justify-content:center;
    padding: 6px 10px; border-radius: 999px;
    border: 1px solid rgba(255,255,255,.16);
    background: rgba(0,0,0,.22);
    margin-right: 6px; margin-bottom: 8px;
    font-weight: 600;
  }
  .chip--pos{ border-color: rgba(100,255,180,.35); background: rgba(40,160,90,.18); }
  .chip--neg{ border-color: rgba(255,120,120,.35); background: rgba(180,50,50,.18); }
  .chip--gold{ border-color: rgba(217,182,93,.50); background: rgba(217,182,93,.14); }
  .cardGrid button{
    transition: transform .08s ease, box-shadow .12s ease;
  }
  .cardGrid button:hover{ transform: translateY(-1px); }
  .cardGrid button:active{ transform: translateY(0px) scale(.99); }
  /* make Streamlit buttons darker */
  .stButton>button{
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,.14);
    background: rgba(0,0,0,.18);
    color: var(--text);
  }
  .stButton>button:hover{
    border-color: rgba(217,182,93,.40);
    box-shadow: 0 8px 24px rgba(0,0,0,.25);
  }
  .hrGold{
    height:1px; background: linear-gradient(90deg, transparent, rgba(217,182,93,.55), transparent);
    margin: 10px 0 14px 0;
  }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("## Blackjack Card Counter — Hi‑Lo (Python)")

left, right = st.columns([1.1, 1.9], gap="large")

with left:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("### Configuration")
    decks = st.slider("Nombre de decks (shoe)", 1, 8, int(st.session_state["shoe_decks"]))
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Nouveau shoe / Reset", use_container_width=True):
            reset_shoe(decks)
            st.rerun()
    with c2:
        if st.button("Undo dernière carte", use_container_width=True):
            undo_last()
            st.rerun()

    st.markdown("<div class='hrGold'></div>", unsafe_allow_html=True)
    st.markdown("### Manche")
    players = st.slider("Nombre de joueurs (cette manche)", 1, 7, int(st.session_state["round_players"]))
    if st.button("Nouvelle manche", use_container_width=True):
        new_round(players)
        st.rerun()

    targets = ["Dealer"] + [f"Joueur {i}" for i in range(1, st.session_state["round_players"] + 1)]
    st.session_state["selected_target"] = st.selectbox(
        "Ajouter les cartes à",
        options=targets,
        index=targets.index(st.session_state.get("selected_target", "Dealer"))
        if st.session_state.get("selected_target", "Dealer") in targets
        else 0,
    )

    st.markdown("<div class='hrGold'></div>", unsafe_allow_html=True)
    rc = st.session_state["running_count"]
    tc = true_count()
    dr = decks_remaining()
    st.markdown(
        f"""
<div class="metricRow">
  <div class="metric">
    <div class="k">Running Count</div>
    <div class="v">{rc:+d}</div>
    <div class="s">Hi‑Lo (2–6:+1, 7–9:0, 10–A:-1)</div>
  </div>
  <div class="metric">
    <div class="k">True Count</div>
    <div class="v">{tc:+.2f}</div>
    <div class="s">decks restants ≈ {dr:.2f}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.caption("Le count persiste entre les manches tant que le shoe n’est pas reset.")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("### Table")

    d_up = dealer_up_rank(st.session_state["dealer_hand"])
    up_txt = d_up if d_up else "—"

    st.markdown("#### Dealer")
    d_total, d_soft = hand_value(st.session_state["dealer_hand"]) if st.session_state["dealer_hand"] else (0, False)
    d_chips = []
    for c in st.session_state["dealer_hand"]:
        v = hilo_value(c.rank)
        tone = "positive" if v > 0 else "negative" if v < 0 else "neutral"
        d_chips.append(card_chip_html(c.label, tone))
    d_line = "".join(d_chips) if d_chips else "<span class='chip'>Aucune carte</span>"
    st.markdown(d_line, unsafe_allow_html=True)
    st.markdown(
        f"{card_chip_html(f'Upcard: {up_txt}', 'gold')} "
        f"{card_chip_html(f'Total: {d_total}'+(' (soft)' if d_soft else ''), 'neutral')}",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='hrGold'></div>", unsafe_allow_html=True)
    st.markdown("#### Joueurs")

    for i, hand in enumerate(st.session_state["player_hands"], start=1):
        total, soft = hand_value(hand) if hand else (0, False)
        chips = []
        for c in hand:
            v = hilo_value(c.rank)
            tone = "positive" if v > 0 else "negative" if v < 0 else "neutral"
            chips.append(card_chip_html(c.label, tone))
        line = "".join(chips) if chips else "<span class='chip'>Aucune carte</span>"

        # Advisor
        base = basic_strategy_action(hand, d_up, can_double=True, can_split=True) if d_up and hand else "—"
        advised = apply_count_deviations(base, hand, d_up, tc) if base != "—" else "—"
        advice_tone = "gold" if advised in {"Split", "Double"} else "neutral"

        st.markdown(f"**Joueur {i}**", unsafe_allow_html=True)
        st.markdown(line, unsafe_allow_html=True)
        st.markdown(
            f"{card_chip_html(f'Total: {total}'+(' (soft)' if soft else ''), 'neutral')} "
            f"{card_chip_html('Conseil: ' + advised, advice_tone)}",
            unsafe_allow_html=True,
        )
        st.markdown("")

    st.markdown("<div class='hrGold'></div>", unsafe_allow_html=True)
    st.markdown("### Ajouter une carte (clic)")

    st.caption(
        "Astuce: choisissez d’abord la cible (Dealer / Joueur), puis cliquez une carte. "
        "Le suit n’affecte pas le count; il sert au visuel."
    )

    # Card grid: ranks x suits
    st.markdown("<div class='cardGrid'>", unsafe_allow_html=True)
    for s in SUITS:
        cols = st.columns(len(RANKS), gap="small")
        for j, r in enumerate(RANKS):
            with cols[j]:
                if st.button(f"{r}{s}", key=f"btn_{r}_{s}", use_container_width=True):
                    add_card_to(st.session_state["selected_target"], r, s)
                    st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    "<div style='text-align:center; color: rgba(232,238,240,.65); padding: 10px 0 0 0;'>"
    "Blackjack Card Counter — Hi‑Lo • Python/Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
