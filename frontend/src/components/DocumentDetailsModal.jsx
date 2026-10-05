import React, { useState, useEffect } from 'react';
import documentService from '../services/documentService';
import {
  X,
  FileText,
  Calendar,
  HardDrive,
  Hash,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Layers,
  Play,
  Loader2
} from 'lucide-react';

export default function DocumentDetailsModal({ document, isOpen, onClose, onDocumentUpdated }) {
  const [activeTab, setActiveTab] = useState('details');
  const [chunks, setChunks] = useState([]);
  const [loadingChunks, setLoadingChunks] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [docState, setDocState] = useState(document);

  useEffect(() => {
    setDocState(document);
    setActiveTab('details');
    setChunks([]);
  }, [document]);

  useEffect(() => {
    if (activeTab === 'chunks' && docState?.id) {
      fetchChunks();
    }
  }, [activeTab, docState]);

  if (!isOpen || !docState) return null;

  const fetchChunks = async () => {
    setLoadingChunks(true);
    try {
      const data = await documentService.getDocumentChunks(docState.id);
      setChunks(data.chunks || []);
    } catch {
      setChunks([]);
    } finally {
      setLoadingChunks(false);
    }
  };

  const handleProcess = async () => {
    setProcessing(true);
    try {
      const updated = await documentService.processDocument(docState.id);
      setDocState(updated);
      if (onDocumentUpdated) onDocumentUpdated(updated);
      if (activeTab === 'chunks') {
        fetchChunks();
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to process document.');
    } finally {
      setProcessing(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5" /> COMPLETED
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <Clock className="w-3.5 h-3.5 animate-spin" /> PROCESSING
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <AlertTriangle className="w-3.5 h-3.5" /> FAILED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/30">
            <Clock className="w-3.5 h-3.5" /> UPLOADED
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-sky-500/10 text-sky-400 flex items-center justify-center border border-sky-500/20">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white truncate max-w-md">
                {docState.original_filename}
              </h3>
              <p className="text-xs text-slate-400 uppercase tracking-wider">{docState.file_type} document</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Controls */}
        <div className="flex border-b border-slate-800 px-6 bg-slate-950/40">
          <button
            onClick={() => setActiveTab('details')}
            className={`py-3 px-4 text-xs font-semibold border-b-2 transition ${
              activeTab === 'details'
                ? 'border-sky-500 text-sky-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Overview & Metadata
          </button>
          <button
            onClick={() => setActiveTab('chunks')}
            className={`py-3 px-4 text-xs font-semibold border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'chunks'
                ? 'border-sky-500 text-sky-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Extracted Chunks ({docState.chunk_count || 0})</span>
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {activeTab === 'details' && (
            <>
              <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-xs text-slate-400">Processing Status</span>
                {getStatusBadge(docState.processing_status)}
              </div>

              {docState.error_message && (
                <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                  <strong className="block font-semibold mb-1">Failure Reason:</strong>
                  <p className="font-mono">{docState.error_message}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800 space-y-1">
                  <span className="text-slate-500 flex items-center gap-1.5">
                    <HardDrive className="w-3.5 h-3.5" /> File Size
                  </span>
                  <p className="font-semibold text-slate-200">{formatSize(docState.file_size)}</p>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800 space-y-1">
                  <span className="text-slate-500 flex items-center gap-1.5">
                    <Hash className="w-3.5 h-3.5" /> Chunks Count
                  </span>
                  <p className="font-semibold text-slate-200">{docState.chunk_count || 0} chunks</p>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800 space-y-1">
                  <span className="text-slate-500 flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5" /> Uploaded At
                  </span>
                  <p className="font-semibold text-slate-200">{formatDate(docState.created_at)}</p>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800 space-y-1">
                  <span className="text-slate-500 flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5" /> Page Count
                  </span>
                  <p className="font-semibold text-slate-200">{docState.page_count ?? 'N/A'}</p>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800 text-[11px] font-mono text-slate-400 space-y-1">
                <span className="text-slate-500 uppercase tracking-wider block font-sans text-[10px]">
                  Internal Storage Identifier
                </span>
                <p className="truncate">{docState.stored_filename}</p>
              </div>
            </>
          )}

          {activeTab === 'chunks' && (
            <div className="space-y-3">
              {loadingChunks ? (
                <div className="py-12 text-center text-slate-400 flex flex-col items-center gap-2">
                  <Loader2 className="w-6 h-6 animate-spin text-sky-500" />
                  <p className="text-xs">Loading chunks...</p>
                </div>
              ) : chunks.length === 0 ? (
                <div className="p-8 text-center bg-slate-950/40 border border-slate-800 rounded-xl space-y-2">
                  <Layers className="w-8 h-8 text-slate-600 mx-auto" />
                  <p className="text-sm font-medium text-slate-300">No chunks available yet</p>
                  <p className="text-xs text-slate-500">
                    Process this document to extract text and segment into chunks.
                  </p>
                </div>
              ) : (
                chunks.map((c) => (
                  <div key={c.id} className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between text-[11px] text-slate-400 border-b border-slate-800/80 pb-2">
                      <span className="font-semibold text-sky-400">Chunk #{c.chunk_index}</span>
                      <div className="flex items-center gap-3">
                        {c.chunk_metadata?.page_number && (
                          <span>Page {c.chunk_metadata.page_number}</span>
                        )}
                        <span>{c.chunk_metadata?.char_count || c.content.length} chars</span>
                      </div>
                    </div>
                    <p className="text-xs text-slate-300 whitespace-pre-wrap leading-relaxed font-sans">
                      {c.content}
                    </p>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 bg-slate-950/80 border-t border-slate-800 flex items-center justify-between">
          <button
            type="button"
            onClick={handleProcess}
            disabled={processing}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-sky-600 hover:bg-sky-500 disabled:opacity-50 transition shadow-md shadow-sky-600/20"
          >
            {processing ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Processing Document...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5" />
                {docState.processing_status === 'COMPLETED' ? 'Re-Process Document' : 'Process Document'}
              </>
            )}
          </button>

          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-medium text-slate-300 hover:bg-slate-800 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
