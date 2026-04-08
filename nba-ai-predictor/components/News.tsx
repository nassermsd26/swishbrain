import React, { useState, useEffect } from 'react';
import { Newspaper, ExternalLink, Calendar, TrendingUp, X } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { getRealNews } from '../services/mockApi';
import Standings from './Standings';
import RecentScores from './RecentScores';

interface NewsItem {
  id: string;
  title: string;
  description: string;
  source: string;
  url: string;
  publishedAt: string;
  category: string;
  fullContent?: string;
}

const News: React.FC = () => {
  const { theme } = useTheme();
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5002/api';
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedArticle, setSelectedArticle] = useState<NewsItem | null>(null);
  const [loadingContent, setLoadingContent] = useState(false);
  const [fullContent, setFullContent] = useState<string>('');

  useEffect(() => {
    const fetchNews = async () => {
      setLoading(true);
      try {
        const realNews = await getRealNews();
        if (realNews.length > 0) {
          setNews(realNews as NewsItem[]);
        } else {
          // Fallback si pas de news
          setNews([]);
        }
      } catch (error) {
        console.error("Error fetching news:", error);
        setNews([]);
      } finally {
        setLoading(false);
      }
    };

    fetchNews();
  }, []);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

    if (diffInHours < 1) return 'Il y a moins d\'une heure';
    if (diffInHours < 24) return `Il y a ${diffInHours} heure${diffInHours > 1 ? 's' : ''}`;
    return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' });
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      'Records': 'bg-purple-500/20 text-purple-300',
      'Team News': 'bg-blue-500/20 text-blue-300',
      'Injuries': 'bg-red-500/20 text-red-300',
      'Awards': 'bg-yellow-500/20 text-yellow-300',
      'Trades': 'bg-green-500/20 text-green-300',
      'Stats': 'bg-cyan-500/20 text-cyan-300'
    };
    return colors[category] || 'bg-gray-500/20 text-gray-300';
  };

  const handleReadMore = async (item: NewsItem) => {
    setSelectedArticle(item);
    setLoadingContent(true);
    setFullContent('');

    try {
      const response = await fetch(`${API_BASE}/news/content?url=${encodeURIComponent(item.url)}`);
      if (response.ok) {
        const data = await response.json();
        setFullContent(data.content || item.description);
      } else {
        setFullContent(item.description);
      }
    } catch (error) {
      console.error("Error fetching full content:", error);
      setFullContent(item.description);
    } finally {
      setLoadingContent(false);
    }
  };

  const closeModal = () => {
    setSelectedArticle(null);
    setFullContent('');
  };

  return (
    <div className="max-w-[1600px] mx-auto px-4 py-8 relative">
      <div className="flex gap-6">
        {/* Sidebar gauche - Derniers scores */}
        <aside className="hidden lg:block flex-shrink-0 sticky top-24 h-[calc(100vh-8rem)]">
          <RecentScores />
        </aside>

        {/* Contenu principal - Même largeur que prédictions */}
        <div className="flex-1 min-w-0 max-w-5xl">
          {/* Background gradient pour thème clair */}
          {theme === 'light' && (
            <div className="absolute inset-0 bg-gradient-to-br from-[#1D428A] via-[#C8102E] to-[#1D428A] opacity-90 -z-10"></div>
          )}
          <div className="mb-8 relative z-10">
            <div className="flex items-center gap-3 mb-4">
              <Newspaper className="w-8 h-8 text-gray-400" />
              <h1 className="text-4xl font-bold text-white">
                Dernières Infos NBA
              </h1>
            </div>
            <p className="text-lg text-gray-300">
              Restez à jour avec les dernières nouvelles, rumeurs et analyses de la NBA
            </p>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20 relative z-10">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
            </div>
          ) : (
            <div className="space-y-4 max-h-[calc(100vh-12rem)] overflow-y-auto pr-2 custom-scrollbar">
              {news.map((item) => (
                <article
                  key={item.id}
                  className={`border rounded-xl p-6 hover:border-[#C8102E] transition-all hover:shadow-lg hover:shadow-[#C8102E]/20 ${theme === 'dark'
                      ? 'bg-white/10 backdrop-blur-md border-white/20'
                      : 'bg-white border-gray-200'
                    }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${getCategoryColor(item.category)}`}>
                      {item.category}
                    </span>
                    <span className={`text-xs flex items-center gap-1 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                      }`}>
                      <Calendar className="w-3 h-3" />
                      {formatDate(item.publishedAt)}
                    </span>
                  </div>

                  <h2 className={`text-xl font-bold mb-3 ${theme === 'dark' ? 'text-white' : 'text-gray-900'
                    }`}>
                    {item.title}
                  </h2>

                  <p className={`text-sm mb-4 line-clamp-3 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                    }`}>
                    {item.description}
                  </p>

                  <div className={`flex items-center justify-between pt-4 border-t ${theme === 'dark' ? 'border-white/20' : 'border-gray-200'
                    }`}>
                    <span className={`text-xs font-medium ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                      }`}>
                      {item.source}
                    </span>
                    <button
                      onClick={() => handleReadMore(item)}
                      className="text-[#C8102E] hover:text-[#a00d25] text-sm font-medium flex items-center gap-1 transition-colors"
                    >
                      Lire plus
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}

          {news.length === 0 && !loading && (
            <div className="text-center py-20 relative z-10">
              <TrendingUp className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-300 text-lg">Aucune actualité disponible pour le moment</p>
            </div>
          )}
        </div>

        {/* Sidebar droite - Standings */}
        <aside className="hidden xl:block flex-shrink-0 sticky top-24 w-72">
          <Standings />
        </aside>
      </div>

      {/* Modal pour afficher le contenu complet */}
      {selectedArticle && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className={`relative max-w-4xl w-full max-h-[90vh] overflow-y-auto rounded-xl shadow-2xl ${theme === 'dark' ? 'bg-gray-900' : 'bg-white'
            }`}>
            {/* Header du modal */}
            <div className={`sticky top-0 z-10 p-6 border-b ${theme === 'dark' ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'
              }`}>
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${getCategoryColor(selectedArticle.category)}`}>
                      {selectedArticle.category}
                    </span>
                    <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'} flex items-center gap-1`}>
                      <Calendar className="w-3 h-3" />
                      {formatDate(selectedArticle.publishedAt)}
                    </span>
                  </div>
                  <h2 className={`text-2xl font-bold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                    {selectedArticle.title}
                  </h2>
                  <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                    Source: {selectedArticle.source}
                  </p>
                </div>
                <button
                  onClick={closeModal}
                  className={`p-2 rounded-lg transition-colors ${theme === 'dark'
                      ? 'hover:bg-gray-800 text-gray-400 hover:text-white'
                      : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
                    }`}
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            {/* Contenu du modal */}
            <div className="p-6">
              {loadingContent ? (
                <div className="flex items-center justify-center py-20">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#C8102E]"></div>
                </div>
              ) : (
                <div className={`prose prose-invert max-w-none ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                  }`}>
                  <p className="whitespace-pre-line leading-relaxed">
                    {fullContent || selectedArticle.description}
                  </p>
                </div>
              )}
            </div>

            {/* Footer du modal */}
            <div className={`sticky bottom-0 p-6 border-t ${theme === 'dark' ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'
              }`}>
              <a
                href={selectedArticle.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-[#C8102E] hover:bg-[#a00d25] text-white font-medium rounded-lg transition-colors"
              >
                Lire l'article complet
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default News;

