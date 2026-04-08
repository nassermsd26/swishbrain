import React, { useState, useEffect } from 'react';
import { Clock, Trophy } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { TEAMS } from '../constants';

interface RecentScore {
  id: string;
  homeTeam: string;
  awayTeam: string;
  homeScore: number;
  awayScore: number;
  date: string;
  dateFull?: string;
  winner: string;
}

const RecentScores: React.FC = () => {
  const { theme } = useTheme();
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5002/api';
  const [scores, setScores] = useState<RecentScore[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecentScores = async () => {
      try {
        // Vérifier le cache local d'abord
        const cachedScores = localStorage.getItem('recent_scores_cache');
        const cacheTimestamp = localStorage.getItem('recent_scores_cache_timestamp');

        if (cachedScores && cacheTimestamp) {
          const cacheDate = new Date(cacheTimestamp);
          const now = new Date();
          const hoursDiff = (now.getTime() - cacheDate.getTime()) / (1000 * 60 * 60);

          // Si le cache a moins d'1 heure, l'utiliser
          if (hoursDiff < 1) {
            const parsedScores = JSON.parse(cachedScores);

            // Vérifier que les scores ne sont pas trop anciens
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const twoDaysAgo = new Date(today);
            twoDaysAgo.setDate(twoDaysAgo.getDate() - 2);

            // Filtrer les scores récents (aujourd'hui, hier et avant-hier)
            const recentScores = parsedScores.filter((score: RecentScore) => {
              if (score.dateFull) {
                const scoreDate = new Date(score.dateFull);
                scoreDate.setHours(0, 0, 0, 0);
                return scoreDate >= twoDaysAgo;
              }
              return true; // Si pas de dateFull, garder le score
            });

            if (recentScores.length > 0) {
              setScores(recentScores);
              setLoading(false);
              console.log("✅ Scores chargés depuis le cache local");
              return;
            }
          }
        }

        // Sinon, appeler l'API
        const response = await fetch(`${API_BASE}/recent-scores`);
        if (response.ok) {
          const data = await response.json();
          const fetchedScores = data.scores || [];
          setScores(fetchedScores);

          // Sauvegarder dans le cache local
          if (fetchedScores.length > 0) {
            localStorage.setItem('recent_scores_cache', JSON.stringify(fetchedScores));
            localStorage.setItem('recent_scores_cache_timestamp', new Date().toISOString());
          }
        } else {
          // Fallback avec des scores simulés
          setScores(generateMockScores());
        }
      } catch (error) {
        console.error("Error fetching recent scores:", error);
        // Essayer le cache en cas d'erreur
        const cachedScores = localStorage.getItem('recent_scores_cache');
        if (cachedScores) {
          setScores(JSON.parse(cachedScores));
        } else {
          setScores(generateMockScores());
        }
      } finally {
        setLoading(false);
      }
    };

    fetchRecentScores();
  }, []);

  const generateMockScores = (): RecentScore[] => {
    // Générer quelques scores récents simulés
    const teams = TEAMS.map(t => t.abbr);
    const mockScores: RecentScore[] = [];

    for (let i = 0; i < 5; i++) {
      const homeIdx = Math.floor(Math.random() * teams.length);
      const awayIdx = Math.floor(Math.random() * teams.length);
      if (homeIdx === awayIdx) continue;

      const homeScore = Math.floor(Math.random() * 30) + 95;
      const awayScore = Math.floor(Math.random() * 30) + 95;

      mockScores.push({
        id: `score-${i}`,
        homeTeam: teams[homeIdx],
        awayTeam: teams[awayIdx],
        homeScore,
        awayScore,
        date: new Date(Date.now() - i * 86400000).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }),
        winner: homeScore > awayScore ? teams[homeIdx] : teams[awayIdx]
      });
    }

    return mockScores;
  };

  // Helper to get team colors/logos (avec fallback pour abréviations alternatives)
  const getTeam = (abbr: string) => {
    const team = TEAMS.find(t => t.abbr === abbr);
    if (team) return team;
    // Fallback pour abréviations alternatives utilisées par l'API
    const abbrMap: Record<string, string> = {
      'NO': 'NOP',
      'PHO': 'PHX',
      'GS': 'GSW',      // Golden State Warriors
      'NY': 'NYK',      // New York Knicks
      'WSH': 'WAS',     // Washington Wizards
      'UTAH': 'UTA',    // Utah Jazz
      'SA': 'SAS',      // San Antonio Spurs
    };
    const normalizedAbbr = abbrMap[abbr] || abbr;
    return TEAMS.find(t => t.abbr === normalizedAbbr);
  };

  if (loading) {
    return (
      <div className={`w-80 p-4 ${theme === 'dark' ? 'bg-gray-900/50' : 'bg-white'} rounded-lg border ${theme === 'dark' ? 'border-gray-800' : 'border-gray-200'}`}>
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-300 rounded w-1/2"></div>
          <div className="h-16 bg-gray-300 rounded"></div>
          <div className="h-16 bg-gray-300 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`w-80 ${theme === 'dark' ? 'bg-gray-900/50' : 'bg-white'} rounded-lg border ${theme === 'dark' ? 'border-gray-800' : 'border-gray-200'} shadow-lg overflow-hidden`}>
      <div className={`p-4 border-b ${theme === 'dark' ? 'border-gray-800' : 'border-gray-200'}`}>
        <div className="flex items-center gap-2">
          <Trophy className={`w-5 h-5 ${theme === 'dark' ? 'text-[#C8102E]' : 'text-[#1D428A]'}`} />
          <h3 className={`font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            Derniers Scores
          </h3>
        </div>
      </div>

      <div className="p-4 max-h-[560px] overflow-y-auto">
        {scores.length === 0 ? (
          <p className={`text-sm text-center ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
            Aucun score récent disponible
          </p>
        ) : (
          <div className="space-y-3">
            {scores.map((score) => {
              const homeTeam = getTeam(score.homeTeam);
              const awayTeam = getTeam(score.awayTeam);
              const isHomeWinner = score.winner === score.homeTeam;

              return (
                <div
                  key={score.id}
                  className={`p-3 rounded-lg border transition-all ${theme === 'dark'
                      ? 'border-gray-800 hover:border-gray-700 bg-gray-950/50'
                      : 'border-gray-200 hover:border-gray-300 bg-gray-50'
                    }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'} flex items-center gap-1`}>
                      <Clock className="w-3 h-3" />
                      {score.date}
                    </span>
                  </div>

                  <div className="space-y-2">
                    {/* Away Team */}
                    <div className={`flex items-center justify-between p-2 rounded ${!isHomeWinner && score.winner === score.awayTeam
                        ? theme === 'dark' ? 'bg-green-900/30' : 'bg-green-50'
                        : ''
                      }`}>
                      <div className="flex items-center gap-2 flex-1">
                        {awayTeam?.logo ? (
                          <img src={awayTeam.logo} alt={score.awayTeam} className="w-6 h-6 object-contain" />
                        ) : (
                          <div className={`w-6 h-6 rounded-full ${theme === 'dark' ? 'bg-gray-700' : 'bg-gray-200'} flex items-center justify-center`}>
                            <span className="text-xs font-bold">{score.awayTeam}</span>
                          </div>
                        )}
                        <span className={`text-sm font-medium ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                          {score.awayTeam}
                        </span>
                      </div>
                      <span className={`text-sm font-bold ${!isHomeWinner && score.winner === score.awayTeam
                          ? theme === 'dark' ? 'text-green-400' : 'text-green-600'
                          : theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                        }`}>
                        {score.awayScore}
                      </span>
                    </div>

                    {/* Home Team */}
                    <div className={`flex items-center justify-between p-2 rounded ${isHomeWinner
                        ? theme === 'dark' ? 'bg-green-900/30' : 'bg-green-50'
                        : ''
                      }`}>
                      <div className="flex items-center gap-2 flex-1">
                        {homeTeam?.logo ? (
                          <img src={homeTeam.logo} alt={score.homeTeam} className="w-6 h-6 object-contain" />
                        ) : (
                          <div className={`w-6 h-6 rounded-full ${theme === 'dark' ? 'bg-gray-700' : 'bg-gray-200'} flex items-center justify-center`}>
                            <span className="text-xs font-bold">{score.homeTeam}</span>
                          </div>
                        )}
                        <span className={`text-sm font-medium ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                          {score.homeTeam}
                        </span>
                      </div>
                      <span className={`text-sm font-bold ${isHomeWinner
                          ? theme === 'dark' ? 'text-green-400' : 'text-green-600'
                          : theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                        }`}>
                        {score.homeScore}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default RecentScores;

