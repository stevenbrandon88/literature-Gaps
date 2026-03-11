#!/usr/bin/env python3
"""
lit_retry_missing.py
====================
Targeted retry for the 20 files that failed in lit_repo_downloader.py
due to em-dash / long filename URL encoding issues.

Uses GitHub API (tree endpoint) to get exact download URLs rather than
constructing them from filenames.

USAGE:
  python lit_retry_missing.py
  python lit_retry_missing.py --dry-run    # show URLs without downloading
"""

import os
import sys
import time
import argparse
import requests
from pathlib import Path

REPO_USER  = "stevenbrandon88"
REPO_NAME  = "literature-Gaps"
BRANCH     = "main"
BASE       = Path(os.environ.get("LIT_DATA_DIR", "./literature/raw"))

# ── Exact local paths for each missing file ────────────────────────────────
# Format: (stream_folder, local_filename, partial_remote_match)
# partial_remote_match = unique substring to identify the file in the API tree

MISSING = [
    # S01 — 11 PDFs with em-dash filenames
    ("s01", "stream001_mdb_econ_deepread_01.pdf",   "Stream 001 \u2014 MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (1).pdf"),
    ("s01", "stream001_mdb_econ_deepread_02.pdf",   "Stream 001 \u2014 MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (2).pdf"),
    ("s01", "stream001_mdb_econ_deepread_03.pdf",   "Stream 001 \u2014 MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (3).pdf"),
    ("s01", "stream001_mdb_econ_deepread_04.pdf",   "Stream 001 \u2014 MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (4).pdf"),
    ("s01", "stream001_mdb_econ_deepread_05.pdf",   "Stream 001 \u2014 MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (5).pdf"),
    ("s01", "stream001_mdb_econ_deepread_06.pdf",   "Stream 001 \u2014 MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (6).pdf"),
    ("s01", "stream001_mdb_econ_deepread_07.pdf",   "Stream 001 \u2014 MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (7).pdf"),
    ("s01", "stream001_mdb_econ_deepread_08.pdf",   "Stream 001 \u2014 MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (8).pdf"),
    ("s01", "stream001_mdb_econ_deepread_09.pdf",   "Stream 001 \u2014 MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (9).pdf"),
    ("s01", "stream001_mdb_econ_deepread_10.pdf",   "Stream 001 \u2014 MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (10).pdf"),
    ("s01", "stream001_mdb_econ_deepread_11.pdf",   "Stream 001 \u2014 MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (11).pdf"),

    # SYNTHESIS — 2 DOCXs with em-dash filenames
    ("synthesis", "stream001_mdb_econ_deepread_01.docx", "Stream 001 \u2014 MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (1).docx"),
    ("synthesis", "stream001_mdb_econ_deepread_02.docx", "Stream 001 \u2014 MDB Econometrics 7 papers included, 9 excluded 4 Deep Read papers (2).docx"),

    # S12 — Honig 2022
    ("s12", "honig_2022_transparency_20000_projects.pdf",
     "American J Political Sci - 2022 - Honig - When Does Transparency Improve Institutional Performance Evidence from 20 000.pdf"),

    # S15 — Privacy paradox SCA
    ("s15", "sca_privacy_paradox_large_survey.pdf",
     "Understanding the effects of conceptual and analytical choices on finding the privacy paradox A specification curve analysis of large-scale survey .pdf"),

    # S18 — WORKING 107
    ("s18", "WORKING_107_PDF_E33.pdf", "WORKING 107 PDF E33.pdf"),

    # S22 — Transport infrastructure + McArthur
    ("s22", "transport_infrastructure_economic_impact_review.pdf",
     "The economic impact of transport infrastructure a review of project-level vs. aggregate-level evidence.pdf"),
    ("s22", "mcarthur_2023_ukib_financialisation_nationalist.pdf",
     "mcarthur-2023-the-uk-infrastructure-bank-and-the-financialisation-of-public-infrastructures-amidst-nationalist.pdf"),
    ("s22", "mcarthur_2023_ukib_financialisation_nationalist_v2.pdf",
     "mcarthur-2023-the-uk-infrastructure-bank-and-the-financialisation-of-public-infrastructures-amidst-nationalist (1).pdf"),

    # MISC — dissertation .doc
    ("misc", "DISSERTATION_ABDULAZIZ_SHAIB_MOHAMED_FINAL.doc",
     "DISSERTATION - ABDUL-AZIZ SHAIB MOHAMED - FINAL.doc"),
]


def get_tree():
    """Fetch full repo tree from GitHub API."""
    url = f"https://api.github.com/repos/{REPO_USER}/{REPO_NAME}/git/trees/{BRANCH}?recursive=1"
    print(f"  Fetching repo tree from GitHub API...")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "tree" not in data:
        print(f"  ERROR: Unexpected API response: {data.get('message', data)}")
        sys.exit(1)
    return {item["path"]: item for item in data["tree"] if item["type"] == "blob"}


def download_url(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, timeout=120, stream=True)
    r.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in r.iter_content(65536):
            f.write(chunk)
    return dest.stat().st_size


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    tree = get_tree()

    # Build lookup: filename → download_url
    # GitHub API gives us the blob SHA; we construct raw URL from path
    path_to_url = {}
    for path, item in tree.items():
        filename = path.split("/")[-1]  # bare filename (no folder prefix in flat repo)
        raw_url = f"https://raw.githubusercontent.com/{REPO_USER}/{REPO_NAME}/{BRANCH}/{path}"
        path_to_url[filename] = raw_url

    print(f"  Tree loaded: {len(path_to_url)} files in repo\n")

    ok = skipped = failed = 0

    for stream, local_name, remote_name in MISSING:
        dest = BASE / stream / local_name

        if dest.exists() and dest.stat().st_size > 0:
            print(f"  [EXISTS] {local_name}")
            skipped += 1
            continue

        # Look up by exact remote filename
        url = path_to_url.get(remote_name)
        if not url:
            # Try case-insensitive fallback
            remote_lower = remote_name.lower()
            for k, v in path_to_url.items():
                if k.lower() == remote_lower:
                    url = v
                    break

        if not url:
            print(f"  ✗ NOT IN REPO: {remote_name}")
            failed += 1
            continue

        if args.dry_run:
            print(f"  [DRY-RUN] {local_name}")
            print(f"    URL: {url}")
            continue

        print(f"  ↓ {local_name}")
        try:
            size = download_url(url, dest)
            print(f"    ✓ {size/1_048_576:.1f} MB")
            ok += 1
        except Exception as e:
            print(f"    ✗ FAILED: {e}")
            failed += 1
        time.sleep(0.1)

    if not args.dry_run:
        print(f"\n  Done: {ok} downloaded, {skipped} already existed, {failed} not found/failed")
        if failed == 0:
            print("  ✅ All missing files resolved.")
        else:
            print("  These files may not exist in the repo — check filenames manually.")


if __name__ == "__main__":
    main()
