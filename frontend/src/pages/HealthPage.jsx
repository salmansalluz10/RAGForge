import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Activity, Database, Cpu, Layers, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

export default function HealthPage() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/health');
      setHealth(res.data);
    } catch (err) {
      setError(err.message || 'Failed to connect to backend service.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col justify-between p-6 md:p-12">
      <div className="max-w-4xl w-full mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-6">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-sky-500/20 text-sky-400 flex items-center justify-center font-bold text-xl border border-sky-500/30">
              RF
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">RAGForge</h1>
              <p className="text-sm text-slate-400">Enterprise AI Document Intelligence & RAG Platform</p>
            </div>
          </div>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-sm font-medium text-slate-300 border border-slate-700 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Status Banner */}
        <div className="rounded-2xl bg-slate-800/60 border border-slate-700/60 p-6 shadow-xl backdrop-blur-md">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <span className="text-xs uppercase tracking-wider font-semibold text-sky-400">System Status</span>
              <h2 className="text-xl font-semibold text-white">Phase 1: Foundation & Infrastructure</h2>
              <p className="text-sm text-slate-300">
                PostgreSQL/pgvector database ready, FastAPI backend active, and React Vite frontend operational.
              </p>
            </div>
            <div className="flex items-center space-x-2 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-3 py-1 rounded-full text-xs font-semibold">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>PHASE 1 VERIFIED</span>
            </div>
          </div>

          {/* Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
              <div className="flex items-center space-x-3 mb-2">
                <Database className="w-5 h-5 text-indigo-400" />
                <span className="text-sm font-medium text-slate-300">Database Engine</span>
              </div>
              <div className="text-base font-semibold text-white">
                {health?.database || (loading ? 'Checking...' : 'Offline')}
              </div>
              <p className="text-xs text-slate-500 mt-1">PostgreSQL + pgvector schema</p>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
              <div className="flex items-center space-x-3 mb-2">
                <Layers className="w-5 h-5 text-sky-400" />
                <span className="text-sm font-medium text-slate-300">Embedding Engine</span>
              </div>
              <div className="text-base font-semibold text-white uppercase">
                {health?.embedding_provider || (loading ? 'Loading...' : 'N/A')}
              </div>
              <p className="text-xs text-slate-500 mt-1">Configurable vector pipeline</p>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
              <div className="flex items-center space-x-3 mb-2">
                <Cpu className="w-5 h-5 text-purple-400" />
                <span className="text-sm font-medium text-slate-300">LLM Provider</span>
              </div>
              <div className="text-base font-semibold text-white uppercase">
                {health?.llm_provider || (loading ? 'Loading...' : 'N/A')}
              </div>
              <p className="text-xs text-slate-500 mt-1">Grounded context reasoning</p>
            </div>
          </div>

          {error && (
            <div className="mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>Backend connection issue: {error}. Check if FastAPI backend is running on port 8000.</span>
            </div>
          )}
        </div>

        {/* Pipeline Architecture Preview */}
        <div className="border border-slate-800 rounded-2xl p-6 bg-slate-950/40">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">
            Production Document Intelligence Pipeline
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-2 text-center text-xs">
            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
              <div className="font-semibold text-slate-200">1. Document</div>
              <div className="text-slate-500 mt-1">PDF / DOCX / TXT</div>
            </div>
            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
              <div className="font-semibold text-slate-200">2. Extraction</div>
              <div className="text-slate-500 mt-1">Page-aware text</div>
            </div>
            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
              <div className="font-semibold text-slate-200">3. Chunking</div>
              <div className="text-slate-500 mt-1">Configurable overlap</div>
            </div>
            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
              <div className="font-semibold text-slate-200">4. Embedding</div>
              <div className="text-slate-500 mt-1">pgvector Storage</div>
            </div>
            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
              <div className="font-semibold text-slate-200">5. Retrieval</div>
              <div className="text-slate-500 mt-1">Top-K Semantic</div>
            </div>
            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
              <div className="font-semibold text-slate-200">6. Grounded AI</div>
              <div className="text-slate-500 mt-1">Answer + Sources</div>
            </div>
          </div>
        </div>
      </div>

      <div className="text-center text-xs text-slate-600 mt-8">
        RAGForge Platform &copy; 2026 &bull; Architecture Ready for Enterprise Document Retrieval
      </div>
    </div>
  );
}
