import React, { useState, useEffect } from 'react';
import { TEAMS, MOCK_SCHEDULE } from '../constants';
import { Calendar, Trophy, ChevronDown, RefreshCw } from 'lucide-react';
import { USE_REAL_BACKEND, getRealSchedule } from '../services/mockApi';
import { GameSchedule } from '../types';
import { useTheme } from '../contexts/ThemeContext';

interface Props {
  onPredict: (teamA: string, teamB: string) => void;
  loading: boolean;
}

const GameSelector: React.FC<Props> = ({ onPredict, loading }) => {
  const { theme } = useTheme();
  const [teamA, setTeamA] = useState<string>(TEAMS[0].abbr);
  const [teamB, setTeamB] = useState<string>(TEAMS[1].abbr);
  const [activeTab, setActiveTab] = useState<'custom' | 'schedule'>('schedule');
  const [schedule, setSchedule] = useState<GameSchedule[]>(MOCK_SCHEDULE);

  // Charger les matchs réels au montage du composant
  useEffect(() => {
    const loadSchedule = async () => {
      if (USE_REAL_BACKEND) {
        const realSchedule = await getRealSchedule();
        if (realSchedule.length > 0) {
          setSchedule(realSchedule);
        }
      }
    };
    loadSchedule();
  }, []);

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
  const tA = getTeam(teamA);
  const tB = getTeam(teamB);

  const handlePredict = () => {
    if (teamA === teamB) {
      alert("Please select two different teams.");
      return;
    }
    onPredict(teamA, teamB);
  };

  return (
    <div className={`rounded-xl shadow-2xl border-2 overflow-hidden mb-8 ${
      theme === 'dark' 
        ? 'bg-gray-900/80 border-gray-700' 
        : 'bg-white border-[#1D428A]'
    }`}>
      {/* Tabs */}
      <div className="flex border-b border-gray-100">
        <button
          onClick={() => setActiveTab('schedule')}
          className={`flex-1 flex items-center justify-center gap-2 py-4 text-sm font-bold tracking-wide transition-colors ${
            activeTab === 'schedule' 
              ? 'bg-[#1D428A] text-white' 
              : 'text-gray-500 hover:bg-gray-50'
          }`}
        >
          <Calendar className="w-4 h-4" />
          SCHEDULE
        </button>
        <button
          onClick={() => setActiveTab('custom')}
          className={`flex-1 flex items-center justify-center gap-2 py-4 text-sm font-bold tracking-wide transition-colors ${
            activeTab === 'custom' 
              ? 'bg-[#1D428A] text-white' 
              : 'text-gray-500 hover:bg-gray-50'
          }`}
        >
          <Trophy className="w-4 h-4" />
          CUSTOM MATCHUP
        </button>
      </div>

      <div className="p-6">
        {activeTab === 'schedule' ? (
          <div className="space-y-6">
            {/* Matchs d'aujourd'hui */}
            {schedule.filter(g => g.isToday).length > 0 && (
              <div>
                <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-3">Aujourd'hui</h3>
                <div className="max-h-72 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {schedule.filter(g => g.isToday).map((game) => (
              <button
                key={game.id}
                disabled={loading}
                onClick={() => onPredict(game.away, game.home)}
                className={`group relative border rounded-xl p-4 hover:border-[#1D428A] hover:shadow-lg transition-all text-left ${
                  theme === 'dark'
                    ? 'border-gray-800 bg-gradient-to-b from-gray-900/80 to-gray-950/80'
                    : 'border-gray-200 bg-gradient-to-b from-white to-gray-50'
                }`}
              >
                <div className="absolute top-3 right-3">
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin text-gray-400"/> : <span className="text-[#1D428A] opacity-0 group-hover:opacity-100 transition-opacity text-sm font-bold">ANALYZE &rarr;</span>}
                </div>
                <div className="mb-3">
                  <span className="text-[10px] font-bold text-white bg-[#C8102E] px-2 py-0.5 rounded uppercase tracking-wider">Live</span>
                  {game.time && game.time !== "" ? (
                    <span className="text-xs text-gray-400 ml-2 font-mono">{game.time} ET</span>
                  ) : (
                    <span className="text-xs text-gray-400 ml-2 font-mono">TBD</span>
                  )}
                </div>
                <div className="flex justify-between items-center">
                  <div className="flex flex-col items-center">
                    {(() => {
                      const team = getTeam(game.away);
                      return team?.logo ? (
                        <img 
                          src={team.logo} 
                          className="w-10 h-10 object-contain mb-1" 
                          alt={game.away}
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.style.display = 'none';
                            const fallback = target.nextElementSibling as HTMLElement;
                            if (fallback) fallback.style.display = 'flex';
                          }}
                        />
                      ) : null;
                    })()}
                    <div 
                      className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center mb-1"
                      style={{ display: getTeam(game.away)?.logo ? 'none' : 'flex' }}
                    >
                      <span className="text-xs font-bold text-gray-300">{game.away}</span>
                    </div>
                    <span className="font-bold text-white text-lg">{game.away}</span>
                  </div>
                  <span className="text-gray-300 font-light text-xl">@</span>
                  <div className="flex flex-col items-center">
                    {(() => {
                      const team = getTeam(game.home);
                      return team?.logo ? (
                        <img 
                          src={team.logo} 
                          className="w-10 h-10 object-contain mb-1" 
                          alt={game.home}
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.style.display = 'none';
                            const fallback = target.nextElementSibling as HTMLElement;
                            if (fallback) fallback.style.display = 'flex';
                          }}
                        />
                      ) : null;
                    })()}
                    <div 
                      className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center mb-1"
                      style={{ display: getTeam(game.home)?.logo ? 'none' : 'flex' }}
                    >
                      <span className="text-xs font-bold text-gray-300">{game.home}</span>
                    </div>
                    <span className="font-bold text-white text-lg">{game.home}</span>
                  </div>
                </div>
              </button>
                  ))}
                </div>
                </div>
              </div>
            )}
            
            {/* Matchs de demain */}
            {schedule.filter(g => !g.isToday).length > 0 && (
              <div>
                <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-3">Demain</h3>
                <div className="max-h-72 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {schedule.filter(g => !g.isToday).map((game) => (
                    <button
                      key={game.id}
                      disabled={loading}
                      onClick={() => onPredict(game.away, game.home)}
                      className={`group relative border rounded-xl p-4 hover:border-[#1D428A] hover:shadow-lg transition-all text-left ${
                  theme === 'dark'
                    ? 'border-gray-800 bg-gradient-to-b from-gray-900/80 to-gray-950/80'
                    : 'border-gray-200 bg-gradient-to-b from-white to-gray-50'
                }`}
                    >
                      <div className="absolute top-3 right-3">
                        {loading ? <RefreshCw className="w-4 h-4 animate-spin text-gray-400"/> : <span className="text-[#1D428A] opacity-0 group-hover:opacity-100 transition-opacity text-sm font-bold">ANALYZE &rarr;</span>}
                      </div>
                      <div className="mb-3">
                        <span className="text-[10px] font-bold text-white bg-blue-600 px-2 py-0.5 rounded uppercase tracking-wider">Tomorrow</span>
                        {game.time && game.time !== "" ? (
                          <span className="text-xs text-gray-400 ml-2 font-mono">{game.time} ET</span>
                        ) : (
                          <span className="text-xs text-gray-400 ml-2 font-mono">TBD</span>
                        )}
                      </div>
                      <div className="flex justify-between items-center">
                        <div className="flex flex-col items-center">
                          {(() => {
                            const team = getTeam(game.away);
                            return team?.logo ? (
                              <img 
                                src={team.logo} 
                                className="w-10 h-10 object-contain mb-1" 
                                alt={game.away}
                                onError={(e) => {
                                  const target = e.target as HTMLImageElement;
                                  target.style.display = 'none';
                                  const fallback = target.nextElementSibling as HTMLElement;
                                  if (fallback) fallback.style.display = 'flex';
                                }}
                              />
                            ) : null;
                          })()}
                          <div 
                            className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center mb-1"
                            style={{ display: getTeam(game.away)?.logo ? 'none' : 'flex' }}
                          >
                            <span className="text-xs font-bold text-gray-300">{game.away}</span>
                          </div>
                          <span className="font-bold text-white text-lg">{game.away}</span>
                        </div>
                        <span className="text-gray-300 font-light text-xl">@</span>
                        <div className="flex flex-col items-center">
                          {(() => {
                            const team = getTeam(game.home);
                            return team?.logo ? (
                              <img 
                                src={team.logo} 
                                className="w-10 h-10 object-contain mb-1" 
                                alt={game.home}
                                onError={(e) => {
                                  const target = e.target as HTMLImageElement;
                                  target.style.display = 'none';
                                  const fallback = target.nextElementSibling as HTMLElement;
                                  if (fallback) fallback.style.display = 'flex';
                                }}
                              />
                            ) : null;
                          })()}
                          <div 
                            className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center mb-1"
                            style={{ display: getTeam(game.home)?.logo ? 'none' : 'flex' }}
                          >
                            <span className="text-xs font-bold text-gray-300">{game.home}</span>
                          </div>
                          <span className="font-bold text-white text-lg">{game.home}</span>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
                </div>
              </div>
            )}
            
            {schedule.filter(g => g.isToday).length === 0 && schedule.filter(g => !g.isToday).length === 0 && (
              <p className="text-gray-500 text-center col-span-full">No games scheduled.</p>
            )}
          </div>
        ) : (
          <div className="flex flex-col md:flex-row items-center gap-6 md:gap-8">
            {/* Away Team Select */}
            <div className="flex-1 w-full group">
              <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Away Team</label>
              <div className="relative">
                <select 
                  value={teamA}
                  onChange={(e) => setTeamA(e.target.value)}
                  className="w-full pl-12 pr-10 py-4 appearance-none rounded-xl border border-gray-300 bg-white text-gray-800 font-bold focus:ring-2 focus:ring-[#1D428A] focus:border-transparent outline-none cursor-pointer hover:border-gray-400 transition-colors"
                >
                  {TEAMS.map(t => <option key={t.id} value={t.abbr}>{t.name}</option>)}
                </select>
                <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
                  {tA && <img src={tA.logo} className="w-6 h-6 object-contain" alt="" />}
                </div>
                <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400">
                  <ChevronDown className="w-5 h-5" />
                </div>
              </div>
            </div>

            <div className="flex flex-col items-center justify-center pt-6">
              <div className="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center text-gray-400 font-bold text-sm shadow-inner">
                VS
              </div>
            </div>

            {/* Home Team Select */}
            <div className="flex-1 w-full group">
              <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Home Team</label>
              <div className="relative">
                <select 
                  value={teamB}
                  onChange={(e) => setTeamB(e.target.value)}
                  className="w-full pl-12 pr-10 py-4 appearance-none rounded-xl border border-gray-300 bg-white text-gray-800 font-bold focus:ring-2 focus:ring-[#1D428A] focus:border-transparent outline-none cursor-pointer hover:border-gray-400 transition-colors"
                >
                  {TEAMS.map(t => <option key={t.id} value={t.abbr}>{t.name}</option>)}
                </select>
                <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
                  {tB && <img src={tB.logo} className="w-6 h-6 object-contain" alt="" />}
                </div>
                <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400">
                  <ChevronDown className="w-5 h-5" />
                </div>
              </div>
            </div>

            <div className="w-full md:w-auto pt-6">
              <button
                onClick={handlePredict}
                disabled={loading}
                className="w-full md:w-auto px-10 py-4 bg-[#C8102E] hover:bg-[#a00d25] text-white font-bold rounded-xl shadow-lg hover:shadow-xl transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 uppercase tracking-wide"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    Processing
                  </>
                ) : (
                  'Run Prediction'
                )}
              </button>
            </div>
          </div>
        )}
      </div>
      
      {/* Footer info */}
      <div className="bg-gray-950/50 px-6 py-3 border-t border-gray-800 flex justify-between items-center text-xs text-gray-500">
        <span>Engine: {USE_REAL_BACKEND ? 'Live Python API' : 'Simulation Mode'}</span>
        <span>SwishAI v2</span>
      </div>
    </div>
  );
};

export default GameSelector;