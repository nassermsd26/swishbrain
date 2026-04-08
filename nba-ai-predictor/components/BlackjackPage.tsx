import React, { useState, useEffect } from 'react';
import { AlertCircle, Clock } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';

const BlackjackPage: React.FC = () => {
  const { theme } = useTheme();
  const { isAuthenticated, user, isAdmin } = useAuth();

  useEffect(() => {
    const iframe = document.getElementById('blackjack-iframe') as HTMLIFrameElement;
    if (iframe && iframe.contentWindow) {
      iframe.contentWindow.postMessage({ type: 'THEME_CHANGE', theme }, '*');
    }
  }, [theme]);

  if (!isAuthenticated || (!isAdmin && user?.subscription_tier !== 'premium' && user?.subscription_tier !== 'vip')) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${theme === 'dark' ? 'bg-gray-950' : 'bg-gray-50'}`}>
        <div className={`text-center p-8 rounded-lg ${theme === 'dark' ? 'bg-gray-900' : 'bg-white'} shadow-lg max-w-md mx-4`}>
          <AlertCircle className="w-16 h-16 mx-auto mb-4 text-[#C8102E]" />
          <h2 className={`text-2xl font-bold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            {!isAuthenticated ? "Connexion requise" : "Abonnement Requis"}
          </h2>
          <p className={`${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            {!isAuthenticated 
              ? "Vous devez être connecté pour jouer au Blackjack. Veuillez vous connecter pour continuer."
              : "Le Blackjack interactif est une fonctionnalité exclusive réservée aux membres Premium et VIP. Veuillez mettre à niveau votre abonnement."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-[calc(100vh-80px)] w-full`}>
      <iframe 
        id="blackjack-iframe"
        src="/blackjack/index.html" 
        className="w-full h-[calc(100vh-80px)] border-none"
        title="Blackjack Game"
        style={{ display: 'block' }}
        onLoad={(e) => {
          const iframe = e.target as HTMLIFrameElement;
          iframe.contentWindow?.postMessage({ type: 'THEME_CHANGE', theme }, '*');
        }}
      >
      </iframe>
    </div>
  );
};

export default BlackjackPage;
