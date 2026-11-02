import React, { useState } from 'react';
import {
  FaCheckCircle,
  FaTimesCircle,
  FaShieldAlt,
  FaFileCode,
  FaCheck,
  FaTimes,
  FaLightbulb,
  FaChevronDown,
  FaChevronRight,
  FaLayerGroup,
  FaExclamationTriangle
} from 'react-icons/fa';

export default function AIDiffReviewPanel({
  changes = [],
  onAcceptFile = null,
  onRejectFile = null,
  onAcceptAll = null,
  onRejectAll = null,
  onClose = null
}) {
  const defaultChanges = [
    {
      file: 'backend/services/auth.py',
      status: 'MODIFIED',
      additions: 14,
      deletions: 3,
      risk: 'LOW',
      reason: 'Updated JWT authentication token generation to include standard project user claims and expiration timestamps.',
      diff: `@@ -15,4 +15,15 @@
-def create_token(user):
-    return jwt.encode({"sub": user.id}, "secret")
+def create_access_token(user: User) -> str:
+    expire = datetime.utcnow() + timedelta(minutes=60)
+    payload = {
+        "sub": str(user.id),
+        "email": user.email,
+        "exp": expire
+    }
+    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
`
    },
    {
      file: 'backend/routes/products.py',
      status: 'MODIFIED',
      additions: 22,
      deletions: 4,
      risk: 'LOW',
      reason: 'Added pagination parameters (skip, limit) and SQLAlchemy query filtering to prevent full table scans on large datasets.',
      diff: `@@ -10,3 +10,21 @@
-@router.get("/products")
-def list_products():
-    return db.query(Product).all()
+@router.get("/products", response_model=List[ProductResponse])
+def list_products(
+    skip: int = Query(0, ge=0),
+    limit: int = Query(20, le=100),
+    db: Session = Depends(get_db)
+):
+    return db.query(Product).offset(skip).limit(limit).all()
`
    }
  ];

  const changeList = changes.length > 0 ? changes : defaultChanges;
  const [selectedFileIdx, setSelectedFileIdx] = useState(0);
  const [showReason, setShowReason] = useState(true);

  const activeChange = changeList[selectedFileIdx] || changeList[0];
  const totalAdditions = changeList.reduce((acc, c) => acc + (c.additions || 0), 0);
  const totalDeletions = changeList.reduce((acc, c) => acc + (c.deletions || 0), 0);

  return (
    <div className="bg-[#090d16] border border-slate-800 rounded-2xl shadow-2xl font-sans overflow-hidden flex flex-col h-[560px]">
      {/* Top Header Banner */}
      <div className="px-5 py-3.5 bg-[#060911] border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <FaShieldAlt className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-white">AI-Generated Code Changes & Diff Review</h3>
            <p className="text-[11px] text-slate-400">
              {changeList.length} files changed • <span className="text-emerald-400 font-mono font-bold">+{totalAdditions}</span> / <span className="text-rose-400 font-mono font-bold">-{totalDeletions}</span> lines
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onRejectAll?.()}
            className="px-3 py-1.5 bg-slate-900 hover:bg-rose-950/60 text-rose-400 rounded-lg text-xs font-bold border border-rose-500/30 transition cursor-pointer"
          >
            Reject All
          </button>
          <button
            onClick={() => onAcceptAll?.()}
            className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold shadow-lg transition flex items-center gap-1.5 cursor-pointer"
          >
            <FaCheck className="w-3 h-3" /> Accept All ({changeList.length})
          </button>
        </div>
      </div>

      {/* Checklist Strip */}
      <div className="px-5 py-2 bg-slate-950 border-b border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-300">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1 text-emerald-400"><FaCheckCircle className="w-3 h-3" /> Architecture Compatible</span>
          <span className="flex items-center gap-1 text-emerald-400"><FaCheckCircle className="w-3 h-3" /> APIs Preserved</span>
          <span className="flex items-center gap-1 text-cyan-400"><FaCheckCircle className="w-3 h-3" /> Tests Verified</span>
        </div>
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
          Risk: LOW
        </span>
      </div>

      {/* Main Split Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Changed Files Navigation List */}
        <div className="w-64 border-r border-slate-800 bg-[#070b14] overflow-y-auto p-2 space-y-1 custom-scrollbar">
          <div className="px-2 py-1 text-[10px] font-mono font-bold uppercase text-slate-400">Affected Files</div>
          {changeList.map((c, idx) => {
            const isSelected = selectedFileIdx === idx;
            return (
              <div
                key={idx}
                onClick={() => setSelectedFileIdx(idx)}
                className={`p-2.5 rounded-xl border transition cursor-pointer text-xs ${
                  isSelected
                    ? 'bg-indigo-600/20 border-cyan-400 text-white shadow-md'
                    : 'bg-slate-900/50 border-slate-800 text-slate-300 hover:bg-slate-900 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between font-mono text-[11px]">
                  <span className="truncate font-semibold">{c.file.split('/').pop()}</span>
                  <span className="text-[10px] text-emerald-400">+{c.additions || 0}</span>
                </div>
                <div className="text-[10px] text-slate-400 truncate mt-0.5 font-mono">{c.file}</div>
              </div>
            );
          })}
        </div>

        {/* Right: Active File Diff & Why This Change Explanation */}
        <div className="flex-1 flex flex-col bg-[#050811] overflow-hidden">
          {/* File Action Bar */}
          <div className="px-4 py-2 border-b border-slate-800 flex items-center justify-between bg-slate-950">
            <span className="font-mono text-xs text-white font-bold">{activeChange.file}</span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => onRejectFile?.(activeChange.file)}
                className="px-2.5 py-1 bg-slate-900 hover:bg-rose-950 text-rose-400 rounded text-xs font-semibold border border-rose-500/20 cursor-pointer"
              >
                Reject File
              </button>
              <button
                onClick={() => onAcceptFile?.(activeChange.file)}
                className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-bold cursor-pointer"
              >
                Accept File
              </button>
            </div>
          </div>

          {/* Collapsible "Why this change?" Box */}
          <div className="p-3 bg-slate-900/70 border-b border-slate-800">
            <button
              onClick={() => setShowReason(!showReason)}
              className="flex items-center gap-1.5 text-xs font-bold text-cyan-400 cursor-pointer"
            >
              <FaLightbulb className="w-3 h-3" />
              <span>WHY DID AIForge MAKE THIS CHANGE?</span>
              {showReason ? <FaChevronDown className="w-2.5 h-2.5" /> : <FaChevronRight className="w-2.5 h-2.5" />}
            </button>
            {showReason && (
              <p className="text-xs text-slate-300 mt-1.5 leading-relaxed bg-slate-950 p-2.5 rounded-lg border border-slate-800 font-sans">
                {activeChange.reason || 'Change improves performance, architectural consistency, and test compatibility.'}
              </p>
            )}
          </div>

          {/* Diff Content Viewer */}
          <div className="flex-1 overflow-y-auto p-4 font-mono text-xs text-slate-300 leading-relaxed custom-scrollbar">
            <pre className="whitespace-pre-wrap">
              {activeChange.diff.split('\n').map((line, lIdx) => {
                if (line.startsWith('+') && !line.startsWith('+++')) {
                  return <div key={lIdx} className="bg-emerald-950/60 text-emerald-300 px-2 py-0.5 rounded">{line}</div>;
                }
                if (line.startsWith('-') && !line.startsWith('---')) {
                  return <div key={lIdx} className="bg-rose-950/60 text-rose-300 px-2 py-0.5 rounded">{line}</div>;
                }
                if (line.startsWith('@@')) {
                  return <div key={lIdx} className="text-indigo-400 bg-indigo-950/30 px-2 py-0.5 my-1 font-bold">{line}</div>;
                }
                return <div key={lIdx} className="text-slate-400 px-2">{line}</div>;
              })}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
