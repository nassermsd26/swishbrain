import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { Send, MessageSquare } from 'lucide-react';

interface AdminUserChatProps {
  userId: number;
}

interface Message {
  id: number;
  user_id: number;
  sender: 'user' | 'admin';
  content: string;
  created_at: string;
}

const AdminUserChat: React.FC<AdminUserChatProps> = ({ userId }) => {
  const { token } = useAuth();
  const { theme } = useTheme();
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5002/api';
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchMessages = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/messages/${userId}`, {
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
  }, [userId, token]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !token || loading) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/messages/${userId}`, {
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
    <div className={`mb-4 flex flex-col h-64 rounded-lg overflow-hidden border ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} shadow-sm`}>
      <div className={`p-2 border-b flex items-center gap-2 text-sm font-bold ${theme === 'dark' ? 'bg-gray-700 border-gray-600 text-white' : 'bg-gray-50 border-gray-200 text-gray-800'}`}>
        <MessageSquare className="w-4 h-4 text-[#1D428A]" />
        Discussion avec l'utilisateur
      </div>
      
      <div className="flex-1 p-3 overflow-y-auto space-y-3 bg-opacity-50">
        {messages.length === 0 ? (
          <div className="text-center text-xs opacity-50 mt-4 italic">Aucun message.</div>
        ) : (
          messages.map(msg => {
            const isMine = msg.sender === 'admin';
            return (
              <div key={msg.id} className={`flex flex-col ${isMine ? 'items-end' : 'items-start'}`}>
                <div className={`max-w-[85%] px-3 py-1.5 rounded-xl text-sm ${isMine ? 'bg-[#1D428A] text-white rounded-br-none' : theme === 'dark' ? 'bg-gray-600 text-white rounded-bl-none' : 'bg-gray-100 text-gray-900 rounded-bl-none'}`}>
                  <div className="text-[10px] opacity-60 mb-0.5">{isMine ? 'Moi (Admin)' : 'Utilisateur'}</div>
                  <div>{msg.content}</div>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSendMessage} className={`p-2 border-t flex gap-2 ${theme === 'dark' ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'}`}>
        <input 
          type="text" 
          value={newMessage}
          onChange={e => setNewMessage(e.target.value)}
          placeholder="Répondre..."
          className={`flex-1 text-sm px-3 py-1.5 rounded-lg border focus:outline-none focus:ring-1 focus:ring-[#1D428A] ${theme === 'dark' ? 'bg-gray-800 border-gray-600 text-white' : 'bg-white border-gray-300'}`}
        />
        <button 
          type="submit" 
          disabled={!newMessage.trim() || loading}
          className="p-1.5 rounded-lg bg-[#1D428A] text-white disabled:opacity-50 hover:bg-[#153265]"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};

export default AdminUserChat;
