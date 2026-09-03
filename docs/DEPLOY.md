# Deploying the FIT-SLM-HC Decision Tool to GitHub Pages

> **Intended live URL:** <https://hantswilliams.github.io/fit-slm-hc/>
>
> The tool lives in `docs/` on `main` and is published with GitHub Pages'
> "deploy from a branch" mode. The sections below cover that setup, an
> Actions-based alternative, custom domains, and local preview.

This folder (`docs/`) is a pure static site. It consists of four files:

- `index.html` — narrative content and form markup
- `style.css`
- `app.js` — scoring, AR/LE computation, verdict logic, charts
- `data.js` — the 25 task rows shown in the reference table and scatter
  plot (23 extended-table rows from Table 5 of the manuscript plus 2
  vignette-only rows), band explanations, and contextual notes

There is no build step, no server, no package manager, and no external
dependencies at runtime. Any HTTP server that can serve static files
(including GitHub Pages) can host it.

---

## Option 1: `/docs` folder on `main` (current setup, recommended)

This is the simplest mode and matches how the repository is laid out.

1. Push the repository to GitHub as `hantswilliams/fit-slm-hc` (the README,
   `CITATION.cff`, and the tool's footer all point at that name).
2. Go to **Settings → Pages**.
3. Under **Build and deployment → Source**, select **Deploy from a branch**.
4. Select branch `main`, folder `/docs`, and click **Save**.

The site becomes available at `https://hantswilliams.github.io/fit-slm-hc/`
within a minute or two. Every push to `main` that touches `docs/` republishes
it automatically; no copying or duplication is needed.

GitHub Pages runs Jekyll on branch deploys by default. This site does not use
Jekyll and has no files Jekyll would mangle (nothing starts with an
underscore), so no `.nojekyll` file is required. Add one to `docs/` only if
you later introduce such files.

---

## Option 2: GitHub Actions workflow

Use this if you would rather publish through Actions (for example, to add a
pre-deploy check that `data.js` still matches
`analysis/data/tasks_master.csv`).

### 1. Enable GitHub Pages with "GitHub Actions" as the source

1. Go to **Settings → Pages**.
2. Under **Build and deployment → Source**, select **GitHub Actions**.

### 2. Add a workflow file

Create `.github/workflows/deploy-pages.yml` at the repo root:

```yaml
name: Deploy FIT-SLM-HC tool to GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - "docs/**"
      - ".github/workflows/deploy-pages.yml"
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Pages
        uses: actions/configure-pages@v5

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: docs

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### 3. Push and wait

The workflow runs on any change under `docs/`. The page URL is printed in the
Actions run summary.

---

## Custom domain (optional)

If you want to serve the tool from your own domain (for example
`fit-slm-hc.example.edu`):

1. In **Settings → Pages → Custom domain**, enter the domain and save.
2. GitHub writes a `CNAME` file into the directory serving the site. With
   Option 1 that is `docs/`; commit it so it is not lost. With Option 2, add
   a `CNAME` file containing only the domain to `docs/` so the workflow
   uploads it.
3. Configure DNS at your registrar:
   - For an apex domain (`example.edu`), add four `A` records pointing to
     GitHub's Pages IPs: `185.199.108.153`, `185.199.109.153`,
     `185.199.110.153`, `185.199.111.153`.
   - For a subdomain (`fit-slm-hc.example.edu`), add a `CNAME` record
     pointing to `hantswilliams.github.io`.
4. Wait for DNS propagation, then tick **Enforce HTTPS** once the certificate
   is issued.

---

## Local preview before deploying

From `docs/`:

```bash
# Python 3 (no install needed)
python3 -m http.server 8000
# then open http://localhost:8000 in a browser
```

or

```bash
# Node (if installed)
npx serve .
```

Opening `index.html` directly via `file://` works in most browsers, but
relative-path behavior is only guaranteed under an HTTP server.

---

## What the deployed site does and does not do

- It runs entirely in the browser. No data entered into the form leaves the
  user's machine.
- It has no backend, no database, no telemetry, and no analytics.
- It does not claim to replace full benchmarking, calibration, or safety
  assessment, and the in-page disclaimer says so. If the tool is embedded in
  institutional or clinical workflows, that disclaimer should remain visible.

---

## Keeping the tool aligned with the manuscript

All tabular content shown in the UI is driven by `data.js` (task rows, band
explanations, contextual notes). Narrative content is in `index.html`, and
behavior is in `app.js`.

After editing the manuscript or the analysis data, spot-check:

- Every row in `MANUSCRIPT_TASKS` (`data.js`) matches the corresponding row
  in `analysis/data/tasks_master.csv` and Table 5 of `manuscript/main.tex`
  (scores, AR, LE, envelope verdict).
- Task and study counts quoted in `index.html` (the "About" panel and the
  latency note) and in `BAND_EXPLANATIONS` / `CONTEXTUAL_NOTES` match the
  manuscript's current numbers.
- The citation block in the footer of `index.html` matches `CITATION.cff`
  and the current citation of record (add the DOI once the preprint is
  deposited).
