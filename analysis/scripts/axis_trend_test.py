"""Axis-sum trend test for FIT-SLM-HC envelope verdicts.

Tests whether axis-sum category predicts envelope membership (AR >= 0.90).

Aug 2026 (aug28) revision: relabeled APPENDIX / EXPLORATORY. The post-hoc
power calculation was removed (the manuscript dropped power figures in the
April 2026 revision; the outputs should not re-introduce them). Primary
presentation: descriptives.py, with sensitivity_suite.py and rater_drift.py.
For the April 2026 revision, the script adds:
  - A 95 percent odds-ratio confidence interval on the 2x2 Fisher table
    (computed via Woolf log-OR with Haldane-Anscombe 0.5 continuity
    correction when any cell is zero).
  - A stratified analysis on the 'symmetric' adaptation subset (where SLM
    and reference model adaptations are comparable).
  - A stratified analysis on the 'slm_favored' subset (informative contrast).
  - A sensitivity summary across subsets.

Inputs
------
  analysis/data/tasks_master.csv

Outputs
-------
  analysis/outputs/axis_trend_test.json
  analysis/outputs/axis_trend_test.txt
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

AR_THRESHOLD = 0.90


def log_comb(n: int, k: int) -> float:
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def fisher_exact_two_sided(a: int, b: int, c: int, d: int) -> dict[str, float]:
    """Fisher's exact test for 2x2 table [[a,b],[c,d]]."""
    n = a + b + c + d
    row1 = a + b
    col1 = a + c

    def prob(x: int) -> float:
        if x < 0 or x > min(row1, col1) or (row1 - x) < 0 or (col1 - x) < 0:
            return 0.0
        return math.exp(
            log_comb(col1, x)
            + log_comb(n - col1, row1 - x)
            - log_comb(n, row1)
        )

    x_min = max(0, row1 + col1 - n)
    x_max = min(row1, col1)
    p_obs = prob(a)
    two_sided = 0.0
    one_sided_less = 0.0
    one_sided_greater = 0.0
    for x in range(x_min, x_max + 1):
        p = prob(x)
        if p <= p_obs + 1e-12:
            two_sided += p
        if x <= a:
            one_sided_less += p
        if x >= a:
            one_sided_greater += p
    return {
        "p_two_sided": two_sided,
        "p_one_sided_less": one_sided_less,
        "p_one_sided_greater": one_sided_greater,
    }


def odds_ratio_woolf(a: int, b: int, c: int, d: int) -> dict[str, object]:
    """Woolf log-OR 95% CI with Haldane-Anscombe continuity correction.

    Applies +0.5 to all cells when any cell is zero. The CI is an
    approximation that readers should treat as directional evidence,
    not a calibrated effect size (see notes).
    """
    has_zero = 0 in (a, b, c, d)
    if has_zero:
        a_, b_, c_, d_ = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    else:
        a_, b_, c_, d_ = float(a), float(b), float(c), float(d)
    if c_ == 0 or b_ == 0:
        return {
            "odds_ratio": None,
            "ci_lower": None,
            "ci_upper": None,
            "note": "undefined (zero cell persists even after correction)",
        }
    or_ = (a_ * d_) / (b_ * c_)
    se_log_or = math.sqrt(1 / a_ + 1 / b_ + 1 / c_ + 1 / d_)
    log_or = math.log(or_)
    z = 1.959963984540054  # standard normal 97.5 percentile
    return {
        "odds_ratio": or_,
        "ci_lower": math.exp(log_or - z * se_log_or),
        "ci_upper": math.exp(log_or + z * se_log_or),
        "note": "Woolf 95% CI with Haldane-Anscombe 0.5 correction"
        if has_zero
        else "Woolf 95% CI (uncorrected)",
    }


def gammainc_upper(a_shape: float, z: float) -> float:
    """Regularized upper incomplete gamma Q(a, z)."""
    if z <= 0:
        return 1.0
    if z < a_shape + 1:
        term = 1.0 / a_shape
        s = term
        for k in range(1, 300):
            term *= z / (a_shape + k)
            s += term
            if abs(term) < 1e-14 * abs(s):
                break
        lower = s * math.exp(-z + a_shape * math.log(z) - math.lgamma(a_shape))
        return max(0.0, 1.0 - lower)
    else:
        b = z + 1 - a_shape
        c_ = 1e300
        d_ = 1.0 / b
        h_cf = d_
        for i in range(1, 300):
            an = -i * (i - a_shape)
            b += 2
            d_ = an * d_ + b
            if abs(d_) < 1e-300:
                d_ = 1e-300
            c_ = b + an / c_
            if abs(c_) < 1e-300:
                c_ = 1e-300
            d_ = 1.0 / d_
            delta = d_ * c_
            h_cf *= delta
            if abs(delta - 1) < 1e-14:
                break
        return h_cf * math.exp(-z + a_shape * math.log(z) - math.lgamma(a_shape))



def cochran_armitage(levels: list[int], inside: list[int], n: list[int]) -> dict[str, float]:
    """Cochran-Armitage trend test across ordered levels."""
    total_n = sum(n)
    total_inside = sum(inside)
    if total_n == 0 or total_inside == 0 or total_inside == total_n:
        return {"z": float("nan"), "p_two_sided": float("nan")}
    p_bar = total_inside / total_n
    num = sum(
        levels[i] * (inside[i] - n[i] * p_bar) for i in range(len(levels))
    )
    var = (
        p_bar
        * (1 - p_bar)
        * (
            total_n * sum(n[i] * levels[i] ** 2 for i in range(len(levels)))
            - (sum(n[i] * levels[i] for i in range(len(levels)))) ** 2
        )
        / total_n
    )
    if var <= 0:
        return {"z": float("nan"), "p_two_sided": float("nan")}
    z = num / math.sqrt(var)
    p = math.erfc(abs(z) / math.sqrt(2))
    return {"z": z, "p_two_sided": p}


def summarize_subset(rows: list[dict[str, str]], label: str) -> dict[str, object]:
    """Run Fisher + Cochran-Armitage + Woolf OR CI on a row subset."""
    low_inside = sum(
        1 for r in rows if int(r["axis_sum"]) <= 5 and float(r["ar"]) >= AR_THRESHOLD
    )
    low_outside = sum(
        1 for r in rows if int(r["axis_sum"]) <= 5 and float(r["ar"]) < AR_THRESHOLD
    )
    high_inside = sum(
        1 for r in rows if int(r["axis_sum"]) >= 6 and float(r["ar"]) >= AR_THRESHOLD
    )
    high_outside = sum(
        1 for r in rows if int(r["axis_sum"]) >= 6 and float(r["ar"]) < AR_THRESHOLD
    )

    fisher_available = (
        (low_inside + low_outside) > 0 and (high_inside + high_outside) > 0
    )
    if fisher_available:
        fisher = fisher_exact_two_sided(
            low_inside, low_outside, high_inside, high_outside
        )
        odds = odds_ratio_woolf(low_inside, low_outside, high_inside, high_outside)
    else:
        fisher = {
            "p_two_sided": None,
            "p_one_sided_less": None,
            "p_one_sided_greater": None,
        }
        odds = {
            "odds_ratio": None,
            "ci_lower": None,
            "ci_upper": None,
            "note": "undefined: one row of the 2x2 is empty in this subset",
        }

    levels = sorted({int(r["axis_sum"]) for r in rows})
    level_totals = [sum(1 for r in rows if int(r["axis_sum"]) == L) for L in levels]
    level_inside = [
        sum(
            1
            for r in rows
            if int(r["axis_sum"]) == L and float(r["ar"]) >= AR_THRESHOLD
        )
        for L in levels
    ]
    if len(levels) >= 2:
        ca = cochran_armitage(levels, level_inside, level_totals)
    else:
        ca = {"z": float("nan"), "p_two_sided": float("nan")}

    mean_ar_by_level = {
        L: round(
            sum(float(r["ar"]) for r in rows if int(r["axis_sum"]) == L)
            / max(1, sum(1 for r in rows if int(r["axis_sum"]) == L)),
            4,
        )
        for L in levels
    }

    def rnd(v):
        if isinstance(v, float):
            if v != v or v in (float("inf"), float("-inf")):
                return None
            return round(v, 4)
        return v

    return {
        "label": label,
        "n_included": len(rows),
        "contingency_2x2": {
            "axis_sum_le_5": {"inside": low_inside, "outside": low_outside},
            "axis_sum_ge_6": {"inside": high_inside, "outside": high_outside},
        },
        "fisher_exact": {
            k: (round(v, 6) if isinstance(v, float) else v)
            for k, v in fisher.items()
        },
        "odds_ratio": {k: rnd(v) for k, v in odds.items()},
        "cochran_armitage_trend": {
            "levels": levels,
            "totals": level_totals,
            "inside_counts": level_inside,
            "z": round(ca["z"], 4) if ca["z"] == ca["z"] else None,
            "p_two_sided": round(ca["p_two_sided"], 6)
            if ca["p_two_sided"] == ca["p_two_sided"]
            else None,
        },
        "mean_ar_by_axis_sum": mean_ar_by_level,
    }


def main() -> None:
    here = Path(__file__).resolve().parent.parent
    rows: list[dict[str, str]] = []
    with (here / "data" / "tasks_master.csv").open() as fh:
        rows = list(csv.DictReader(fh))

    # Trend-eligible: scored rows, excluding the composite (no axis sum) and
    # the 4-bit quantization variant.
    trend_eligible = [
        r
        for r in rows
        if r["is_variant"] == "0" and r["axis_sum"] != ""
    ]

    full_results = summarize_subset(trend_eligible, "full (excl. variant + composite)")
    symmetric_only = [
        r for r in trend_eligible if r.get("adaptation_symmetry") == "symmetric"
    ]
    symmetric_results = summarize_subset(symmetric_only, "symmetric adaptation only")
    slm_favored_only = [
        r for r in trend_eligible if r.get("adaptation_symmetry") == "slm_favored"
    ]
    slm_favored_results = summarize_subset(slm_favored_only, "SLM-favored adaptation only")

    stratum_counts: dict[str, dict[str, int]] = {}
    for r in rows:
        s = r.get("adaptation_symmetry", "unknown") or "unknown"
        stratum_counts.setdefault(s, {"rows": 0, "trend_eligible": 0})
        stratum_counts[s]["rows"] += 1
    for r in trend_eligible:
        s = r.get("adaptation_symmetry", "unknown") or "unknown"
        stratum_counts[s]["trend_eligible"] += 1

    results = {
        "ar_threshold": AR_THRESHOLD,
        "stratum_composition": stratum_counts,
        "full": full_results,
        "symmetric_only": symmetric_results,
        "slm_favored_only": slm_favored_results,
        "notes": {
            "adaptation_symmetry_classification": (
                "Assigned per row based on model naming and source-paper context."
                " 'slm_favored' rows are those where the SLM was task fine-tuned,"
                " LoRA-adapted, or domain-instruction-tuned (e.g. MMedIns-Llama3-8B,"
                " RadPhi-3, Meerkat-7B, Zheng-2026 OPT-350M fine-tunes, explicit"
                " LoRA variants) and the reference was a zero-shot cloud LLM."
                " 'symmetric' rows use comparable prompting on both sides, or both"
                " sides are fine-tuned (e.g. Hou-2025 ICD-10 where both Llama-1B"
                " and GPT-4o mini were fine-tuned). Classification is a reviewer-"
                " facing approximation, not a re-reading of each paper's protocol."
            ),
            "odds_ratio_note": (
                "Woolf log-OR 95 percent CI with Haldane-Anscombe 0.5"
                " continuity correction applied when any cell is zero."
                " Point OR and CI are approximate and should be read as"
                " directional evidence, not a calibrated effect size."
            ),
        },
    }

    out_dir = here / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "axis_trend_test.json").write_text(json.dumps(results, indent=2))

    def fmt_block(block: dict[str, object]) -> list[str]:
        c = block["contingency_2x2"]
        low = c["axis_sum_le_5"]
        high = c["axis_sum_ge_6"]
        lines = [
            f"-- {block['label']} (n={block['n_included']}) --",
            f"  axis sum <= 5 : inside={low['inside']}, outside={low['outside']}",
            f"  axis sum >= 6 : inside={high['inside']}, outside={high['outside']}",
        ]
        fe = block["fisher_exact"]
        if fe["p_two_sided"] is not None:
            lines.append(f"  Fisher p (two-sided): {fe['p_two_sided']}")
        else:
            lines.append(
                "  Fisher exact: not computed (one row of the 2x2 is empty)"
            )
        or_block = block["odds_ratio"]
        if or_block["odds_ratio"] is not None:
            ci_low = or_block["ci_lower"]
            ci_high = or_block["ci_upper"]
            ci_str = (
                f" (95% CI {ci_low} to {ci_high})"
                if ci_low is not None and ci_high is not None
                else ""
            )
            lines.append(
                f"  Odds ratio (low vs. high axis inside): {or_block['odds_ratio']}{ci_str}"
            )
            lines.append(f"    [{or_block.get('note','')}]")
        else:
            lines.append(
                f"  Odds ratio: undefined [{or_block.get('note','')}]"
            )
        ca = block["cochran_armitage_trend"]
        lines.append(
            f"  Cochran-Armitage: z={ca['z']}, p(two-sided)={ca['p_two_sided']}"
        )
        lines.append(
            f"  Levels {ca['levels']} totals {ca['totals']} inside {ca['inside_counts']}"
        )
        mar = block["mean_ar_by_axis_sum"]
        lines.append(f"  Mean AR by axis sum: {mar}")
        return lines

    header = [
        "Axis-Sum Trend Test for Envelope Membership (APPENDIX: exploratory)",
        "=" * 46,
        f"AR threshold: {AR_THRESHOLD}",
        "",
        "Stratum composition (all rows):",
    ]
    for s, c in stratum_counts.items():
        header.append(
            f"  {s}: {c['rows']} rows total, {c['trend_eligible']} trend-eligible"
        )
    header.append("")

    out_lines = header
    for key in ("full", "symmetric_only", "slm_favored_only"):
        out_lines += fmt_block(results[key])
        out_lines.append("")

    out_lines.append("Interpretation:")
    out_lines.append(
        "  APPENDIX / EXPLORATORY (aug28 revision). Retained for transparency;"
    )
    out_lines.append(
        "  no longer the primary analysis. Reasons: rows cluster by source"
    )
    out_lines.append(
        "  study (7 of 21 trend-eligible rows share one study and one SLM"
    )
    out_lines.append(
        "  checkpoint); pass-1 axis scores were not assigned blind to AR;"
    )
    out_lines.append(
        "  and the full-sample association is not robust to same-rater"
    )
    out_lines.append(
        "  re-scoring (pass 2) or to removal of the two axis-sum-7 tasks"
    )
    out_lines.append(
        "  (see sensitivity_suite outputs). The symmetric-only stratum still"
    )
    out_lines.append(
        "  lacks high-axis comparisons, so its 2x2 test is not computable."
    )
    out_lines.append(
        "  Primary presentation: descriptives outputs."
    )
    out_lines.append("")

    text = "\n".join(out_lines)
    (out_dir / "axis_trend_test.txt").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
