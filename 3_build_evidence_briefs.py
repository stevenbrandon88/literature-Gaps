#!/usr/bin/env python3
"""
3_build_evidence_briefs.py
===========================
Retrieves relevant passages from the vector DB and writes structured
evidence briefs grounded in your actual literature — NO API COST.

Uses local retrieval + structured summarisation only.

USAGE:
  python 3_build_evidence_briefs.py           # build all 10 standard briefs
  python 3_build_evidence_briefs.py --gate G1 # one gate only
  python 3_build_evidence_briefs.py --topic "QE SIDS outcomes"  # custom query
  python 3_build_evidence_briefs.py --list    # show all topics

OUTPUT:
  ./literature/briefs/<topic>.md

REQUIREMENTS:
  pip install chromadb sentence-transformers
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

DB_DIR    = Path("./literature/vectordb")
BRIEF_DIR = Path("./literature/briefs")

TOPICS = {
    "G1_quality_at_entry": {
        "gate": "G1",
        "query": "quality at entry preparation project design outcomes MDB development",
        "title": "G1: Quality at Entry — Literature Evidence",
        "streams": ["s01", "s03", "s06", "s14"],
    },
    "G2_supervision_quality": {
        "gate": "G2",
        "query": "supervision quality implementation monitoring project execution outcomes",
        "title": "G2: Supervision Quality — Literature Evidence",
        "streams": ["s02", "s04", "s06"],
    },
    "G3_symbiotic_intent": {
        "gate": "G3",
        "query": "donor intent governance conditionality aid effectiveness political economy",
        "title": "G3: Symbiotic Intent — Literature Evidence",
        "streams": ["s07", "s11", "s12"],
    },
    "G4_nation_state": {
        "gate": "G4",
        "query": "country context institutional quality governance fragile states SIDS",
        "title": "G4: Nation-State Factors — Literature Evidence",
        "streams": ["s17", "s18", "s07"],
    },
    "G5_currency_debt": {
        "gate": "G5",
        "query": "debt sustainability currency risk collateralisation small island developing states",
        "title": "G5: Currency & Debt Trap — Literature Evidence",
        "streams": ["s19", "s18", "s13"],
    },
    "G6_climate_resilience": {
        "gate": "G6",
        "query": "climate adaptation finance resilience SIDS GCF green bonds",
        "title": "G6: Climate Resilience — Literature Evidence",
        "streams": ["s08", "s20", "s21"],
    },
    "G7_collapse_risk": {
        "gate": "G7",
        "query": "project collapse failure non-linear systems cascading risk",
        "title": "G7: Collapse Risk — Literature Evidence",
        "streams": ["s26", "s22", "s17"],
    },
    "OR_empirical": {
        "gate": None,
        "query": "odds ratio project performance quality evaluation MDB econometrics causal identification",
        "title": "Empirical Foundation — OR=27.8 Literature Support",
        "streams": ["s01", "s09", "s14", "s15"],
    },
    "SIDS_finance": {
        "gate": None,
        "query": "SIDS development finance multilateral access climate vulnerability Pacific Caribbean",
        "title": "SIDS Finance — Literature Evidence",
        "streams": ["s18", "s08", "s19", "s13"],
    },
    "chinese_finance": {
        "gate": None,
        "query": "Chinese development finance Belt Road extractive governance debt trap",
        "title": "Chinese Development Finance — Literature Evidence",
        "streams": ["s11", "s07", "s12"],
    },
}


def check_deps():
    for pkg in ["chromadb", "sentence_transformers"]:
        try:
            __import__(pkg)
        except ImportError:
            print(f"Missing: {pkg}. Run: pip install chromadb sentence-transformers")
            sys.exit(1)


def retrieve_passages(query, collection, model, streams=None, n=12):
    embedding = model.encode([query]).tolist()
    kwargs = dict(query_embeddings=embedding, n_results=n,
                  include=["documents", "metadatas", "distances"])
    if streams:
        kwargs["where"] = {"stream": {"$in": streams}}
    results = collection.query(**kwargs)
    passages = []
    for doc, meta, dist in zip(results["documents"][0],
                                results["metadatas"][0],
                                results["distances"][0]):
        passages.append({
            "text": doc.strip(),
            "filename": meta["filename"],
            "stream": meta["stream"],
            "similarity": round(1 - dist, 3)
        })
    return sorted(passages, key=lambda x: x["similarity"], reverse=True)


def format_brief(topic_cfg, passages):
    """
    Assemble a structured evidence brief from retrieved passages.
    No LLM — pure extraction and formatting.
    """
    title  = topic_cfg["title"]
    gate   = topic_cfg.get("gate")
    now    = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Group by source file (deduplicate)
    by_file = {}
    for p in passages:
        fn = p["filename"]
        if fn not in by_file or p["similarity"] > by_file[fn]["similarity"]:
            by_file[fn] = p

    top_sources = sorted(by_file.values(), key=lambda x: x["similarity"], reverse=True)

    lines = []
    lines.append(f"# {title}")
    lines.append(f"*Generated: {now} | Sources: {len(top_sources)} papers | Streams: {', '.join(topic_cfg.get('streams') or ['all'])}*")
    lines.append("")

    if gate:
        lines.append(f"## LSR Gate {gate} — Evidence Summary")
    else:
        lines.append(f"## Evidence Summary")
    lines.append("")
    lines.append("### Key Sources (by relevance)")
    lines.append("")

    for i, p in enumerate(top_sources[:8], 1):
        lines.append(f"**[{i}] {p['filename']}**  ")
        lines.append(f"Stream: `{p['stream']}` | Similarity: `{p['similarity']}`")
        lines.append("")
        # Show up to 500 chars of the most relevant passage
        excerpt = p["text"][:500].strip()
        if len(p["text"]) > 500:
            excerpt += "..."
        lines.append(f"> {excerpt}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("### All Retrieved Passages")
    lines.append("")
    for p in passages:
        lines.append(f"**{p['filename']}** (stream: `{p['stream']}`, sim: `{p['similarity']}`)")
        lines.append("")
        lines.append(f"> {p['text'][:300].strip()}...")
        lines.append("")

    lines.append("---")
    lines.append(f"*Brief generated by 3_build_evidence_briefs.py — LSR Platform v1.0*")

    return "\n".join(lines)


def build_brief(topic_key, topic_cfg, collection, model):
    print(f"  Building: {topic_cfg['title']}")

    passages = retrieve_passages(
        topic_cfg["query"], collection, model,
        streams=topic_cfg.get("streams"), n=12
    )

    if not passages:
        print(f"  ⚠ No passages found for {topic_key}")
        return None

    brief_text = format_brief(topic_cfg, passages)

    BRIEF_DIR.mkdir(parents=True, exist_ok=True)
    outpath = BRIEF_DIR / f"{topic_key}.md"
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(brief_text)

    print(f"    ✓ {len(passages)} passages → {outpath}")
    return outpath


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str,  help="Custom topic query")
    parser.add_argument("--gate",  type=str,  help="LSR gate (G1-G7)")
    parser.add_argument("--list",  action="store_true")
    parser.add_argument("--all",   action="store_true", help="Build all briefs (default)")
    args = parser.parse_args()

    if args.list:
        print("\nAvailable topics:")
        for k, v in TOPICS.items():
            gate = f"[{v['gate']}]" if v['gate'] else "     "
            print(f"  {gate} {k:<30} {v['title']}")
        return

    check_deps()
    import chromadb
    from sentence_transformers import SentenceTransformer

    if not DB_DIR.exists():
        print("Vector DB not found. Run 1_ingest_literature.py first.")
        sys.exit(1)

    print("Loading model and DB...")
    model      = SentenceTransformer("all-MiniLM-L6-v2")
    client_db  = chromadb.PersistentClient(path=str(DB_DIR))
    collection = client_db.get_collection("lsr_literature")
    print(f"DB: {collection.count():,} chunks\n")

    if args.gate:
        topics_to_run = {k: v for k, v in TOPICS.items() if v.get("gate") == args.gate.upper()}
        if not topics_to_run:
            print(f"Gate {args.gate} not found. Use --list.")
            return
    elif args.topic:
        topics_to_run = {"custom": {
            "gate": None,
            "query": args.topic,
            "title": f"Custom: {args.topic}",
            "streams": None,
        }}
    else:
        topics_to_run = TOPICS

    print(f"Building {len(topics_to_run)} brief(s)...\n")
    built = []
    for topic_key, topic_cfg in topics_to_run.items():
        result = build_brief(topic_key, topic_cfg, collection, model)
        if result:
            built.append(result)

    print(f"\n✅ {len(built)} briefs saved to: {BRIEF_DIR.resolve()}")
    print("Run: python 4_wire_into_backend.py")

if __name__ == "__main__":
    main()
