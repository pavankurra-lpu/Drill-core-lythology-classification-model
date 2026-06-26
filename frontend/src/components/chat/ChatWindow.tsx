import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Database } from 'lucide-react';
import MessageBubble from './MessageBubble';
import chatApi from '../../api/chat';
import toast from 'react-hot-toast';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  sources?: any[];
}

interface ChatWindowProps {
  sessionId: string;
  initialMessages: any[];
}

const ChatWindow: React.FC<ChatWindowProps> = ({ sessionId, initialMessages }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Sync initial messages
  useEffect(() => {
    const formatted = initialMessages.map(msg => ({
      id: msg.id.toString(),
      sender: msg.role === 'user' ? 'user' as const : 'assistant' as const,
      content: msg.content,
      sources: msg.sources
    }));
    setMessages(formatted);
  }, [initialMessages]);

  // Scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || loading) return;

    const userText = inputValue;
    setInputValue('');
    setLoading(true);

    // Append user message immediately
    const userMsg: Message = {
      id: Date.now().toString(),
      sender: 'user',
      content: userText
    };
    setMessages(prev => [...prev, userMsg]);

    try {
      const response = await chatApi.sendMessage(sessionId, userText);
      
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        content: response.content,
        sources: response.sources
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: any) {
      toast.error('Failed to get response from AI assistant.');
      // Remove user message on failure to keep timeline correct
      setMessages(prev => prev.filter(m => m.id !== userMsg.id));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/10">
      {/* Scrollable conversation */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 max-h-[500px]">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-500 max-w-sm mx-auto">
            <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-full mb-3">
              <Database className="h-6 w-6" />
            </div>
            <h4 className="text-white font-bold text-xs">Stratigraphic AI Assistant</h4>
            <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
              Ask about minerals, formations, explain rock classification results, or query uploaded PDF geological reports.
            </p>
          </div>
        ) : (
          messages.map(msg => (
            <MessageBubble 
              key={msg.id} 
              sender={msg.sender} 
              content={msg.content} 
              sources={msg.sources}
            />
          ))
        )}
        
        {loading && (
          <div className="flex items-center gap-2 text-slate-400 text-xs pl-4 py-2">
            <Loader2 className="h-4 w-4 animate-spin text-indigo-400" />
            <span>Analyzing borehole context...</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input controls */}
      <form onSubmit={handleSend} className="p-4 border-t border-slate-800 bg-slate-950/20 flex gap-3">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          disabled={loading}
          className="glass-input flex-1 px-4 py-3 rounded-xl text-xs placeholder:text-slate-500"
          placeholder="Inquire about lithology makeup, stratigraphic horizons..."
        />
        <button
          type="submit"
          disabled={loading || !inputValue.trim()}
          className="p-3 rounded-xl bg-gradient-primary hover:opacity-95 text-white active:scale-95 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
};

export default ChatWindow;
