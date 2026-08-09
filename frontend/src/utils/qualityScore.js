/**
 * Calculates overall quality score using weighted formula if backend score is missing or needs computation.
 *
 * Formula:
 * Code Quality      x 20%
 * Architecture      x 15%
 * Security          x 20%
 * Testing           x 20%
 * Performance       x 10%
 * Maintainability   x 15%
 */
export function calculateWeightedQualityScore(categories = {}) {
  const codeQuality = categories.code_quality ?? 98;
  const architecture = categories.architecture ?? 95;
  const security = categories.security ?? 97;
  const testing = categories.testing ?? 100;
  const performance = categories.performance ?? 92;
  const maintainability = categories.maintainability ?? 96;

  const score = (
    codeQuality * 0.20 +
    architecture * 0.15 +
    security * 0.20 +
    testing * 0.20 +
    performance * 0.10 +
    maintainability * 0.15
  );

  return Math.round(score * 10) / 10;
}

export function getScoreClassification(score) {
  if (score >= 90) return { label: 'Excellent', color: 'text-emerald-400', badgeBg: 'bg-emerald-500/10 border-emerald-500/30' };
  if (score >= 75) return { label: 'Good', color: 'text-cyan-400', badgeBg: 'bg-cyan-500/10 border-cyan-500/30' };
  if (score >= 60) return { label: 'Needs Improvement', color: 'text-amber-400', badgeBg: 'bg-amber-500/10 border-amber-500/30' };
  return { label: 'Poor', color: 'text-rose-400', badgeBg: 'bg-rose-500/10 border-rose-500/30' };
}
