#!/usr/bin/env python3
"""
2_test_retrieval.py
===================
Tests the vector DB by running sample queries against your literature corpus.

USAGE:
  python 2_test_retrieval.py
  python 2_test_retrieval.py --query "your custom query here"
  python 2_test_retrieval.py --stream s01

REQUIREMENTS:
  pip install chromadb sentence-transformers
"""

import os
import sys
import argparse
from pathlib import Path

DB_DIR = Path("./literature/vectordb")

TEST_QUERIES = [
    "quality at entry project outcomes SIDS",
    "principal agent disbursement delays development projects",
    "halo effect evaluation bias MDB",
    "heterogeneous treatment effects causal forest",
    "Chinese development finance Belt and Road",
    "debt sustainability small island developing states",
    "specification curve robustness multiverse analysis",
]

def check_deps():
    for pkg in ["chromadb", "sentence_transformers"]:
        try:
            __import__(pkg)
        except ImportError:
            print(f"Missing: {pkg}. Run: pip install chromadb sentence-transformers")
            sys.exit(1)

def retrieve(query, collection, model, n=3, stream_filter=None):
    embedding = model.encode([query]).tolist()
    where = {"stream": stream_filter} if stream_filter else None
    kwargs = dict(query_embeddings=embedding, n_results=n, include=["documents","metadatas","distances"])
    if where:
        kwargs["where"] = where
    results = collection.query(**kwargs)
    return results

def main():
    check_deps()
    import chromadb
    from sentence_transformers import SentenceTransformer

    if not DB_DIR.exists():
        print("Vector DB not found. Run 1_ingest_literature.py first.")
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("--query",  type=str, help="Custom query")
    parser.add_argument("--stream", type=str, help="Filter by stream")
    parser.add_argument("--n",      type=int, default=3, help="Results per query")
    args = parser.parse_args()

    print("Loading model...")
    model  = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=str(DB_DIR))
    collection = client.get_collection("lsr_literature")

    count = collection.count()
    print(f"DB loaded: {count:,} chunks\n")

    queries = [args.query] if args.query else TEST_QUERIES

    for query in queries:
        print(f"{'='*60}")
        print(f"QUERY: {query}")
        print(f"{'='*60}")
        results = retrieve(query, collection, model, n=args.n, stream_filter=args.stream)
        docs  = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]
        for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists), 1):
            print(f"\n  [{i}] {meta['filename']}  (stream: {meta['stream']}, similarity: {1-dist:.3f})")
            print(f"  {doc[:300].strip()}...")
        print()

    print("✅ Retrieval working. Run: python 3_build_evidence_briefs.py")

if __name__ == "__main__":
    main()
