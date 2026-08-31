# FIT-SLM-HC

**A Task–Technology Fit Framework for Identifying Tasks Suited to Small
Language Models in Healthcare** — publication repository.

FIT-SLM-HC scores a clinical task on three ordinal axes (Reasoning
Complexity, Knowledge Boundedness, Output Structure) and evaluates whether a
locally deployed small language model can stand in for a cloud LLM using two
relative metrics — Accuracy Ratio (AR) and Latency Efficiency (LE) — against
a named reference model, plus an absolute latency target. The framework is
model-agnostic: it certifies a measurement procedure, not any particular
model.

## Try the decision tool

**https://hantswilliams.github.io/fit-slm-hc/** — score a task, enter your
benchmark numbers, and get an envelope verdict against adjustable governance
thresholds. Runs entirely client-side; no data leaves the browser.

## Citing

Preprint: Williams H. *FIT-SLM-HC: A Task–Technology Fit Framework for
Identifying Tasks Suited to Small Language Models in Healthcare.* JMIR
Preprints. <!-- DOI added upon deposit -->

Machine-readable citation metadata: [`CITATION.cff`](CITATION.cff).

## Repository layout

```
manuscript/        LaTeX source (main.tex), references.bib, compiled main.pdf,
                   figures + the scripts that generate them, verify_bib.py
analysis/          Everything behind Section 3 of the paper:
  data/            tasks_master.csv (Table 5 rows), both axis-scoring passes
  scripts/         six pure-stdlib Python scripts (descriptives, sensitivity
                   suite, rater drift, threshold sensitivity, agreement,
                   exploratory trend tests)
  outputs/         regenerated artifacts of all six scripts
docs/              the decision tool (static HTML/JS, served via GitHub Pages)
```

## Reproducing the analyses

Python 3.10+, no third-party dependencies:

```bash
python3 analysis/scripts/descriptives.py
python3 analysis/scripts/sensitivity_suite.py
python3 analysis/scripts/rater_drift.py
python3 analysis/scripts/threshold_sensitivity.py
python3 analysis/scripts/compute_irr.py
python3 analysis/scripts/axis_trend_test.py
```

Every quantitative claim in the manuscript reconciles against
`analysis/outputs/`; see `analysis/README.md` for what each analysis does
and does not show (including the blinding status of the two scoring passes).

## Building the manuscript

```bash
cd manuscript
latexmk -pdf main.tex        # or: tectonic main.tex
```

Figures are committed; to regenerate them (matplotlib required):

```bash
cd manuscript/figures && python3 figure1_schematic.py && python3 figure2_scatter.py
```

`manuscript/verify_bib.py` checks every DOI/arXiv entry in `references.bib`
against Crossref/arXiv (network required).

`manuscript/main.docx` is a Word working copy for tracked-changes review,
generated from the LaTeX source (math rendered as plain text; IEEE-numbered
citations). The LaTeX source and `main.pdf` are canonical; edits accepted in
the Word copy should be carried back into `main.tex`.

## License

Code and data in this repository are released under the [MIT License](LICENSE).
The manuscript text, compiled PDF, and figures (`manuscript/`) are
© 2026 Hants Williams; the preprint is distributed via JMIR Preprints under
its terms.

## Additional materials

Earlier drafts and additional exploratory materials from the framework's
development are held in a separate private working repository and are
available from the author on reasonable request
(hants.williams@stonybrook.edu).
