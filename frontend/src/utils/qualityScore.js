/**
 * Classification of a measured score (0-100). A missing score is "Not evaluated", never a grade.
 */
export function getScoreClassification(score) {
  if (score == null || Number.isNaN(Number(score))) {
    return { label: 'Not evaluated', color: 'text-slate-400', badgeBg: 'bg-slate-800/60 border-slate-700' };
  }
  if (score >= 90) return { label: 'Excellent', color: 'text-emerald-400', badgeBg: 'bg-emerald-500/10 border-emerald-500/30' };
  if (score >= 75) return { label: 'Good', color: 'text-cyan-400', badgeBg: 'bg-cyan-500/10 border-cyan-500/30' };
  if (score >= 60) return { label: 'Needs Improvement', color: 'text-amber-400', badgeBg: 'bg-amber-500/10 border-amber-500/30' };
  return { label: 'Poor', color: 'text-rose-400', badgeBg: 'bg-rose-500/10 border-rose-500/30' };
}
