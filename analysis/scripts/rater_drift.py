"""Direction-of-drift analysis for the two scoring passes (aug28 revision).

Cohen's kappa (compute_irr.py) measures agreement but is blind to direction.
This script reports, per axis and pooled:

  - the 3x3 cross-tabulation of pass-1 vs pass-2 scores;
  - each disagreement with its direction (up = pass 2 scored higher);
  - an exact two-sided sign test on the disagreements;
  - Bowker's test of marginal homogeneity (reduces to McNemar when only one
    off-diagonal pair is occupied);
  - the tasks whose axis sum crosses the 5/6 band boundary between passes.

Addresses review findings F2 and F10: all eight disagreements moved scores
upward, which is systematic drift in rubric application, not symmetric noise.

Inputs:  analysis/data/rater1_scores.csv, rater2_scores.csv,
         tasks_master.csv (for AR and variant flags)
Outputs: analysis/outputs/rater_drift.json, rater_drift.txt
"""

from __future__ import annotations

import csv
import json
import sys
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from axis_trend_test import gammainc_upper  # noqa: E402  (chi-square upper tail)

AXES = (("r", "reasoning_r"), ("k", "knowledge_k"), ("o", "output_o"))


def sign_test_two_sided(n_up: int, n_down: int) -> float:
    """Exact two-sided sign test on the disagreements."""
    n = n_up + n_down
    if n == 0:
        return 1.0
    k = min(n_up, n_down)
    tail = sum(comb(n, i) for i in range(k + 1)) * 0.5**n
    return min(1.0, 2 * tail)


def bowker(table: dict[tuple[int, int], int]) -> dict[str, float | int | None]:
    """Bowker's test of marginal homogeneity on a square table."""
    chi2, df = 0.0, 0
    for i in range(1, 4):
        for j in range(i + 1, 4):
            nij, nji = table.get((i, j), 0), table.get((j, i), 0)
            if nij + nji > 0:
                chi2 += (nij - nji) ** 2 / (nij + nji)
                df += 1
    if df == 0:
        return {"chi2": None, "df": 0, "p": None}
    return {"chi2": round(chi2, 4), "df": df, "p": round(gammainc_upper(df / 2, chi2 / 2), 6)}


def main() -> None:
    here = Path(__file__).resolve().parent.parent

    def load(name: str) -> dict[str, dict[str, str]]:
        with (here / "data" / name).open() as fh:
            return {r["task_id"]: r for r in csv.DictReader(fh)}

    r1, r2 = load("rater1_scores.csv"), load("rater2_scores.csv")
    master = load("tasks_master.csv")
    common = sorted(set(r1) & set(r2))

    per_axis, pooled_up, pooled_down = {}, 0, 0
    for label, col in AXES:
        table: dict[tuple[int, int], int] = {}
        disagreements = []
        for tid in common:
            a, b = int(r1[tid][col]), int(r2[tid][col])
            table[(a, b)] = table.get((a, b), 0) + 1
            if a != b:
                disagreements.append(
                    {"task_id": tid, "task_name": r1[tid]["task_name"],
                     "pass1": a, "pass2": b, "direction": "up" if b > a else "down"}
                )
        ups = sum(1 for d in disagreements if d["direction"] == "up")
        downs = len(disagreements) - ups
        pooled_up += ups
        pooled_down += downs
        per_axis[label] = {
            "crosstab": {f"{i}->{j}": n for (i, j), n in sorted(table.items())},
            "n_disagreements": len(disagreements),
            "n_up": ups,
            "n_down": downs,
            "sign_test_p_two_sided": round(sign_test_two_sided(ups, downs), 4),
            "bowker_marginal_homogeneity": bowker(table),
            "disagreements": disagreements,
        }

    band_movers = []
    for tid in common:
        m = master.get(tid)
        if m is None or m["is_variant"] != "0" or m["axis_sum"] == "":
            continue
        s1 = sum(int(r1[tid][c]) for _, c in AXES)
        s2 = sum(int(r2[tid][c]) for _, c in AXES)
        if (s1 <= 5) != (s2 <= 5):
            band_movers.append(
                {"task_id": tid, "task_name": m["task_name"],
                 "sum_pass1": s1, "sum_pass2": s2, "ar": float(m["ar"])}
            )

    results = {
        "n_tasks_scored_by_both_passes": len(common),
        "per_axis": per_axis,
        "pooled": {
            "n_disagreements": pooled_up + pooled_down,
            "n_up": pooled_up,
            "n_down": pooled_down,
            "sign_test_p_two_sided": round(sign_test_two_sided(pooled_up, pooled_down), 4),
        },
        "band_movers_5_to_6": band_movers,
        "note": (
            "Both passes come from the same rater; pass 1 (published) was"
            " assigned with AR visible, pass 2 was AR-blind. One-directional"
            " drift means kappa alone overstates the stability of the scoring."
        ),
    }

    out_dir = here / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "rater_drift.json").write_text(json.dumps(results, indent=2))

    lines = [
        "FIT-SLM-HC Rater Drift (pass 1 -> pass 2, aug28 revision)",
        "=" * 57,
        f"Tasks scored by both passes: {len(common)}",
        "",
    ]
    for label, _ in AXES:
        ax = per_axis[label]
        bk = ax["bowker_marginal_homogeneity"]
        bk_str = "n/a (no disagreements)" if bk["p"] is None else (
            f"chi2={bk['chi2']}, df={bk['df']}, p={bk['p']}"
        )
        lines.append(
            f"Axis {label}: {ax['n_disagreements']} disagreements"
            f" ({ax['n_up']} up, {ax['n_down']} down);"
            f" sign test p={ax['sign_test_p_two_sided']}; Bowker {bk_str}"
        )
        for d in ax["disagreements"]:
            lines.append(
                f"    {d['task_id']} {d['task_name']}: {d['pass1']} -> {d['pass2']} ({d['direction']})"
            )
    po = results["pooled"]
    lines += [
        "",
        f"Pooled: {po['n_disagreements']} disagreements, {po['n_up']} up,"
        f" {po['n_down']} down; exact sign test p = {po['sign_test_p_two_sided']}",
        "",
        "Band movers (axis sum crosses 5/6 between passes):",
    ]
    for m in band_movers:
        lines.append(
            f"    {m['task_id']} {m['task_name']}: {m['sum_pass1']} -> {m['sum_pass2']}"
            f" (AR {m['ar']}, inside at 0.90)"
        )
    lines += [
        "",
        "Reading:",
        "  Every disagreement raised the score on the second (AR-blind) pass.",
        "  Symmetric noise would scatter in both directions; a pooled 8-0",
        "  split (p = 0.008) is systematic drift in how the rubric was",
        "  applied. Kappa cannot see this. The affected boundaries are",
        "  r 1/2, r 2/3, and k 1/2 - the same boundaries the manuscript",
        "  already flags as needing sharper rubric language.",
    ]
    text = "\n".join(lines)
    (out_dir / "rater_drift.txt").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
