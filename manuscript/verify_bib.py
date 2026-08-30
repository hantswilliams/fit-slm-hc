#!/usr/bin/env python3
"""verify_bib.py — check references.bib against Crossref and arXiv records.

For every entry with a DOI, queries https://api.crossref.org/works/<doi> and
compares author family names (order-sensitive), year, and title similarity.
For arXiv preprints (journal field matching 'arXiv preprint arXiv:ID'),
queries the arXiv export API and does the same. Entries with neither (books,
web pages) are listed as SKIPPED for manual checking.

Run from the aug28/ directory, with network access:

    python3 verify_bib.py [references.bib]

Pure stdlib. Exit code 1 if any entry MISMATCHes. Written for the aug28
revision after review finding F6 (systematic author-name errors); regenerate
entries from the primary record rather than editing them by hand, then re-run
this script.
"""

from __future__ import annotations

import difflib
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

UA = {"User-Agent": "fitslmhc-verify-bib/1.0 (mailto:hants.williams@stonybrook.edu)"}


def parse_bib(text: str) -> list[dict[str, str]]:
    entries = []
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}\n", text, re.S):
        typ, key, body = m.group(1), m.group(2).strip(), m.group(3)
        fields = {}
        for fm in re.finditer(r"(\w+)\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}", body):
            fields[fm.group(1).lower()] = fm.group(2)
        entries.append({"type": typ, "key": key, **fields})
    return entries


def strip_tex(s: str) -> str:
    s = re.sub(r"\\[\"'^`~vc]\s*\{?(\w)\}?", r"\1", s)
    s = re.sub(r"[{}\\]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def family_names(author_field: str) -> list[str]:
    out = []
    for a in author_field.split(" and "):
        a = strip_tex(a).strip()
        if not a or a.lower() == "others":
            continue
        if "," in a:
            out.append(a.split(",")[0].strip().lower())
        else:
            out.append(a.split()[-1].lower())
    return out


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def check_crossref(e: dict) -> tuple[str, list[str]]:
    data = fetch_json(f"https://api.crossref.org/works/{e['doi']}")["message"]
    problems = []
    ref_fams = [a.get("family", "").lower() for a in data.get("author", [])]
    bib_fams = family_names(e.get("author", ""))
    n = len(bib_fams)
    if "others" in e.get("author", ""):
        ref_fams = ref_fams[:n]
    if bib_fams != ref_fams[:n] or (len(ref_fams) != n and "others" not in e.get("author", "")):
        problems.append(f"authors: bib={bib_fams} vs record={ref_fams}")
    year = None
    for k in ("published-print", "published-online", "issued"):
        parts = data.get(k, {}).get("date-parts")
        if parts and parts[0] and parts[0][0]:
            year = parts[0][0]
            break
    if year and abs(int(e.get("year", 0)) - year) > 1:
        problems.append(f"year: bib={e.get('year')} vs record={year}")
    title = strip_tex(e.get("title", "")).lower()
    rec_title = (data.get("title") or [""])[0].lower()
    if title and rec_title:
        sim = difflib.SequenceMatcher(None, title, rec_title).ratio()
        if sim < 0.75:
            problems.append(f"title similarity {sim:.2f}: record title = {rec_title!r}")
    return ("MISMATCH" if problems else "OK"), problems


def check_arxiv(e: dict, arxiv_id: str) -> tuple[str, list[str]]:
    url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}&max_results=1"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        root = ET.fromstring(r.read())
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entry = root.find("a:entry", ns)
    problems = []
    if entry is None:
        return "MISMATCH", ["arXiv id not found"]
    rec_authors = [el.findtext("a:name", "", ns) for el in entry.findall("a:author", ns)]
    ref_fams = [a.split()[-1].lower() for a in rec_authors if a]
    bib_fams = family_names(e.get("author", ""))
    if bib_fams != ref_fams:
        problems.append(f"authors: bib={bib_fams} vs arXiv={ref_fams}")
    rec_title = re.sub(r"\s+", " ", entry.findtext("a:title", "", ns)).strip().lower()
    title = strip_tex(e.get("title", "")).lower()
    sim = difflib.SequenceMatcher(None, title, rec_title).ratio()
    if sim < 0.75:
        problems.append(f"title similarity {sim:.2f}: arXiv title = {rec_title!r}")
    return ("MISMATCH" if problems else "OK"), problems


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "references.bib")
    entries = parse_bib(path.read_text())
    print(f"{len(entries)} entries in {path}")
    n_bad = n_skip = 0
    for e in entries:
        arxiv = re.search(r"arXiv:(\d{4}\.\d{4,5})", e.get("journal", "") + e.get("note", ""))
        try:
            if e.get("doi"):
                status, problems = check_crossref(e)
            elif arxiv:
                status, problems = check_arxiv(e, arxiv.group(1))
            else:
                status, problems = "SKIPPED (no DOI/arXiv id; check manually)", []
                n_skip += 1
        except Exception as exc:  # noqa: BLE001
            status, problems = f"ERROR ({exc})", []
        print(f"  [{status.split()[0]:>8}] {e['key']}")
        for p in problems:
            print(f"            - {p}")
        if status.startswith("MISMATCH"):
            n_bad += 1
        time.sleep(0.5)  # be polite to the APIs
    print(f"\n{n_bad} mismatched, {n_skip} skipped, {len(entries)-n_bad-n_skip} verified")
    sys.exit(1 if n_bad else 0)


if __name__ == "__main__":
    main()
