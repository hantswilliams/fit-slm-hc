"""Primary descriptive presentation for the aug28 revision (FIT-SLM-HC).

Replaces the inferential trend test as the lead analysis (author decision D3,
CHANGES_aug28.md). Reports, for the unique axis-scored tasks:

  - mean / median / min / max AR and inside-counts (AR >= 0.80 / 0.90 / 0.95)
    by axis sum;
  - the same broken out per axis for r (reasoning) and k (knowledge);
  - o (output structure) coverage only: 20/1/0 across levels 1/2/3, which
    cannot support any per-level analysis (manuscript finding F8);
  - the headline counts the manuscript quotes (18 low-axis tasks, 16 at
    AR >= 0.90, 13 above 1.0).

Inputs:  analysis/data/tasks_master.csv
Outputs: analysis/outputs/descriptives.json, descriptives.txt
"""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path

AR_THRESHOLDS = (0.80, 0.90, 0.95)


def group_stats(rows: list[dict[str, str]], key_name: str, key_fn) -> dict:
    groups: dict[int, list[dict[str, str]]] = {}
    for r in rows:
        groups.setdefault(key_fn(r), []).append(r)
    out = {}
    for level in sorted(groups):
        ars = [float(r["ar"]) for r in groups[level]]
        out[str(level)] = {
            "n": len(ars),
            "mean_ar": round(statistics.mean(ars), 3),
            "median_ar": round(statistics.median(ars), 3),
            "min_ar": round(min(ars), 3),
            "max_ar": round(max(ars), 3),
            "inside_at": {
                f"{t:.2f}": sum(1 for a in ars if a >= t) for t in AR_THRESHOLDS
            },
            "task_ids": [r["task_id"] for r in groups[level]],
        }
    return out


def fmt_group(title: str, stats: dict) -> list[str]:
    lines = [title]
    header = (
        f"  {'level':<6}{'n':>3}{'mean AR':>9}{'median':>8}{'min':>7}{'max':>7}"
        f"{'>=0.80':>8}{'>=0.90':>8}{'>=0.95':>8}"
    )
    lines.append(header)
    for level, s in stats.items():
        lines.append(
            f"  {level:<6}{s['n']:>3}{s['mean_ar']:>9.3f}{s['median_ar']:>8.3f}"
            f"{s['min_ar']:>7.3f}{s['max_ar']:>7.3f}"
            f"{s['inside_at']['0.80']:>8}{s['inside_at']['0.90']:>8}{s['inside_at']['0.95']:>8}"
        )
    return lines


def main() -> None:
    here = Path(__file__).resolve().parent.parent
    with (here / "data" / "tasks_master.csv").open() as fh:
        rows = list(csv.DictReader(fh))

    unique = [r for r in rows if r["is_variant"] == "0"]
    scored = [r for r in unique if r["axis_sum"] != ""]

    by_sum = group_stats(scored, "axis_sum", lambda r: int(r["axis_sum"]))
    by_r = group_stats(scored, "r", lambda r: int(r["reasoning_r"]))
    by_k = group_stats(scored, "k", lambda r: int(r["knowledge_k"]))

    o_counts = {
        str(v): sum(1 for r in scored if int(r["output_o"]) == v) for v in (1, 2, 3)
    }

    low = [r for r in scored if int(r["axis_sum"]) <= 5]
    headline = {
        "unique_tasks": len(unique),
        "axis_scored_tasks": len(scored),
        "low_axis_tasks_le_5": len(low),
        "low_axis_inside_0_90": sum(1 for r in low if float(r["ar"]) >= 0.90),
        "low_axis_above_1_0": sum(1 for r in low if float(r["ar"]) > 1.0),
        "high_axis_tasks_ge_6": len(scored) - len(low),
    }

    results = {
        "note": (
            "Descriptive presentation only; no inferential claim intended."
            " Rows cluster by source study and axis scores are single-rater"
            " (pass 1 not AR-blind); see sensitivity_suite and rater_drift."
        ),
        "headline": headline,
        "by_axis_sum": by_sum,
        "by_reasoning_r": by_r,
        "by_knowledge_k": by_k,
        "output_o_coverage": {
            "counts": o_counts,
            "statement": (
                "Output structure cannot be analyzed per level: coverage is"
                f" {o_counts['1']}/{o_counts['2']}/{o_counts['3']} across"
                " levels 1/2/3. The o-axis mechanism remains untested by this"
                " snapshot (manuscript finding F8)."
            ),
        },
    }

    out_dir = here / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "descriptives.json").write_text(json.dumps(results, indent=2))

    lines = [
        "FIT-SLM-HC Descriptives (primary presentation, aug28 revision)",
        "=" * 62,
        "",
        f"Unique tasks: {headline['unique_tasks']}"
        f" (axis-scored: {headline['axis_scored_tasks']};"
        f" composite row excluded from axis groupings)",
        f"Axis sum <= 5: {headline['low_axis_tasks_le_5']} tasks,"
        f" {headline['low_axis_inside_0_90']} at AR >= 0.90,"
        f" {headline['low_axis_above_1_0']} above AR 1.0",
        "",
    ]
    lines += fmt_group("By axis sum (r+k+o):", by_sum)
    lines.append("")
    lines += fmt_group("By reasoning complexity (r):", by_r)
    lines.append("")
    lines += fmt_group("By knowledge boundedness (k):", by_k)
    lines.append("")
    lines.append("Output structure (o): coverage only")
    lines.append(f"  {results['output_o_coverage']['statement']}")
    lines.append("")
    lines.append("Reading:")
    lines.append(
        "  Mean AR is flat and non-monotonic across axis sums 3-6 and drops"
    )
    lines.append(
        "  only at axis sum 7 (two tasks, both open-domain medical exam QA)."
    )
    lines.append(
        "  The sample separates the axis-sum-7 tasks from the rest; it does"
    )
    lines.append(
        "  not establish an ordering within axis sums 3-6."
    )

    text = "\n".join(lines)
    (out_dir / "descriptives.txt").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
