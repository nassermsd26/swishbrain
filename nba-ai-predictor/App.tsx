import React, { useState } from 'react';
import Header from './components/Header';
import HomePage from './components/HomePage';
import GameSelector from './components/GameSelector';
import News from './components/News';
import PredictionPage from './components/PredictionPage';
import HistoryPage from './components/HistoryPage';
import ProfilePage from './components/ProfilePage';
import AdminPage from './components/AdminPage';
import Footer from './components/Footer';
import BasketballLoader from './components/BasketballLoader';
import RecentScores from './components/RecentScores';
import Standings from './components/Standings';
import LoginModal from './components/LoginModal';
import BlackjackPage from './components/BlackjackPage';
import PendingApprovalPage from './components/PendingApprovalPage';
import ParrainagePage from './components/ParrainagePage';
import { simulatePrediction } from './services/mockApi';
import { PredictionResult } from './types';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';

const AppContent: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<'home' | 'news' | 'history' | 'predictions' | 'prediction' | 'profile' | 'admin' | 'blackjack' | 'parrainage'>('home');
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loginModalOpen, setLoginModalOpen] = useState(false);
  const [loginModalMode, setLoginModalMode] = useState<'login' | 'register'>('login');
  const { theme } = useTheme();
  const { token, isAuthenticated, isAdmin, user, updateUser } = useAuth();

  const handlePrediction = async (teamA: string, teamB: string) => {
    // Vérifier si l'utilisateur est connecté
    if (!isAuthenticated || !token) {
      setError("Vous devez être connecté pour générer des prédictions. Veuillez vous connecter pour continuer.");
      return;
    }

    setLoading(true);
    setError(null);
    setPrediction(null);

    try {
      const result = await simulatePrediction(teamA, teamB, token);
      
      // Update tokens if they were returned and user is loaded
      if (result.tokens_remaining !== undefined && user) {
        updateUser({ ...user, tokens: result.tokens_remaining });
      }

      setPrediction(result);
      setCurrentPage('prediction');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to generate prediction. Please try again.";
      setError(errorMessage);
      console.error("Prediction error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setCurrentPage('predictions');
    setPrediction(null);
  };

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-gray-950' : 'bg-gray-50'} pb-20 transition-colors`}>
      <Header currentPage={currentPage === 'prediction' ? 'predictions' : currentPage} onNavigate={(page) => {
        if (page === 'predictions' && currentPage === 'prediction') {
          handleBack();
        } else {
          setCurrentPage(page);
        }
      }} />

      <main className="min-h-screen">
        {isAuthenticated && user && user.approved === 0 ? (
          <PendingApprovalPage />
        ) : currentPage === 'home' ? (
          <HomePage
            onNavigate={(page) => setCurrentPage(page)}
            onOpenLogin={(mode) => {
              setLoginModalMode(mode);
              setLoginModalOpen(true);
            }}
          />
        ) : currentPage === 'news' ? (
          <News />
        ) : currentPage === 'history' ? (
          <HistoryPage />
        ) : currentPage === 'profile' ? (
          <ProfilePage />
        ) : currentPage === 'blackjack' ? (
          <BlackjackPage />
        ) : currentPage === 'admin' && isAdmin ? (
          <AdminPage />
        ) : currentPage === 'parrainage' && user?.subscription_tier !== 'basic' ? (
          <ParrainagePage />
        ) : currentPage === 'prediction' && prediction ? (
          <PredictionPage prediction={prediction} onBack={handleBack} />
        ) : (
          <div className="flex gap-6 max-w-[1600px] mx-auto px-4 pt-8">
            {/* Sidebar gauche - Derniers scores avec animation */}
            <aside className="hidden lg:block flex-shrink-0 sticky top-24 h-[calc(100vh-8rem)]">
              <RecentScores />
            </aside>

            {/* Contenu principal - Agrandi */}
            <div className="flex-1 min-w-0 max-w-5xl">
              <div className="text-center mb-8">
                <h2 className={`text-4xl font-bold mb-3 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                  Match Analysis Engine
                </h2>
                <p className={`max-w-3xl mx-auto text-lg ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                  Sélectionnez un match pour lancer notre moteur de prédiction IA. Nous analysons la disponibilité des joueurs, les statistiques historiques et les confrontations directes.
                </p>
              </div>

              <div className="mb-8">
                <GameSelector onPredict={handlePrediction} loading={loading} />
              </div>

              {loading && <BasketballLoader />}

              {error && (
                <div className="fixed inset-0 flex items-center justify-center z-50 bg-black/50 backdrop-blur-sm">
                  <div className={`p-8 rounded-lg text-center max-w-md mx-4 shadow-2xl ${theme === 'dark'
                      ? 'bg-gray-900 border border-red-500/50 text-red-300'
                      : 'bg-white border border-red-200 text-red-600'
                    }`}>
                    <div className="mb-4">
                      <svg className="w-16 h-16 mx-auto text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                    </div>
                    <h3 className={`text-xl font-bold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                      {error.includes("jetons") ? "Abonnement Requis" : "Connexion requise"}
                    </h3>
                    <p className={`mb-6 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                      {error}
                    </p>
                    <button
                      onClick={() => {
                        setError(null);
                        if (error.includes("jetons")) {
                          setCurrentPage('home');
                        } else {
                          setLoginModalMode('login');
                          setLoginModalOpen(true);
                        }
                      }}
                      className="px-6 py-3 bg-[#C8102E] hover:bg-[#a00d25] text-white font-bold rounded-lg transition-colors"
                    >
                      {error.includes("jetons") ? "Voir les abonnements" : "Se connecter"}
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Sidebar droite - Standings */}
            <aside className="hidden xl:block flex-shrink-0 sticky top-24 h-[calc(100vh-8rem)]">
              <Standings />
            </aside>
          </div>
        )}
      </main>
      <Footer />

      {/* Login Modal */}
      <LoginModal
        isOpen={loginModalOpen}
        onClose={() => setLoginModalOpen(false)}
        initialMode={loginModalMode}
      />
    </div>
  );
};

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;