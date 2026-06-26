import React from 'react';
import { Database, FileText } from 'lucide-react';
import GlassCard from '../ui/GlassCard';

interface Source {
  source: string;
  snippet: string;
  score: number;
}

interface MessageBubbleProps {
  sender: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ sender, content, sources }) => {
  const isAssistant = sender === 'assistant';

  return (
    <div className={`flex w-full ${isAssistant ? 'justify-start' : 'justify-end'}`}>
      <div className={`max-w-[80%] flex flex-col gap-1.5`}>
        {/* Main message bubble */}
        <div 
          className={`px-4 py-3 rounded-2xl text-xs leading-relaxed ${
            isAssistant 
              ? 'glass-panel bg-slate-900/60 text-slate-100 border-l-4 border-l-indigo-500' 
              : 'bg-indigo-600 text-white rounded-br-none shadow-[0_4px_15px_-4px_rgba(99,102,241,0.4)]'
          }`}
        >
          {/* Format newlines as paragraphs */}
          {content.split('\n').map((para, i) => (
            <p key={i} className={para.trim() ? 'mb-2 last:mb-0' : ''}>
              {para}
            </p>
          ))}
        </div>

        {/* Source Citations */}
        {isAssistant && sources && sources.length > 0 && (
          <div className="pl-2 space-y-1.5">
            <span className="text-[9px] uppercase font-bold text-slate-500 tracking-wider flex items-center gap-1">
              <Database className="h-3 w-3 text-indigo-400" />
              <span>Referenced Sources ({sources.length})</span>
            </span>
            <div className="flex flex-wrap gap-2">
              {sources.map((src, i) => (
                <div 
                  key={i} 
                  title={src.snippet}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800/60 border border-slate-700/40 text-[9px] text-slate-400 hover:text-slate-200 transition-colors"
                >
                  <FileText className="h-3 w-3 text-indigo-400" />
                  <span className="truncate max-w-[120px] font-semibold">{src.source}</span>
                  <span className="text-[8px] px-1 rounded bg-indigo-500/10 text-indigo-400 font-bold border border-indigo-500/20">
                    {Math.round(src.score * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
