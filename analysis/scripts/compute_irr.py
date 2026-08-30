"""Inter-rater reliability analysis for FIT-SLM-HC task axis scoring.

Computes per-axis percent agreement, Cohen's kappa, and linearly weighted
kappa between two rater score files. Outputs both a JSON artifact and a
plain-text summary.

Inputs
------
  analysis/data/rater1_scores.csv
  analysis/data/rater2_scores.csv

Outputs
-------
  analysis/outputs/irr_results.json
  analysis/outputs/irr_summary.txt

Notes
-----
This is a pilot/methods-development reliability exercise. Rater 2 is an
independent second pass against the same task descriptions used in Table 2,
not a fully blinded external annotator. Results should be interpreted as
establishing feasibility and surfacing ambiguous axes, not as a
final reliability estimate.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

AXES = ("reasoning_r", "knowledge_k", "output_o")
AXIS_LABELS = {
    "reasoning_r": "Reasoning Complexity (r)",
    "knowledge_k": "Knowledge Boundedness (k)",
    "output_o": "Output Structure (o)",
}


def load_scores(path: Path) -> dict[str, dict[str, int]]:
    scores: dict[str, dict[str, int]] = {}
    with path.open() as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            scores[row["task_id"]] = {axis: int(row[axis]) for axis in AXES}
    return scores


def percent_agreement(pairs: list[tuple[int, int]]) -> float:
    if not pairs:
        return float("nan")
    return sum(1 for a, b in pairs if a == b) / len(pairs)


def cohens_kappa(pairs: list[tuple[int, int]], weight: str = "unweighted") -> float:
    """Compute Cohen's kappa, optionally with linear or quadratic weights."""
    if not pairs:
        return float("nan")
    labels = sorted({v for pair in pairs for v in pair})
    idx = {label: i for i, label in enumerate(labels)}
    n = len(pairs)
    k = len(labels)

    # Observed matrix
    obs = [[0.0] * k for _ in range(k)]
    for a, b in pairs:
        obs[idx[a]][idx[b]] += 1
    for i in range(k):
        for j in range(k):
            obs[i][j] /= n

    # Marginals
    row_marg = [sum(obs[i][j] for j in range(k)) for i in range(k)]
    col_marg = [sum(obs[i][j] for i in range(k)) for j in range(k)]

    if weight == "unweighted":
        w = [[0.0 if i == j else 1.0 for j in range(k)] for i in range(k)]
    elif weight == "linear":
        max_d = max(1, k - 1)
        w = [[abs(i - j) / max_d for j in range(k)] for i in range(k)]
    elif weight == "quadratic":
        max_d = max(1, (k - 1) ** 2)
        w = [[((i - j) ** 2) / max_d for j in range(k)] for i in range(k)]
    else:
        raise ValueError(f"Unknown weight: {weight}")

    po = sum(
        (1 - w[i][j]) * obs[i][j] for i in range(k) for j in range(k)
    )
    pe = sum(
        (1 - w[i][j]) * row_marg[i] * col_marg[j]
        for i in range(k)
        for j in range(k)
    )

    if pe == 1.0:
        return float("nan")
    return (po - pe) / (1 - pe)


def confusion(pairs: list[tuple[int, int]]) -> dict[str, int]:
    c: Counter[tuple[int, int]] = Counter(pairs)
    return {f"({a},{b})": n for (a, b), n in sorted(c.items())}


def interpret_kappa(kappa: float) -> str:
    # aug28 revision: benchmark adjectives ("substantial", "almost perfect")
    # removed. Landis-Koch glosses describe inter-rater agreement between
    # independent annotators; both passes here come from the same rater, so
    # the numbers are reported without a benchmark label. Direction-of-drift
    # analysis lives in rater_drift.py.
    if kappa != kappa:  # NaN
        return "undefined"
    return "same-rater; no benchmark gloss"


def main() -> None:
    here = Path(__file__).resolve().parent.parent
    data_dir = here / "data"
    out_dir = here / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    r1 = load_scores(data_dir / "rater1_scores.csv")
    r2 = load_scores(data_dir / "rater2_scores.csv")

    common = sorted(set(r1) & set(r2))
    missing_r1 = sorted(set(r2) - set(r1))
    missing_r2 = sorted(set(r1) - set(r2))

    results: dict[str, object] = {
        "n_tasks_scored_by_both": len(common),
        "tasks_missing_from_rater1": missing_r1,
        "tasks_missing_from_rater2": missing_r2,
        "per_axis": {},
    }

    for axis in AXES:
        pairs = [(r1[t][axis], r2[t][axis]) for t in common]
        results["per_axis"][axis] = {
            "label": AXIS_LABELS[axis],
            "n_pairs": len(pairs),
            "percent_agreement": round(percent_agreement(pairs), 4),
            "cohens_kappa_unweighted": round(cohens_kappa(pairs, "unweighted"), 4),
            "cohens_kappa_linear_weighted": round(cohens_kappa(pairs, "linear"), 4),
            "cohens_kappa_quadratic_weighted": round(
                cohens_kappa(pairs, "quadratic"), 4
            ),
            "confusion_counts": confusion(pairs),
        }

    # Overall: pool all axes
    pooled = [
        (r1[t][axis], r2[t][axis]) for t in common for axis in AXES
    ]
    results["pooled_across_axes"] = {
        "n_pairs": len(pooled),
        "percent_agreement": round(percent_agreement(pooled), 4),
        "cohens_kappa_unweighted": round(cohens_kappa(pooled, "unweighted"), 4),
        "cohens_kappa_linear_weighted": round(cohens_kappa(pooled, "linear"), 4),
    }

    (out_dir / "irr_results.json").write_text(json.dumps(results, indent=2))

    # Text summary
    lines = [
        "FIT-SLM-HC Inter-Rater Reliability Summary",
        "=" * 46,
        f"Tasks scored by both raters: {results['n_tasks_scored_by_both']}",
        "",
    ]
    for axis in AXES:
        r = results["per_axis"][axis]
        lines.append(f"{r['label']}")
        lines.append(f"  Percent agreement:      {r['percent_agreement']:.3f}")
        lines.append(
            f"  Cohen's kappa (unwtd):  {r['cohens_kappa_unweighted']:.3f} "
            f"({interpret_kappa(r['cohens_kappa_unweighted'])})"
        )
        lines.append(
            f"  Cohen's kappa (linear): {r['cohens_kappa_linear_weighted']:.3f} "
            f"({interpret_kappa(r['cohens_kappa_linear_weighted'])})"
        )
        lines.append("")
    p = results["pooled_across_axes"]
    lines.append("Pooled across axes")
    lines.append(f"  Percent agreement:      {p['percent_agreement']:.3f}")
    lines.append(
        f"  Cohen's kappa (unwtd):  {p['cohens_kappa_unweighted']:.3f} "
        f"({interpret_kappa(p['cohens_kappa_unweighted'])})"
    )
    lines.append(
        f"  Cohen's kappa (linear): {p['cohens_kappa_linear_weighted']:.3f} "
        f"({interpret_kappa(p['cohens_kappa_linear_weighted'])})"
    )
    lines.append("")
    lines.append(
        "Note: Both passes were produced by the same author. Pass 1 (published"
        " scores) was assigned with AR values visible; pass 2 was an"
        " AR-blind delayed re-read of the task descriptions. These figures"
        " measure one rater\'s consistency across sittings, not inter-rater"
        " reliability, and kappa is blind to direction: all eight"
        " disagreements moved scores upward (see rater_drift outputs)."
    )

    (out_dir / "irr_summary.txt").write_text("\n".join(lines))

    print("\n".join(lines))


if __name__ == "__main__":
    main()
