# FIT-SLM-HC Supplementary Analysis (aug28 revision)

Data, scripts, and outputs backing the quantitative claims in the aug28
revision of the manuscript (`../main_updated_august28_26.tex`, in
preparation; revision plan and change log in `../revision_plan.md` and
`../CHANGES_aug28.md`). This directory supersedes
`../../analysis/` (the April/August-16 version); the earlier directory is
kept untouched as the historical record for the published drafts.

## What changed from the previous analysis directory

- `data/tasks_master.csv` corrected against the primary sources:
  T07 Pathology IE reference score 98 -> 97 (AR 0.93 -> 0.94) and
  T08 4-bit variant SLM score 71 -> 69 (AR 0.72 -> 0.71). The denominator
  choice (97, from "over 97%" in the source's running text) is decision D1
  in `../CHANGES_aug28.md`. Envelope verdicts are unchanged at all three
  thresholds under either denominator.
- The **descriptive presentation is now primary** (decision D3):
  `descriptives.py` leads; the Fisher / odds-ratio / Cochran-Armitage
  machinery in `axis_trend_test.py` is retained but relabeled
  APPENDIX / EXPLORATORY, and its post-hoc power calculation was removed
  (the manuscript dropped power figures in April 2026; the outputs no
  longer re-introduce them).
- Two new scripts answer the August 2026 peer review directly:
  `sensitivity_suite.py` (findings F2-F5) and `rater_drift.py` (F2, F10).

## Blinding status of the two scoring passes (important)

Both rater files were produced by the manuscript author.

- `rater1_scores.csv` - the published pass used in Table 2. It was
  assigned **with AR values visible** (not outcome-blind).
- `rater2_scores.csv` - a delayed re-read of the task descriptions
  **without reference to the original scores or AR values** (AR-blind).

The kappa figures therefore measure one rater's consistency across
sittings, not inter-rater reliability, and all eight pass-1 -> pass-2
disagreements moved scores upward (see `rater_drift` outputs). A blinded
multi-annotator study remains future work.

## Layout

```
analysis/
  data/
    tasks_master.csv          # Table 2 rows with (r,k,o), AR, LE, metric,
                              #   adaptation_symmetry; aug28 corrections applied
    rater1_scores.csv         # published axis scores (pass 1, not AR-blind)
    rater2_scores.csv         # delayed AR-blind re-score (pass 2)
  scripts/
    descriptives.py           # PRIMARY: mean/median/range AR and inside-counts
                              #   by axis sum and per axis (r, k); o coverage
    sensitivity_suite.py      # pass-2 rescore; leave-one-study-out; one-task-
                              #   per-study enumeration; drop-sum-7; MedS-excluded
    rater_drift.py            # direction of scoring disagreements; exact sign
                              #   tests; Bowker marginal homogeneity; band movers
    threshold_sensitivity.py  # envelope verdicts at AR 0.80/0.90/0.95,
                              #   stratified by adaptation_symmetry (unchanged)
    compute_irr.py            # percent agreement + kappa per axis (benchmark
                              #   gloss removed; see rater_drift for direction)
    axis_trend_test.py        # APPENDIX/EXPLORATORY: Fisher exact + Cochran-
                              #   Armitage + Woolf OR CI (power removed)
  outputs/                    # regenerated artifacts of all six scripts
```

## Reproducing the results

Python 3.10+; no third-party dependencies (pure stdlib).

```
cd manuscript_narrativetutorial/august_2026/healthcare_specific/aug28
python3 analysis/scripts/descriptives.py
python3 analysis/scripts/sensitivity_suite.py
python3 analysis/scripts/rater_drift.py
python3 analysis/scripts/threshold_sensitivity.py
python3 analysis/scripts/compute_irr.py
python3 analysis/scripts/axis_trend_test.py
```

Each script prints to stdout and writes into `analysis/outputs/`.

## Key facts the manuscript's Section 3 must match

- 22 unique tasks (23 rows; T08 is a quantization variant of T07), 21
  axis-scored (the composite T21 has no single axis profile), 18 with
  axis sum <= 5, of which 16 reach AR >= 0.90 and 13 exceed 1.0.
- Mean AR by axis sum (pass-1 scores): 1.155 / 1.031 / 1.147 / 1.050 /
  0.790 for sums 3/4/5/6/7 - flat and non-monotonic across 3-6, dropping
  only at 7 (two tasks, both open-domain exam QA).
- The 2x2 association (OR 16.0, Fisher p 0.080) collapses under the
  AR-blind pass-2 scores (OR 3.25, p 0.54); the Cochran-Armitage trend
  survives pass 2 (p 0.028) but vanishes when the two axis-sum-7 tasks
  are removed (z -0.42, p 0.68). Fisher p exceeds 0.05 in every
  leave-one-study-out subset.
- Scoring drift: 8 of 8 disagreements upward (exact sign test p 0.008);
  three inside-envelope tasks cross the 5/6 band boundary between passes.
- Output-structure coverage is 20/1/0 across levels 1/2/3: the o axis is
  untested by this snapshot.

Any change to `data/` requires re-running all six scripts and reconciling
the manuscript's quantitative claims against the regenerated outputs.
