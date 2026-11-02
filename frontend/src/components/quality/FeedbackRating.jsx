import React, { useState } from 'react';
import { FaThumbsUp, FaThumbsDown, FaStar, FaPaperPlane, FaCheck } from 'react-icons/fa';
import { submitFeedback } from '../../services/observability';

export default function FeedbackRating({ projectId = 'aiforge-demo' }) {
  const [helpful, setHelpful] = useState(true);
  const [rating, setRating] = useState(5);
  const [selectedTags, setSelectedTags] = useState([]);
  const [comment, setComment] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const availableTags = [
    'Code quality',
    'UI / UX Design',
    'Architecture',
    'Tests',
    'Performance',
    'Requirements understanding'
  ];

  const toggleTag = (t) => {
    if (selectedTags.includes(t)) {
      setSelectedTags(selectedTags.filter((item) => item !== t));
    } else {
      setSelectedTags([...selectedTags, t]);
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    await submitFeedback({
      project_id: projectId,
      helpful: helpful,
      rating: rating,
      tags: selectedTags,
      comment: comment
    });
    setSubmitting(false);
    setSubmitted(true);
  };

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans mt-6">
      <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-4 border-b border-slate-800 pb-3">
        User Feedback & Project Quality Assessment
      </h3>

      {submitted ? (
        <div className="p-4 bg-emerald-950/60 border border-emerald-500/30 rounded-xl text-xs text-emerald-400 font-bold flex items-center gap-2">
          <FaCheck /> Thank you for your feedback! Your evaluation response has been recorded.
        </div>
      ) : (
        <div className="space-y-4 text-xs font-sans">
          {/* Helpfulness */}
          <div className="flex items-center gap-4">
            <span className="text-slate-300 font-semibold">Was AIForge's generated project useful?</span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setHelpful(true)}
                className={`px-3 py-1.5 rounded-xl border flex items-center gap-1.5 font-bold transition ${
                  helpful ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-slate-900 text-slate-400 border-slate-800'
                }`}
              >
                <FaThumbsUp /> Yes
              </button>
              <button
                type="button"
                onClick={() => setHelpful(false)}
                className={`px-3 py-1.5 rounded-xl border flex items-center gap-1.5 font-bold transition ${
                  !helpful ? 'bg-rose-500/10 text-rose-400 border-rose-500/30' : 'bg-slate-900 text-slate-400 border-slate-800'
                }`}
              >
                <FaThumbsDown /> No
              </button>
            </div>
          </div>

          {/* Star Rating */}
          <div className="flex items-center gap-3">
            <span className="text-slate-300 font-semibold">Generation Quality:</span>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => setRating(star)}
                  className={`text-lg transition ${star <= rating ? 'text-amber-400' : 'text-slate-700'}`}
                >
                  <FaStar />
                </button>
              ))}
            </div>
          </div>

          {/* Tag Selectors */}
          <div>
            <label className="text-slate-400 block mb-1.5">What could be improved?</label>
            <div className="flex flex-wrap gap-2">
              {availableTags.map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => toggleTag(t)}
                  className={`px-3 py-1 rounded-lg border text-[11px] transition ${
                    selectedTags.includes(t) ? 'bg-indigo-600 text-white border-indigo-500 font-bold' : 'bg-slate-900 text-slate-400 border-slate-800'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Comment */}
          <div>
            <textarea
              rows={2}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Optional feedback..."
              className="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting}
            className="px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-cyan-500/20 flex items-center gap-1.5 disabled:opacity-50"
          >
            <FaPaperPlane className="w-3 h-3" /> Submit Feedback
          </button>
        </div>
      )}
    </div>
  );
}
