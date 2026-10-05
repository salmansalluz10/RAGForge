import React, { useState, useEffect } from 'react';
import collectionService from '../services/collectionService';
import documentService from '../services/documentService';
import {
  FolderKanban,
  Plus,
  Trash2,
  Edit2,
  FileText,
  Calendar,
  Layers,
  X,
  Check,
  Loader2,
  AlertCircle,
  FolderPlus
} from 'lucide-react';

export default function CollectionsPage() {
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Create / Edit Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCol, setEditingCol] = useState(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [saving, setSaving] = useState(false);

  // Manage Documents Modal
  const [managingCol, setManagingCol] = useState(null);
  const [allDocs, setAllDocs] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);

  useEffect(() => {
    fetchCollections();
  }, []);

  const fetchCollections = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await collectionService.listCollections();
      setCollections(data.items || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch collections.');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenCreate = () => {
    setEditingCol(null);
    setName('');
    setDescription('');
    setIsModalOpen(true);
  };

  const handleOpenEdit = (col) => {
    setEditingCol(col);
    setName(col.name);
    setDescription(col.description || '');
    setIsModalOpen(true);
  };

  const handleSaveCollection = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    setSaving(true);
    try {
      if (editingCol) {
        const updated = await collectionService.updateCollection(editingCol.id, {
          name: name.trim(),
          description: description.trim() || null,
        });
        setCollections((prev) => prev.map((c) => (c.id === editingCol.id ? { ...c, ...updated } : c)));
      } else {
        const created = await collectionService.createCollection({
          name: name.trim(),
          description: description.trim() || null,
        });
        setCollections((prev) => [created, ...prev]);
      }
      setIsModalOpen(false);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to save collection.');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteCollection = async (id) => {
    if (!confirm('Are you sure you want to delete this collection? Documents will remain intact.')) return;
    try {
      await collectionService.deleteCollection(id);
      setCollections((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete collection.');
    }
  };

  const handleOpenManageDocs = async (col) => {
    setManagingCol(col);
    setLoadingDocs(true);
    try {
      const docData = await documentService.getDocuments({ limit: 100 });
      setAllDocs(docData.items || []);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoadingDocs(false);
    }
  };

  const handleToggleDocInCollection = async (doc) => {
    if (!managingCol) return;
    const isInside = doc.collection_id === managingCol.id;

    try {
      if (isInside) {
        await collectionService.removeDocument(managingCol.id, doc.id);
        setAllDocs((prev) =>
          prev.map((d) => (d.id === doc.id ? { ...d, collection_id: null } : d))
        );
      } else {
        await collectionService.addDocument(managingCol.id, doc.id);
        setAllDocs((prev) =>
          prev.map((d) => (d.id === doc.id ? { ...d, collection_id: managingCol.id } : d))
        );
      }
      // Refresh collections to update count
      fetchCollections();
    } catch (err) {
      alert('Failed to update document collection membership.');
    }
  };

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Document Collections</h1>
          <p className="text-sm text-slate-400">
            Cluster your knowledge assets into domains, projects, or categories for targeted RAG retrieval
          </p>
        </div>
        <button
          onClick={handleOpenCreate}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-sky-600 hover:bg-sky-500 shadow-lg shadow-sky-600/20 transition"
        >
          <Plus className="w-4 h-4" />
          Create Collection
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Grid */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-sky-500" />
          <p className="text-sm">Loading collections...</p>
        </div>
      ) : collections.length === 0 ? (
        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-12 text-center space-y-4">
          <div className="h-14 w-14 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mx-auto border border-indigo-500/20">
            <FolderPlus className="w-7 h-7" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-white">No collections yet</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Create collections like "Financials", "Legal", or "Engineering" to scope your questions and retrieval.
            </p>
          </div>
          <button
            onClick={handleOpenCreate}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-sky-600 hover:bg-sky-500 transition"
          >
            <Plus className="w-3.5 h-3.5" />
            Create First Collection
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {collections.map((col) => (
            <div
              key={col.id}
              className="bg-slate-900/70 border border-slate-800 p-6 rounded-2xl flex flex-col justify-between hover:border-slate-700 transition group space-y-4"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    <FolderKanban className="w-5 h-5" />
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleOpenEdit(col)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-sky-400 hover:bg-sky-500/10 transition"
                      title="Edit Collection"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteCollection(col.id)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition"
                      title="Delete Collection"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <h3 className="text-base font-semibold text-white truncate">{col.name}</h3>
                <p className="text-xs text-slate-400 line-clamp-2 min-h-[32px]">
                  {col.description || 'No description provided.'}
                </p>
              </div>

              <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs text-slate-400">
                  <FileText className="w-3.5 h-3.5 text-sky-400" />
                  <span>{col.document_count || 0} documents</span>
                </div>
                <button
                  onClick={() => handleOpenManageDocs(col)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition"
                >
                  Manage Docs
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white">
                {editingCol ? 'Edit Collection' : 'Create New Collection'}
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveCollection} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Collection Name
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Q4 Financial Audit"
                  className="mt-1 w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Description
                </label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe what documents belong here..."
                  className="mt-1 w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-500 resize-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-medium text-slate-300 hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!name.trim() || saving}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-sky-600 hover:bg-sky-500 transition disabled:opacity-50"
                >
                  {saving ? 'Saving...' : editingCol ? 'Update Collection' : 'Create Collection'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Manage Documents Modal */}
      {managingCol && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl max-h-[80vh] flex flex-col p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white">Manage Documents in {managingCol.name}</h3>
                <p className="text-xs text-slate-400">Toggle which documents are indexed under this collection</p>
              </div>
              <button onClick={() => setManagingCol(null)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 py-2">
              {loadingDocs ? (
                <div className="py-8 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-sky-400" /> Loading documents...
                </div>
              ) : allDocs.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-6">No documents uploaded yet.</p>
              ) : (
                allDocs.map((doc) => {
                  const isInThisCol = doc.collection_id === managingCol.id;
                  return (
                    <div
                      key={doc.id}
                      onClick={() => handleToggleDocInCollection(doc)}
                      className={`flex items-center justify-between p-3 rounded-xl border text-xs cursor-pointer transition ${
                        isInThisCol
                          ? 'bg-sky-500/10 border-sky-500/30 text-white'
                          : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:bg-slate-800/40'
                      }`}
                    >
                      <div className="flex items-center gap-2.5 truncate pr-2">
                        <FileText className={`w-4 h-4 ${isInThisCol ? 'text-sky-400' : 'text-slate-500'}`} />
                        <span className="truncate font-medium">{doc.original_filename}</span>
                        <span className="text-[10px] uppercase text-slate-500">{doc.file_type}</span>
                      </div>
                      <div
                        className={`h-5 w-5 rounded-md flex items-center justify-center border transition ${
                          isInThisCol
                            ? 'bg-sky-500 border-sky-500 text-white'
                            : 'border-slate-700 bg-slate-900'
                        }`}
                      >
                        {isInThisCol && <Check className="w-3.5 h-3.5" />}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-800">
              <button
                onClick={() => setManagingCol(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-slate-800 hover:bg-slate-700 transition"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
