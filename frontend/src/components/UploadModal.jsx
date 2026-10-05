import React, { useState, useRef } from 'react';
import documentService from '../services/documentService';
import { UploadCloud, X, File, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

const ALLOWED_TYPES = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
const ALLOWED_EXTS = ['.pdf', '.docx', '.txt'];
const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25 MB

export default function UploadModal({ isOpen, onClose, onUploadSuccess }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const inputRef = useRef(null);

  if (!isOpen) return null;

  const validateAndSelectFile = (file) => {
    setError('');
    setSuccess(false);

    if (!file) return;

    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTS.includes(ext)) {
      setError(`Unsupported file type '${ext}'. Please upload a PDF, DOCX, or TXT file.`);
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError('File size exceeds the 25 MB limit.');
      return;
    }

    setSelectedFile(file);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSelectFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSelectFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setProgress(0);
    setError('');

    try {
      const doc = await documentService.uploadDocument(selectedFile, null, (pct) => {
        setProgress(pct);
      });
      setSuccess(true);
      setTimeout(() => {
        onUploadSuccess(doc);
        handleClose();
      }, 1000);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    if (uploading) return;
    setSelectedFile(null);
    setProgress(0);
    setError('');
    setSuccess(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
          <div>
            <h3 className="text-lg font-semibold text-white">Upload Document</h3>
            <p className="text-xs text-slate-400">PDF, DOCX, or TXT up to 25 MB</p>
          </div>
          <button
            onClick={handleClose}
            disabled={uploading}
            className="text-slate-400 hover:text-slate-200 p-1 rounded-lg transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5">
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm flex items-center gap-2">
              <CheckCircle className="w-4 h-4 shrink-0" />
              <span>Document uploaded successfully!</span>
            </div>
          )}

          {/* Dropzone */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition flex flex-col items-center justify-center gap-3 ${
              dragActive
                ? 'border-sky-500 bg-sky-500/10'
                : selectedFile
                ? 'border-slate-700 bg-slate-800/40'
                : 'border-slate-700 hover:border-slate-600 bg-slate-950/40'
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx,.txt"
              className="hidden"
              onChange={handleFileChange}
            />

            <div className="h-12 w-12 rounded-xl bg-sky-500/10 text-sky-400 flex items-center justify-center border border-sky-500/20">
              <UploadCloud className="w-6 h-6" />
            </div>

            {selectedFile ? (
              <div className="space-y-1">
                <p className="text-sm font-medium text-slate-200 break-all">{selectedFile.name}</p>
                <p className="text-xs text-slate-400">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB &bull; Ready to upload
                </p>
              </div>
            ) : (
              <div className="space-y-1">
                <p className="text-sm font-medium text-slate-200">
                  Click to select or drag and drop your file here
                </p>
                <p className="text-xs text-slate-500">Supports PDF, Word DOCX, and Plain TXT</p>
              </div>
            )}
          </div>

          {/* Upload Progress Bar */}
          {uploading && (
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-slate-400">
                <span>Uploading file...</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-sky-500 h-full transition-all duration-300 rounded-full"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-slate-950/60 border-t border-slate-800 flex justify-end gap-3">
          <button
            type="button"
            onClick={handleClose}
            disabled={uploading}
            className="px-4 py-2 rounded-xl text-sm font-medium text-slate-300 hover:bg-slate-800 transition"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            className="flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-semibold text-white bg-sky-600 hover:bg-sky-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {uploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Uploading...
              </>
            ) : (
              'Upload Document'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
