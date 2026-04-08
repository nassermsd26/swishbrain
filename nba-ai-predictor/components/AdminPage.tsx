import React, { useEffect, useState } from 'react';
import {
  Shield, Users, Trash2, ChevronDown, ChevronUp,
  Calendar, Mail, BarChart3, Check, MessageSquare, Coins,
  Crown, Star, Zap, TrendingUp, UserCheck, Clock, Diamond,
  ShieldCheck, ShieldOff, RefreshCw, AlertCircle, BanknoteIcon,
  XCircle, PauseCircle
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import AdminUserChat from './AdminUserChat';

interface UserEntry {
  id: number;
  email: string;
  username: string;
  role: string;
  approved: number;
  subscription_tier: string;
  tokens?: number;
  diamonds?: number;
  created_at: string;
  prediction_count: number;
  history: any[];
  referred_by?: number | null;
}

interface WithdrawalEntry {
  id: number;
  user_id: number;
  username: string;
  email: string;
  diamonds: number;
  amount: number;
  crypto_addr: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5002/api';

const tierConfig: Record<string, { label: string; color: string; bg: string; icon: React.ReactNode }> = {
  basic:   { label: 'Basic',   color: 'text-gray-300',   bg: 'bg-gray-700/50 border-gray-600',      icon: <Star className="w-3 h-3" /> },
  premium: { label: 'Premium', color: 'text-blue-300',   bg: 'bg-blue-900/30 border-blue-600/50',   icon: <Zap className="w-3 h-3" /> },
  vip:     { label: 'VIP',     color: 'text-purple-300', bg: 'bg-purple-900/30 border-purple-600/50', icon: <Crown className="w-3 h-3" /> },
  free:    { label: 'Free',    color: 'text-slate-400',  bg: 'bg-slate-800/50 border-slate-700',    icon: null },
};

const AdminPage: React.FC = () => {
  const { token, isAdmin, user: currentUser } = useAuth();
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const [users, setUsers] = useState<UserEntry[]>([]);
  const [withdrawals, setWithdrawals] = useState<WithdrawalEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [withdrawalsLoading, setWithdrawalsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedUser, setExpandedUser] = useState<number | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);
  const [tokenAmounts, setTokenAmounts] = useState<Record<number, number>>({});
  const [roleLoading, setRoleLoading] = useState<number | null>(null);
  const [filterPending, setFilterPending] = useState(false);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/admin/users`, { headers: { 'Authorization': `Bearer ${token}` } });
      if (!res.ok) throw new Error((await res.json()).error || 'Erreur serveur');
      const data = await res.json();
      setUsers(data.users);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
    } finally { setLoading(false); }
  };

  const fetchWithdrawals = async () => {
    try {
      setWithdrawalsLoading(true);
      const res = await fetch(`${API_URL}/admin/withdrawals`, { headers: { 'Authorization': `Bearer ${token}` } });
      if (!res.ok) throw new Error((await res.json()).error || 'Erreur serveur');
      const data = await res.json();
      setWithdrawals(data.withdrawals);
    } catch (err) {
      console.error('Erreur withdrawals', err);
    } finally { setWithdrawalsLoading(false); }
  };

  useEffect(() => { 
    if (isAdmin && token) {
      fetchUsers();
      fetchWithdrawals();
    }
  }, [isAdmin, token]);

  const handleRefreshAll = () => {
    fetchUsers();
    fetchWithdrawals();
  };

  const handleDelete = async (userId: number) => {
    try {
      const res = await fetch(`${API_URL}/admin/users/${userId}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` } });
      if (!res.ok) throw new Error((await res.json()).error);
      setUsers(prev => prev.filter(u => u.id !== userId));
      setDeleteConfirm(null);
    } catch (err) { setError(err instanceof Error ? err.message : 'Erreur'); }
  };

  const handleApprove = async (userId: number) => {
    try {
      const res = await fetch(`${API_URL}/admin/users/${userId}/approve`, { method: 'PUT', headers: { 'Authorization': `Bearer ${token}` } });
      if (!res.ok) throw new Error((await res.json()).error);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, approved: 1 } : u));
    } catch (err) { setError(err instanceof Error ? err.message : 'Erreur'); }
  };

  const handleSuspend = async (userId: number) => {
    try {
      const res = await fetch(`${API_URL}/admin/users/${userId}/suspend`, { method: 'PUT', headers: { 'Authorization': `Bearer ${token}` } });
      if (!res.ok) throw new Error((await res.json()).error);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, approved: 0 } : u));
    } catch (err) { setError(err instanceof Error ? err.message : 'Erreur'); }
  };

  const handleSubscriptionChange = async (userId: number, tier: string) => {
    try {
      const res = await fetch(`${API_URL}/admin/users/${userId}/subscription`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier })
      });
      if (!res.ok) throw new Error((await res.json()).error);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, subscription_tier: tier } : u));
    } catch (err) { setError(err instanceof Error ? err.message : 'Erreur'); }
  };

  const handleAddTokens = async (userId: number, amount: number) => {
    try {
      const res = await fetch(`${API_URL}/admin/users/${userId}/tokens/add`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount })
      });
      if (!res.ok) throw new Error((await res.json()).error);
      const data = await res.json();
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, tokens: data.new_tokens } : u));
    } catch (err) { setError(err instanceof Error ? err.message : 'Erreur'); }
  };

  const handleToggleRole = async (userId: number, currentRole: string) => {
    const newRole = currentRole === 'admin' ? 'user' : 'admin';
    if (!window.confirm(`Êtes-vous sûr de vouloir ${newRole === 'admin' ? 'promouvoir cet utilisateur en admin' : 'rétrograder cet admin en utilisateur'} ?`)) return;
    try {
      setRoleLoading(userId);
      const res = await fetch(`${API_URL}/admin/users/${userId}/role`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: newRole })
      });
      if (!res.ok) throw new Error((await res.json()).error);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, role: newRole } : u));
    } catch (err) { setError(err instanceof Error ? err.message : 'Erreur'); }
    finally { setRoleLoading(null); }
  };

  const handleUpdateWithdrawalStatus = async (reqId: number, status: string) => {
    if (!window.confirm(`Confirmer le statut : ${status === 'approved' ? 'VALIDER' : 'REFUSER'} ?`)) return;
    try {
      const res = await fetch(`${API_URL}/admin/withdrawals/${reqId}/status`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });
      if (!res.ok) throw new Error((await res.json()).error);
      setWithdrawals(prev => prev.map(w => w.id === reqId ? { ...w, status: status as any } : w));
    } catch (err) { setError(err instanceof Error ? err.message : 'Erreur'); }
  };

  if (!isAdmin) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className={`text-center p-10 rounded-2xl border ${isDark ? 'bg-gray-900 border-red-500/20' : 'bg-white border-red-200'} shadow-xl`}>
        <Shield className="w-16 h-16 mx-auto mb-4 text-red-500 opacity-60" />
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Accès refusé</h2>
        <p className={`mt-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>Réservé aux administrateurs.</p>
      </div>
    </div>
  );

  if (loading && users.length === 0) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="flex flex-col items-center gap-4">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-[#1D428A] border-t-[#C8102E]" />
        <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>Chargement...</p>
      </div>
    </div>
  );

  // ── Computed stats ──
  const pendingCount   = users.filter(u => u.approved === 0).length;
  const totalPredictions = users.reduce((s, u) => s + u.prediction_count, 0);
  const approvedCount  = users.filter(u => u.approved === 1 && u.role !== 'admin').length;
  const totalDiamonds  = users.reduce((s, u) => s + (u.diamonds ?? 0), 0);
  const totalReferrals = users.filter(u => u.referred_by != null && u.approved === 1).length;
  const pendingWithdrawalsCount = withdrawals.filter(w => w.status === 'pending').length;

  const statCards = [
    { label: 'Utilisateurs',  value: users.length,      icon: Users,      color: 'from-blue-500 to-blue-600',        glow: 'shadow-blue-500/20' },
    { label: 'En attente',    value: pendingCount,       icon: Clock,      color: 'from-amber-500 to-orange-500',     glow: 'shadow-amber-500/20',   pulse: pendingCount > 0 },
    { label: 'Approuvés',     value: approvedCount,      icon: UserCheck,  color: 'from-green-500 to-emerald-600',    glow: 'shadow-green-500/20' },
    { label: 'Retraits',      value: pendingWithdrawalsCount, icon: BanknoteIcon, color: 'from-emerald-400 to-teal-500', glow: 'shadow-emerald-500/20', pulse: pendingWithdrawalsCount > 0 },
    { label: 'Parrainages',   value: totalReferrals,     icon: Diamond,    color: 'from-amber-400 to-yellow-500',    glow: 'shadow-yellow-500/20' },
    { label: 'Diamonds total',value: totalDiamonds,      icon: Diamond,    color: 'from-cyan-400 to-teal-500',       glow: 'shadow-cyan-400/20' },
  ];

  const displayedUsers = filterPending ? users.filter(u => u.approved === 0) : users;

  return (
    <div className={`min-h-screen ${isDark ? 'bg-gray-950' : 'bg-gray-50'}`}>
      <div className="max-w-7xl mx-auto px-4 py-8">

        {/* ── Header ── */}
        <div className="flex items-center gap-4 mb-8">
          <div className="p-3.5 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 shadow-lg shadow-orange-500/30">
            <Shield className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className={`text-3xl font-black ${isDark ? 'text-white' : 'text-gray-900'}`}>Admin Dashboard</h1>
            <p className={`text-sm mt-0.5 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
              Gérez les utilisateurs, approuvez les comptes, validez les retraits crypto
            </p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            {pendingCount > 0 && (
              <button
                onClick={() => setFilterPending(f => !f)}
                className={`px-4 py-2 rounded-xl text-sm font-semibold transition-colors ${
                  filterPending
                    ? 'bg-amber-500 text-white'
                    : 'bg-amber-500/20 text-amber-400 border border-amber-500/30 hover:bg-amber-500/30'
                }`}
              >
                {filterPending ? 'Tous les utilisateurs' : `⏳ ${pendingCount} comptes en attente`}
              </button>
            )}
            <button
              onClick={handleRefreshAll}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-[#1D428A] text-white hover:bg-[#153265] transition-colors"
            >
              {(loading || withdrawalsLoading) ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              Actualiser
            </button>
          </div>
        </div>

        {/* ── Error ── */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300 underline text-sm">Fermer</button>
          </div>
        )}

        {/* ── Stats cards ── */}
        <div className="grid grid-cols-2 lg:grid-cols-6 gap-4 mb-8">
          {statCards.map(({ label, value, icon: Icon, color, glow, pulse }) => (
            <div
              key={label}
              className={`p-5 rounded-2xl border ${isDark ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'} shadow-sm relative overflow-hidden`}
            >
              {pulse && (
                <div className="absolute inset-0 animate-pulse bg-amber-500/5 rounded-2xl pointer-events-none" />
              )}
              <div className="flex items-start justify-between">
                <div>
                  <p className={`text-[10px] font-semibold uppercase tracking-wider mb-1 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{label}</p>
                  <p className={`text-3xl font-black ${isDark ? 'text-white' : 'text-gray-900'} ${pulse && value > 0 ? (label === 'Retraits' ? 'text-emerald-400' : 'text-amber-400') : ''}`}>{value}</p>
                </div>
                <div className={`p-2.5 rounded-xl bg-gradient-to-br ${color} shadow-lg ${glow}`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* ── Demandes de retrait ── */}
        <div className={`rounded-2xl border overflow-hidden mb-8 ${isDark ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'} shadow-sm`}>
          <div className={`px-6 py-4 border-b flex items-center justify-between ${isDark ? 'border-gray-800 bg-gray-900/80' : 'border-gray-200 bg-gray-50'}`}>
            <div className="flex items-center gap-2">
              <BanknoteIcon className={`w-5 h-5 ${isDark ? 'text-emerald-400' : 'text-emerald-500'}`} />
              <h2 className={`font-bold text-lg ${isDark ? 'text-white' : 'text-gray-900'}`}>
                Demandes de retrait ({withdrawals.length})
              </h2>
            </div>
            {pendingWithdrawalsCount > 0 && (
              <span className="px-3 py-1 text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-full animate-pulse">
                {pendingWithdrawalsCount} à traiter
              </span>
            )}
          </div>
          
          <div className={`divide-y max-h-96 overflow-y-auto ${isDark ? 'divide-gray-800' : 'divide-gray-100'}`}>
            {withdrawals.length === 0 ? (
              <div className={`py-12 text-center ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>
                <BanknoteIcon className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>Aucune demande de retrait.</p>
              </div>
            ) : (
              withdrawals.map(w => (
                <div key={w.id} className={`px-6 py-4 flex flex-col lg:flex-row lg:items-center justify-between gap-4 transition-colors ${
                  isDark ? 'hover:bg-gray-800/40' : 'hover:bg-gray-50'
                }`}>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1">
                      <span className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>{w.username}</span>
                      <span className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{w.email}</span>
                      {w.status === 'pending' ? (
                        <span className="px-2 py-0.5 text-[10px] font-bold uppercase bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-full animate-pulse">En attente</span>
                      ) : w.status === 'approved' ? (
                        <span className="px-2 py-0.5 text-[10px] font-bold uppercase bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-full">Validé</span>
                      ) : (
                        <span className="px-2 py-0.5 text-[10px] font-bold uppercase bg-red-500/20 text-red-400 border border-red-500/30 rounded-full">Refusé</span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-sm mt-2">
                       <span className="font-black text-emerald-500 bg-emerald-500/10 px-2 py-1 rounded border border-emerald-500/20">{w.amount}€</span>
                       <span className="font-bold text-amber-400 bg-amber-400/10 px-2 py-1 rounded border border-amber-400/20">{w.diamonds} 💎</span>
                    </div>
                    <div className={`mt-3 text-xs font-mono p-3 rounded-lg border flex items-center justify-between ${isDark ? 'bg-gray-950 border-gray-800 text-gray-300' : 'bg-gray-100 border-gray-200 text-gray-700'}`}>
                      <div>
                        <span className={isDark ? 'text-gray-500 font-sans' : 'text-gray-400 font-sans'}>Adresse Crypto : </span>
                        {w.crypto_addr}
                      </div>
                      <button 
                        onClick={() => {
                          navigator.clipboard.writeText(w.crypto_addr);
                          alert('Adresse copiée !');
                        }}
                        className={`px-2 py-1 rounded text-[10px] font-bold uppercase transition-colors ${
                          isDark ? 'bg-gray-800 text-gray-400 hover:text-white' : 'bg-gray-200 text-gray-500 hover:text-gray-900'
                        }`}
                      >
                        Copier
                      </button>
                    </div>
                    <div className={`mt-2 text-[10px] ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>
                      Date: {new Date(w.created_at).toLocaleString('fr-FR')}
                    </div>
                  </div>
                  
                  {w.status === 'pending' && (
                    <div className="flex items-center gap-2">
                      <button onClick={() => handleUpdateWithdrawalStatus(w.id, 'approved')} className="flex items-center gap-1 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-bold rounded-xl transition-all shadow-lg shadow-emerald-500/20 active:scale-95">
                        <Check className="w-4 h-4" /> Valider
                      </button>
                      <button onClick={() => handleUpdateWithdrawalStatus(w.id, 'rejected')} className="flex items-center gap-1 px-4 py-2 bg-red-500 hover:bg-red-600 text-white text-xs font-bold rounded-xl transition-all shadow-lg shadow-red-500/20 active:scale-95">
                        <Trash2 className="w-4 h-4" /> Refuser
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* ── Users table ── */}
        <div className={`rounded-2xl border overflow-hidden ${isDark ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'} shadow-sm`}>
          {/* Table header */}
          <div className={`px-6 py-4 border-b flex items-center justify-between ${isDark ? 'border-gray-800 bg-gray-900/80' : 'border-gray-200 bg-gray-50'}`}>
            <div className="flex items-center gap-2">
              <Users className={`w-5 h-5 ${isDark ? 'text-gray-400' : 'text-gray-500'}`} />
              <h2 className={`font-bold text-lg ${isDark ? 'text-white' : 'text-gray-900'}`}>
                {filterPending ? `En attente (${pendingCount})` : `Utilisateurs (${users.length})`}
              </h2>
            </div>
            {pendingCount > 0 && (
              <span className="px-3 py-1 text-xs font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-full animate-pulse">
                {pendingCount} en attente
              </span>
            )}
          </div>

          <div className={`divide-y ${isDark ? 'divide-gray-800' : 'divide-gray-100'}`}>
            {displayedUsers.map(user => {
              const tier = tierConfig[user.subscription_tier] || tierConfig.free;
              const isExpanded = expandedUser === user.id;
              const isSelf = currentUser?.id === user.id;

              return (
                <div key={user.id}>
                  {/* ── User row ── */}
                  <div
                    className={`px-6 py-4 flex items-center gap-4 cursor-pointer transition-colors ${
                      isDark
                        ? isExpanded ? 'bg-gray-800/60' : 'hover:bg-gray-800/40'
                        : isExpanded ? 'bg-blue-50/60' : 'hover:bg-gray-50'
                    }`}
                    onClick={() => setExpandedUser(isExpanded ? null : user.id)}
                  >
                    {/* Avatar */}
                    <div
                      className={`w-10 h-10 rounded-xl flex items-center justify-center font-black text-sm flex-shrink-0 ${
                        user.role === 'admin'
                          ? 'bg-gradient-to-br from-amber-500 to-orange-600 text-white shadow-lg shadow-orange-500/30'
                          : 'bg-gradient-to-br from-[#1D428A] to-[#153265] text-white'
                      }`}
                    >
                      {user.username.charAt(0).toUpperCase()}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`font-bold truncate ${isDark ? 'text-white' : 'text-gray-900'}`}>
                          {user.username}
                        </span>
                        {user.role === 'admin' ? (
                          <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-full">Admin</span>
                        ) : user.approved === 0 ? (
                          <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-full animate-pulse">En attente</span>
                        ) : (
                          <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-green-500/20 text-green-400 border border-green-500/30 rounded-full">Actif</span>
                        )}
                        {user.role !== 'admin' && (
                          <span className={`px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider border rounded-full flex items-center gap-1 ${tier.bg} ${tier.color}`}>
                            {tier.icon}{tier.label}
                          </span>
                        )}
                        {/* Diamonds badge */}
                        {(user.diamonds ?? 0) > 0 && (
                          <span className="px-2 py-0.5 text-[10px] font-bold bg-amber-400/20 text-amber-400 border border-amber-400/30 rounded-full flex items-center gap-1">
                            💎 {user.diamonds}
                          </span>
                        )}
                      </div>
                      <div className={`flex items-center gap-3 text-xs mt-0.5 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                        <span className="flex items-center gap-1"><Mail className="w-3 h-3" />{user.email}</span>
                        <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{new Date(user.created_at).toLocaleDateString('fr-FR')}</span>
                      </div>
                    </div>

                    {/* Stats + Actions */}
                    <div className="flex items-center gap-3 flex-shrink-0" onClick={e => e.stopPropagation()}>
                      {/* Prediction count */}
                      <div className="text-right hidden sm:block">
                        <div className={`text-sm font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>{user.prediction_count}</div>
                        <div className={`text-[10px] ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>prédictions</div>
                      </div>

                      {user.role !== 'admin' && (
                        <>
                          {/* Subscription select */}
                          <select
                            value={user.subscription_tier || 'basic'}
                            onChange={e => handleSubscriptionChange(user.id, e.target.value)}
                            className={`text-xs px-2 py-1.5 rounded-lg border focus:outline-none focus:ring-2 focus:ring-[#1D428A] ${
                              isDark ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-300 text-gray-900'
                            }`}
                          >
                            <option value="basic">Basic</option>
                            <option value="premium">Premium</option>
                            <option value="vip">VIP</option>
                          </select>

                          {/* Tokens */}
                          <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border ${isDark ? 'bg-yellow-500/10 border-yellow-500/20' : 'bg-yellow-50 border-yellow-200'}`}>
                            <Coins className="w-3.5 h-3.5 text-yellow-500" />
                            <span className={`text-xs font-bold ${isDark ? 'text-yellow-400' : 'text-yellow-600'}`}>{user.tokens ?? 0}</span>
                            <input
                              type="number"
                              min={1}
                              max={10000}
                              value={tokenAmounts[user.id] ?? 10}
                              onChange={e => setTokenAmounts(prev => ({ ...prev, [user.id]: Math.max(1, parseInt(e.target.value) || 1) }))}
                              className={`w-12 text-xs px-1.5 py-0.5 rounded border focus:outline-none ${
                                isDark ? 'bg-gray-900 border-gray-700 text-white' : 'bg-white border-gray-300'
                              }`}
                            />
                            <button
                              onClick={() => handleAddTokens(user.id, tokenAmounts[user.id] ?? 10)}
                              className="px-2 py-0.5 text-[10px] font-bold bg-yellow-500 hover:bg-yellow-600 text-white rounded-md transition-colors"
                            >
                              +Add
                            </button>
                          </div>

                          {/* Approve */}
                          {user.approved === 0 ? (
                            <button
                              onClick={() => handleApprove(user.id)}
                              className="flex items-center gap-1 px-3 py-1.5 bg-green-500 hover:bg-green-600 text-white text-xs font-bold rounded-lg transition-colors shadow-md shadow-green-500/20"
                            >
                              <Check className="w-3.5 h-3.5" />
                              Approuver
                            </button>
                          ) : (
                            <button
                              onClick={() => handleSuspend(user.id)}
                              className="flex items-center gap-1 px-2.5 py-1.5 text-[10px] font-bold rounded-lg transition-all bg-amber-500/20 text-amber-400 border border-amber-500/30 hover:bg-amber-500/40"
                              title="Remettre en attente"
                            >
                              <PauseCircle className="w-3 h-3" /> Remettre en attente
                            </button>
                          )}
                        </>
                      )}

                      {/* ── Toggle Admin role ── */}
                      {!isSelf && (
                        <button
                          onClick={() => handleToggleRole(user.id, user.role)}
                          disabled={roleLoading === user.id}
                          title={user.role === 'admin' ? 'Rétrograder en utilisateur' : 'Promouvoir en admin'}
                          className={`flex items-center gap-1 px-2.5 py-1.5 text-[10px] font-bold rounded-lg transition-all ${
                            user.role === 'admin'
                              ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30 hover:bg-orange-500/40'
                              : 'bg-blue-500/20 text-blue-400 border border-blue-500/30 hover:bg-blue-500/40'
                          } disabled:opacity-50`}
                        >
                          {roleLoading === user.id
                            ? <RefreshCw className="w-3 h-3 animate-spin" />
                            : user.role === 'admin'
                              ? <><ShieldOff className="w-3 h-3" /> Rétrograder</>
                              : <><ShieldCheck className="w-3 h-3" /> Passer Admin</>
                          }
                        </button>
                      )}

                      {/* Delete */}
                      {!isSelf && user.role !== 'admin' && (
                        deleteConfirm === user.id ? (
                          <div className="flex items-center gap-1">
                            <button onClick={() => handleDelete(user.id)} className="px-2.5 py-1.5 bg-red-500 hover:bg-red-600 text-white text-xs font-bold rounded-lg transition-colors">
                              Confirmer
                            </button>
                            <button onClick={() => setDeleteConfirm(null)} className={`px-2.5 py-1.5 text-xs font-bold rounded-lg transition-colors ${isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}>
                              Annuler
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setDeleteConfirm(user.id)}
                            className={`p-2 rounded-lg transition-colors ${isDark ? 'text-gray-600 hover:text-red-400 hover:bg-red-900/20' : 'text-gray-400 hover:text-red-500 hover:bg-red-50'}`}
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )
                      )}
                    </div>

                    {/* Expand arrow */}
                    <div className={`flex-shrink-0 ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </div>
                  </div>

                  {/* ── Expanded panel ── */}
                  {isExpanded && (
                    <div className={`px-6 py-5 ${isDark ? 'bg-gray-950/50 border-t border-gray-800' : 'bg-gray-50/80 border-t border-gray-100'}`}>
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

                        {/* Chat (only pending) */}
                        {user.approved === 0 && (
                          <div className={`rounded-xl overflow-hidden border ${isDark ? 'border-gray-800' : 'border-gray-200'}`}>
                            <div className={`flex items-center gap-2 px-4 py-2.5 ${isDark ? 'bg-gray-800 border-b border-gray-700' : 'bg-gray-100 border-b border-gray-200'}`}>
                              <MessageSquare className="w-4 h-4 text-[#1D428A]" />
                              <span className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-800'}`}>Chat avec l'utilisateur</span>
                            </div>
                            <AdminUserChat userId={user.id} />
                          </div>
                        )}

                        {/* Diamonds & Referral info */}
                        <div className={`rounded-xl border p-4 ${isDark ? 'border-amber-500/20 bg-amber-500/5' : 'border-amber-200 bg-amber-50'}`}>
                          <div className="flex items-center gap-2 mb-3">
                            <span className="text-lg">💎</span>
                            <span className={`text-sm font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Parrainage</span>
                          </div>
                          <div className="space-y-1 text-sm">
                            <div className="flex justify-between">
                              <span className={isDark ? 'text-gray-400' : 'text-gray-600'}>Diamonds gagnés</span>
                              <span className="font-bold text-amber-400">{user.diamonds ?? 0} 💎</span>
                            </div>
                            <div className="flex justify-between">
                              <span className={isDark ? 'text-gray-400' : 'text-gray-600'}>Parrainé par</span>
                              <span className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                {user.referred_by
                                  ? users.find(u => u.id === user.referred_by)?.username ?? `#${user.referred_by}`
                                  : '—'}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className={isDark ? 'text-gray-400' : 'text-gray-600'}>Filleuls approuvés</span>
                              <span className="font-bold text-green-400">
                                {users.filter(u => u.referred_by === user.id && u.approved === 1).length}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Prediction history */}
                        <div className={`rounded-xl border ${isDark ? 'border-gray-800 bg-gray-900' : 'border-gray-200 bg-white'} ${user.approved === 0 ? '' : 'lg:col-span-1'}`}>
                          <div className={`flex items-center gap-2 px-4 py-2.5 border-b ${isDark ? 'border-gray-800' : 'border-gray-200'}`}>
                            <BarChart3 className="w-4 h-4 text-[#1D428A]" />
                            <span className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-800'}`}>
                              Historique ({user.history.length} prédictions)
                            </span>
                          </div>

                          <div className="p-4">
                            {user.history.length === 0 ? (
                              <p className={`text-sm italic text-center py-4 ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>
                                Aucune prédiction pour cet utilisateur.
                              </p>
                            ) : (
                              <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                                {user.history.map((pred: any, idx: number) => (
                                  <div
                                    key={idx}
                                    className={`flex items-center justify-between p-3 rounded-xl text-sm ${
                                      isDark ? 'bg-gray-800 border border-gray-700' : 'bg-gray-50 border border-gray-200'
                                    }`}
                                  >
                                    <div className="flex items-center gap-3">
                                      {pred.teamA?.logo && <img src={pred.teamA.logo} alt="" className="w-6 h-6 object-contain" />}
                                      <span className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>{pred.teamA?.abbr || '??'}</span>
                                      <span className={`text-xs ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>vs</span>
                                      <span className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>{pred.teamB?.abbr || '??'}</span>
                                      {pred.teamB?.logo && <img src={pred.teamB.logo} alt="" className="w-6 h-6 object-contain" />}
                                    </div>
                                    <div className="flex items-center gap-3">
                                      <span className={`px-2 py-0.5 rounded-lg text-xs font-bold ${isDark ? 'bg-[#1D428A]/30 text-blue-300' : 'bg-blue-100 text-blue-700'}`}>
                                        {pred.winner || '??'}
                                      </span>
                                      {pred.confidence && (
                                        <span className={`text-xs font-semibold ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                          {(pred.confidence * 100).toFixed(0)}%
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {displayedUsers.length === 0 && (
              <div className={`py-16 text-center ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>
                <Users className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>{filterPending ? 'Aucun utilisateur en attente.' : 'Aucun utilisateur trouvé.'}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;
