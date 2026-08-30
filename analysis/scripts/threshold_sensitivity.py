"""Threshold sensitivity analysis for FIT-SLM-HC envelope verdicts.

For each of AR >= 0.80, 0.90, 0.95, compute:
  - per-task envelope verdict
  - counts of inside/outside by axis-sum bucket

Inputs
------
  analysis/data/tasks_master.csv

Outputs
-------
  analysis/outputs/threshold_sensitivity_per_task.csv
  analysis/outputs/threshold_sensitivity_summary.json
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

THRESHOLDS = (0.80, 0.90, 0.95)


def bucket(axis_sum: str) -> str:
    if axis_sum == "" or axis_sum is None:
        return "composite (var.)"
    n = int(axis_sum)
    if n == 3:
        return "low (3)"
    if n == 4:
        return "low-mod (4)"
    if n == 5:
        return "mod (5)"
    if n == 6:
        return "high (6)"
    if n >= 7:
        return "high (>=7)"
    return "other"


def main() -> None:
    here = Path(__file__).resolve().parent.parent
    rows: list[dict[str, str]] = []
    with (here / "data" / "tasks_master.csv").open() as fh:
        rows = list(csv.DictReader(fh))

    out_rows: list[dict[str, object]] = []
    for row in rows:
        ar = float(row["ar"])
        out_row = {
            "task_id": row["task_id"],
            "task_name": row["task_name"],
            "axis_sum": row["axis_sum"],
            "ar": ar,
            "is_variant": row["is_variant"],
            "adaptation_symmetry": row.get("adaptation_symmetry", "unknown")
            or "unknown",
        }
        for t in THRESHOLDS:
            out_row[f"inside_at_{t:.2f}"] = int(ar >= t)
        out_rows.append(out_row)

    # Per-task CSV
    out_dir = here / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    per_task_path = out_dir / "threshold_sensitivity_per_task.csv"
    with per_task_path.open("w", newline="") as fh:
        fieldnames = list(out_rows[0].keys())
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    # Summary: both "all rows" and "unique tasks" (exclude 4-bit variant)
    def summarize(rows_subset: list[dict[str, object]]) -> dict[str, object]:
        summary: dict[str, object] = {
            "n_rows": len(rows_subset),
            "by_threshold": {},
            "by_bucket": {},
        }
        for t in THRESHOLDS:
            inside = sum(r[f"inside_at_{t:.2f}"] for r in rows_subset)
            summary["by_threshold"][f"{t:.2f}"] = {
                "inside": inside,
                "outside": len(rows_subset) - inside,
                "percent_inside": round(inside / len(rows_subset), 4),
            }
        # bucket breakdown
        buckets: dict[str, list[dict[str, object]]] = {}
        for r in rows_subset:
            b = bucket(r["axis_sum"])
            buckets.setdefault(b, []).append(r)
        for b, subset in buckets.items():
            entry: dict[str, object] = {"n": len(subset), "by_threshold": {}}
            for t in THRESHOLDS:
                inside = sum(r[f"inside_at_{t:.2f}"] for r in subset)
                entry["by_threshold"][f"{t:.2f}"] = {
                    "inside": inside,
                    "outside": len(subset) - inside,
                }
            summary["by_bucket"][b] = entry
        return summary

    all_rows = out_rows
    unique_rows = [r for r in out_rows if r["is_variant"] == "0"]
    symmetric_rows = [
        r for r in unique_rows if r["adaptation_symmetry"] == "symmetric"
    ]
    slm_favored_rows = [
        r for r in unique_rows if r["adaptation_symmetry"] == "slm_favored"
    ]

    summary = {
        "all_rows": summarize(all_rows),
        "unique_tasks_excl_variants": summarize(unique_rows),
        "low_axis_subset_unique_tasks_axis_sum_le_5": summarize(
            [
                r
                for r in unique_rows
                if r["axis_sum"] != ""
                and int(r["axis_sum"]) <= 5
            ]
        ),
        "high_axis_subset_unique_tasks_axis_sum_ge_6": summarize(
            [
                r
                for r in unique_rows
                if r["axis_sum"] != ""
                and int(r["axis_sum"]) >= 6
            ]
        ),
        "symmetric_only_unique_tasks": summarize(symmetric_rows),
        "slm_favored_only_unique_tasks": summarize(slm_favored_rows),
    }

    (out_dir / "threshold_sensitivity_summary.json").write_text(
        json.dumps(summary, indent=2)
    )

    # Also print a compact human-readable block
    def fmt_block(name: str, block: dict[str, object]) -> list[str]:
        lines = [f"== {name} (n={block['n_rows']}) =="]
        for t in THRESHOLDS:
            s = block["by_threshold"][f"{t:.2f}"]
            lines.append(
                f"  AR >= {t:.2f}: inside={s['inside']}, outside={s['outside']} "
                f"({s['percent_inside']*100:.1f}% inside)"
            )
        return lines

    out_lines = []
    out_lines += fmt_block("All rows", summary["all_rows"])
    out_lines += fmt_block(
        "Unique tasks (excl. 4-bit variant)", summary["unique_tasks_excl_variants"]
    )
    out_lines += fmt_block(
        "Unique tasks, axis sum <= 5",
        summary["low_axis_subset_unique_tasks_axis_sum_le_5"],
    )
    out_lines += fmt_block(
        "Unique tasks, axis sum >= 6",
        summary["high_axis_subset_unique_tasks_axis_sum_ge_6"],
    )
    out_lines += fmt_block(
        "Unique tasks, symmetric adaptation only",
        summary["symmetric_only_unique_tasks"],
    )
    out_lines += fmt_block(
        "Unique tasks, SLM-favored adaptation only",
        summary["slm_favored_only_unique_tasks"],
    )
    text = "\n".join(out_lines)
    (out_dir / "threshold_sensitivity_summary.txt").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
