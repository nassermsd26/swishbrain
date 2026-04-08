import React, { useState, useEffect, useMemo } from 'react';
import { Trophy, Users, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { TEAMS } from '../constants';

interface TeamStanding {
  rank: number;
  team: string;
  wins: number;
  losses: number;
  winPct: number;
  gamesBehind: number;
  streak: string;
  conference: string;
}

interface PlayerStanding {
  rank: number;
  name: string;
  team: string;
  points: number;
  rebounds: number;
  assists: number;
  position: string;
}

const Standings: React.FC = () => {
  const { theme } = useTheme();
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5002/api';
  const [view, setView] = useState<'teams' | 'players'>('teams');
  const [teamStandings, setTeamStandings] = useState<TeamStanding[]>([]);
  const [playerStandings, setPlayerStandings] = useState<PlayerStanding[]>([]);
  const [loading, setLoading] = useState(true);
  const [conference, setConference] = useState<'all' | 'east' | 'west'>('all');
  const [playerCategory, setPlayerCategory] = useState<'points' | 'rebounds' | 'assists'>('points');
  const [showAverages, setShowAverages] = useState<boolean>(true); // Toggle pour PPG/RPG/APG vs totaux

  useEffect(() => {
    const fetchStandings = async () => {
      setLoading(true);
      try {
        if (view === 'teams') {
          const response = await fetch(`${API_BASE}/standings/teams`);
          console.log('Standings fetch response status:', response.status);
          if (response.ok) {
            const data = await response.json();
            console.log('Standings data received:', data);
            console.log('Number of standings:', data.standings?.length || 0);
            if (data.standings && data.standings.length > 0) {
              console.log('First standing:', data.standings[0]);
              setTeamStandings(data.standings);
            } else {
              console.warn('No standings in response:', data);
              setTeamStandings([]);
            }
          } else {
            const errorText = await response.text();
            console.error('Failed to fetch standings:', response.status, response.statusText, errorText);
            setTeamStandings([]);
          }
        } else {
          const response = await fetch(`${API_BASE}/standings/players?category=${playerCategory}&averages=${showAverages}`);
          if (response.ok) {
            const data = await response.json();
            setPlayerStandings(data.standings || []);
          } else {
            console.error('Failed to fetch player standings:', response.status, response.statusText);
          }
        }
      } catch (error) {
        console.error("Error fetching standings:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchStandings();
  }, [view, playerCategory, showAverages]);

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

  // Filtrer et trier les standings
  const filteredTeamStandings = useMemo(() => {
    let filtered = conference === 'all'
      ? teamStandings
      : teamStandings.filter(s => s.conference && s.conference.toLowerCase() === conference);

    // Si "Tous", trier globalement par win percentage (puis wins) plutôt que par rang par conférence
    if (conference === 'all') {
      filtered = [...filtered].sort((a, b) => {
        // Trier par win percentage décroissant
        if (b.winPct !== a.winPct) {
          return b.winPct - a.winPct;
        }
        // Si égalité, trier par nombre de victoires
        if (b.wins !== a.wins) {
          return b.wins - a.wins;
        }
        // Si encore égalité, trier par nombre de défaites (moins de défaites = mieux)
        return a.losses - b.losses;
      });

      // Réassigner les rangs globaux après tri
      filtered = filtered.map((standing, index) => ({
        ...standing,
        rank: index + 1
      }));
    } else {
      // Pour Est/Ouest, garder le rang par conférence et trier par rang
      filtered = [...filtered].sort((a, b) => a.rank - b.rank);
    }

    return filtered;
  }, [teamStandings, conference]);

  // Debug log
  useEffect(() => {
    console.log('Team standings state:', teamStandings.length);
    console.log('Filtered standings:', filteredTeamStandings.length);
    console.log('Conference filter:', conference);
  }, [teamStandings, filteredTeamStandings, conference]);

  const getStreakIcon = (streak: string) => {
    if (streak.startsWith('W')) return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (streak.startsWith('L')) return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-gray-500" />;
  };

  return (
    <div className={`w-full ${theme === 'dark' ? 'bg-gray-900/50' : 'bg-white'} rounded-lg border ${theme === 'dark' ? 'border-gray-800' : 'border-gray-200'} shadow-lg h-[calc(100vh-6rem)] flex flex-col`}>
      {/* Header avec toggle */}
      <div className={`p-4 border-b ${theme === 'dark' ? 'border-gray-800' : 'border-gray-200'}`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Trophy className={`w-5 h-5 ${theme === 'dark' ? 'text-[#C8102E]' : 'text-[#1D428A]'}`} />
            <h3 className={`font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
              Classements
            </h3>
          </div>
        </div>

        {/* Toggle Teams/Players */}
        <div className="flex gap-2">
          <button
            onClick={() => setView('teams')}
            className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${view === 'teams'
                ? 'bg-[#1D428A] text-white'
                : theme === 'dark'
                  ? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
          >
            <Users className="w-4 h-4 inline mr-1" />
            Équipes
          </button>
          <button
            onClick={() => setView('players')}
            className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${view === 'players'
                ? 'bg-[#1D428A] text-white'
                : theme === 'dark'
                  ? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
          >
            <Trophy className="w-4 h-4 inline mr-1" />
            Joueurs
          </button>
        </div>

        {/* Filtre conférence pour les équipes */}
        {view === 'teams' && (
          <div className="flex gap-2 mt-3">
            <button
              onClick={() => setConference('all')}
              className={`flex-1 px-2 py-1 rounded text-xs font-medium transition-colors ${conference === 'all'
                  ? 'bg-[#C8102E] text-white'
                  : theme === 'dark'
                    ? 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
            >
              Tous
            </button>
            <button
              onClick={() => setConference('east')}
              className={`flex-1 px-2 py-1 rounded text-xs font-medium transition-colors ${conference === 'east'
                  ? 'bg-[#C8102E] text-white'
                  : theme === 'dark'
                    ? 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
            >
              Est
            </button>
            <button
              onClick={() => setConference('west')}
              className={`flex-1 px-2 py-1 rounded text-xs font-medium transition-colors ${conference === 'west'
                  ? 'bg-[#C8102E] text-white'
                  : theme === 'dark'
                    ? 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
            >
              Ouest
            </button>
          </div>
        )}

        {/* Filtre catégorie pour les joueurs */}
        {view === 'players' && (
          <div className="space-y-2 mt-3">
            <div className="flex gap-2">
              <button
                onClick={() => setPlayerCategory('points')}
                className={`flex-1 px-2 py-1 rounded text-xs font-medium transition-colors ${playerCategory === 'points'
                    ? 'bg-[#C8102E] text-white'
                    : theme === 'dark'
                      ? 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
              >
                Points
              </button>
              <button
                onClick={() => setPlayerCategory('rebounds')}
                className={`flex-1 px-2 py-1 rounded text-xs font-medium transition-colors ${playerCategory === 'rebounds'
                    ? 'bg-[#C8102E] text-white'
                    : theme === 'dark'
                      ? 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
              >
                Rebonds
              </button>
              <button
                onClick={() => setPlayerCategory('assists')}
                className={`flex-1 px-2 py-1 rounded text-xs font-medium transition-colors ${playerCategory === 'assists'
                    ? 'bg-[#C8102E] text-white'
                    : theme === 'dark'
                      ? 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
              >
                Passes
              </button>
            </div>
            {/* Toggle Totaux / Moyennes */}
            <div className="flex items-center justify-center gap-3 px-2 py-1.5 rounded-lg bg-gray-800/50 dark:bg-gray-700/50">
              <span className={`text-xs font-medium transition-colors ${!showAverages
                  ? theme === 'dark' ? 'text-white font-semibold' : 'text-gray-900 font-semibold'
                  : theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`}>
                Totaux
              </span>
              <button
                onClick={() => setShowAverages(!showAverages)}
                className={`relative w-14 h-7 rounded-full transition-all duration-300 ease-in-out shadow-inner ${showAverages
                    ? 'bg-[#C8102E]'
                    : theme === 'dark' ? 'bg-gray-600' : 'bg-gray-400'
                  }`}
                aria-label={showAverages ? 'Afficher les totaux' : 'Afficher les moyennes'}
              >
                <div
                  className={`absolute top-0.5 left-0.5 w-6 h-6 bg-white rounded-full shadow-lg transition-transform duration-300 ease-in-out flex items-center justify-center ${showAverages ? 'translate-x-7' : 'translate-x-0'
                    }`}
                >
                  <div className={`w-2 h-2 rounded-full transition-colors ${showAverages ? 'bg-[#C8102E]' : 'bg-gray-400'
                    }`} />
                </div>
              </button>
              <span className={`text-xs font-medium transition-colors ${showAverages
                  ? theme === 'dark' ? 'text-white font-semibold' : 'text-gray-900 font-semibold'
                  : theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`}>
                Moyennes
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Contenu */}
      <div className="p-4 flex-1 overflow-y-auto custom-scrollbar">
        {loading ? (
          <div className="flex items-center justify-center py-10">
            <div className={`animate-spin rounded-full h-8 w-8 border-b-2 ${theme === 'dark' ? 'border-[#C8102E]' : 'border-[#1D428A]'}`}></div>
          </div>
        ) : view === 'teams' ? (
          <div className="space-y-2">
            {loading ? (
              <p className={`text-sm text-center ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                Chargement...
              </p>
            ) : filteredTeamStandings.length === 0 ? (
              <p className={`text-sm text-center ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                Aucun classement disponible (Total: {teamStandings.length})
              </p>
            ) : (
              filteredTeamStandings.map((standing) => {
                const team = getTeam(standing.team);
                return (
                  <div
                    key={`${standing.team}-${standing.rank}`}
                    className={`p-2 rounded-lg border transition-all ${theme === 'dark'
                        ? 'border-gray-800 hover:border-gray-700 bg-gray-950/50'
                        : 'border-gray-200 hover:border-gray-300 bg-gray-50'
                      }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-bold w-6 text-center ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                        {standing.rank}
                      </span>
                      {team?.logo ? (
                        <img src={team.logo} alt={standing.team} className="w-6 h-6 object-contain" />
                      ) : (
                        <div className={`w-6 h-6 rounded-full ${theme === 'dark' ? 'bg-gray-700' : 'bg-gray-200'} flex items-center justify-center`}>
                          <span className="text-xs font-bold">{standing.team}</span>
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <div className={`text-sm font-medium truncate ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                          {standing.team}
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                          <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>
                            {standing.wins}-{standing.losses}
                          </span>
                          <span className={theme === 'dark' ? 'text-gray-500' : 'text-gray-500'}>
                            ({standing.winPct.toFixed(1)}%)
                          </span>
                          {standing.gamesBehind > 0 && (
                            <span className={theme === 'dark' ? 'text-gray-500' : 'text-gray-500'}>
                              -{standing.gamesBehind}GB
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        {getStreakIcon(standing.streak)}
                        <span className={`text-xs font-medium ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                          {standing.streak}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        ) : (
          <div className="space-y-2">
            {playerStandings.length === 0 ? (
              <p className={`text-sm text-center ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                Aucun classement disponible
              </p>
            ) : (
              playerStandings.map((player) => {
                const team = getTeam(player.team);
                return (
                  <div
                    key={`${player.name}-${player.rank}`}
                    className={`p-2 rounded-lg border transition-all ${theme === 'dark'
                        ? 'border-gray-800 hover:border-gray-700 bg-gray-950/50'
                        : 'border-gray-200 hover:border-gray-300 bg-gray-50'
                      }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-bold w-6 text-center ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                        {player.rank}
                      </span>
                      {team?.logo ? (
                        <img src={team.logo} alt={player.team} className="w-5 h-5 object-contain" />
                      ) : null}
                      <div className="flex-1 min-w-0">
                        <div className={`text-sm font-medium truncate ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                          {player.name}
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                          {/* Afficher la statistique sélectionnée en premier et en plus grand */}
                          {playerCategory === 'points' && (
                            <span className={`font-bold text-base ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                              {showAverages ? `${player.points.toFixed(1)} PPG` : `${player.points.toFixed(0)} PTS`}
                            </span>
                          )}
                          {playerCategory === 'rebounds' && (
                            <span className={`font-bold text-base ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                              {showAverages ? `${player.rebounds.toFixed(1)} RPG` : `${player.rebounds.toFixed(0)} REB`}
                            </span>
                          )}
                          {playerCategory === 'assists' && (
                            <span className={`font-bold text-base ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                              {showAverages ? `${player.assists.toFixed(1)} APG` : `${player.assists.toFixed(0)} AST`}
                            </span>
                          )}

                          {/* Afficher les autres stats en plus petit */}
                          {playerCategory !== 'points' && (
                            <span className={`${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                              {showAverages ? `${player.points.toFixed(1)} PPG` : `${player.points.toFixed(0)} PTS`}
                            </span>
                          )}
                          {playerCategory !== 'rebounds' && (
                            <span className={`${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                              {showAverages ? `${player.rebounds.toFixed(1)} RPG` : `${player.rebounds.toFixed(0)} REB`}
                            </span>
                          )}
                          {playerCategory !== 'assists' && (
                            <span className={`${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                              {showAverages ? `${player.assists.toFixed(1)} APG` : `${player.assists.toFixed(0)} AST`}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Standings;

