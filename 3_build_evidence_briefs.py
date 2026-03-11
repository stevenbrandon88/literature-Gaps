#!/usr/bin/env python3
"""
3_build_evidence_briefs.py
===========================
Retrieves relevant passages from the vector DB and uses Claude API
to write structured evidence briefs grounded in your actual literature.

USAGE:
  python 3_build_evidence_briefs.py                    # run all standard topics
  python 3_build_evidence_briefs.py --topic "QE SIDS"  # custom topic
  python 3_build_evidence_briefs.py --gate G1          # brief for LSR gate
  python 3_build_evidence_briefs.py --list             # list available gates/topics

OUTPUT:
  ./literature/briefs/<topic>.md

REQUIREMENTS:
  pip install chromadb sentence-transformers anthropic
  Set ANTHROPIC_API_KEY environment variable
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

DB_DIR    = Path("./literature/vectordb")
BRIEF_DIR = Path("./literature/briefs")

# ── Standard evidence brief topics mapped to LSR gates ────────────────────────
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
    for pkg in ["chromadb", "sentence_transformers", "anthropic"]:
        try:
            __import__(pkg)
        except ImportError:
            print(f"Missing: {pkg}. Run: pip install chromadb sentence-transformers anthropic")
            sys.exit(1)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY environment variable first.")
        sys.exit(1)


def retrieve_passages(query, collection, model, streams=None, n=8):
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
            "text": doc,
            "filename": meta["filename"],
            "stream": meta["stream"],
            "similarity": round(1 - dist, 3)
        })
    return passages


def build_brief(topic_key, topic_cfg, collection, model, client):
    import anthropic

    print(f"  Building: {topic_cfg['title']}")

    passages = retrieve_passages(
        topic_cfg["query"], collection, model,
        streams=topic_cfg.get("streams"), n=10
    )

    if not passages:
        print(f"  ⚠ No passages found for {topic_key}")
        return None

    passage_text = "\n\n".join([
        f"[Source: {p['filename']} | Stream: {p['stream']} | Similarity: {p['similarity']}]\n{p['text']}"
        for p in passages
    ])

    system = """You are an academic research assistant synthesising development finance literature 
for a PhD thesis on the Law of Symbiotic Resilience (LSR). Write in formal academic prose.
Be concise, precise, and grounded strictly in the provided passages. 
Do not invent citations — only reference sources explicitly provided."""

    prompt = f"""Based on the following literature passages, write a structured evidence brief for:

TOPIC: {topic_cfg['title']}

The brief should:
1. Summarise the key empirical findings (2-3 paragraphs)
2. Identify the main theoretical mechanisms
3. Note any gaps or contradictions in the literature
4. Connect to LSR framework where relevant

LITERATURE PASSAGES:
{passage_text}

Write the brief now in academic prose (400-600 words). Include in-text references to source filenames."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
        system=system
    )

    brief_text = response.content[0].text

    # Save
    BRIEF_DIR.mkdir(parents=True, exist_ok=True)
    outpath = BRIEF_DIR / f"{topic_key}.md"
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(f"# {topic_cfg['title']}\n")
        f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n")
        f.write(brief_text)
        f.write("\n\n---\n\n## Source Passages\n\n")
        for p in passages:
            f.write(f"**{p['filename']}** (stream: {p['stream']}, similarity: {p['similarity']})\n\n")
            f.write(f"> {p['text'][:300]}...\n\n")

    print(f"    ✓ Saved: {outpath}")
    return outpath


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, help="Custom topic query")
    parser.add_argument("--gate",  type=str, help="LSR gate (G1-G7)")
    parser.add_argument("--list",  action="store_true")
    parser.add_argument("--all",   action="store_true", help="Build all standard briefs")
    args = parser.parse_args()

    if args.list:
        print("\nAvailable topics:")
        for k, v in TOPICS.items():
            gate = f"[{v['gate']}]" if v['gate'] else "     "
            print(f"  {gate} {k:<30} {v['title']}")
        return

    check_deps()
    import chromadb
    import anthropic
    from sentence_transformers import SentenceTransformer

    if not DB_DIR.exists():
        print("Vector DB not found. Run 1_ingest_literature.py first.")
        sys.exit(1)

    print("Loading model and DB...")
    model      = SentenceTransformer("all-MiniLM-L6-v2")
    client_db  = chromadb.PersistentClient(path=str(DB_DIR))
    collection = client_db.get_collection("lsr_literature")
    client_ai  = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    print(f"DB: {collection.count():,} chunks\n")

    if args.gate:
        topics_to_run = {k: v for k, v in TOPICS.items() if v.get("gate") == args.gate.upper()}
        if not topics_to_run:
            print(f"Gate {args.gate} not found. Use --list to see options.")
            return
    elif args.topic:
        topics_to_run = {"custom": {
            "gate": None,
            "query": args.topic,
            "title": f"Custom: {args.topic}",
            "streams": None,
        }}
    elif args.all:
        topics_to_run = TOPICS
    else:
        # Default: run first 3
        topics_to_run = dict(list(TOPICS.items())[:3])

    print(f"Building {len(topics_to_run)} evidence brief(s)...\n")
    for topic_key, topic_cfg in topics_to_run.items():
        build_brief(topic_key, topic_cfg, collection, model, client_ai)

    print(f"\n✅ Briefs saved to: {BRIEF_DIR.resolve()}")
    print("Run: python 4_wire_into_backend.py")

if __name__ == "__main__":
    main()
