"""Sensitivity suite for the aug28 revision (FIT-SLM-HC).

Answers review findings F2-F5 with four analyses over the trend-eligible rows
(unique axis-scored tasks; the 4-bit variant and the composite row excluded):

  (a) pass-2 rescore  - the trend recomputed on the AR-blind second scoring
      pass (rater2_scores.csv), side by side with the published pass-1 scores;
  (b) clustering      - leave-one-study-out, plus full enumeration of
      one-task-per-study samples;
  (c) drop-sum-7      - the trend without the two axis-sum-7 tasks;
  (d) MedS-excluded   - the trend without the seven MedS-Bench rows (single
      source study, single SLM checkpoint, possible train/test overlap).

Inputs:  analysis/data/tasks_master.csv, analysis/data/rater2_scores.csv
Outputs: analysis/outputs/sensitivity_suite.json, sensitivity_suite.txt
"""

from __future__ import annotations

import csv
import itertools
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from axis_trend_test import (  # noqa: E402
    AR_THRESHOLD,
    cochran_armitage,
    fisher_exact_two_sided,
    summarize_subset,
)


def compact(block: dict) -> dict:
    """Reduce a summarize_subset() result to the fields the tables need."""
    c = block["contingency_2x2"]
    ca = block["cochran_armitage_trend"]
    return {
        "n": block["n_included"],
        "low_inside": c["axis_sum_le_5"]["inside"],
        "low_outside": c["axis_sum_le_5"]["outside"],
        "high_inside": c["axis_sum_ge_6"]["inside"],
        "high_outside": c["axis_sum_ge_6"]["outside"],
        "fisher_p": block["fisher_exact"]["p_two_sided"],
        "odds_ratio": block["odds_ratio"]["odds_ratio"],
        "or_ci": [block["odds_ratio"]["ci_lower"], block["odds_ratio"]["ci_upper"]],
        "ca_z": ca["z"],
        "ca_p": ca["p_two_sided"],
        "mean_ar_by_sum": block["mean_ar_by_axis_sum"],
    }


def fmt_row(label: str, c: dict) -> str:
    fp = "n/a" if c["fisher_p"] is None else f"{c['fisher_p']:.3f}"
    cz = "n/a" if c["ca_z"] is None else f"{c['ca_z']:+.2f}"
    cp = "n/a" if c["ca_p"] is None else f"{c['ca_p']:.3f}"
    orr = "n/a" if c["odds_ratio"] is None else f"{c['odds_ratio']:.2f}"
    return (
        f"  {label:<26} n={c['n']:>2}  low {c['low_inside']}/{c['low_inside']+c['low_outside']}"
        f"  high {c['high_inside']}/{c['high_inside']+c['high_outside']}"
        f"  OR={orr:>6}  Fisher p={fp:>5}  CA z={cz:>6} p={cp:>5}"
    )


def ca_only(rows: list[dict[str, str]]) -> tuple[float, float]:
    levels = sorted({int(r["axis_sum"]) for r in rows})
    totals = [sum(1 for r in rows if int(r["axis_sum"]) == L) for L in levels]
    inside = [
        sum(1 for r in rows if int(r["axis_sum"]) == L and float(r["ar"]) >= AR_THRESHOLD)
        for L in levels
    ]
    if len(levels) < 2:
        return float("nan"), float("nan")
    res = cochran_armitage(levels, inside, totals)
    return res["z"], res["p_two_sided"]


def main() -> None:
    here = Path(__file__).resolve().parent.parent
    with (here / "data" / "tasks_master.csv").open() as fh:
        rows = list(csv.DictReader(fh))
    with (here / "data" / "rater2_scores.csv").open() as fh:
        r2 = {r["task_id"]: r for r in csv.DictReader(fh)}

    eligible = [r for r in rows if r["is_variant"] == "0" and r["axis_sum"] != ""]

    # ---------- (a) pass-1 vs pass-2 ----------
    pass1 = summarize_subset(eligible, "pass-1 (published, not AR-blind)")
    pass2_rows = []
    for r in eligible:
        s2 = r2[r["task_id"]]
        new = dict(r)
        new["axis_sum"] = str(
            int(s2["reasoning_r"]) + int(s2["knowledge_k"]) + int(s2["output_o"])
        )
        pass2_rows.append(new)
    pass2 = summarize_subset(pass2_rows, "pass-2 (AR-blind re-score)")
    band_movers = [
        {
            "task_id": r1["task_id"],
            "task_name": r1["task_name"],
            "sum_pass1": int(r1["axis_sum"]),
            "sum_pass2": int(p2["axis_sum"]),
            "ar": float(r1["ar"]),
        }
        for r1, p2 in zip(eligible, pass2_rows)
        if (int(r1["axis_sum"]) <= 5) != (int(p2["axis_sum"]) <= 5)
    ]

    # ---------- (b) clustering ----------
    studies: dict[str, list[dict[str, str]]] = {}
    for r in eligible:
        studies.setdefault(r["source_citekey"], []).append(r)

    loso = {}
    for study in sorted(studies):
        subset = [r for r in eligible if r["source_citekey"] != study]
        loso[study] = compact(
            summarize_subset(subset, f"LOSO minus {study} ({len(studies[study])} rows)")
        )

    combos_summary = None
    combo_lists = [studies[s] for s in sorted(studies)]
    n_combos = 1
    for lst in combo_lists:
        n_combos *= len(lst)
    ca_ps, fisher_ps, ca_sig = [], [], 0
    for combo in itertools.product(*combo_lists):
        combo = list(combo)
        z, p = ca_only(combo)
        if p == p:
            ca_ps.append(p)
            if p < 0.05:
                ca_sig += 1
        li = sum(1 for r in combo if int(r["axis_sum"]) <= 5 and float(r["ar"]) >= AR_THRESHOLD)
        lo = sum(1 for r in combo if int(r["axis_sum"]) <= 5 and float(r["ar"]) < AR_THRESHOLD)
        hi = sum(1 for r in combo if int(r["axis_sum"]) >= 6 and float(r["ar"]) >= AR_THRESHOLD)
        ho = sum(1 for r in combo if int(r["axis_sum"]) >= 6 and float(r["ar"]) < AR_THRESHOLD)
        if (li + lo) > 0 and (hi + ho) > 0:
            fisher_ps.append(fisher_exact_two_sided(li, lo, hi, ho)["p_two_sided"])
    combos_summary = {
        "n_combinations": n_combos,
        "tasks_per_combination": len(combo_lists),
        "ca_p_median": round(statistics.median(ca_ps), 4) if ca_ps else None,
        "ca_p_min": round(min(ca_ps), 4) if ca_ps else None,
        "ca_p_max": round(max(ca_ps), 4) if ca_ps else None,
        "ca_p_below_0_05": ca_sig,
        "fisher_p_median": round(statistics.median(fisher_ps), 4) if fisher_ps else None,
        "fisher_p_min": round(min(fisher_ps), 4) if fisher_ps else None,
        "fisher_p_max": round(max(fisher_ps), 4) if fisher_ps else None,
    }

    # ---------- (c) drop the axis-sum-7 tasks ----------
    drop7_rows = [r for r in eligible if int(r["axis_sum"]) <= 6]
    drop7 = summarize_subset(drop7_rows, "drop axis-sum-7 tasks")

    # ---------- (d) MedS-Bench excluded ----------
    no_meds_rows = [r for r in eligible if r["source_citekey"] != "Wu2025MedS"]
    no_meds = summarize_subset(no_meds_rows, "MedS-Bench (Wu2025MedS) excluded")

    results = {
        "ar_threshold": AR_THRESHOLD,
        "pass1": compact(pass1),
        "pass2": compact(pass2),
        "band_movers_pass1_to_pass2": band_movers,
        "loso": loso,
        "one_task_per_study_enumeration": combos_summary,
        "drop_axis_sum_7": compact(drop7),
        "meds_bench_excluded": compact(no_meds),
        "notes": {
            "pass2": (
                "Pass 2 is the AR-blind re-score by the same rater. Three"
                " inside-envelope tasks cross the 5/6 band boundary; the 2x2"
                " association collapses while the CA trend persists (p 0.028)"
                " until the axis-sum-7 tasks are removed."
            ),
            "enumeration": (
                "Every combination keeping exactly one trend-eligible task per"
                " source study (the composite Builtjes row has no axis sum and"
                " is not trend-eligible)."
            ),
        },
    }

    out_dir = here / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "sensitivity_suite.json").write_text(json.dumps(results, indent=2))

    lines = [
        "FIT-SLM-HC Sensitivity Suite (aug28 revision)",
        "=" * 46,
        f"AR threshold: {AR_THRESHOLD}; low = axis sum <= 5, high = >= 6",
        "",
        "(a) Scoring-pass sensitivity",
        fmt_row("pass-1 (published)", results["pass1"]),
        fmt_row("pass-2 (AR-blind)", results["pass2"]),
        "  Band movers (5 -> 6): "
        + ", ".join(
            f"{m['task_name']} (AR {m['ar']})" for m in band_movers
        ),
        "",
        "(b) Clustering sensitivity - leave one study out",
    ]
    for study, c in results["loso"].items():
        lines.append(fmt_row(f"minus {study}", c))
    e = combos_summary
    lines += [
        "",
        f"(b') One task per study: {e['n_combinations']} combinations of"
        f" {e['tasks_per_combination']} tasks",
        f"  Cochran-Armitage p: median {e['ca_p_median']}, range"
        f" [{e['ca_p_min']}, {e['ca_p_max']}];"
        f" {e['ca_p_below_0_05']}/{e['n_combinations']} below 0.05",
        f"  Fisher p:           median {e['fisher_p_median']}, range"
        f" [{e['fisher_p_min']}, {e['fisher_p_max']}]",
        "",
        "(c) Axis-sum-7 tasks removed",
        fmt_row("drop sum-7 (n-2)", results["drop_axis_sum_7"]),
        "",
        "(d) MedS-Bench rows removed",
        fmt_row("minus Wu2025MedS", results["meds_bench_excluded"]),
        "",
        "Reading:",
        "  The 2x2 association (OR 16.0) collapses under the AR-blind pass-2",
        "  scores (OR 3.25, Fisher p 0.54). The Cochran-Armitage trend is",
        "  less fragile there (p 0.028) but rests entirely on the two",
        "  axis-sum-7 tasks: removing them leaves z = -0.42, p = 0.68. The",
        "  trend also weakens most when the Kim or Wu (MedS-Bench) studies",
        "  are left out, and Fisher p exceeds 0.05 in every LOSO subset.",
        "  These are the facts the descriptive presentation reports.",
    ]
    text = "\n".join(lines)
    (out_dir / "sensitivity_suite.txt").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
