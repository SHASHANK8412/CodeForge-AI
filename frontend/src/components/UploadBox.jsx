import React, { useState } from 'react';
import { FaCloudUploadAlt, FaFileAlt, FaCheckCircle, FaExclamationCircle, FaSpinner } from 'react-icons/fa';

export default function UploadBox({ onUploadSuccess }) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const handleFiles = async (files) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    setMessage(null);
    setError(null);

    const file = files[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      setMessage(`✓ ${data.filename} uploaded & indexed (${data.chunks} chunks).`);
      if (onUploadSuccess) onUploadSuccess(data);
    } catch (err) {
      setError(err.message || 'Upload error occurred');
    } finally {
      setUploading(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files);
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-xl p-6 text-center transition-all bg-slate-900 ${
        isDragging
          ? 'border-indigo-500 bg-indigo-950/40'
          : 'border-slate-800 hover:border-slate-700'
      }`}
    >
      <div className="flex flex-col items-center justify-center space-y-3">
        <div className="bg-indigo-950/60 p-4 rounded-full border border-indigo-800 text-indigo-400">
          <FaCloudUploadAlt className="w-8 h-8" />
        </div>
        <div>
          <h4 className="text-sm font-semibold text-white">Upload Project Knowledge Documents</h4>
          <p className="text-xs text-slate-400 mt-1">
            Drag & drop PDF, Markdown (.md), TXT, or DOCX files here
          </p>
        </div>

        <label className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-4 py-2 rounded-lg cursor-pointer transition active:scale-95 shadow">
          <span>Select Document</span>
          <input
            type="file"
            accept=".pdf,.txt,.md,.docx"
            onChange={(e) => handleFiles(e.target.files)}
            className="hidden"
            disabled={uploading}
          />
        </label>

        {uploading && (
          <div className="flex items-center gap-2 text-xs text-indigo-400 animate-pulse mt-2">
            <FaSpinner className="animate-spin" />
            <span>Processing document & generating vectors...</span>
          </div>
        )}

        {message && (
          <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-950/60 px-3 py-1.5 rounded border border-emerald-800 mt-2">
            <FaCheckCircle />
            <span>{message}</span>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 text-xs text-rose-400 bg-rose-950/60 px-3 py-1.5 rounded border border-rose-800 mt-2">
            <FaExclamationCircle />
            <span>{error}</span>
          </div>
        )}
      </div>
    </div>
  );
}
