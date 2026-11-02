"""
Adaptive calibration (method CALIBRATION_METHOD).

Every comparable run adds one record per model (raw v1 and v2) and metric: the prediction made BEFORE the run,
the measured outcome, the absolute and relative error. Records are grouped so that only materially similar
experiments are combined:

  group = model version | method | metric | kind (load / dependency) | state (stable / saturated)
          | workers | CPU limit | utilisation band of the prediction (low < 0.5 <= mid < 0.85 <= high)

Per group:
  bias            mean relative error (observed / predicted - 1); > 0 means the model is optimistic
  correction      multiplicative: the median observed / predicted ratio of the group's records
  validation      leave-one-out: each record is corrected with the factor computed from the OTHER records only,
                  and its error measured against its own observation. The correction's accuracy is reported only
                  from these held-out errors - never from the records the factor was fitted to.
  established     at least MIN_HISTORY (5) comparable records
  applied         a correction is applied to new predictions only when the group is established AND the held-out
                  error of the corrected predictions is lower than the raw model's error on the same records
Fewer records, or a correction that does not beat the raw model out of sample, are reported as such.
"""

import statistics
from typing import Any, Dict, List, Optional

CALIBRATION_METHOD = "median-ratio, leave-one-out validated (calibration/2)"
MIN_HISTORY = 5


def band(prediction: Dict[str, Any]) -> str:
    if prediction.get("saturated"):
        return "saturated"
    u = prediction.get("utilization") or 0.0
    return "high" if u >= 0.85 else "mid" if u >= 0.5 else "low"


def group_key(prediction: Dict[str, Any], metric: str, kind: str = "load") -> str:
    inp = prediction.get("inputs") or {}
    return "|".join([prediction.get("model_version", "reality-model/1"), prediction.get("method", "?"), metric, kind,
                     "saturated" if prediction.get("saturated") else "stable", f"w{inp.get('workers')}",
                     f"cpu{inp.get('cpus')}", f"util-{band(prediction)}"])


def _rel(observed: float, predicted: float) -> Optional[float]:
    return (observed - predicted) / predicted if predicted else None


def evaluate(pairs: List[Dict[str, float]]) -> Dict[str, Any]:
    """pairs: [{"predicted", "observed"}] of one group, oldest first."""
    pairs = [x for x in pairs if x.get("predicted")]
    n = len(pairs)
    if not n:
        return {"records": 0, "established": False, "note": "no comparable records"}
    rel = [_rel(x["observed"], x["predicted"]) for x in pairs]
    out: Dict[str, Any] = {"records": n, "established": n >= MIN_HISTORY, "method": CALIBRATION_METHOD,
                           "bias_pct": round(100 * statistics.fmean(rel), 1),
                           "raw_mean_abs_error_pct": round(100 * statistics.fmean(abs(r) for r in rel), 1),
                           "raw_mean_abs_error": round(statistics.fmean(abs(x["observed"] - x["predicted"]) for x in pairs), 3)}
    ratios = [x["observed"] / x["predicted"] for x in pairs]
    out["factor"] = round(statistics.median(ratios), 4)
    out["ratio_range"] = [round(min(ratios), 3), round(max(ratios), 3)]
    if n < MIN_HISTORY:
        out.update(validated=False, applied=False,
                   note=f"insufficient history: {n} of {MIN_HISTORY} comparable runs; no correction and no accuracy claim")
        return out
    held_out = []
    for i, x in enumerate(pairs):
        others = [r for j, r in enumerate(ratios) if j != i]
        corrected = x["predicted"] * statistics.median(others)
        held_out.append(_rel(x["observed"], corrected))
    loo_mae = statistics.fmean(abs(r) for r in held_out)
    raw_mae = statistics.fmean(abs(r) for r in rel)
    srt = sorted(held_out)
    out.update(
        loo_mean_abs_error_pct=round(100 * loo_mae, 1), loo_bias_pct=round(100 * statistics.fmean(held_out), 1),
        loo_error_range_pct=[round(100 * srt[0], 1), round(100 * srt[-1], 1)],
        validated=loo_mae < raw_mae, applied=loo_mae < raw_mae,
        note=("the correction reduced the held-out error ({:.1f}% -> {:.1f}%) over {} runs".format(100 * raw_mae, 100 * loo_mae, n)
              if loo_mae < raw_mae else
              "the correction did not reduce the held-out error ({:.1f}% raw vs {:.1f}% corrected): it is not applied"
              .format(100 * raw_mae, 100 * loo_mae)))
    return out


def correct(value: Optional[float], ev: Dict[str, Any]) -> Dict[str, Any]:
    """A calibrated value for a new prediction, with what it rests on; None unless the group's correction is
    established and validated out of sample."""
    if value is None:
        return {"value": None, "note": "the model gives no value for this metric"}
    if not ev.get("applied"):
        return {"value": None, "records": ev.get("records", 0), "note": ev.get("note", "no calibration group")}
    return {"value": round(value * ev["factor"], 2), "factor": ev["factor"], "records": ev["records"],
            "held_out_error_range_pct": ev.get("loo_error_range_pct"), "method": CALIBRATION_METHOD,
            "note": f"model x median observed/predicted of {ev['records']} comparable runs; the held-out error range "
                    f"{ev.get('loo_error_range_pct')}% is empirical (leave-one-out), not a statistical confidence interval"}
