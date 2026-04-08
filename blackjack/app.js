/* Swishbrain Blackjack Simulator - Full State Machine */

let DECK_SIZE = 52;

let stateHistory = []; // Pour garder la trace et pouvoir annuler

let state = {
    bankroll: 1000,
    currentBet: 50,
    decks: 6,
    rules: "S17",
    playersCnt: 1,
    mySeat: 1,
    
    runningCount: 0,
    cardsDealt: 0,
    history: [],

    phase: "CONFIG", // "CONFIG", "DEAL", "PLAY", "DEALER", "RESULT"
    
    dealerCards: [],
    players: [], // Array of { seat, type(main/other), hands: [{cards: [], status: active/bust/stand/blackjack/surrender, doubled: bool}] }
    
    activeSeatIndex: 0,
    activeHandIndex: 0,
    
    dealSequence: [],
    dealIndex: 0,
    
    waitingForCard: false,
    currentAction: null // tracking if the current card to be drawn is from a Hit, Double, or initial Deal
};

const DOM = {
    btnRejouer: document.getElementById('btnRejouer'),
    btnUndo: document.getElementById('btnUndo'),
    btnNouvelleManche: document.getElementById('btnNouvelleManche'),
    
    decksSelect: document.getElementById('decksSelect'),
    rulesSelect: document.getElementById('rulesSelect'),
    playersSelect: document.getElementById('playersSelect'),
    seatSelect: document.getElementById('seatSelect'),
    
    adviceMain: document.getElementById('adviceMain'),
    advicePill: document.getElementById('advicePill'),
    adviceReason: document.getElementById('adviceReason'),
    
    valRC: document.getElementById('valRC'),
    valTC: document.getElementById('valTC'),
    
    inputBankroll: document.getElementById('inputBankroll'),
    inputBet: document.getElementById('inputBet'),
    
    zoneDealer: document.getElementById('zoneDealer'),
    cardsDealer: document.getElementById('cardsDealer'),
    totalDealer: document.getElementById('totalDealer'),
    
    playersContainer: document.getElementById('playersContainer'),
    
    lblActionTitle: document.getElementById('lblActionTitle'),
    lblActionSub: document.getElementById('lblActionSub'),
    
    actionGrid: document.getElementById('actionGrid'),
    rankGrid: document.getElementById('rankGrid'),
    
    btnActionHit: document.getElementById('btnActionHit'),
    btnActionStand: document.getElementById('btnActionStand'),
    btnActionDouble: document.getElementById('btnActionDouble'),
    btnActionSplit: document.getElementById('btnActionSplit')
};

// --- Math & Rules ---
function getHiLoValue(rank) {
    if (['2','3','4','5','6'].includes(rank)) return 1;
    if (['10','J','Q','K','A'].includes(rank)) return -1;
    return 0; // 7,8,9
}

function getCardValue(rank) {
    if (['J','Q','K'].includes(rank)) return 10;
    if (rank === 'A') return 11;
    return parseInt(rank);
}

function handValue(cards) {
    let total = 0;
    let aces = 0;
    for (let c of cards) {
        if (c === 'A') aces++;
        total += getCardValue(c);
    }
    while (total > 21 && aces > 0) {
        total -= 10;
        aces--;
    }
    return total;
}

function isSoft(cards) {
    let total = 0;
    let aces = 0;
    for (let c of cards) {
        if (c === 'A') aces++;
        total += getCardValue(c);
    }
    if (total <= 21 && aces > 0) return true;
    while (total > 21 && aces > 0) {
        total -= 10;
        aces--;
        if (total <= 21 && aces > 0) return true;
    }
    return false;
}

function isPair(cards) {
    if (cards.length !== 2) return false;
    let v1 = getCardValue(cards[0]);
    let v2 = getCardValue(cards[1]);
    return v1 === v2;
}

function getTrueCount() {
    let decksRemaining = state.decks - (state.cardsDealt / DECK_SIZE);
    if (decksRemaining < 0.5) decksRemaining = 0.5;
    return state.runningCount / decksRemaining;
}

function rankToUpValue(c) {
    if (['10','J','Q','K'].includes(c)) return 10;
    if (c === 'A') return 11;
    return parseInt(c);
}

function basicStrategy(cards, dealerUp, rules = "S17") {
    let p = handValue(cards);
    let d = rankToUpValue(dealerUp);
    let is_soft = isSoft(cards);
    let pair = isPair(cards);
    
    if (pair) {
        let val = getCardValue(cards[0]);
        if (val === 11) return "SPLIT";
        if (val === 10) return "STAND";
        if (val === 9) return (d === 7 || d === 10 || d === 11) ? "STAND" : "SPLIT";
        if (val === 8) return "SPLIT";
        if (val === 7) return d >= 8 ? "HIT" : "SPLIT";
        if (val === 6) return d >= 7 ? "HIT" : (rules === "H17" && d === 2 ? "SPLIT" : "SPLIT");
        if (val === 5) return d >= 10 ? "HIT" : "DOUBLE";
        if (val === 4) return (d === 5 || d === 6) ? "SPLIT" : "HIT";
        if (val === 3 || val === 2) return d >= 8 ? "HIT" : "SPLIT";
    }
    
    if (is_soft) {
        if (p >= 20) return "STAND";
        if (p === 19) return (rules==="H17" && d===6) ? "DOUBLE" : "STAND";
        if (p === 18) {
            if (d >= 9) return "HIT";
            if (d >= 3 && d <= 6) return "DOUBLE";
            if (rules==="H17" && d===2) return "DOUBLE";
            return "STAND"; // d=2 S17, or d=7,8
        }
        if (p === 17) return (d >= 3 && d <= 6) ? "DOUBLE" : "HIT";
        if (p === 16 || p === 15) return (d >= 4 && d <= 6) ? "DOUBLE" : "HIT";
        if (p === 14 || p === 13) return (d === 5 || d === 6) ? "DOUBLE" : "HIT";
    }
    
    if (p >= 17) return "STAND";
    if (p >= 13 && p <= 16) return d >= 7 ? "HIT" : "STAND";
    if (p === 12) return (d >= 4 && d <= 6) ? "STAND" : "HIT";
    if (p === 11) return (rules==="H17" && d===11) ? "DOUBLE" : (d===11 ? "HIT" : "DOUBLE");
    if (p === 10) return d >= 10 ? "HIT" : "DOUBLE";
    if (p === 9) return (d >= 3 && d <= 6) ? "DOUBLE" : "HIT";
    return "HIT";
}

function applyDeviations(action, cards, dealerUp, tc) {
    let p = handValue(cards);
    let d = rankToUpValue(dealerUp);
    let pair = isPair(cards);
    let is_soft = isSoft(cards);
    
    // Ins16
    if (p === 16 && d === 10 && tc >= 0) return {a: "STAND", r: "Deviation Il18: Stand 16 vs 10 à TC >= 0"};
    if (p === 15 && d === 10 && tc >= 4) return {a: "STAND", r: "Deviation Il18: Stand 15 vs 10 à TC >= 4"};
    if (pair && getCardValue(cards[0]) === 10 && d === 5 && tc >= 5) return {a: "SPLIT", r: "Deviation Il18: Split 10s vs 5 à TC >= 5"};
    if (pair && getCardValue(cards[0]) === 10 && d === 6 && tc >= 4) return {a: "SPLIT", r: "Deviation Il18: Split 10s vs 6 à TC >= 4"};
    if (p === 10 && d === 10 && tc >= 4) return {a: "DOUBLE", r: "Deviation Il18: Double 10 vs 10 à TC >= 4"};
    if (p === 12 && d === 3 && tc >= 2) return {a: "STAND", r: "Deviation Il18: Stand 12 vs 3 à TC >= 2"};
    if (p === 12 && d === 2 && tc >= 3) return {a: "STAND", r: "Deviation Il18: Stand 12 vs 2 à TC >= 3"};
    if (p === 11 && d === 11 && tc >= 1) return {a: "DOUBLE", r: "Deviation Il18: Double 11 vs A à TC >= 1"};
    if (p === 9 && d === 2 && tc >= 1) return {a: "DOUBLE", r: "Deviation Il18: Double 9 vs 2 à TC >= 1"};
    if (p === 10 && d === 11 && tc >= 4) return {a: "DOUBLE", r: "Deviation Il18: Double 10 vs A à TC >= 4"};
    if (p === 9 && d === 7 && tc >= 3) return {a: "DOUBLE", r: "Deviation Il18: Double 9 vs 7 à TC >= 3"};
    if (p === 16 && d === 9 && tc >= 5) return {a: "STAND", r: "Deviation Il18: Stand 16 vs 9 à TC >= 5"};
    if (p === 13 && d === 2 && tc <= -1) return {a: "HIT", r: "Deviation Il18: Hit 13 vs 2 à TC <= -1"};
    if (p === 12 && d === 4 && tc <= 0) return {a: "HIT", r: "Deviation Il18: Hit 12 vs 4 à TC <= 0"};
    if (p === 12 && d === 5 && tc <= -2) return {a: "HIT", r: "Deviation Il18: Hit 12 vs 5 à TC <= -2"};
    if (p === 12 && d === 6 && tc <= -1) return {a: "HIT", r: "Deviation Il18: Hit 12 vs 6 à TC <= -1"};
    
    return {a: action, r: "Action de Stratégie de Base optimale."};
}

// --- State Management ---
function saveState() {
    stateHistory.push(JSON.parse(JSON.stringify(state)));
    if (stateHistory.length > 50) stateHistory.shift();
}

function undo() {
    if (stateHistory.length > 0) {
        state = stateHistory.pop();
        render();
    }
}

// --- State Machine ---
function resetShoe() {
    state.runningCount = 0;
    state.cardsDealt = 0;
    state.history = [];
    DOM.historyList = document.querySelector('.history-list');
    if(DOM.historyList) DOM.historyList.innerHTML = '<div class="history-empty">Nouvelle chaussure, aucun historique.</div>';
    newRound();
}

function newRound() {
    state.decks = parseInt(DOM.decksSelect.value);
    state.rules = DOM.rulesSelect.value;
    state.playersCnt = parseInt(DOM.playersSelect.value);
    state.mySeat = parseInt(DOM.seatSelect.value);
    if(DOM.inputBet && !DOM.inputBet.disabled) {
        state.currentBet = parseFloat(DOM.inputBet.value) || 50;
    }
    if(DOM.inputBankroll && !DOM.inputBankroll.disabled) {
        state.bankroll = parseFloat(DOM.inputBankroll.value) || 1000;
    }
    
    if (state.mySeat > state.playersCnt) state.mySeat = state.playersCnt;
    
    state.dealerCards = [];
    state.players = [];
    
    // Init Players
    for (let i = 1; i <= state.playersCnt; i++) {
        state.players.push({
            seat: i,
            type: i === state.mySeat ? 'main' : 'other',
            hands: [ { cards: [], status: 'active', doubled: false, bet: i === state.mySeat ? state.currentBet : 0 } ]
        });
    }
    
    // Build Deal Sequence: P1, P2.. Pn, D, P1, P2.. Pn
    state.dealSequence = [];
    for (let loop=0; loop<2; loop++) {
        for (let i=0; i<state.playersCnt; i++) {
            state.dealSequence.push({ target: 'player', seatIndex: i });
        }
    }
    state.dealSequence.push({ target: 'dealer' }); // Single dealer upcard
    
    state.dealIndex = 0;
    state.phase = "DEAL";
    state.waitingForCard = true;
    
    render();
}

function nextTurn() {
    if (state.phase === "DEAL") return; // Handled sequentially
    
    if (state.phase === "PLAY") {
        let seat = state.players[state.activeSeatIndex];
        let hand = seat.hands[state.activeHandIndex];
        
        let handVal = handValue(hand.cards);
        
        // Check auto-resolves
        if (hand.status === 'active') {
            if (handVal > 21) hand.status = 'bust';
            else if (handVal === 21) hand.status = (hand.cards.length === 2 && seat.hands.length === 1) ? 'blackjack' : 'stand';
        }
        
        if (hand.status !== 'active') { // Needs to move to next hand or seat
            if (state.activeHandIndex < seat.hands.length - 1) {
                state.activeHandIndex++; // Next hand for split
                let nextHand = seat.hands[state.activeHandIndex];
                if (nextHand.cards.length < 2) {
                    state.waitingForCard = true;
                }
            } else {
                // Next Seat
                if (state.activeSeatIndex < state.playersCnt - 1) {
                    state.activeSeatIndex++;
                    state.activeHandIndex = 0;
                } else {
                    // All players done, Dealer's turn
                    state.phase = "DEALER";
                    state.waitingForCard = true;
                }
            }
        }
    }
    
    if (state.phase === "DEALER") {
        let dVal = handValue(state.dealerCards);
        let is_soft = isSoft(state.dealerCards);
        let needsHit = false;
        
        if (dVal < 17) needsHit = true;
        else if (dVal === 17 && is_soft && state.rules === "H17") needsHit = true;
        
        if (!needsHit) {
            state.phase = "RESULT";
            state.waitingForCard = false;
            autoLogResult();
        } else {
            state.waitingForCard = true; // Wait for dealer to draw
        }
    }
    
    render();
}

function processAction(action) {
    if (state.phase !== "PLAY") return;
    saveState();
    let seat = state.players[state.activeSeatIndex];
    let hand = seat.hands[state.activeHandIndex];
    
    state.currentAction = action;
    
    if (action === "STAND") {
        hand.status = "stand";
        nextTurn();
    } 
    else if (action === "HIT") {
        state.waitingForCard = true;
    }
    else if (action === "DOUBLE") {
        hand.doubled = true;
        hand.bet *= 2;
        state.waitingForCard = true; // Wait for 1 card only
    }
    else if (action === "SPLIT") {
        // Create new hand, move second card there
        let card2 = hand.cards.pop();
        seat.hands.push({ cards: [card2], status: 'active', doubled: false, bet: hand.bet });
        state.waitingForCard = true; // Wait for card to hit the first hand
    }
    
    render();
}

function receiveCard(rank) {
    saveState();
    state.cardsDealt++;
    state.runningCount += getHiLoValue(rank);
    
    if (state.phase === "DEAL") {
        let step = state.dealSequence[state.dealIndex];
        if (step.target === 'player') {
            state.players[step.seatIndex].hands[0].cards.push(rank);
        } else if (step.target === 'dealer') {
            state.dealerCards.push(rank);
        }
        
        state.dealIndex++;
        if (state.dealIndex >= state.dealSequence.length) {
            state.phase = "PLAY";
            state.activeSeatIndex = 0;
            state.activeHandIndex = 0;
            state.waitingForCard = false;
            nextTurn(); // Evaluate initial blackjacks
        }
    } 
    else if (state.phase === "PLAY" && state.waitingForCard) {
        let hand = state.players[state.activeSeatIndex].hands[state.activeHandIndex];
        hand.cards.push(rank);
        
        if (state.currentAction === "DOUBLE") {
            hand.status = "stand"; // Auto stand after receiving
        }
        state.waitingForCard = false;
        state.currentAction = null;
        nextTurn();
    }
    else if (state.phase === "DEALER" && state.waitingForCard) {
        state.dealerCards.push(rank);
        state.waitingForCard = false;
        nextTurn();
    }
    
    render();
}

function autoLogResult() {
    let tc = getTrueCount().toFixed(1);
    let mySeatObj = state.players.find(p => p.type === 'main');
    let dVal = handValue(state.dealerCards);
    let dBlackjack = state.dealerCards.length === 2 && dVal === 21;
    
    let histList = document.querySelector('.history-list');
    if (histList) {
        let empty = histList.querySelector('.history-empty');
        if (empty) empty.remove();
        
        mySeatObj.hands.forEach((hand, idx) => {
            let hVal = handValue(hand.cards);
            let hBlackjack = hand.cards.length === 2 && hVal === 21 && mySeatObj.hands.length === 1;
            let type = 'push';
            let detailStr = '';
            
            if (hand.status === 'bust') {
                type = 'lose';
                detailStr = 'BUST';
            } else if (hBlackjack && !dBlackjack) {
                type = 'win';
                detailStr = 'BJ 3:2';
            } else if (!hBlackjack && dBlackjack) {
                type = 'lose';
            } else if (hBlackjack && dBlackjack) {
                type = 'push';
            } else if (dVal > 21) {
                type = 'win';
                detailStr = 'D.BUST';
            } else if (hVal > dVal) {
                type = 'win';
            } else if (hVal < dVal) {
                type = 'lose';
            }
            
            let handProfit = 0;
            if (type === 'win') {
                if (detailStr.includes('BJ')) handProfit = hand.bet * 1.5;
                else handProfit = hand.bet;
            } else if (type === 'lose') {
                handProfit = -hand.bet;
            }
            state.bankroll += handProfit;
            let profitStr = handProfit > 0 ? `+${handProfit}€` : (handProfit < 0 ? `${handProfit}€` : `0€`);
            
            let label = type === 'win' ? 'GAGNÉ' : (type === 'lose' ? 'PERDU' : 'PUSH');
            let colorCode = type === 'win' ? '#3ff19f' : (type === 'lose' ? '#ff6b7e' : '#a8b2c4');
            
            let c = document.createElement('div');
            c.className = `history-item`;
            c.style.borderLeft = `4px solid ${colorCode}`; 
            c.style.background = '#11141a';
            c.style.padding = '10px 14px';
            c.style.borderRadius = '8px';
            c.style.marginBottom = '8px';

            c.innerHTML = `
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span style="color:${colorCode}; font-weight:800; font-size:0.9rem;">${label} <span style="font-size:0.8rem; margin-left:8px;">${profitStr}</span> ${detailStr ? `<span style="font-size:0.7rem; background:rgba(255,255,255,0.1); padding:2px 6px; border-radius:4px; margin-left:6px;">${detailStr}</span>` : ''}</span>
                    <span style="color:#8b929c; font-size:0.8rem; font-family:'JetBrains Mono';">TC: ${tc}</span>
                </div>
                <div style="font-size:0.8rem; color:#8b929c;">
                    Toi: ${hVal} <span style="margin:0 4px;">vs</span> D: ${dVal} 
                    ${hand.doubled ? `<span style="color:#4a8bf5; margin-left:6px; font-weight:700;">(Mise x2: ${hand.bet}€)</span>` : ''}
                    ${mySeatObj.hands.length > 1 ? `<span style="color:#b8861e; margin-left:6px; font-weight:700;">(Main ${idx+1})</span>` : ''}
                </div>
            `;
            histList.prepend(c);
            if (histList.children.length > 20) histList.lastChild.remove();
        });
    }
}

// --- UI Generators ---
function getCardHtml(rank, isSmall = false) {
    let cls = isSmall ? 'card-filled-sm' : 'card-filled';
    let isRed = ['♥','♦'].includes(rank) ? 'red' : '';
    return `<div class="${cls} ${isRed}">${rank}</div>`;
}

// --- Render Logic ---
function render() {
    // 1. Update Counts
    DOM.valRC.textContent = (state.runningCount > 0 ? "+" : "") + state.runningCount;
    DOM.valTC.textContent = (getTrueCount() > 0 ? "+" : "") + getTrueCount().toFixed(2);
    
    // 2. Render Dealer
    DOM.cardsDealer.innerHTML = state.dealerCards.map(r => getCardHtml(r)).join('');
    if (state.phase === "DEAL" || state.dealerCards.length === 0) {
        let emptyCount = state.phase === "DEAL" ? 1 : 2;
        DOM.cardsDealer.innerHTML += '<div class="card-empty">+</div>'.repeat(emptyCount);
    }
    
    let dVal = handValue(state.dealerCards);
    DOM.totalDealer.textContent = `Total ${dVal === 0 ? '—' : dVal}`;
    if (dVal > 21) DOM.zoneDealer.style.boxShadow = "inset 0 0 20px rgba(218, 23, 49, 0.4)";
    else DOM.zoneDealer.style.boxShadow = "none";

    // 3. Render Players Container
    DOM.playersContainer.innerHTML = '';
    state.players.forEach((p, pIndex) => {
        let isMySeat = (p.type === 'main');
        let isActiveSeat = (state.phase === "PLAY" && state.activeSeatIndex === pIndex);
        
        let zoneHtml = `<div class="zone ${isMySeat ? 'player-zone' : 'other-zone'} ${isActiveSeat ? 'active-turn' : ''}">`;
        
        zoneHtml += `
            <div class="zone-header">
                <div class="zone-title">
                    ${isMySeat ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>' : ''}
                    Siège ${p.seat} ${isMySeat ? '(Toi)' : ''}
                </div>
            </div>
        `;
        
        p.hands.forEach((hand, hIndex) => {
            let isActiveHand = (isActiveSeat && state.activeHandIndex === hIndex);
            let hVal = handValue(hand.cards);
            let st = hand.status; // active, bust, stand, blackjack
            
            let statusBadge = '';
            if (st === 'bust') statusBadge = '<span class="hand-status bust">BUST</span>';
            else if (st === 'blackjack') statusBadge = '<span class="hand-status blackjack">BLACKJACK</span>';
            else if (isActiveHand) statusBadge = '<span class="hand-status active">AU TOUR</span>';
            
            zoneHtml += `<div class="hand-container">
                <div class="hand-row">
                    <div class="zone-total">Total ${hVal === 0 ? '—' : hVal}${isSoft(hand.cards) && hVal<21 ? ' (Soft)' : ''}</div>
                    ${statusBadge}
                </div>
                <div class="cards-area">
                    ${hand.cards.map(c => getCardHtml(c, !isMySeat)).join('')}
                    ${isActiveHand && state.waitingForCard ? `<div class="${isMySeat ? 'card-empty' : 'card-empty-sm'}">+</div>` : ''}
                </div>
            </div>`;
        });
        
        zoneHtml += `</div>`;
        DOM.playersContainer.innerHTML += zoneHtml;
    });

    // 4. Update Control Panel (Action vs Cards)
    if (state.phase === "CONFIG") {
        DOM.actionGrid.style.display = 'none';
        DOM.rankGrid.style.display = 'none';
        DOM.lblActionTitle.textContent = "EN ATTENTE";
        DOM.lblActionSub.textContent = "Lancez une nouvelle manche";
    } 
    else if (state.phase === "DEAL" || state.waitingForCard) {
        DOM.actionGrid.style.display = 'none';
        DOM.rankGrid.style.display = 'grid';
        
        let targetStr = "";
        if (state.phase === "DEAL") {
            let step = state.dealSequence[state.dealIndex];
            targetStr = step.target === 'dealer' ? "Dealer" : `Siège ${state.players[step.seatIndex].seat}`;
            DOM.lblActionTitle.textContent = "DONNE INITIALE: QUELLE CARTE ?";
        } else if (state.phase === "PLAY") {
            let s = state.players[state.activeSeatIndex];
            targetStr = `Siège ${s.seat}`;
            DOM.lblActionTitle.textContent = "TIRAGE: QUELLE CARTE ?";
        } else if (state.phase === "DEALER") {
            targetStr = "Dealer";
            DOM.lblActionTitle.textContent = "DEALER JOUE: QUELLE CARTE ?";
        }
        DOM.lblActionSub.textContent = `Cible: ${targetStr}`;
    } 
    else if (state.phase === "PLAY" && !state.waitingForCard) {
        DOM.rankGrid.style.display = 'none';
        DOM.actionGrid.style.display = 'grid';
        
        let s = state.players[state.activeSeatIndex];
        let h = s.hands[state.activeHandIndex];
        
        DOM.lblActionTitle.textContent = s.type === 'main' ? "À TON TOUR : SÉLECTIONNE TON ACTION" : "TOUR DES AUTRES : ACTION DU JOUEUR";
        DOM.lblActionSub.textContent = `Cible: Siège ${s.seat}`;
        
        // Button Logic
        DOM.btnActionSplit.disabled = !isPair(h.cards);
        DOM.btnActionDouble.disabled = h.cards.length > 2;
    }
    else if (state.phase === "RESULT") {
        DOM.actionGrid.style.display = 'none';
        DOM.rankGrid.style.display = 'none';
        DOM.lblActionTitle.textContent = "FIN DE MANCHE";
        DOM.lblActionSub.textContent = "Sélectionnez le résultat à gauche";
    }
    
    // 5. Update Advice Engine
    if (state.phase === "PLAY" && state.players[state.activeSeatIndex].type === 'main' && !state.waitingForCard) {
        let hand = state.players[state.activeSeatIndex].hands[state.activeHandIndex];
        let dUp = state.dealerCards[0] || '10'; // Fallback
        
        let baseAction = basicStrategy(hand.cards, dUp, state.rules);
        let finalAdvice = applyDeviations(baseAction, hand.cards, dUp, getTrueCount());
        
        DOM.adviceMain.textContent = finalAdvice.a;
        DOM.advicePill.textContent = "CONSEIL OPTIMAL";
        DOM.adviceReason.textContent = finalAdvice.r;
        
        DOM.adviceMain.style.color = (finalAdvice.a === "STAND") ? "#da1731" : (finalAdvice.a === "HIT" ? "#2dc479" : (finalAdvice.a === "DOUBLE" ? "#4a8bf5" : "#b8861e"));
    } else if (state.phase === "DEALER") {
        DOM.adviceMain.textContent = "DEALER";
        DOM.advicePill.textContent = "PHASE";
        DOM.adviceReason.textContent = "Le croupier tire ses cartes.";
        DOM.adviceMain.style.color = "white";
    } else if (state.phase === "RESULT") {
        DOM.adviceMain.textContent = "TERMINÉ";
        DOM.advicePill.textContent = "RÉSOLU";
        DOM.adviceReason.textContent = "Lancez une Nouvelle manche.";
        DOM.adviceMain.style.color = "white";
    } else {
        DOM.adviceMain.textContent = "ATTENTE";
        DOM.advicePill.textContent = "SUIVI";
        DOM.adviceReason.textContent = "Rentrez les cartes distribuées.";
        DOM.adviceMain.style.color = "#8b929c";
    }
    
    // 6. Update Betting Widget
    if (DOM.inputBankroll) {
        if (state.phase === "CONFIG" || state.phase === "RESULT") {
            DOM.inputBankroll.disabled = false;
        } else {
            DOM.inputBankroll.disabled = true;
            DOM.inputBankroll.value = parseFloat(state.bankroll.toFixed(2));
        }
    }
    if (DOM.inputBet) {
        if (state.phase === "CONFIG" || state.phase === "RESULT") {
            DOM.inputBet.disabled = false;
        } else {
            DOM.inputBet.disabled = true;
            DOM.inputBet.value = state.currentBet;
        }
    }
}

// --- Event Listeners ---
DOM.btnRejouer.onclick = () => { saveState(); resetShoe(); };
if(DOM.btnUndo) DOM.btnUndo.onclick = undo;
DOM.btnNouvelleManche.onclick = () => { saveState(); newRound(); };

document.querySelectorAll('.rank-btn').forEach(btn => {
    btn.onclick = () => {
        if (state.phase === "CONFIG" || state.phase === "RESULT") return;
        receiveCard(btn.getAttribute('data-val'));
    };
});

DOM.btnActionHit.onclick = () => processAction("HIT");
DOM.btnActionStand.onclick = () => processAction("STAND");
DOM.btnActionDouble.onclick = () => processAction("DOUBLE");
DOM.btnActionSplit.onclick = () => processAction("SPLIT");

// Re-render when config changes just to be clean
DOM.decksSelect.onchange = () => { state.decks = parseInt(DOM.decksSelect.value); render(); };
DOM.rulesSelect.onchange = () => { state.rules = DOM.rulesSelect.value; render(); };
DOM.playersSelect.onchange = () => { state.playersCnt = parseInt(DOM.playersSelect.value); render(); };
DOM.seatSelect.onchange = () => { state.mySeat = parseInt(DOM.seatSelect.value); render(); };

// Init logic
render();
