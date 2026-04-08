import React, { useState, useRef, useEffect } from 'react';
import {
  Menu, X, Newspaper, BarChart3, Sun, Moon, User, Shield, Users,
  LogOut, ChevronDown, LogIn, Zap, TrendingUp, History, Home, Gamepad2, Circle
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import LoginModal from './LoginModal';

interface HeaderProps {
  currentPage?: 'home' | 'news' | 'history' | 'predictions' | 'profile' | 'admin' | 'blackjack' | 'parrainage';
  onNavigate?: (page: 'home' | 'news' | 'history' | 'predictions' | 'profile' | 'admin' | 'blackjack' | 'parrainage') => void;
}

const Header: React.FC<HeaderProps> = ({ currentPage = 'home', onNavigate }) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [gamesMenuOpen, setGamesMenuOpen] = useState(false);
  const [balanceMenuOpen, setBalanceMenuOpen] = useState(false);
  const [loginModalOpen, setLoginModalOpen] = useState(false);
  const [loginModalMode, setLoginModalMode] = useState<'login' | 'register'>('login');
  const userMenuRef = useRef<HTMLDivElement>(null);
  const gamesMenuRef = useRef<HTMLDivElement>(null);
  const balanceMenuRef = useRef<HTMLDivElement>(null);
  const { theme, toggleTheme } = useTheme();
  const { user, isAuthenticated, isAdmin, logout } = useAuth();

  const [balanceDisplay, setBalanceDisplay] = useState<'both' | 'tokens' | 'diamonds'>(() => {
    if (typeof localStorage !== 'undefined') {
      return (localStorage.getItem('balanceDisplayPref') as any) || 'both';
    }
    return 'both';
  });

  const handleUpdateBalanceDisplay = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value as 'both' | 'tokens' | 'diamonds';
    setBalanceDisplay(val);
    localStorage.setItem('balanceDisplayPref', val);
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) setUserMenuOpen(false);
      if (gamesMenuRef.current && !gamesMenuRef.current.contains(event.target as Node)) setGamesMenuOpen(false);
      if (balanceMenuRef.current && !balanceMenuRef.current.contains(event.target as Node)) setBalanceMenuOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const navItems = [
    { id: 'home', label: 'Accueil', icon: Home, page: 'home' as const },
    { id: 'predictions', label: 'Prédictions', icon: BarChart3, page: 'predictions' as const },
    { id: 'news', label: 'Actualités', icon: Newspaper, page: 'news' as const },
    ...(isAuthenticated ? [{ id: 'history', label: 'Historique', icon: History, page: 'history' as const }] : []),
  ];

  const isGamesActive = currentPage === 'blackjack';

  return (
    <>
      <header className="bg-[#1D428A] text-white shadow-lg sticky top-0 z-50">
        {/* Subtle bottom shine */}
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />

        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between gap-4">

            {/* ── Logo ── */}
            <button onClick={() => onNavigate?.('home')} className="flex items-center gap-3 group flex-shrink-0">
              {/* Basketball icon */}
              <div className="relative">
                <div className="relative bg-gradient-to-br from-[#C8102E] to-[#1D428A] p-2.5 rounded-xl shadow-lg group-hover:scale-105 transition-transform duration-200">
                  <div className="relative w-8 h-8">
                    <Circle className="w-8 h-8 text-white" strokeWidth={2.5} />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-full h-0.5 bg-white/70" />
                    </div>
                    <div className="absolute inset-0 flex items-center justify-center rotate-90">
                      <div className="w-full h-0.5 bg-white/70" />
                    </div>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <Zap className="w-3.5 h-3.5 text-yellow-300" fill="currentColor" />
                    </div>
                  </div>
                </div>
              </div>
              {/* Brand */}
              <div className="flex flex-col leading-none">
                <h1 className="text-2xl font-black tracking-tight text-white">Swishbrain</h1>
                <div className="flex items-center gap-1 mt-0.5">
                  <TrendingUp className="w-2.5 h-2.5 text-[#C8102E]" />
                  <span className="text-[10px] text-gray-300 font-medium">Intelligence Artificielle</span>
                </div>
              </div>
            </button>

            {/* ── Desktop Nav ── */}
            <nav className="hidden md:flex items-center gap-0.5">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentPage === item.page;
                return (
                  <button
                    key={item.id}
                    onClick={() => onNavigate?.(item.page)}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                      isActive ? 'bg-[#C8102E] text-white shadow-md' : 'text-gray-200 hover:bg-white/10'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {item.label}
                  </button>
                );
              })}

              {/* 🎮 Petit Jeux dropdown */}
              <div className="relative" ref={gamesMenuRef}>
                <button
                  onClick={() => setGamesMenuOpen(!gamesMenuOpen)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150 ${
                    isGamesActive ? 'bg-[#C8102E] text-white shadow-md' : 'text-gray-200 hover:bg-white/10'
                  }`}
                >
                  <Gamepad2 className="w-4 h-4" />
                  Petit Jeux
                  <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${gamesMenuOpen ? 'rotate-180' : ''}`} />
                </button>

                {gamesMenuOpen && (
                  <div
                    className={`absolute top-full left-0 mt-2 w-44 rounded-xl overflow-hidden shadow-2xl border z-50 ${
                      theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
                    }`}
                  >
                    <div className="p-1">
                      <button
                        onClick={() => { onNavigate?.('blackjack'); setGamesMenuOpen(false); }}
                        className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-left ${
                          theme === 'dark' ? 'text-gray-200 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-100'
                        }`}
                      >
                        <span className="text-base">🃏</span> Blackjack
                      </button>
                      <div className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm opacity-40 cursor-not-allowed ${
                        theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                      }`}>
                        <span className="text-base">🏀</span>
                        <div>
                          <div>NBA Quiz</div>
                          <div className="text-[10px]">Bientôt...</div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </nav>

            {/* ── Right controls ── */}
            <div className="hidden md:flex items-center gap-2">
              {/* Season badge */}
              <div className="text-xs font-bold bg-[#C8102E] px-3 py-1.5 rounded-full whitespace-nowrap">
                2025–26
              </div>

              {/* Balance Dropdown */}
              {isAuthenticated && user && !isAdmin && (
                <div className="relative" ref={balanceMenuRef}>
                  <button
                    onClick={() => setBalanceMenuOpen(!balanceMenuOpen)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-gray-200 hover:bg-white/10 transition-colors border border-white/10 font-bold text-xs bg-black/20"
                  >
                    {(balanceDisplay === 'both' || balanceDisplay === 'tokens') && (
                      <span className="flex items-center gap-0.5 text-yellow-400"><Zap className="w-3 h-3" />{user.tokens ?? 0}</span>
                    )}
                    {balanceDisplay === 'both' && <span className="text-gray-400 mx-0.5">|</span>}
                    {(balanceDisplay === 'both' || balanceDisplay === 'diamonds') && (
                      <span className="flex items-center gap-0.5 text-blue-300">💎 {user.diamonds ?? 0}</span>
                    )}
                    <ChevronDown className={`w-3.5 h-3.5 ml-1 transition-transform duration-200 ${balanceMenuOpen ? 'rotate-180' : ''}`} />
                  </button>

                  {balanceMenuOpen && (
                    <div className={`absolute top-full right-0 mt-2 w-48 rounded-xl shadow-xl border overflow-hidden z-50 ${
                      theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
                    }`}>
                      <div className="p-1">
                        <button
                          onClick={() => { handleUpdateBalanceDisplay({target: {value: 'both'}} as any); setBalanceMenuOpen(false); }}
                          className={`w-full flex items-center gap-2 px-3 py-2 rounded-md text-xs font-semibold text-left transition-colors ${
                            balanceDisplay === 'both' ? 'bg-white/10' : 'hover:bg-white/5'
                          } ${theme === 'dark' ? 'text-gray-200' : 'text-gray-700'}`}
                        >
                          Tout afficher
                        </button>
                        <button
                          onClick={() => { handleUpdateBalanceDisplay({target: {value: 'tokens'}} as any); setBalanceMenuOpen(false); }}
                          className={`w-full flex items-center gap-2 px-3 py-2 rounded-md text-xs font-semibold text-left transition-colors ${
                            balanceDisplay === 'tokens' ? 'bg-white/10' : 'hover:bg-white/5'
                          } ${theme === 'dark' ? 'text-gray-200' : 'text-gray-700'}`}
                        >
                          Jetons uniquement
                        </button>
                        <button
                          onClick={() => { handleUpdateBalanceDisplay({target: {value: 'diamonds'}} as any); setBalanceMenuOpen(false); }}
                          className={`w-full flex items-center gap-2 px-3 py-2 rounded-md text-xs font-semibold text-left transition-colors ${
                            balanceDisplay === 'diamonds' ? 'bg-white/10' : 'hover:bg-white/5'
                          } ${theme === 'dark' ? 'text-gray-200' : 'text-gray-700'}`}
                        >
                          Diamonds uniquement
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Theme toggle */}
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg text-gray-200 hover:bg-white/20 hover:scale-110 transition-all duration-200"
                aria-label="Toggle theme"
              >
                {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>

              {/* User menu */}
              {isAuthenticated && user ? (
                <div className="relative" ref={userMenuRef}>
                  <button
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-gray-200 hover:bg-white/10 transition-colors border border-white/10"
                  >
                    <div className="w-7 h-7 rounded-lg bg-[#C8102E] flex items-center justify-center text-white font-bold text-xs">
                      {user.username.charAt(0).toUpperCase()}
                    </div>
                    <div className="hidden lg:flex flex-col items-start">
                      <span className="text-sm font-semibold text-white leading-none pb-0.5">{user.username}</span>
                    </div>
                    <ChevronDown className={`w-4 h-4 ml-1 transition-transform duration-200 ${userMenuOpen ? 'rotate-180' : ''}`} />
                  </button>

                  {userMenuOpen && (
                    <div className={`absolute right-0 mt-2 w-56 rounded-xl shadow-xl border overflow-hidden z-50 ${
                      theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
                    }`}>
                      <div className={`px-4 py-3 border-b ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}>
                        <p className={`text-sm font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>{user.username}</p>
                        <p className={`text-xs truncate ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>{user.email}</p>
                      </div>

                      <div className="p-1">
                        <button
                          onClick={() => { onNavigate?.('profile'); setUserMenuOpen(false); }}
                          className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-left transition-colors ${
                            theme === 'dark' ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-100'
                          }`}
                        >
                          <User className="w-4 h-4" /> Profil
                        </button>
                        {user.subscription_tier !== 'basic' && (
                          <button
                            onClick={() => { onNavigate?.('parrainage'); setUserMenuOpen(false); }}
                            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-left transition-colors ${
                              theme === 'dark' ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-100'
                            }`}
                          >
                            <Users className="w-4 h-4" /> Parrainage
                          </button>
                        )}
                        {isAdmin && (
                          <button
                            onClick={() => { onNavigate?.('admin'); setUserMenuOpen(false); }}
                            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-left transition-colors ${
                              theme === 'dark' ? 'text-amber-400 hover:bg-amber-900/20' : 'text-amber-600 hover:bg-amber-50'
                            }`}
                          >
                            <Shield className="w-4 h-4" /> Admin Dashboard
                          </button>
                        )}
                        <div className={`h-px my-1 ${theme === 'dark' ? 'bg-gray-700' : 'bg-gray-200'}`} />
                        <button
                          onClick={() => { logout(); setUserMenuOpen(false); }}
                          className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-left transition-colors ${
                            theme === 'dark' ? 'text-red-400 hover:bg-red-900/20' : 'text-red-600 hover:bg-red-50'
                          }`}
                        >
                          <LogOut className="w-4 h-4" /> Déconnexion
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <button
                  onClick={() => { setLoginModalMode('login'); setLoginModalOpen(true); }}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg text-gray-200 hover:bg-white/10 transition-colors text-sm font-medium"
                >
                  <LogIn className="w-4 h-4" />
                  <span className="hidden lg:block">Connexion</span>
                </button>
              )}
            </div>

            {/* ── Mobile controls ── */}
            <div className="md:hidden flex items-center gap-2">
              <button onClick={toggleTheme} className="p-2 hover:bg-white/20 hover:scale-110 rounded-lg transition-all duration-200">
                {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
              <button onClick={() => setMenuOpen(!menuOpen)} className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                {menuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>
        </div>

        {/* ── Mobile menu ── */}
        {menuOpen && (
          <nav className="md:hidden border-t border-white/20">
            <div className="px-4 py-3 flex flex-col gap-1">
              {navItems.map(item => {
                const Icon = item.icon;
                const isActive = currentPage === item.page;
                return (
                  <button
                    key={item.id}
                    onClick={() => { onNavigate?.(item.page); setMenuOpen(false); }}
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all text-left ${
                      isActive ? 'bg-[#C8102E] text-white' : 'text-gray-200 hover:bg-white/10'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="font-medium">{item.label}</span>
                  </button>
                );
              })}
              <button
                onClick={() => { onNavigate?.('blackjack'); setMenuOpen(false); }}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all text-left ${
                  isGamesActive ? 'bg-[#C8102E] text-white' : 'text-gray-200 hover:bg-white/10'
                }`}
              >
                <Gamepad2 className="w-5 h-5" />
                <span className="font-medium">Petit Jeux</span>
              </button>

              <div className="border-t border-white/20 my-2" />

              {isAuthenticated && user ? (
                <>
                  <div className="px-4 py-2">
                    <p className="text-sm font-semibold text-white">{user.username}</p>
                    <p className="text-xs text-gray-300">{user.email}</p>
                    
                    {!isAdmin && (
                      <div className="mt-2">
                        <select 
                          value={balanceDisplay}
                          onChange={(e) => handleUpdateBalanceDisplay(e)}
                          className="w-full text-xs bg-black/20 text-white rounded px-2 py-1 outline-none border border-white/10"
                        >
                          <option value="both">Solde complet</option>
                          <option value="tokens">Jetons uniquement</option>
                          <option value="diamonds">Diamonds uniquement</option>
                        </select>
                        <div className="text-xs font-bold flex items-center gap-1 mt-2">
                          {(balanceDisplay === 'both' || balanceDisplay === 'tokens') && (
                            <span className="flex items-center gap-0.5 text-yellow-400"><Zap className="w-3 h-3" />{user.tokens ?? 0}</span>
                          )}
                          {balanceDisplay === 'both' && <span className="text-gray-400">|</span>}
                          {(balanceDisplay === 'both' || balanceDisplay === 'diamonds') && (
                            <span className="flex items-center gap-0.5 text-blue-300">💎 {user.diamonds ?? 0}</span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                  <button onClick={() => { onNavigate?.('profile'); setMenuOpen(false); }} className="flex items-center gap-3 px-4 py-3 rounded-lg text-left text-gray-200 hover:bg-white/10 transition-colors">
                    <User className="w-5 h-5" /> <span className="font-medium">Profil</span>
                  </button>
                  {user.subscription_tier !== 'basic' && (
                    <button onClick={() => { onNavigate?.('parrainage'); setMenuOpen(false); }} className="flex items-center gap-3 px-4 py-3 rounded-lg text-left text-gray-200 hover:bg-white/10 transition-colors">
                      <Users className="w-5 h-5" /> <span className="font-medium">Parrainage</span>
                    </button>
                  )}
                  {isAdmin && (
                    <button onClick={() => { onNavigate?.('admin'); setMenuOpen(false); }} className="flex items-center gap-3 px-4 py-3 rounded-lg text-left text-amber-400 hover:bg-amber-500/20 transition-colors">
                      <Shield className="w-5 h-5" /> <span className="font-medium">Admin Dashboard</span>
                    </button>
                  )}
                  <button onClick={() => { logout(); setMenuOpen(false); }} className="flex items-center gap-3 px-4 py-3 rounded-lg text-left text-red-300 hover:bg-red-500/20 transition-colors">
                    <LogOut className="w-5 h-5" /> <span className="font-medium">Déconnexion</span>
                  </button>
                </>
              ) : (
                <button
                  onClick={() => { setLoginModalMode('login'); setLoginModalOpen(true); setMenuOpen(false); }}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg text-left text-gray-200 hover:bg-white/10 transition-colors"
                >
                  <LogIn className="w-5 h-5" /> <span className="font-medium">Connexion</span>
                </button>
              )}
            </div>
          </nav>
        )}
      </header>

      <LoginModal
        isOpen={loginModalOpen}
        onClose={() => setLoginModalOpen(false)}
        initialMode={loginModalMode}
      />
    </>
  );
};

export default Header;