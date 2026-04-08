import React from 'react';
import { Activity, Github, Twitter, Mail } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const Footer: React.FC = () => {
  const { theme } = useTheme();

  return (
    <footer className={`mt-20 border-t ${
      theme === 'dark' 
        ? 'bg-gray-950 border-gray-800 text-gray-400' 
        : 'bg-white border-gray-200 text-gray-600'
    }`}>
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Logo et description */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <div className="bg-[#1D428A] p-1.5 rounded-lg">
                <Activity className="w-6 h-6 text-[#C8102E]" />
              </div>
              <h3 className={`text-xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                Swishbrain
              </h3>
            </div>
            <p className={`text-sm mb-4 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              Prédictions NBA basées sur l'intelligence artificielle. Analysez les matchs, 
              consultez les statistiques et obtenez des prédictions précises avec notre IA.
            </p>
            <div className="flex gap-4">
              <a href="#" className={`p-2 rounded-lg transition-colors ${
                theme === 'dark' 
                  ? 'hover:bg-gray-800 text-gray-400 hover:text-white' 
                  : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
              }`}>
                <Twitter className="w-5 h-5" />
              </a>
              <a href="#" className={`p-2 rounded-lg transition-colors ${
                theme === 'dark' 
                  ? 'hover:bg-gray-800 text-gray-400 hover:text-white' 
                  : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
              }`}>
                <Github className="w-5 h-5" />
              </a>
              <a href="#" className={`p-2 rounded-lg transition-colors ${
                theme === 'dark' 
                  ? 'hover:bg-gray-800 text-gray-400 hover:text-white' 
                  : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
              }`}>
                <Mail className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Liens rapides */}
          <div>
            <h4 className={`font-bold mb-4 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
              Liens Rapides
            </h4>
            <ul className="space-y-2">
              <li>
                <a href="#" className={`text-sm hover:text-[#C8102E] transition-colors ${
                  theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                }`}>
                  Prédictions
                </a>
              </li>
              <li>
                <a href="#" className={`text-sm hover:text-[#C8102E] transition-colors ${
                  theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                }`}>
                  Actualités
                </a>
              </li>
              <li>
                <a href="#" className={`text-sm hover:text-[#C8102E] transition-colors ${
                  theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                }`}>
                  Statistiques
                </a>
              </li>
            </ul>
          </div>

          {/* Informations */}
          <div>
            <h4 className={`font-bold mb-4 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
              Informations
            </h4>
            <ul className="space-y-2">
              <li>
                <a href="#" className={`text-sm hover:text-[#C8102E] transition-colors ${
                  theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                }`}>
                  À propos
                </a>
              </li>
              <li>
                <a href="#" className={`text-sm hover:text-[#C8102E] transition-colors ${
                  theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                }`}>
                  Confidentialité
                </a>
              </li>
              <li>
                <a href="#" className={`text-sm hover:text-[#C8102E] transition-colors ${
                  theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                }`}>
                  Conditions
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className={`mt-8 pt-8 border-t text-center text-sm ${
          theme === 'dark' 
            ? 'border-gray-800 text-gray-500' 
            : 'border-gray-200 text-gray-500'
        }`}>
          <p>© 2025 Swishbrain. Tous droits réservés.</p>
          <p className="mt-1">SwishAI v2 • Données NBA officielles</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;

