import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { Send, Clock } from 'lucide-react';

interface Message {
  id: number;
  user_id: number;
  sender: 'user' | 'admin';
  content: string;
  created_at: string;
}

const PendingApprovalPage: React.FC = () => {
  const { user, token, logout } = useAuth();
  const { theme } = useTheme();
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5002/api';
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchMessages = async () => {
    if (!user || !token) return;
    try {
      const res = await fetch(`${API_BASE}/messages/${user.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchMessages();
    const interval = setInterval(fetchMessages, 5000);
    return () => clearInterval(interval);
  }, [user, token]);

  useEffect(() => {
    // Scroll the messages container instead of using scrollIntoView
    // which causes the entire window to shift downward.
    if (messagesEndRef.current) {
      const parent = messagesEndRef.current.parentElement;
      if (parent) {
        parent.scrollTo({
          top: parent.scrollHeight,
          behavior: 'smooth'
        });
      }
    }
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !user || !token || loading) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/messages/${user.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ content: newMessage })
      });

      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, data]);
        setNewMessage('');
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`flex flex-col h-[calc(100vh-8rem)] max-w-4xl mx-auto p-4`}>
      <div className={`text-center mb-8 p-8 rounded-2xl ${theme === 'dark' ? 'bg-gray-900 border border-gray-800' : 'bg-white border border-gray-200'}`}>
        <Clock className="w-16 h-16 mx-auto mb-4 text-[#1D428A]" />
        <h2 className={`text-3xl font-bold mb-4 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
          Compte en attente de validation
        </h2>
        <p className={`text-lg ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
          Bonjour {user?.username}, votre compte a bien été créé mais doit être validé par un administrateur avant de pouvoir accéder aux prédictions.
        </p>
        <p className={`mt-2 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
          Vous pouvez discuter avec l'administrateur ci-dessous si vous avez des questions ou pour accélérer votre validation.
        </p>
        <button onClick={logout} className="mt-6 text-sm underline text-red-500 hover:text-red-400">
          Se déconnecter
        </button>
      </div>

      <div className={`flex-1 flex flex-col rounded-2xl overflow-hidden shadow-xl ${theme === 'dark' ? 'bg-gray-900 border border-gray-800' : 'bg-white border border-gray-200'}`}>
        {/* En-tête du chat */}
        <div className="bg-[#1D428A] text-white p-4 font-bold flex items-center gap-2">
          Discussion avec l'Administration
        </div>

        {/* Historique des messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 mt-10 italic">
              Aucun message. Envoyez le premier message.
            </div>
          ) : (
            messages.map((msg) => {
              const isMine = msg.sender === 'user';
              return (
                <div key={msg.id} className={`flex flex-col ${isMine ? 'items-end' : 'items-start'}`}>
                  <div className={`max-w-[80%] px-4 py-2 rounded-2xl ${isMine ? 'bg-[#1D428A] text-white rounded-br-none' : theme === 'dark' ? 'bg-gray-800 text-gray-100 rounded-bl-none' : 'bg-gray-100 text-gray-900 rounded-bl-none'}`}>
                    <div className="text-xs opacity-50 mb-1 font-semibold">
                      {isMine ? 'Moi' : 'Admin'}
                    </div>
                    <div>{msg.content}</div>
                    <div className="text-[10px] opacity-40 mt-1 text-right">
                      {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                </div>
              );
            })
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Zone de saisie */}
        <form onSubmit={handleSendMessage} className={`p-4 border-t flex gap-2 ${theme === 'dark' ? 'border-gray-800 bg-gray-900' : 'border-gray-200 bg-white'}`}>
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Écrivez votre message à l'administrateur..."
            className={`flex-1 px-4 py-3 rounded-xl border focus:outline-none focus:ring-2 focus:ring-[#1D428A] ${theme === 'dark' ? 'bg-gray-800 border-gray-700 text-white placeholder-gray-500' : 'bg-gray-50 border-gray-200 text-gray-900'}`}
          />
          <button
            type="submit"
            disabled={!newMessage.trim() || loading}
            className="p-3 rounded-xl bg-[#1D428A] text-white hover:bg-[#153265] disabled:opacity-50 transition-colors"
          >
            <Send className="w-6 h-6" />
          </button>
        </form>
      </div>
    </div>
  );
};

export default PendingApprovalPage;
