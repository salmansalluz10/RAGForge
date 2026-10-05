import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import dashboardService from '../services/dashboardService';
import {
  FileText,
  FolderKanban,
  MessageSquare,
  Sparkles,
  ArrowUpRight,
  ShieldCheck,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Layers,
  Loader2,
  RefreshCw
} from 'lucide-react';

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const data = await dashboardService.getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load dashboard metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto w-full space-y-8">
      {/* Top Welcome Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-sky-950/70 via-slate-900 to-slate-900 border border-sky-500/20 p-8 shadow-xl relative overflow-hidden flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="relative z-10 space-y-2 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-400 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Knowledge & Vector Engine</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">
            Welcome back, {user?.name || 'Engineer'}
          </h1>
          <p className="text-slate-400 text-sm leading-relaxed">
            RAGForge ingests PDF, DOCX, and TXT files, chunks them with preserved metadata, generates high-dimensional embeddings, and provides grounded retrieval with verifiable citations.
          </p>
        </div>

        <button
          onClick={fetchStats}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-xs font-semibold text-slate-300 border border-slate-700 transition shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Stats
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Documents */}
        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl flex flex-col justify-between space-y-4 hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Documents</span>
            <div className="p-2 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div>
            <span className="text-3xl font-extrabold text-white">{stats?.total_documents ?? 0}</span>
            <p className="text-[11px] text-slate-500 mt-1">Files in storage</p>
          </div>
          <Link to="/documents" className="text-xs text-sky-400 hover:text-sky-300 font-medium flex items-center gap-1 pt-2 border-t border-slate-800/80">
            View Documents <ArrowUpRight className="w-3 h-3" />
          </Link>
        </div>

        {/* Collections */}
        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl flex flex-col justify-between space-y-4 hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Collections</span>
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <FolderKanban className="w-4 h-4" />
            </div>
          </div>
          <div>
            <span className="text-3xl font-extrabold text-white">{stats?.total_collections ?? 0}</span>
            <p className="text-[11px] text-slate-500 mt-1">Knowledge clusters</p>
          </div>
          <Link to="/collections" className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 pt-2 border-t border-slate-800/80">
            View Collections <ArrowUpRight className="w-3 h-3" />
          </Link>
        </div>

        {/* Conversations */}
        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl flex flex-col justify-between space-y-4 hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Conversations</span>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <MessageSquare className="w-4 h-4" />
            </div>
          </div>
          <div>
            <span className="text-3xl font-extrabold text-white">{stats?.total_conversations ?? 0}</span>
            <p className="text-[11px] text-slate-500 mt-1">Active chat threads</p>
          </div>
          <Link to="/chat" className="text-xs text-emerald-400 hover:text-emerald-300 font-medium flex items-center gap-1 pt-2 border-t border-slate-800/80">
            Open Chat <ArrowUpRight className="w-3 h-3" />
          </Link>
        </div>

        {/* Vector Chunks */}
        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-2xl flex flex-col justify-between space-y-4 hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Vector Chunks</span>
            <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <div>
            <span className="text-3xl font-extrabold text-white">{stats?.total_chunks ?? 0}</span>
            <p className="text-[11px] text-slate-500 mt-1">Indexed in vector DB</p>
          </div>
          <div className="text-xs text-purple-400 font-medium flex items-center gap-1 pt-2 border-t border-slate-800/80">
            pgvector semantic storage
          </div>
        </div>
      </div>

      {/* Processing Status Breakdown */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
          Document Processing Pipeline Status
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between">
            <div className="flex items-center gap-2 text-emerald-400 font-semibold">
              <CheckCircle2 className="w-4 h-4" />
              <span>COMPLETED</span>
            </div>
            <span className="text-lg font-bold text-white">{stats?.status_counts?.COMPLETED ?? 0}</span>
          </div>

          <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between">
            <div className="flex items-center gap-2 text-amber-400 font-semibold">
              <Clock className="w-4 h-4 animate-spin" />
              <span>PROCESSING</span>
            </div>
            <span className="text-lg font-bold text-white">{stats?.status_counts?.PROCESSING ?? 0}</span>
          </div>

          <div className="p-3.5 rounded-xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sky-400 font-semibold">
              <FileText className="w-4 h-4" />
              <span>UPLOADED</span>
            </div>
            <span className="text-lg font-bold text-white">{stats?.status_counts?.UPLOADED ?? 0}</span>
          </div>

          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-between">
            <div className="flex items-center gap-2 text-rose-400 font-semibold">
              <AlertTriangle className="w-4 h-4" />
              <span>FAILED</span>
            </div>
            <span className="text-lg font-bold text-white">{stats?.status_counts?.FAILED ?? 0}</span>
          </div>
        </div>
      </div>

      {/* Recent Activity: Documents & Conversations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Documents */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white">Recent Documents</h3>
            <Link to="/documents" className="text-xs text-sky-400 hover:text-sky-300 font-medium">
              View All
            </Link>
          </div>

          {stats?.recent_documents?.length === 0 ? (
            <p className="text-xs text-slate-500 text-center py-6">No documents uploaded yet.</p>
          ) : (
            <div className="space-y-2">
              {stats?.recent_documents?.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-3 rounded-xl bg-slate-950/40 border border-slate-800/80 text-xs"
                >
                  <div className="flex items-center gap-2.5 truncate pr-2">
                    <FileText className="w-4 h-4 text-sky-400 shrink-0" />
                    <span className="text-slate-200 font-medium truncate">{doc.original_filename}</span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-[10px] text-slate-500 uppercase">{doc.file_type}</span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                        doc.processing_status === 'COMPLETED'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                          : doc.processing_status === 'FAILED'
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                          : 'bg-sky-500/10 text-sky-400 border border-sky-500/30'
                      }`}
                    >
                      {doc.processing_status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Conversations */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white">Recent Conversations</h3>
            <Link to="/chat" className="text-xs text-emerald-400 hover:text-emerald-300 font-medium">
              Open Chat
            </Link>
          </div>

          {stats?.recent_conversations?.length === 0 ? (
            <p className="text-xs text-slate-500 text-center py-6">No conversations yet.</p>
          ) : (
            <div className="space-y-2">
              {stats?.recent_conversations?.map((conv) => (
                <Link
                  key={conv.id}
                  to="/chat"
                  className="flex items-center justify-between p-3 rounded-xl bg-slate-950/40 border border-slate-800/80 text-xs hover:border-slate-700 transition block"
                >
                  <div className="flex items-center gap-2.5 truncate pr-2">
                    <MessageSquare className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span className="text-slate-200 font-medium truncate">{conv.title}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 text-slate-500 text-[11px]">
                    <span>{conv.message_count || 0} msgs</span>
                    <span>&bull;</span>
                    <span>{new Date(conv.updated_at).toLocaleDateString()}</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
