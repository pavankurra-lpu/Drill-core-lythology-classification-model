import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import chatApi from '../api/chat';
import GlassCard from '../components/ui/GlassCard';
import ChatWindow from '../components/chat/ChatWindow';
import { 
  MessageSquare, 
  Plus, 
  UploadCloud, 
  FileText, 
  Search, 
  BookOpen, 
  Database,
  Trash2,
  Brain
} from 'lucide-react';
import toast from 'react-hot-toast';

const ChatPage: React.FC = () => {
  const queryClient = useQueryClient();
  const location = useLocation();
  
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [ragFile, setRagFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);

  // 1. Fetch Sessions
  const { data: sessions, isLoading: sessionsLoading } = useQuery({
    queryKey: ['chat-sessions'],
    queryFn: () => chatApi.listSessions()
  });

  // 2. Fetch Active Session Messages
  const { data: messagesResponse, isLoading: messagesLoading } = useQuery({
    queryKey: ['chat-messages', activeSessionId],
    queryFn: () => chatApi.getSessionMessages(activeSessionId!),
    enabled: !!activeSessionId
  });

  const messages = messagesResponse || [];

  // 3. Create Session Mutation
  const createSessionMutation = useMutation({
    mutationFn: () => chatApi.createSession(),
    onSuccess: (newSession) => {
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] });
      setActiveSessionId(newSession.id.toString());
      toast.success('New session created.');
    }
  });

  // 4. Delete Session Mutation
  const deleteSessionMutation = useMutation({
    mutationFn: (id: string) => chatApi.deleteSession(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] });
      setActiveSessionId(null);
      toast.success('Session deleted.');
    }
  });

  // Initialize active session
  useEffect(() => {
    if (sessions && sessions.length > 0 && !activeSessionId) {
      setActiveSessionId(sessions[0].id.toString());
    }
  }, [sessions, activeSessionId]);

  // Handle passed in predictions for automatic explanation trigger
  useEffect(() => {
    if (location.state?.prediction && activeSessionId) {
      const pred = location.state.prediction;
      chatApi.sendMessage(
        activeSessionId, 
        `Explain this prediction: rock type is ${pred.rock_type}, lithology class is ${pred.lithology_class}, confidence is ${pred.confidence_score.toFixed(1)}%.`
      ).then(() => {
        queryClient.invalidateQueries({ queryKey: ['chat-messages', activeSessionId] });
      });
      // Clear location state so it doesn't fire repeatedly
      window.history.replaceState({}, document.title);
    }
  }, [location.state, activeSessionId]);

  // RAG Ingestion
  const handleUploadRAG = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ragFile) return;

    setUploading(true);
    const toastId = toast.loading('Reading and indexing PDF text into FAISS vector store...');
    try {
      await chatApi.uploadRAGReport(ragFile);
      toast.success('Geological report successfully indexed!', { id: toastId });
      setRagFile(null);
    } catch (err) {
      toast.error('Failed to index document.', { id: toastId });
    } finally {
      setUploading(false);
    }
  };

  // Semantic Search
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    try {
      const results = await chatApi.semanticSearch(searchQuery);
      setSearchResults(results);
      if (results.length === 0) {
        toast.error('No matching records found.');
      }
    } catch (err) {
      toast.error('Search query failed.');
    }
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-4 gap-6 h-[calc(100vh-140px)] overflow-hidden">
      
      {/* Session List Sidebar */}
      <GlassCard className="p-4 flex flex-col h-full overflow-hidden">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
            <MessageSquare className="h-4 w-4 text-indigo-400" />
            <span>AI Sessions</span>
          </h3>
          <button
            onClick={() => createSessionMutation.mutate()}
            className="p-1.5 rounded-lg bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-400 border border-indigo-500/20 active:scale-95 transition-all cursor-pointer"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
          {sessionsLoading ? (
            <div className="text-center text-xs text-slate-500 py-6">Loading sessions...</div>
          ) : !sessions || sessions.length === 0 ? (
            <div className="text-center text-xs text-slate-500 py-6">No sessions yet.</div>
          ) : (
            sessions.map((sess: any) => (
              <div
                key={sess.id}
                onClick={() => setActiveSessionId(sess.id.toString())}
                className={`group flex items-center justify-between p-3 rounded-xl cursor-pointer text-xs transition-colors ${
                  activeSessionId === sess.id.toString()
                    ? 'bg-slate-800 text-white font-medium border border-indigo-500/20'
                    : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-300'
                }`}
              >
                <div className="flex items-center gap-2.5 truncate">
                  <MessageSquare className="h-4 w-4 text-indigo-500" />
                  <span className="truncate">Session #{sess.id}</span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSessionMutation.mutate(sess.id.toString());
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition-opacity"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            ))
          )}
        </div>
      </GlassCard>

      {/* Main Chat Dialogue */}
      <GlassCard className="xl:col-span-2 flex flex-col h-full overflow-hidden">
        {activeSessionId ? (
          <ChatWindow 
            sessionId={activeSessionId} 
            initialMessages={messages} 
          />
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
            <Brain className="h-10 w-10 text-slate-600 mb-4 animate-pulse" />
            <h4 className="text-white font-bold text-sm">Geological dialogue node</h4>
            <p className="text-xs text-slate-400 mt-2 max-w-xs">
              Select an active AI session on the sidebar or compile a new connection node.
            </p>
          </div>
        )}
      </GlassCard>

      {/* RAG Knowledge Ingestion panel */}
      <div className="space-y-6 flex flex-col h-full overflow-hidden">
        
        {/* Document indexing */}
        <GlassCard className="p-4 bg-slate-900/20 flex flex-col">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <UploadCloud className="h-4 w-4 text-indigo-400" />
            <span>RAG Document Uploader</span>
          </h4>
          <form onSubmit={handleUploadRAG} className="space-y-3">
            <div className="border border-dashed border-slate-700 hover:border-indigo-500/40 rounded-xl p-4 text-center cursor-pointer transition-colors relative">
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setRagFile(e.target.files?.[0] || null)}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              <FileText className="h-6 w-6 text-slate-500 mx-auto mb-2" />
              <span className="text-[10px] text-slate-400 font-semibold block truncate">
                {ragFile ? ragFile.name : 'Upload geological PDF'}
              </span>
            </div>
            <button
              type="submit"
              disabled={uploading || !ragFile}
              className="w-full py-2.5 rounded-xl font-semibold text-xs text-indigo-400 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploading ? 'Indexing report...' : 'Index Report'}
            </button>
          </form>
        </GlassCard>

        {/* Semantic Search */}
        <GlassCard className="p-4 flex-1 flex flex-col overflow-hidden bg-slate-900/20">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Search className="h-4 w-4 text-indigo-400" />
            <span>Semantic Search</span>
          </h4>
          <form onSubmit={handleSearch} className="flex gap-2 mb-3">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="glass-input flex-1 px-3 py-2 rounded-xl text-[10px] placeholder:text-slate-500"
              placeholder="Query mineral structure, stratigraphy..."
            />
            <button
              type="submit"
              className="px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white cursor-pointer"
            >
              <Search className="h-3.5 w-3.5" />
            </button>
          </form>

          {/* Results list */}
          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {searchResults.map((res, i) => (
              <div 
                key={i} 
                className="p-2.5 rounded-xl bg-slate-950/40 border border-slate-800 text-[10px] space-y-1"
              >
                <div className="flex items-center justify-between text-indigo-400 font-bold">
                  <span>{res.metadata?.source_file || 'Ingested Document'}</span>
                  <span className="bg-indigo-500/10 px-1 rounded text-[8px]">
                    {Math.round(res.score * 100)}% Match
                  </span>
                </div>
                <p className="text-slate-400 leading-normal line-clamp-3 italic">"{res.text}"</p>
              </div>
            ))}
            {searchResults.length === 0 && (
              <div className="h-full flex items-center justify-center text-center text-slate-600 text-[10px]">
                No semantic matches requested.
              </div>
            )}
          </div>
        </GlassCard>

      </div>

    </div>
  );
};

export default ChatPage;
