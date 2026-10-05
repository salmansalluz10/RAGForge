import React, { useState, useEffect } from 'react';
import documentService from '../services/documentService';
import UploadModal from '../components/UploadModal';
import DocumentDetailsModal from '../components/DocumentDetailsModal';
import {
  Upload,
  Search,
  Filter,
  FileText,
  Trash2,
  Eye,
  RefreshCw,
  Clock,
  CheckCircle2,
  AlertTriangle,
  FileCode,
  FileSpreadsheet,
  AlertCircle,
  Play,
  Loader2
} from 'lucide-react';

export default function DocumentsPage() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [processingIds, setProcessingIds] = useState(new Set());

  // Modals
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [docToDelete, setDocToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (search.trim()) params.search = search.trim();
      if (statusFilter) params.status = statusFilter;

      const data = await documentService.getDocuments(params);
      setDocuments(data.items || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch documents.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [statusFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchDocuments();
  };

  const handleDelete = async () => {
    if (!docToDelete) return;
    setDeleting(true);
    try {
      await documentService.deleteDocument(docToDelete.id);
      setDocuments((prev) => prev.filter((d) => d.id !== docToDelete.id));
      setDocToDelete(null);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete document.');
    } finally {
      setDeleting(false);
    }
  };

  const handleProcessRow = async (docId) => {
    setProcessingIds((prev) => new Set(prev).add(docId));
    try {
      const updated = await documentService.processDocument(docId);
      setDocuments((prev) => prev.map((d) => (d.id === docId ? updated : d)));
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to process document.');
    } finally {
      setProcessingIds((prev) => {
        const next = new Set(prev);
        next.delete(docId);
        return next;
      });
    }
  };

  const getFileIcon = (fileType) => {
    switch (fileType.toLowerCase()) {
      case 'pdf':
        return <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20"><FileText className="w-5 h-5" /></div>;
      case 'docx':
        return <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20"><FileSpreadsheet className="w-5 h-5" /></div>;
      default:
        return <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><FileCode className="w-5 h-5" /></div>;
    }
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
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3 h-3" /> COMPLETED
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <Clock className="w-3 h-3 animate-spin" /> PROCESSING
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <AlertTriangle className="w-3 h-3" /> FAILED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/30">
            <Clock className="w-3 h-3" /> UPLOADED
          </span>
        );
    }
  };

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto w-full space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Document Management</h1>
          <p className="text-sm text-slate-400">
            Upload, inspect, and organize knowledge assets for semantic RAG retrieval
          </p>
        </div>
        <button
          onClick={() => setIsUploadOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-sky-600 hover:bg-sky-500 shadow-lg shadow-sky-600/20 transition"
        >
          <Upload className="w-4 h-4" />
          Upload Document
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-slate-900/60 border border-slate-800 p-3.5 rounded-2xl">
        <form onSubmit={handleSearchSubmit} className="relative w-full sm:w-96">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search by filename..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 bg-slate-950 border border-slate-700/80 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition"
          />
        </form>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500 transition"
            >
              <option value="">All Statuses</option>
              <option value="UPLOADED">Uploaded</option>
              <option value="PROCESSING">Processing</option>
              <option value="COMPLETED">Completed</option>
              <option value="FAILED">Failed</option>
            </select>
          </div>

          <button
            onClick={fetchDocuments}
            disabled={loading}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Refresh list"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Documents List */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="py-20 text-center text-slate-400 flex flex-col items-center gap-3">
          <RefreshCw className="w-8 h-8 animate-spin text-sky-500" />
          <p className="text-sm">Loading documents...</p>
        </div>
      ) : documents.length === 0 ? (
        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-12 text-center space-y-4">
          <div className="h-14 w-14 rounded-2xl bg-sky-500/10 text-sky-400 flex items-center justify-center mx-auto border border-sky-500/20">
            <FileText className="w-7 h-7" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-white">No documents found</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Upload your PDF, DOCX, or TXT knowledge documents to index them into vector embeddings.
            </p>
          </div>
          <button
            onClick={() => setIsUploadOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-sky-600 hover:bg-sky-500 transition"
          >
            <Upload className="w-3.5 h-3.5" />
            Upload Now
          </button>
        </div>
      ) : (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/60 text-xs font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-6 py-4">Document</th>
                  <th className="px-6 py-4">Size</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Chunks</th>
                  <th className="px-6 py-4">Uploaded</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        {getFileIcon(doc.file_type)}
                        <div className="min-w-0">
                          <p className="font-medium text-slate-100 truncate max-w-xs">{doc.original_filename}</p>
                          <span className="text-[11px] text-slate-400 uppercase">{doc.file_type}</span>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-400 text-xs">{formatSize(doc.file_size)}</td>
                    <td className="px-6 py-4">{getStatusBadge(doc.processing_status)}</td>
                    <td className="px-6 py-4 text-slate-300 font-mono text-xs">{doc.chunk_count || 0}</td>
                    <td className="px-6 py-4 text-slate-400 text-xs">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => handleProcessRow(doc.id)}
                          disabled={processingIds.has(doc.id) || doc.processing_status === 'PROCESSING'}
                          className={`p-1.5 rounded-lg transition ${
                            doc.processing_status === 'COMPLETED'
                              ? 'text-slate-400 hover:text-sky-400 hover:bg-sky-500/10'
                              : 'text-sky-400 hover:text-white bg-sky-500/20 hover:bg-sky-500/30 border border-sky-500/30'
                          }`}
                          title={doc.processing_status === 'COMPLETED' ? 'Re-process Document' : 'Process Document'}
                        >
                          {processingIds.has(doc.id) || doc.processing_status === 'PROCESSING' ? (
                            <Loader2 className="w-4 h-4 animate-spin text-sky-400" />
                          ) : (
                            <Play className="w-4 h-4" />
                          )}
                        </button>
                        <button
                          onClick={() => setSelectedDoc(doc)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-sky-400 hover:bg-sky-500/10 transition"
                          title="View Details & Chunks"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setDocToDelete(doc)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition"
                          title="Delete Document"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={(newDoc) => {
          setDocuments((prev) => [newDoc, ...prev]);
        }}
      />

      {/* Details Modal */}
      <DocumentDetailsModal
        document={selectedDoc}
        isOpen={!!selectedDoc}
        onClose={() => setSelectedDoc(null)}
        onDocumentUpdated={(updated) => {
          setDocuments((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
          setSelectedDoc(updated);
        }}
      />

      {/* Delete Confirmation Dialog */}
      {docToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-rose-400">
              <div className="p-2 rounded-xl bg-rose-500/10 border border-rose-500/20">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white">Delete Document</h3>
            </div>
            <p className="text-sm text-slate-300">
              Are you sure you want to delete <strong className="text-white">{docToDelete.original_filename}</strong>? This will permanently erase the stored file and all associated vector embeddings.
            </p>
            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setDocToDelete(null)}
                disabled={deleting}
                className="px-4 py-2 rounded-xl text-sm font-medium text-slate-300 hover:bg-slate-800 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="px-4 py-2 rounded-xl text-sm font-semibold text-white bg-rose-600 hover:bg-rose-500 transition"
              >
                {deleting ? 'Deleting...' : 'Delete Permanently'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
