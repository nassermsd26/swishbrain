import React, { useState, useEffect, useMemo } from 'react';
import { History, Calendar, Trophy, TrendingUp, AlertCircle, Clock, Eye, CheckCircle, XCircle, Trash2, CalendarX } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { TEAMS } from '../constants';
import { PredictionResult } from '../types';
import Standings from './Standings';
import RecentScores from './RecentScores';
import PredictionPage from './PredictionPage';

interface HistoryItem extends PredictionResult {
  timestamp: string;
  isOffSchedule?: boolean;  // True si le match n'est pas dans le programme
  actualResult?: {
    completed: boolean;
    scoreA?: number;  // Score réel de teamA
    scoreB?: number;  // Score réel de teamB
    actualWinner?: string;
    isCorrect?: boolean;
  };
}

const HistoryPage: React.FC = () => {
  const { theme } = useTheme();
  const { isAuthenticated, token } = useAuth();
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5002/api';
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPrediction, setSelectedPrediction] = useState<PredictionResult | null>(null);
  const [activeTab, setActiveTab] = useState<'past' | 'upcoming' | 'offSchedule'>('past');
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [scheduledGames, setScheduledGames] = useState<Array<{ home: string, away: string }>>([]);

  useEffect(() => {
    const fetchHistory = async () => {
      if (!isAuthenticated || !token) {
        setError("Vous devez être connecté pour voir votre historique");
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_BASE}/history`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          const historyItems = data.history || [];

          // Filtrer les doublons basés sur matchId ou teamA-teamB-timestamp
          const seenMatches = new Set<string>();
          const uniqueHistoryItems = historyItems.filter((item: HistoryItem) => {
            // Créer une clé unique pour chaque match
            const matchKey = `${item.teamA.abbr}-${item.teamB.abbr}-${item.timestamp}`;
            if (seenMatches.has(matchKey)) {
              return false; // Doublon, on l'exclut
            }
            seenMatches.add(matchKey);
            return true;
          });

          // Récupérer les résultats réels pour chaque match
          const historyWithResults = await Promise.all(
            uniqueHistoryItems.map(async (item: HistoryItem) => {
              try {
                const resultResponse = await fetch(
                  `${API_BASE}/game-result?teamA=${item.teamA.abbr}&teamB=${item.teamB.abbr}&date=${item.timestamp}`
                );
                if (resultResponse.ok) {
                  const resultData = await resultResponse.json();
                  if (resultData.completed) {
                    // Déterminer les scores pour chaque équipe de la prédiction
                    const predictedWinner = item.winner;
                    const actualWinner = resultData.actualWinner;
                    const isCorrect = predictedWinner === actualWinner;

                    // Trouver les scores pour teamA et teamB en comparant les abréviations
                    let scoreA, scoreB;
                    if (resultData.scores) {
                      scoreA = resultData.scores[item.teamA.abbr] ?? null;
                      scoreB = resultData.scores[item.teamB.abbr] ?? null;
                    }

                    // Fallback si scores n'est pas disponible
                    if (scoreA === null || scoreB === null) {
                      if (resultData.homeTeam === item.teamA.abbr) {
                        scoreA = resultData.homeScore;
                        scoreB = resultData.awayScore;
                      } else if (resultData.awayTeam === item.teamA.abbr) {
                        scoreA = resultData.awayScore;
                        scoreB = resultData.homeScore;
                      } else {
                        // Si l'ordre ne correspond pas, utiliser l'ordre de la prédiction
                        scoreA = resultData.homeScore;
                        scoreB = resultData.awayScore;
                      }
                    }

                    return {
                      ...item,
                      actualResult: {
                        completed: true,
                        scoreA: scoreA,  // Score réel de teamA
                        scoreB: scoreB,  // Score réel de teamB
                        actualWinner: actualWinner,
                        isCorrect: isCorrect
                      }
                    };
                  }
                }
              } catch (err) {
                console.error("Error fetching game result:", err);
              }
              return {
                ...item,
                actualResult: { completed: false }
              };
            })
          );

          setHistory(historyWithResults);
        } else {
          const errorData = await response.json().catch(() => ({ error: response.statusText }));
          setError(errorData.error || "Erreur lors du chargement de l'historique");
          console.error("Erreur historique:", errorData);
        }
      } catch (err) {
        setError("Erreur de connexion au serveur");
        console.error("Error fetching history:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [isAuthenticated, token]);

  // Récupérer le programme actuel (aujourd'hui et demain)
  useEffect(() => {
    const fetchSchedule = async () => {
      try {
        const response = await fetch(`${API_BASE}/schedule`);
        if (response.ok) {
          const data = await response.json();
          const games = data.games || [];
          setScheduledGames(games.map((g: any) => ({ home: g.home, away: g.away })));

          // #region agent log
          fetch('http://127.0.0.1:7243/ingest/6ee6481c-2918-418a-902a-abe6882cde4d', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'HistoryPage.tsx:useEffect-fetchSchedule', message: 'Schedule fetched', data: { gamesCount: games.length, games: games.map((g: any) => ({ home: g.home, away: g.away })) }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'A' }) }).catch(() => { });
          // #endregion
        }
      } catch (err) {
        console.error("Error fetching schedule:", err);

        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/6ee6481c-2918-418a-902a-abe6882cde4d', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'HistoryPage.tsx:useEffect-fetchSchedule', message: 'Error fetching schedule', data: { error: String(err) }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'A' }) }).catch(() => { });
        // #endregion
      }
    };
    fetchSchedule();
  }, []);

  const formatDate = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return timestamp;
    }
  };

  const getTeam = (abbr: string) => TEAMS.find(t => t.abbr === abbr);

  // Séparer les matchs passés, à venir et hors programme
  const { pastGames, upcomingGames, offScheduleGames } = useMemo(() => {
    const past: HistoryItem[] = [];
    const upcoming: HistoryItem[] = [];
    const offSchedule: HistoryItem[] = [];

    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/6ee6481c-2918-418a-902a-abe6882cde4d', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'HistoryPage.tsx:useMemo-classification', message: 'Starting classification', data: { historyCount: history.length, scheduledGamesCount: scheduledGames.length }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'B' }) }).catch(() => { });
    // #endregion

    history.forEach(item => {
      // Vérifier si le match est dans le programme actuel (aujourd'hui ou demain)
      const isInSchedule = scheduledGames.some(game =>
        (game.home === item.teamA.abbr && game.away === item.teamB.abbr) ||
        (game.home === item.teamB.abbr && game.away === item.teamA.abbr)
      );

      // #region agent log
      fetch('http://127.0.0.1:7243/ingest/6ee6481c-2918-418a-902a-abe6882cde4d', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'HistoryPage.tsx:useMemo-classification', message: 'Classifying match', data: { matchId: item.matchId, teamA: item.teamA.abbr, teamB: item.teamB.abbr, isOffSchedule: item.isOffSchedule, isInSchedule: isInSchedule, completed: item.actualResult?.completed }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'post-fix', hypothesisId: 'C' }) }).catch(() => { });
      // #endregion

      // Un match est hors programme seulement s'il n'est PAS dans le programme actuel ET qu'il n'est pas complété
      // Si un match est dans le programme actuel, il ne peut jamais être "hors programme", même s'il a été marqué comme tel
      const shouldBeOffSchedule = !isInSchedule && !item.actualResult?.completed;

      // #region agent log
      fetch('http://127.0.0.1:7243/ingest/6ee6481c-2918-418a-902a-abe6882cde4d', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'HistoryPage.tsx:useMemo-classification', message: 'Classification decision', data: { matchId: item.matchId, shouldBeOffSchedule: shouldBeOffSchedule, isInSchedule: isInSchedule, completed: item.actualResult?.completed }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'post-fix', hypothesisId: 'C' }) }).catch(() => { });
      // #endregion

      if (item.actualResult?.completed) {
        past.push(item);
      } else if (shouldBeOffSchedule) {
        offSchedule.push(item);

        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/6ee6481c-2918-418a-902a-abe6882cde4d', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'HistoryPage.tsx:useMemo-classification', message: 'Match classified as offSchedule', data: { matchId: item.matchId, reason: 'not_in_current_schedule' }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'post-fix', hypothesisId: 'C' }) }).catch(() => { });
        // #endregion
      } else {
        upcoming.push(item);

        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/6ee6481c-2918-418a-902a-abe6882cde4d', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'HistoryPage.tsx:useMemo-classification', message: 'Match classified as upcoming', data: { matchId: item.matchId }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'post-fix', hypothesisId: 'C' }) }).catch(() => { });
        // #endregion
      }
    });

    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/6ee6481c-2918-418a-902a-abe6882cde4d', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'HistoryPage.tsx:useMemo-classification', message: 'Classification complete', data: { pastCount: past.length, upcomingCount: upcoming.length, offScheduleCount: offSchedule.length }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'B' }) }).catch(() => { });
    // #endregion

    return { pastGames: past, upcomingGames: upcoming, offScheduleGames: offSchedule };
  }, [history, scheduledGames]);

  // Calculer les statistiques (seulement pour les matchs du programme, pas hors programme)
  const stats = useMemo(() => {
    const total = pastGames.length;
    const wins = pastGames.filter(item => item.actualResult?.isCorrect).length;
    const losses = total - wins;
    const winRate = total > 0 ? ((wins / total) * 100).toFixed(1) : '0.0';

    return { total, wins, losses, winRate };
  }, [pastGames]);

  const handleViewPrediction = (item: HistoryItem) => {
    setSelectedPrediction(item as PredictionResult);
  };

  const handleBackToHistory = () => {
    setSelectedPrediction(null);
  };

  const handleDeletePrediction = async (matchId: string) => {
    if (!isAuthenticated || !token) return;

    if (!confirm('Êtes-vous sûr de vouloir supprimer cette prédiction ?')) {
      return;
    }

    setDeletingId(matchId);
    try {
      const response = await fetch(`${API_BASE}/history/${matchId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        // Recharger l'historique
        const historyResponse = await fetch(`${API_BASE}/history`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (historyResponse.ok) {
          const data = await historyResponse.json();
          const historyItems = data.history || [];

          // Filtrer les doublons
          const seenMatches = new Set<string>();
          const uniqueHistoryItems = historyItems.filter((item: HistoryItem) => {
            const matchKey = `${item.teamA.abbr}-${item.teamB.abbr}-${item.timestamp}`;
            if (seenMatches.has(matchKey)) {
              return false;
            }
            seenMatches.add(matchKey);
            return true;
          });

          // Récupérer les résultats réels
          const historyWithResults = await Promise.all(
            uniqueHistoryItems.map(async (item: HistoryItem) => {
              try {
                const resultResponse = await fetch(
                  `${API_BASE}/game-result?teamA=${item.teamA.abbr}&teamB=${item.teamB.abbr}&date=${item.timestamp}`
                );
                if (resultResponse.ok) {
                  const resultData = await resultResponse.json();
                  if (resultData.completed) {
                    const predictedWinner = item.winner;
                    const actualWinner = resultData.actualWinner;
                    const isCorrect = predictedWinner === actualWinner;

                    let scoreA, scoreB;
                    if (resultData.scores) {
                      scoreA = resultData.scores[item.teamA.abbr] ?? null;
                      scoreB = resultData.scores[item.teamB.abbr] ?? null;
                    }

                    if (scoreA === null || scoreB === null) {
                      if (resultData.homeTeam === item.teamA.abbr) {
                        scoreA = resultData.homeScore;
                        scoreB = resultData.awayScore;
                      } else if (resultData.awayTeam === item.teamA.abbr) {
                        scoreA = resultData.awayScore;
                        scoreB = resultData.homeScore;
                      } else {
                        scoreA = resultData.homeScore;
                        scoreB = resultData.awayScore;
                      }
                    }

                    return {
                      ...item,
                      actualResult: {
                        completed: true,
                        scoreA: scoreA,
                        scoreB: scoreB,
                        actualWinner: actualWinner,
                        isCorrect: isCorrect
                      }
                    };
                  }
                }
              } catch (err) {
                console.error("Error fetching game result:", err);
              }
              return {
                ...item,
                actualResult: { completed: false }
              };
            })
          );

          setHistory(historyWithResults);
        }
      } else {
        const errorData = await response.json().catch(() => ({ error: response.statusText }));
        alert(errorData.error || "Erreur lors de la suppression");
      }
    } catch (err) {
      console.error("Error deleting prediction:", err);
      alert("Erreur lors de la suppression");
    } finally {
      setDeletingId(null);
    }
  };

  // Si une prédiction est sélectionnée, afficher la page de prédiction
  if (selectedPrediction) {
    return <PredictionPage prediction={selectedPrediction} onBack={handleBackToHistory} />;
  }

  if (!isAuthenticated) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${theme === 'dark' ? 'bg-gray-950' : 'bg-gray-50'}`}>
        <div className={`text-center p-8 rounded-lg ${theme === 'dark' ? 'bg-gray-900' : 'bg-white'} shadow-lg`}>
          <AlertCircle className="w-16 h-16 mx-auto mb-4 text-[#C8102E]" />
          <h2 className={`text-2xl font-bold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            Connexion requise
          </h2>
          <p className={`${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            Vous devez être connecté pour voir votre historique de prédictions.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-gray-950' : 'bg-gray-50'} py-8`}>
      <div className="max-w-[1600px] mx-auto px-4">
        <div className="flex gap-6">
          {/* Sidebar gauche - Derniers scores */}
          <aside className="hidden lg:block flex-shrink-0 sticky top-24 h-[calc(100vh-8rem)]">
            <RecentScores />
          </aside>

          {/* Contenu principal - Agrandi */}
          <div className="flex-1 min-w-0 max-w-5xl">
            <div className="mb-8">
              <div className="flex items-center gap-3 mb-4">
                <History className={`w-8 h-8 ${theme === 'dark' ? 'text-[#C8102E]' : 'text-[#1D428A]'}`} />
                <h1 className={`text-4xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                  Historique des Prédictions
                </h1>
              </div>
              <p className={`text-lg ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                Retrouvez toutes vos analyses de matchs précédentes
              </p>

              {/* Statistiques */}
              {stats.total > 0 && (
                <div className={`mt-6 p-4 rounded-lg ${theme === 'dark' ? 'bg-gray-900' : 'bg-white'} border ${theme === 'dark' ? 'border-gray-800' : 'border-gray-200'}`}>
                  <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-green-500" />
                      <span className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                        Gagnants: <span className="text-green-500">{stats.wins}</span>
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <XCircle className="w-5 h-5 text-red-500" />
                      <span className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                        Perdants: <span className="text-red-500">{stats.losses}</span>
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Trophy className={`w-5 h-5 ${theme === 'dark' ? 'text-yellow-400' : 'text-yellow-600'}`} />
                      <span className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                        Taux de réussite: <span className="text-yellow-500">{stats.winRate}%</span>
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Tabs - Centrés */}
              <div className="mt-6 flex justify-center gap-2 border-b border-gray-200 dark:border-gray-800">
                <button
                  onClick={() => setActiveTab('past')}
                  className={`px-6 py-2 font-medium transition-colors ${activeTab === 'past'
                      ? 'border-b-2 border-[#C8102E] text-[#C8102E]'
                      : theme === 'dark' ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'
                    }`}
                >
                  Matchs Passés ({pastGames.length})
                </button>
                <button
                  onClick={() => setActiveTab('upcoming')}
                  className={`px-6 py-2 font-medium transition-colors ${activeTab === 'upcoming'
                      ? 'border-b-2 border-[#C8102E] text-[#C8102E]'
                      : theme === 'dark' ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'
                    }`}
                >
                  Matchs à Venir ({upcomingGames.length})
                </button>
                <button
                  onClick={() => setActiveTab('offSchedule')}
                  className={`px-6 py-2 font-medium transition-colors ${activeTab === 'offSchedule'
                      ? 'border-b-2 border-[#C8102E] text-[#C8102E]'
                      : theme === 'dark' ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'
                    }`}
                >
                  <CalendarX className="w-4 h-4 inline mr-1" />
                  Hors Programme ({offScheduleGames.length})
                </button>
              </div>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-20">
                <div className={`animate-spin rounded-full h-12 w-12 border-b-2 ${theme === 'dark' ? 'border-[#C8102E]' : 'border-[#1D428A]'}`}></div>
              </div>
            ) : error ? (
              <div className={`p-6 rounded-lg text-center ${theme === 'dark' ? 'bg-red-900/30 border border-red-500/50 text-red-300' : 'bg-red-50 border border-red-200 text-red-600'}`}>
                {error}
              </div>
            ) : history.length === 0 ? (
              <div className={`text-center py-20 ${theme === 'dark' ? 'bg-gray-900' : 'bg-white'} rounded-lg shadow-lg`}>
                <History className={`w-16 h-16 mx-auto mb-4 ${theme === 'dark' ? 'text-gray-600' : 'text-gray-400'}`} />
                <h3 className={`text-xl font-semibold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                  Aucune prédiction
                </h3>
                <p className={`${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                  Analysez un match pour voir votre historique ici
                </p>
              </div>
            ) : (() => {
              const currentGames = activeTab === 'past' ? pastGames : activeTab === 'upcoming' ? upcomingGames : offScheduleGames;

              if (currentGames.length === 0) {
                return (
                  <div className={`text-center py-20 ${theme === 'dark' ? 'bg-gray-900' : 'bg-white'} rounded-lg shadow-lg`}>
                    <History className={`w-16 h-16 mx-auto mb-4 ${theme === 'dark' ? 'text-gray-600' : 'text-gray-400'}`} />
                    <h3 className={`text-xl font-semibold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                      {activeTab === 'past' ? 'Aucun match passé' : activeTab === 'upcoming' ? 'Aucun match à venir' : 'Aucune prédiction hors programme'}
                    </h3>
                    <p className={`${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                      {activeTab === 'past'
                        ? 'Les matchs passés apparaîtront ici une fois qu\'ils auront été joués'
                        : activeTab === 'upcoming'
                          ? 'Les matchs à venir apparaîtront ici'
                          : 'Les prédictions hors programme (matchs personnalisés) apparaîtront ici'}
                    </p>
                  </div>
                );
              }

              return (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                  {currentGames.map((item) => {
                    const teamA = getTeam(item.teamA.abbr);
                    const teamB = getTeam(item.teamB.abbr);
                    const isTeamAWinner = item.winner === item.teamA.abbr;

                    const isCorrect = item.actualResult?.isCorrect;
                    const isCompleted = item.actualResult?.completed;

                    // Vérifier si le match est réellement hors programme (pas dans le programme actuel)
                    const isInSchedule = scheduledGames.some(game =>
                      (game.home === item.teamA.abbr && game.away === item.teamB.abbr) ||
                      (game.home === item.teamB.abbr && game.away === item.teamA.abbr)
                    );
                    const isActuallyOffSchedule = !isInSchedule && !isCompleted;

                    // Déterminer la couleur de la bordure selon le résultat
                    let borderColor = '';
                    if (isCompleted) {
                      borderColor = isCorrect
                        ? 'border-green-500 dark:border-green-600'
                        : 'border-red-500 dark:border-red-600';
                    }

                    return (
                      <div
                        key={item.matchId}
                        onClick={() => handleViewPrediction(item)}
                        className={`rounded-lg border-2 shadow-lg overflow-hidden transition-all hover:shadow-xl cursor-pointer ${isCompleted
                            ? borderColor
                            : theme === 'dark'
                              ? 'border-gray-800 hover:border-gray-700'
                              : 'border-gray-200 hover:border-gray-300'
                          } ${theme === 'dark'
                            ? 'bg-gray-900 hover:bg-gray-800'
                            : 'bg-white hover:bg-gray-50'
                          }`}
                      >
                        {/* Header avec date et résultat */}
                        <div className={`p-4 border-b ${theme === 'dark' ? 'border-gray-800 bg-gray-950/50' : 'border-gray-200 bg-gray-50'}`}>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 text-sm">
                              <Calendar className={`w-4 h-4 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`} />
                              <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>
                                {formatDate(item.timestamp)}
                              </span>
                              {isActuallyOffSchedule && (
                                <span className="px-2 py-0.5 text-xs font-semibold bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded">
                                  <CalendarX className="w-3 h-3 inline mr-1" />
                                  Hors Programme
                                </span>
                              )}
                            </div>
                            {isCompleted && (
                              <div className="flex items-center gap-1">
                                {isCorrect ? (
                                  <>
                                    <CheckCircle className="w-5 h-5 text-green-500" />
                                    <span className="text-xs font-semibold text-green-500">Gagnant</span>
                                  </>
                                ) : (
                                  <>
                                    <XCircle className="w-5 h-5 text-red-500" />
                                    <span className="text-xs font-semibold text-red-500">Perdu</span>
                                  </>
                                )}
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Match */}
                        <div className="p-6">
                          <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3 flex-1">
                              {teamA?.logo && (
                                <img src={teamA.logo} alt={item.teamA.abbr} className="w-10 h-10 object-contain" />
                              )}
                              <span className={`font-semibold ${isTeamAWinner ? (theme === 'dark' ? 'text-white' : 'text-gray-900') : (theme === 'dark' ? 'text-gray-400' : 'text-gray-600')}`}>
                                {item.teamA.abbr}
                              </span>
                            </div>
                            <span className={`text-2xl font-bold ${isTeamAWinner ? 'text-[#C8102E]' : (theme === 'dark' ? 'text-gray-600' : 'text-gray-400')}`}>
                              {item.scoreA}
                            </span>
                          </div>

                          <div className="flex items-center justify-center mb-4">
                            <span className={`text-sm ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>VS</span>
                          </div>

                          <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3 flex-1">
                              {teamB?.logo && (
                                <img src={teamB.logo} alt={item.teamB.abbr} className="w-10 h-10 object-contain" />
                              )}
                              <span className={`font-semibold ${!isTeamAWinner ? (theme === 'dark' ? 'text-white' : 'text-gray-900') : (theme === 'dark' ? 'text-gray-400' : 'text-gray-600')}`}>
                                {item.teamB.abbr}
                              </span>
                            </div>
                            <span className={`text-2xl font-bold ${!isTeamAWinner ? 'text-[#C8102E]' : (theme === 'dark' ? 'text-gray-600' : 'text-gray-400')}`}>
                              {item.scoreB}
                            </span>
                          </div>

                          {/* Résultat réel si disponible */}
                          {isCompleted && item.actualResult && (
                            <div className={`mt-4 p-3 rounded-lg ${isCorrect
                                ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                                : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
                              }`}>
                              <div className="text-xs font-semibold mb-2 text-gray-600 dark:text-gray-400">
                                Résultat réel:
                              </div>
                              <div className="flex items-center justify-between text-sm mb-1">
                                <span className="text-black dark:text-white font-semibold">
                                  {item.teamA.abbr}: {item.actualResult.scoreA ?? 'N/A'}
                                </span>
                                <span className="text-black dark:text-white font-semibold">
                                  {item.teamB.abbr}: {item.actualResult.scoreB ?? 'N/A'}
                                </span>
                              </div>
                              <div className="text-xs mt-1 text-black dark:text-white">
                                Vainqueur réel: <span className="font-semibold">{item.actualResult.actualWinner}</span>
                              </div>
                            </div>
                          )}

                          {/* Stats */}
                          <div className={`mt-4 pt-4 border-t ${theme === 'dark' ? 'border-gray-800' : 'border-gray-200'}`}>
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <Trophy className={`w-4 h-4 ${theme === 'dark' ? 'text-yellow-400' : 'text-yellow-600'}`} />
                                <span className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                                  Prédit: {item.winner}
                                </span>
                              </div>
                            </div>
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <TrendingUp className={`w-4 h-4 ${theme === 'dark' ? 'text-green-400' : 'text-green-600'}`} />
                                <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                                  Confiance: {item.confidence}%
                                </span>
                              </div>
                            </div>
                            <div className="flex items-center justify-between mb-2">
                              <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                                Total: {item.totalPoints} pts
                              </span>
                              <span className={`text-xs px-2 py-1 rounded ${item.bettingAnalysis.riskLevel === 'Secure'
                                  ? theme === 'dark' ? 'bg-green-900/30 text-green-400' : 'bg-green-100 text-green-700'
                                  : item.bettingAnalysis.riskLevel === 'Risky'
                                    ? theme === 'dark' ? 'bg-yellow-900/30 text-yellow-400' : 'bg-yellow-100 text-yellow-700'
                                    : theme === 'dark' ? 'bg-red-900/30 text-red-400' : 'bg-red-100 text-red-700'
                                }`}>
                                {item.bettingAnalysis.riskLevel}
                              </span>
                            </div>
                            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-800 flex gap-2">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleViewPrediction(item);
                                }}
                                className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg transition-colors ${theme === 'dark'
                                    ? 'bg-[#C8102E] hover:bg-[#a00d25] text-white'
                                    : 'bg-[#C8102E] hover:bg-[#a00d25] text-white'
                                  }`}
                              >
                                <Eye className="w-4 h-4" />
                                <span className="text-sm font-medium">Voir</span>
                              </button>
                              {(activeTab === 'offSchedule' || activeTab === 'upcoming') && (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleDeletePrediction(item.matchId);
                                  }}
                                  disabled={deletingId === item.matchId}
                                  className={`px-4 py-2 rounded-lg transition-colors ${deletingId === item.matchId
                                      ? 'bg-gray-400 cursor-not-allowed'
                                      : theme === 'dark'
                                        ? 'bg-red-600 hover:bg-red-700 text-white'
                                        : 'bg-red-500 hover:bg-red-600 text-white'
                                    }`}
                                >
                                  {deletingId === item.matchId ? (
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                  ) : (
                                    <Trash2 className="w-4 h-4" />
                                  )}
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              );
            })()}
          </div>

          {/* Sidebar droite - Standings */}
          <aside className="hidden xl:block flex-shrink-0 sticky top-24 h-[calc(100vh-8rem)]">
            <Standings />
          </aside>
        </div>
      </div>
    </div>
  );
};

export default HistoryPage;

