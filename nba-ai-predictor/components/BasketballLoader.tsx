import React from 'react';
import { useTheme } from '../contexts/ThemeContext';

const BasketballLoader: React.FC = () => {
  const { theme } = useTheme();

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="flex flex-col items-center justify-center">
      <div className="relative w-64 h-64 mb-8">
        {/* Panier de basket */}
        <div className="absolute top-0 left-1/2 transform -translate-x-1/2">
          <svg width="120" height="120" viewBox="0 0 120 120" className="text-[#C8102E]">
            {/* Panneau */}
            <rect x="40" y="0" width="40" height="30" fill="currentColor" rx="2" />
            {/* Filet */}
            <path
              d="M 45 30 Q 50 40 50 50 Q 50 60 45 70 Q 50 60 55 60 Q 50 50 55 50 Q 50 40 55 30"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
            <path
              d="M 55 30 Q 60 40 60 50 Q 60 60 55 70 Q 60 60 65 60 Q 60 50 65 50 Q 60 40 65 30"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
            <path
              d="M 65 30 Q 70 40 70 50 Q 70 60 65 70 Q 70 60 75 60 Q 70 50 75 50 Q 70 40 75 30"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
        </div>

        {/* Balle de basket animée */}
        <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 animate-bounce-basketball">
          <svg width="60" height="60" viewBox="0 0 60 60" className="text-[#FF8C00]">
            <circle cx="30" cy="30" r="28" fill="currentColor" />
            {/* Lignes de la balle */}
            <path
              d="M 30 2 Q 10 15 10 30 Q 10 45 30 58"
              fill="none"
              stroke="black"
              strokeWidth="1.5"
            />
            <path
              d="M 30 2 Q 50 15 50 30 Q 50 45 30 58"
              fill="none"
              stroke="black"
              strokeWidth="1.5"
            />
            <ellipse cx="30" cy="30" rx="25" ry="8" fill="none" stroke="black" strokeWidth="1.5" />
          </svg>
        </div>

        {/* Trajectoire (ligne pointillée) */}
        <svg className="absolute inset-0 w-full h-full" style={{ zIndex: -1 }}>
          <path
            d="M 60 240 Q 60 120 60 60"
            fill="none"
            stroke={theme === 'dark' ? 'rgba(200, 16, 46, 0.3)' : 'rgba(200, 16, 46, 0.2)'}
            strokeWidth="2"
            strokeDasharray="5,5"
          />
        </svg>
      </div>

      <p className={`font-medium text-lg mb-2 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
        Calcul en cours...
      </p>
        <p className={`text-sm ${theme === 'dark' ? 'text-gray-500' : 'text-gray-500'}`}>
          Analyse des données • Vérification des blessures • Génération de la prédiction
        </p>
      </div>
    </div>
  );
};

export default BasketballLoader;

