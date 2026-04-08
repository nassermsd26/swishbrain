import React, { useState } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { Share2, Copy, CheckCircle2, Gift, Users, Trophy, Zap, BanknoteIcon, Loader2 } from 'lucide-react';

const MILESTONES = [
  { diamonds: 1, label: '1 Parrainage', reward: null, icon: '💎', color: 'from-blue-500 to-blue-700', glow: 'shadow-blue-500/40' },
  { diamonds: 2, label: '2 Parrainages', reward: null, icon: '💎💎', color: 'from-violet-500 to-violet-700', glow: 'shadow-violet-500/40' },
  { diamonds: 3, label: '3 Parrainages', reward: '20€', icon: '💎💎💎', color: 'from-amber-500 to-orange-600', glow: 'shadow-amber-500/50', highlight: true },
  { diamonds: 4, label: '4 Parrainages', reward: null, icon: '💎💎💎💎', color: 'from-pink-500 to-rose-600', glow: 'shadow-pink-500/40' },
  { diamonds: 5, label: '5 Parrainages', reward: '50€', icon: '💎💎💎💎💎', color: 'from-emerald-400 to-cyan-500', glow: 'shadow-emerald-400/50', highlight: true },
];

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5002/api';

const ParrainagePage: React.FC = () => {
  const { theme } = useTheme();
  const { user, token } = useAuth();
  const [copied, setCopied] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [cryptoAddr, setCryptoAddr] = useState('');
  const [withdrawLoading, setWithdrawLoading] = useState(false);
  const [withdrawDone, setWithdrawDone] = useState(false);
  const [withdrawError, setWithdrawError] = useState<string | null>(null);

  const displayCode = user?.referral_code || '------';
  const diamonds = user?.diamonds ?? 0;

  const handleCopy = () => {
    if (user?.referral_code) {
      navigator.clipboard.writeText(user.referral_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleWithdraw = async () => {
    if (!user || !token) return;
    if (!cryptoAddr.trim()) {
      setWithdrawError('Veuillez entrer votre adresse crypto.');
      return;
    }
    setWithdrawLoading(true);
    setWithdrawError(null);
    try {
      const res = await fetch(`${API_URL}/withdrawals`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ crypto_addr: cryptoAddr.trim() })
      });
      if (!res.ok) throw new Error((await res.json()).error || 'Erreur lors de l\'envoi');
      setWithdrawDone(true);
      setShowModal(false);
    } catch (e) {
      setWithdrawError(e instanceof Error ? e.message : 'Erreur inconnue');
    } finally {
      setWithdrawLoading(false);
    }
  };

  const progressPercent = Math.min((diamonds / 5) * 100, 100);
  const canWithdraw = diamonds >= 3;
  const withdrawAmount = diamonds >= 5 ? 50 : 20;

  return (
    <div className={`min-h-[calc(100vh-80px)] ${theme === 'dark' ? 'bg-gray-950 text-white' : 'bg-gray-50 text-gray-900'} py-12 px-4 transition-colors relative overflow-hidden`}>

      {/* ── Crypto Address Modal ── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className={`relative w-full max-w-md rounded-3xl shadow-2xl border p-8 ${
            theme === 'dark' ? 'bg-gray-900 border-gray-700' : 'bg-white border-gray-200'
          }`}>
            {/* Close */}
            <button
              onClick={() => { setShowModal(false); setWithdrawError(null); }}
              className="absolute top-4 right-4 text-gray-400 hover:text-white text-2xl leading-none"
            >×</button>

            {/* Header */}
            <div className="text-center mb-6">
              <div className="text-4xl mb-3">💸</div>
              <h2 className="text-2xl font-black text-emerald-400 mb-1">Demande de retrait</h2>
              <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                Montant : <span className="font-black text-white">{withdrawAmount}€</span> pour <span className="text-amber-400 font-bold">{diamonds} 💎</span>
              </p>
            </div>

            {/* Input crypto */}
            <div className="mb-6">
              <label className={`block text-xs font-bold uppercase tracking-wider mb-2 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                🔐 Adresse crypto (USDT / BTC / ETH…)
              </label>
              <input
                type="text"
                value={cryptoAddr}
                onChange={e => setCryptoAddr(e.target.value)}
                placeholder="0x... ou bc1... ou T..."
                className={`w-full px-4 py-3 rounded-xl border text-sm font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all ${
                  theme === 'dark'
                    ? 'bg-gray-800 border-gray-600 text-white placeholder-gray-500'
                    : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-400'
                }`}
              />
              <p className={`text-xs mt-1.5 ${theme === 'dark' ? 'text-gray-600' : 'text-gray-400'}`}>
                Vérifiez bien votre adresse avant de confirmer — aucun remboursement possible.
              </p>
            </div>

            {/* Error */}
            {withdrawError && (
              <div className="mb-4 px-4 py-2 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                {withdrawError}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={() => { setShowModal(false); setWithdrawError(null); }}
                className={`flex-1 py-3 rounded-xl font-bold text-sm transition-colors ${
                  theme === 'dark' ? 'bg-gray-800 text-gray-400 hover:bg-gray-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                Annuler
              </button>
              <button
                onClick={handleWithdraw}
                disabled={withdrawLoading || !cryptoAddr.trim()}
                className="flex-1 py-3 rounded-xl font-bold text-sm bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-white shadow-lg shadow-emerald-500/30 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {withdrawLoading
                  ? <><Loader2 className="w-4 h-4 animate-spin" /> Envoi...</>
                  : '✅ Confirmer le retrait'
                }
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Background decorations */}
      <div className="absolute top-0 left-0 w-full h-96 bg-gradient-to-br from-[#1D428A]/20 to-[#C8102E]/10 blur-3xl pointer-events-none opacity-60" />
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-gradient-to-tl from-amber-500/10 to-transparent blur-3xl pointer-events-none" />

      <div className="max-w-4xl mx-auto relative z-10">

        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center p-4 rounded-2xl bg-gradient-to-br from-[#1D428A] to-[#0A2351] shadow-xl mb-6 shadow-[#1D428A]/30">
            <Users className="w-12 h-12 text-blue-400" />
          </div>
          <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-4">
            Programme de{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-orange-500">
              Parrainage
            </span>
          </h1>
          <p className={`text-xl max-w-2xl mx-auto ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            Chaque ami parrainé = <span className="text-amber-400 font-bold">1 💎 Diamond</span>. Cumulez vos diamonds pour débloquer des récompenses en cash !
          </p>
        </div>

        {/* Rule Banner */}
        <div className={`flex items-center justify-center gap-6 mb-12 p-5 rounded-2xl border ${
          theme === 'dark' ? 'bg-amber-500/10 border-amber-500/30' : 'bg-amber-50 border-amber-200'
        }`}>
          <div className="flex items-center gap-3">
            <span className="text-3xl">💎</span>
            <div>
              <p className="font-black text-amber-400 text-lg">1 Parrainage</p>
              <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>= 1 Diamond</p>
            </div>
          </div>
          <div className={`w-px h-12 ${theme === 'dark' ? 'bg-gray-700' : 'bg-gray-300'}`} />
          <div className="flex items-center gap-3">
            <span className="text-3xl">🔄</span>
            <div>
              <p className="font-black text-emerald-400 text-lg">Cumulable</p>
              <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Pas de limite</p>
            </div>
          </div>
          <div className={`w-px h-12 ${theme === 'dark' ? 'bg-gray-700' : 'bg-gray-300'}`} />
          <div className="flex items-center gap-3">
            <span className="text-3xl">💶</span>
            <div>
              <p className="font-black text-blue-400 text-lg">Cash Rewards</p>
              <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Virement direct</p>
            </div>
          </div>
        </div>

        {/* ====== CHEMIN / MILESTONE PATH ====== */}
        <div className={`relative rounded-3xl p-8 mb-12 shadow-2xl border overflow-hidden ${
          theme === 'dark'
            ? 'bg-gradient-to-br from-gray-900 to-gray-800 border-gray-700/50'
            : 'bg-white border-gray-200'
        }`}>
          {/* Titre du chemin */}
          <div className="flex items-center gap-3 mb-8">
            <Trophy className="w-6 h-6 text-amber-400" />
            <h2 className="text-2xl font-black">Votre Chemin de Récompenses</h2>
          </div>

          {/* Progression actuelle */}
          <div className="mb-10">
            <div className="flex justify-between items-center mb-2">
              <span className={`text-sm font-bold ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                Vos diamonds actuels
              </span>
              <span className="text-amber-400 font-black text-lg">{diamonds} / 5 💎</span>
            </div>
            <div className={`h-3 rounded-full overflow-hidden ${theme === 'dark' ? 'bg-gray-700' : 'bg-gray-200'}`}>
              <div
                className="h-full rounded-full bg-gradient-to-r from-amber-400 to-orange-500 transition-all duration-700"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* Étapes du chemin */}
          <div className="relative">
            {/* Ligne connectrice */}
            <div className={`absolute top-10 left-10 right-10 h-1 rounded-full ${theme === 'dark' ? 'bg-gray-700' : 'bg-gray-200'} z-0`} />
            {/* Ligne de progression */}
            <div
              className="absolute top-10 left-10 h-1 rounded-full bg-gradient-to-r from-amber-400 to-orange-500 transition-all duration-700 z-0"
              style={{ width: `calc(${progressPercent}% * 0.8)` }}
            />

            <div className="relative z-10 flex justify-between items-start">
              {MILESTONES.map((milestone, idx) => {
                const isUnlocked = diamonds >= milestone.diamonds;
                const isCurrent = diamonds === milestone.diamonds;

                return (
                  <div key={idx} className="flex flex-col items-center gap-3" style={{ width: '18%' }}>
                    {/* Cercle du palier */}
                    <div className={`relative w-20 h-20 rounded-full flex items-center justify-center border-4 transition-all duration-500 ${
                      isUnlocked
                        ? `bg-gradient-to-br ${milestone.color} border-white/20 shadow-lg ${milestone.glow}`
                        : theme === 'dark'
                          ? 'bg-gray-800 border-gray-600'
                          : 'bg-gray-100 border-gray-300'
                    } ${isCurrent ? 'scale-110 ring-4 ring-amber-400/40' : ''}`}>
                      <span className={`text-2xl ${!isUnlocked ? 'opacity-30 grayscale' : ''}`}>
                        💎
                      </span>
                      {/* Badge diamant count */}
                      <div className={`absolute -top-2 -right-2 w-6 h-6 rounded-full flex items-center justify-center text-xs font-black ${
                        isUnlocked ? 'bg-amber-400 text-gray-900' : theme === 'dark' ? 'bg-gray-700 text-gray-400' : 'bg-gray-300 text-gray-600'
                      }`}>
                        {milestone.diamonds}
                      </div>
                    </div>

                    {/* Label */}
                    <div className="text-center">
                      <p className={`text-xs font-bold ${
                        isUnlocked
                          ? theme === 'dark' ? 'text-white' : 'text-gray-900'
                          : theme === 'dark' ? 'text-gray-500' : 'text-gray-400'
                      }`}>
                        {milestone.label}
                      </p>

                      {/* Récompense */}
                      {milestone.reward ? (
                        <div className={`mt-2 px-3 py-1 rounded-full text-sm font-black transition-all ${
                          isUnlocked
                            ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg shadow-emerald-500/30'
                            : theme === 'dark' ? 'bg-gray-700/50 text-gray-500 border border-gray-600' : 'bg-gray-100 text-gray-400 border border-gray-200'
                        }`}>
                          {isUnlocked ? '✅' : '🔒'} {milestone.reward}
                        </div>
                      ) : (
                        <div className={`mt-2 px-3 py-1 rounded-full text-xs font-bold ${
                          isUnlocked
                            ? 'text-amber-400'
                            : theme === 'dark' ? 'text-gray-600' : 'text-gray-300'
                        }`}>
                          {isUnlocked ? '+1 💎' : '···'}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Message palier suivant */}
          {diamonds < 5 && (
            <div className={`mt-8 p-4 rounded-xl border ${
              theme === 'dark' ? 'bg-blue-900/20 border-blue-500/30' : 'bg-blue-50 border-blue-200'
            }`}>
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-blue-400 flex-shrink-0" />
                <p className={`text-sm font-medium ${theme === 'dark' ? 'text-blue-300' : 'text-blue-700'}`}>
                  {diamonds < 3
                    ? `Encore ${3 - diamonds} parrainage(s) pour débloquer 20€ 💶`
                    : diamonds < 5
                      ? `Encore ${5 - diamonds} parrainage(s) pour débloquer 50€ 💶`
                      : '🎉 Félicitations ! Vous avez atteint le palier maximum !'
                  }
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Code de parrainage */}
        <div className={`relative rounded-3xl p-8 mb-12 shadow-2xl overflow-hidden border transition-all hover:scale-[1.01] duration-300 ${
          theme === 'dark'
            ? 'bg-gradient-to-br from-gray-900 to-gray-800 border-gray-700/50'
            : 'bg-white border-gray-200'
        }`}>
          <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-amber-400/10 to-transparent blur-2xl pointer-events-none rounded-full" />
          
          <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-8">
            <div className="flex-1 text-center md:text-left">
              <h2 className="text-2xl font-bold mb-2">Votre Code Unique</h2>
              <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>
                Partagez ce code avec vos amis. À chaque inscription avec votre code,{' '}
                <span className="text-amber-400 font-bold">vous gagnez 1 💎 diamond</span>.
              </p>
            </div>

            <div className="flex-shrink-0 flex flex-col items-center">
              <div className={`px-8 py-4 rounded-2xl text-4xl font-black mb-4 tracking-wider flex items-center justify-center min-w-[200px] border shadow-inner ${
                theme === 'dark' ? 'bg-gray-950/50 border-gray-700 text-amber-400' : 'bg-gray-50 border-gray-200 text-amber-600'
              }`}>
                {displayCode}
              </div>
              
              <button
                onClick={handleCopy}
                disabled={!user?.referral_code}
                className={`flex items-center gap-2 px-8 py-3 rounded-xl font-bold transition-all duration-300 transform active:scale-95 ${
                  copied
                    ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/30'
                    : 'bg-gradient-to-r from-[#1D428A] to-[#2B5DD1] text-white hover:shadow-lg hover:shadow-blue-500/30'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {copied ? (
                  <><CheckCircle2 className="w-5 h-5" /> Code Copié !</>
                ) : (
                  <><Copy className="w-5 h-5" /> Copier le Code</>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* How it works */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <div className={`p-6 rounded-2xl border transition-colors ${
            theme === 'dark' ? 'bg-gray-800/50 border-gray-700' : 'bg-white border-gray-100 shadow-xl shadow-gray-200/50'
          }`}>
            <div className="w-12 h-12 rounded-full bg-blue-500/20 text-blue-500 flex items-center justify-center mb-4">
              <Share2 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold mb-2">1. Partagez</h3>
            <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              Envoyez votre code unique à vos amis passionnés de NBA.
            </p>
          </div>

          <div className={`p-6 rounded-2xl border transition-colors ${
            theme === 'dark' ? 'bg-gray-800/50 border-gray-700' : 'bg-white border-gray-100 shadow-xl shadow-gray-200/50'
          }`}>
            <div className="w-12 h-12 rounded-full bg-amber-500/20 text-amber-500 flex items-center justify-center mb-4">
              <Users className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold mb-2">2. Inscription</h3>
            <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              Vos amis entrent votre code au moment de leur inscription sur SwishBrain.
            </p>
          </div>

          <div className={`p-6 rounded-2xl border transition-colors ${
            theme === 'dark' ? 'bg-gray-800/50 border-gray-700' : 'bg-white border-gray-100 shadow-xl shadow-gray-200/50'
          }`}>
            <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-500 flex items-center justify-center mb-4">
              <Gift className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold mb-2">3. Encaissez</h3>
            <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              Atteignez 3 💎 pour 20€ ou 5 💎 pour 50€. Récompenses cumulables !
            </p>
          </div>
        </div>

        {/* ── Withdrawal Request Block ── */}
        {canWithdraw ? (
          <div className={`mt-8 rounded-3xl p-8 border-2 relative overflow-hidden ${
            theme === 'dark'
              ? 'bg-gradient-to-br from-emerald-900/30 to-teal-900/20 border-emerald-500/40'
              : 'bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-300'
          }`}>
            {/* Glow */}
            <div className="absolute top-0 right-0 w-48 h-48 bg-emerald-400/10 blur-3xl pointer-events-none rounded-full" />
            <div className="relative z-10">
              <div className="flex flex-col md:flex-row items-center gap-6">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-3xl">💸</span>
                    <h2 className="text-2xl font-black text-emerald-400">Retrait disponible !</h2>
                  </div>
                  <p className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                    Vous avez <strong className="text-amber-400">{diamonds} 💎</strong> diamonds.
                    {diamonds >= 5
                      ? ' Vous pouvez retirer 50€ !'
                      : ' Vous pouvez retirer 20€ (ou attendez 5 💎 pour 50€).'}
                  </p>
                  <p className={`text-xs mt-1 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-500'}`}>
                    Un message sera automatiquement envoyé à l'administrateur pour traiter votre demande.
                  </p>
                </div>

                <div className="flex flex-col items-center gap-3">
                  {/* Amount badge */}
                  <div className={`px-6 py-3 rounded-2xl text-3xl font-black border ${
                    theme === 'dark' ? 'bg-emerald-900/30 border-emerald-500/40 text-emerald-400' : 'bg-emerald-100 border-emerald-300 text-emerald-700'
                  }`}>
                    {diamonds >= 5 ? '50€' : '20€'}
                  </div>

                  {withdrawDone ? (
                    <div className="flex items-center gap-2 px-6 py-3 bg-emerald-500 text-white rounded-xl font-bold text-sm">
                      <CheckCircle2 className="w-5 h-5" />
                      Demande envoyée !
                    </div>
                  ) : (
                    <button
                      onClick={() => setShowModal(true)}
                      className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/30 transition-all active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                      <BanknoteIcon className="w-5 h-5" /> Demander mon retrait
                    </button>
                  )}

                  {withdrawError && (
                    <p className="text-red-400 text-xs text-center">{withdrawError}</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Teaser when not enough diamonds */
          <div className={`mt-8 p-6 rounded-2xl border ${
            theme === 'dark' ? 'bg-gray-800/30 border-gray-700' : 'bg-gray-100 border-gray-200'
          } flex items-center gap-4`}>
            <span className="text-3xl opacity-40">💸</span>
            <div>
              <p className={`font-bold ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                Retrait disponible à partir de 3 💎
              </p>
              <p className={`text-sm ${theme === 'dark' ? 'text-gray-600' : 'text-gray-400'}`}>
                Il vous manque encore {3 - diamonds} parrainage{3 - diamonds > 1 ? 's' : ''} pour débloquer 20€.
              </p>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default ParrainagePage;
