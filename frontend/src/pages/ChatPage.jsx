import React, { useState, useEffect, useRef } from 'react';
import chatService from '../services/chatService';
import collectionService from '../services/collectionService';
import {
  MessageSquare,
  Plus,
  Send,
  Trash2,
  Edit2,
  FileText,
  Sparkles,
  Bot,
  User as UserIcon,
  Loader2,
  ExternalLink,
  X,
  ChevronRight,
  FolderKanban,
  Check
} from 'lucide-react';

export default function ChatPage() {
  const [conversations, setConversations] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(null);
  const [currentConv, setCurrentConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [collections, setCollections] = useState([]);
  const [selectedCollectionId, setSelectedCollectionId] = useState('');

  // Modals & Editing
  const [editingConvId, setEditingConvId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [activeCitation, setActiveCitation] = useState(null);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (currentConvId) {
      loadConversation(currentConvId);
    }
  }, [currentConvId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, sending]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [convsRes, colsRes] = await Promise.all([
        chatService.listConversations(),
        collectionService.listCollections(),
      ]);
      setConversations(convsRes.items || []);
      setCollections(colsRes.items || []);

      if (convsRes.items && convsRes.items.length > 0) {
        setCurrentConvId(convsRes.items[0].id);
      }
    } catch (err) {
      console.error('Failed to load chat data:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await chatService.getConversation(id);
      setCurrentConv(conv);
      setMessages(conv.messages || []);
    } catch (err) {
      console.error('Failed to load conversation:', err);
    }
  };

  const handleNewChat = async () => {
    try {
      const newConv = await chatService.createConversation({
        title: 'New Conversation',
        collection_id: selectedCollectionId || null,
      });
      setConversations((prev) => [newConv, ...prev]);
      setCurrentConvId(newConv.id);
      setMessages([]);
    } catch (err) {
      alert('Failed to create new conversation.');
    }
  };

  const handleSendMessage = async (e) => {
    e?.preventDefault();
    if (!inputMessage.trim() || sending) return;

    const userText = inputMessage.trim();
    setInputMessage('');

    let convId = currentConvId;
    if (!convId) {
      try {
        const newConv = await chatService.createConversation({
          title: userText.slice(0, 30),
          collection_id: selectedCollectionId || null,
        });
        setConversations((prev) => [newConv, ...prev]);
        convId = newConv.id;
        setCurrentConvId(newConv.id);
      } catch {
        alert('Could not start conversation.');
        return;
      }
    }

    // Optimistically append user message
    const tempUserMsg = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: userText,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setSending(true);

    try {
      const assistantMsg = await chatService.sendMessage(convId, userText);
      setMessages((prev) => [...prev, assistantMsg]);

      // Update conversation in list (title might have updated)
      const updatedConv = await chatService.getConversation(convId);
      setConversations((prev) =>
        prev.map((c) => (c.id === convId ? { ...c, title: updatedConv.title } : c))
      );
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to generate answer.');
    } finally {
      setSending(false);
    }
  };

  const handleDeleteConversation = async (e, convId) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this conversation?')) return;

    try {
      await chatService.deleteConversation(convId);
      const remaining = conversations.filter((c) => c.id !== convId);
      setConversations(remaining);
      if (currentConvId === convId) {
        if (remaining.length > 0) {
          setCurrentConvId(remaining[0].id);
        } else {
          setCurrentConvId(null);
          setCurrentConv(null);
          setMessages([]);
        }
      }
    } catch (err) {
      alert('Failed to delete conversation.');
    }
  };

  const handleSaveRename = async (convId) => {
    if (!editTitle.trim()) return;
    try {
      const updated = await chatService.updateConversation(convId, editTitle.trim());
      setConversations((prev) => prev.map((c) => (c.id === convId ? updated : c)));
      if (currentConv?.id === convId) {
        setCurrentConv(updated);
      }
      setEditingConvId(null);
    } catch (err) {
      alert('Failed to update title.');
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      {/* Left Chat Sidebar */}
      <aside className="w-80 bg-slate-900/80 border-r border-slate-800 flex flex-col shrink-0">
        <div className="p-4 border-b border-slate-800 space-y-3">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-sm font-semibold text-white shadow-lg shadow-sky-600/20 transition"
          >
            <Plus className="w-4 h-4" />
            New Document Chat
          </button>

          {/* Collection Filter */}
          <div className="flex items-center gap-2 px-2 py-1.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
            <FolderKanban className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <select
              value={selectedCollectionId}
              onChange={(e) => setSelectedCollectionId(e.target.value)}
              className="bg-transparent w-full text-slate-300 focus:outline-none text-xs"
            >
              <option value="" className="bg-slate-900">All Collections</option>
              {collections.map((col) => (
                <option key={col.id} value={col.id} className="bg-slate-900">
                  {col.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {loading ? (
            <div className="p-6 text-center text-slate-500 text-xs flex items-center justify-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-sky-500" />
              Loading conversations...
            </div>
          ) : conversations.length === 0 ? (
            <div className="p-6 text-center text-slate-500 text-xs">
              No conversations yet. Click "New Document Chat" to begin.
            </div>
          ) : (
            conversations.map((c) => {
              const isActive = c.id === currentConvId;
              const isEditing = editingConvId === c.id;

              return (
                <div
                  key={c.id}
                  onClick={() => !isEditing && setCurrentConvId(c.id)}
                  className={`group relative flex items-center justify-between p-3 rounded-xl text-xs font-medium cursor-pointer transition ${
                    isActive
                      ? 'bg-sky-500/15 text-white border border-sky-500/30'
                      : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0 pr-2">
                    <MessageSquare className={`w-4 h-4 shrink-0 ${isActive ? 'text-sky-400' : 'text-slate-500'}`} />
                    {isEditing ? (
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSaveRename(c.id)}
                        autoFocus
                        className="bg-slate-950 border border-slate-700 rounded px-1.5 py-0.5 text-xs text-white focus:outline-none w-36"
                      />
                    ) : (
                      <span className="truncate">{c.title}</span>
                    )}
                  </div>

                  <div className="flex items-center gap-1 shrink-0">
                    {isEditing ? (
                      <button
                        onClick={() => handleSaveRename(c.id)}
                        className="p-1 hover:text-emerald-400"
                      >
                        <Check className="w-3.5 h-3.5" />
                      </button>
                    ) : (
                      <>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingConvId(c.id);
                            setEditTitle(c.title);
                          }}
                          className="opacity-0 group-hover:opacity-100 p-1 hover:text-sky-400 transition"
                          title="Rename"
                        >
                          <Edit2 className="w-3 h-3" />
                        </button>
                        <button
                          onClick={(e) => handleDeleteConversation(e, c.id)}
                          className="opacity-0 group-hover:opacity-100 p-1 hover:text-rose-400 transition"
                          title="Delete"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </aside>

      {/* Main Chat Interface */}
      <main className="flex-1 flex flex-col h-full bg-slate-950 overflow-hidden relative">
        {/* Top Chat Header */}
        <header className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/50 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-sky-500/20 text-sky-400 flex items-center justify-center border border-sky-500/30">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white">
                {currentConv ? currentConv.title : 'Document Intelligence Chat'}
              </h2>
              <p className="text-[11px] text-slate-400">
                Grounded semantic question-answering with exact source citations
              </p>
            </div>
          </div>
        </header>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-4 text-slate-400">
              <div className="h-16 w-16 rounded-2xl bg-sky-500/10 text-sky-400 flex items-center justify-center border border-sky-500/20 shadow-xl shadow-sky-500/5">
                <Bot className="w-8 h-8" />
              </div>
              <div className="space-y-1">
                <h3 className="text-base font-semibold text-white">Ask your documents anything</h3>
                <p className="text-xs text-slate-400">
                  RAGForge retrieves relevant semantic chunks from your uploaded PDF, DOCX, and TXT files and answers with verified sources.
                </p>
              </div>
              <div className="grid grid-cols-1 gap-2 w-full pt-4 text-xs">
                <button
                  onClick={() => setInputMessage("Summarize the key objectives across my uploaded documents.")}
                  className="p-3 text-left rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition"
                >
                  &ldquo;Summarize the key objectives across my uploaded documents.&rdquo;
                </button>
                <button
                  onClick={() => setInputMessage("What are the primary financial figures or metrics reported?")}
                  className="p-3 text-left rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition"
                >
                  &ldquo;What are the primary financial figures or metrics reported?&rdquo;
                </button>
              </div>
            </div>
          ) : (
            messages.map((m) => {
              const isUser = m.role === 'user';
              return (
                <div
                  key={m.id}
                  className={`flex gap-3.5 max-w-3xl ${isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}
                >
                  {/* Avatar */}
                  <div
                    className={`h-8 w-8 rounded-xl flex items-center justify-center shrink-0 text-xs font-bold ${
                      isUser
                        ? 'bg-sky-600 text-white'
                        : 'bg-slate-800 border border-slate-700 text-sky-400'
                    }`}
                  >
                    {isUser ? <UserIcon className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>

                  {/* Bubble */}
                  <div className="space-y-2 max-w-2xl">
                    <div
                      className={`p-4 rounded-2xl text-sm leading-relaxed ${
                        isUser
                          ? 'bg-sky-600 text-white rounded-tr-none'
                          : 'bg-slate-900/90 border border-slate-800/90 text-slate-200 rounded-tl-none shadow-md'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{m.content}</p>
                    </div>

                    {/* Source Citations */}
                    {!isUser && m.sources && m.sources.length > 0 && (
                      <div className="space-y-1.5 pt-1">
                        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block">
                          Verified Sources ({m.sources.length}):
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {m.sources.map((s, idx) => (
                            <button
                              key={idx}
                              onClick={() => setActiveCitation(s)}
                              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-sky-500/50 text-[11px] text-slate-300 hover:text-white transition group"
                            >
                              <FileText className="w-3 h-3 text-sky-400" />
                              <span className="font-medium truncate max-w-xs">{s.document_name}</span>
                              {s.page_number && (
                                <span className="text-slate-500 group-hover:text-slate-400">
                                  p. {s.page_number}
                                </span>
                              )}
                              <ExternalLink className="w-2.5 h-2.5 text-slate-500 group-hover:text-sky-400" />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}

          {sending && (
            <div className="flex gap-3.5 max-w-2xl mr-auto animate-in fade-in">
              <div className="h-8 w-8 rounded-xl bg-slate-800 border border-slate-700 text-sky-400 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 text-slate-400 text-xs flex items-center gap-3">
                <Loader2 className="w-4 h-4 animate-spin text-sky-400" />
                <span>Searching vector embeddings and reasoning over context...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/40">
          <form onSubmit={handleSendMessage} className="max-w-3xl mx-auto flex gap-3 items-end">
            <div className="relative flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                rows={1}
                placeholder="Ask a question about your documents... (Press Enter to send)"
                className="w-full pl-4 pr-10 py-3 bg-slate-900 border border-slate-700/80 rounded-2xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent resize-none transition"
              />
            </div>
            <button
              type="submit"
              disabled={!inputMessage.trim() || sending}
              className="p-3 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:opacity-40 disabled:cursor-not-allowed text-white shadow-lg shadow-sky-600/20 transition shrink-0"
              title="Send Message"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>

        {/* Citation Detail Drawer/Modal */}
        {activeCitation && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-sky-400" />
                  <h3 className="text-sm font-bold text-white truncate max-w-xs">
                    {activeCitation.document_name}
                  </h3>
                </div>
                <button
                  onClick={() => setActiveCitation(null)}
                  className="text-slate-400 hover:text-white p-1 rounded-lg"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
                  <span className="text-slate-500">Page Number</span>
                  <p className="font-semibold text-slate-200">
                    {activeCitation.page_number ? `Page ${activeCitation.page_number}` : 'N/A'}
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
                  <span className="text-slate-500">Vector Similarity Score</span>
                  <p className="font-semibold text-emerald-400">
                    {typeof activeCitation.score === 'number' ? activeCitation.score.toFixed(4) : activeCitation.score}
                  </p>
                </div>
              </div>

              <div className="space-y-1.5">
                <span className="text-xs font-semibold text-slate-400">Retrieved Context Snippet:</span>
                <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-300 font-mono leading-relaxed whitespace-pre-wrap max-h-56 overflow-y-auto">
                  {activeCitation.snippet}
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  onClick={() => setActiveCitation(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
