import React from 'react';
import { BarChart3, TrendingUp, Zap, Target, Users, Award, ArrowRight, Play, Newspaper, History, Gamepad2 } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';

interface HomePageProps {
  onNavigate: (page: 'predictions' | 'news' | 'history' | 'blackjack') => void;
  onOpenLogin?: (mode: 'login' | 'register') => void;
}

const HomePage: React.FC<HomePageProps> = ({ onNavigate, onOpenLogin }) => {
  const { theme } = useTheme();
  const { isAuthenticated } = useAuth();

  const features = [
    {
      icon: Zap,
      title: 'Prédictions IA',
      description: 'Analysez n\'importe quel match NBA avec notre moteur de prédiction IA avancé',
      color: 'from-yellow-400 to-orange-500',
      action: () => onNavigate('predictions')
    },
    {
      icon: TrendingUp,
      title: 'Statistiques en Temps Réel',
      description: 'Suivez les classements des équipes et des joueurs de la saison 2025-26',
      color: 'from-blue-400 to-cyan-500',
      action: () => onNavigate('predictions')
    },
    {
      icon: Newspaper,
      title: 'Actualités NBA',
      description: 'Restez informé des dernières nouvelles et transferts de la NBA',
      color: 'from-purple-400 to-pink-500',
      action: () => onNavigate('news')
    },
    {
      icon: History,
      title: 'Historique Personnel',
      description: 'Consultez toutes vos prédictions précédentes et suivez vos performances',
      color: 'from-green-400 to-emerald-500',
      action: () => onNavigate('history'),
      requiresAuth: true
    },
    {
      icon: Gamepad2,
      title: 'Petit Jeux 🎮',
      description: 'Testez vos connaissances NBA avec notre quiz interactif et jouez au Blackjack',
      color: 'from-pink-500 to-purple-600',
      action: () => onNavigate('blackjack')
    }
  ];

  const stats = [
    { label: 'Modèle IA', value: 'SwishAI v2', icon: Target },
    { label: 'Saison', value: '2025-26', icon: Award },
    { label: 'Utilisateurs', value: '+6000', icon: Users },
    { label: 'Précision', value: '85%+', icon: TrendingUp }
  ];

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-gray-950' : 'bg-gray-50'}`}>
      {/* Hero Section */}
      <div className={`relative overflow-hidden ${theme === 'dark' ? 'bg-gradient-to-br from-gray-900 via-gray-950 to-gray-900' : 'bg-gradient-to-br from-blue-50 via-white to-red-50'}`}>
        <div className="max-w-7xl mx-auto px-4 py-20 sm:py-24">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-6 bg-[#C8102E]/10 border border-[#C8102E]/20">
              <Zap className="w-4 h-4 text-[#C8102E]" />
              <span className={`text-sm font-semibold ${theme === 'dark' ? 'text-[#C8102E]' : 'text-[#C8102E]'}`}>
                Intelligence Artificielle NBA
              </span>
            </div>
            <h1 className={`text-5xl sm:text-6xl md:text-7xl font-extrabold mb-6 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
              Prédictions NBA
              <br />
              <span className="bg-gradient-to-r from-[#C8102E] to-[#1D428A] bg-clip-text text-transparent">
                Intelligentes
              </span>
            </h1>
            <p className={`text-xl sm:text-2xl mb-8 max-w-3xl mx-auto ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
              Analysez les matchs NBA avec l'intelligence artificielle. 
              Prédictions précises basées sur les statistiques, les blessures et les performances historiques.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => onNavigate('predictions')}
                className="group px-8 py-4 bg-gradient-to-r from-[#C8102E] to-[#1D428A] text-white rounded-xl font-semibold text-lg shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center gap-2 hover:scale-105"
              >
                <Play className="w-5 h-5" />
                Commencer une Prédiction
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
              {!isAuthenticated && (
                <button
                  onClick={() => onOpenLogin?.('register')}
                  className={`px-8 py-4 rounded-xl font-semibold text-lg border-2 transition-all duration-300 flex items-center justify-center gap-2 ${
                    theme === 'dark'
                      ? 'border-gray-700 text-gray-300 hover:bg-gray-800'
                      : 'border-gray-300 text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <Users className="w-5 h-5" />
                  Créer un Compte
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className={`py-12 ${theme === 'dark' ? 'bg-gray-900/50' : 'bg-white'}`}>
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <div
                  key={index}
                  className={`text-center p-6 rounded-xl ${theme === 'dark' ? 'bg-gray-800/50 border border-gray-700' : 'bg-gray-50 border border-gray-200'}`}
                >
                  <Icon className={`w-8 h-8 mx-auto mb-3 ${theme === 'dark' ? 'text-[#C8102E]' : 'text-[#1D428A]'}`} />
                  <div className={`text-2xl font-bold mb-1 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                    {stat.value}
                  </div>
                  <div className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                    {stat.label}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className={`text-4xl font-bold mb-4 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            Fonctionnalités
          </h2>
          <p className={`text-lg ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            Découvrez tout ce que notre plateforme peut faire pour vous
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => {
            if (feature.requiresAuth && !isAuthenticated) return null;
            const Icon = feature.icon;
            return (
              <div
                key={index}
                onClick={feature.action}
                className={`group cursor-pointer p-6 rounded-xl border transition-all duration-300 hover:scale-105 hover:shadow-xl ${
                  theme === 'dark'
                    ? 'bg-gray-900 border-gray-800 hover:border-gray-700'
                    : 'bg-white border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <h3 className={`text-xl font-bold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                  {feature.title}
                </h3>
                <p className={`text-sm mb-4 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                  {feature.description}
                </p>
                <div className={`flex items-center gap-2 text-sm font-semibold ${theme === 'dark' ? 'text-[#C8102E]' : 'text-[#1D428A]'}`}>
                  En savoir plus
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Pricing Section */}
      <div className={`py-16 ${theme === 'dark' ? 'bg-gray-900/50' : 'bg-white'}`}>
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className={`text-4xl font-bold mb-4 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
              Nos Abonnements
            </h2>
            <p className={`text-lg ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              Choisissez le forfait qui correspond à vos besoins
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Basic */}
            <div className={`rounded-2xl border-2 p-8 transition-transform hover:-translate-y-2 ${theme === 'dark' ? 'bg-gray-800 border-gray-600' : 'bg-gray-50 border-gray-300'}`}>
              <h3 className={`text-2xl font-bold mb-4 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>Basic</h3>
              <div className="mb-6">
                <span className={`text-4xl font-extrabold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>20€</span>
                <span className={`text-lg ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>/semaine</span>
              </div>
              <ul className={`space-y-4 mb-8 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                <li className="flex items-center gap-2"><ArrowRight className="w-4 h-4 text-gray-400" /> Prédictions limitées</li>
                <li className="flex items-center gap-2"><ArrowRight className="w-4 h-4 text-gray-400" /> Stats de base</li>
              </ul>
              <button 
                onClick={() => onOpenLogin?.('register')} 
                className={`w-full py-3 rounded-xl font-bold transition-colors ${theme === 'dark' ? 'bg-gray-700 hover:bg-gray-600 text-white' : 'bg-gray-200 hover:bg-gray-300 text-gray-900'}`}
              >
                Choisir Basic
              </button>
            </div>

            {/* Premium */}
            <div className={`transform scale-105 rounded-2xl border-2 p-8 transition-transform hover:-translate-y-2 shadow-xl ${theme === 'dark' ? 'bg-gray-900 border-blue-500 shadow-blue-900/20' : 'bg-white border-blue-500 shadow-blue-100'}`}>
              <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-bold uppercase tracking-wide">Populaire</div>
              <h3 className="text-2xl font-bold mb-4 text-blue-500">Premium</h3>
              <div className="mb-6">
                <span className={`text-4xl font-extrabold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>50€</span>
                <span className={`text-lg ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>/mois</span>
              </div>
              <ul className={`space-y-4 mb-8 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                <li className="flex items-center gap-2"><ArrowRight className="w-4 h-4 text-blue-500" /> Prédictions illimitées</li>
                <li className="flex items-center gap-2"><ArrowRight className="w-4 h-4 text-blue-500" /> Historique complet</li>
                <li className="flex items-center gap-2"><ArrowRight className="w-4 h-4 text-blue-500" /> Actus en temps réel</li>
              </ul>
              <button 
                onClick={() => onOpenLogin?.('register')} 
                className="w-full py-3 rounded-xl font-bold transition-colors bg-blue-500 hover:bg-blue-600 text-white shadow-lg"
              >
                Choisir Premium
              </button>
            </div>

            {/* VIP */}
            <div className={`rounded-2xl border-2 p-8 transition-transform hover:-translate-y-2 ${theme === 'dark' ? 'bg-purple-900/20 border-purple-500/50' : 'bg-purple-50 border-purple-200'}`}>
              <h3 className="text-2xl font-bold mb-4 text-purple-600 dark:text-purple-400">VIP</h3>
              <div className="mb-6">
                <span className={`text-4xl font-extrabold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>350€</span>
                <span className={`text-lg ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>/an</span>
              </div>
              <ul className={`space-y-4 mb-8 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                <li className="flex items-center gap-2"><ArrowRight className="w-4 h-4 text-purple-500" /> Tout de Premium</li>
                <li className="flex items-center gap-2"><ArrowRight className="w-4 h-4 text-purple-500" /> Analyse IA personnalisée</li>
                <li className="flex items-center gap-2"><ArrowRight className="w-4 h-4 text-purple-500" /> Support dédié 24/7</li>
              </ul>
              <button 
                onClick={() => onOpenLogin?.('register')} 
                className="w-full py-3 rounded-xl font-bold transition-colors bg-purple-600 hover:bg-purple-700 text-white shadow-lg shadow-purple-500/30"
              >
                Devenir VIP
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className={`py-16 ${theme === 'dark' ? 'bg-gray-900/30' : 'bg-gray-100'}`}>
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className={`text-4xl font-bold mb-4 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
              Comment ça fonctionne ?
            </h2>
            <p className={`text-lg ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              Trois étapes simples pour obtenir vos prédictions
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '1',
                title: 'Sélectionnez un Match',
                description: 'Choisissez deux équipes NBA que vous souhaitez analyser'
              },
              {
                step: '2',
                title: 'Analyse IA',
                description: 'Notre moteur IA analyse les statistiques, blessures et performances historiques'
              },
              {
                step: '3',
                title: 'Obtenez la Prédiction',
                description: 'Recevez une prédiction détaillée avec scores, confiance et analyse de paris'
              }
            ].map((item, index) => (
              <div
                key={index}
                className={`text-center p-8 rounded-xl ${theme === 'dark' ? 'bg-gray-800/50 border border-gray-700' : 'bg-white border border-gray-200'}`}
              >
                <div className={`w-16 h-16 rounded-full bg-gradient-to-br from-[#C8102E] to-[#1D428A] flex items-center justify-center mx-auto mb-4 text-white text-2xl font-bold`}>
                  {item.step}
                </div>
                <h3 className={`text-xl font-bold mb-3 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                  {item.title}
                </h3>
                <p className={`${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                  {item.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className={`py-16 ${theme === 'dark' ? 'bg-gradient-to-r from-gray-900 to-gray-800' : 'bg-gradient-to-r from-[#1D428A] to-[#C8102E]'}`}>
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className={`text-4xl font-bold mb-4 ${theme === 'dark' ? 'text-white' : 'text-white'}`}>
            Prêt à commencer ?
          </h2>
          <p className={`text-xl mb-8 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-100'}`}>
            Créez un compte gratuitement et commencez à analyser les matchs NBA dès maintenant
          </p>
          <button
            onClick={() => onNavigate('predictions')}
            className="px-8 py-4 bg-white text-[#1D428A] rounded-xl font-semibold text-lg shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 flex items-center gap-2 mx-auto"
          >
            <Play className="w-5 h-5" />
            Lancer une Prédiction
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default HomePage;

