#!/usr/bin/env python3
"""
4_wire_into_backend.py
=======================
Adds a /search and /evidence endpoints to the LSR backend
so the accreditation engine can query the literature automatically.

Run this once to patch lsr_backend.py with vector DB support.

USAGE:
  python 4_wire_into_backend.py              # patch backend
  python 4_wire_into_backend.py --test       # test the endpoints

REQUIREMENTS:
  pip install chromadb sentence-transformers flask anthropic
"""

import os
import sys
from pathlib import Path

BACKEND_PATH = Path("../LSR-Engine/lsr_backend.py")
DB_DIR       = Path("./literature/vectordb")
BRIEF_DIR    = Path("./literature/briefs")

SEARCH_MODULE = '''
# ── Vector DB search module ───────────────────────────────────────────────────
# Auto-injected by 4_wire_into_backend.py

import chromadb
from sentence_transformers import SentenceTransformer

_vdb_model      = None
_vdb_collection = None

def _load_vdb():
    global _vdb_model, _vdb_collection
    if _vdb_model is None:
        print("Loading vector DB...")
        _vdb_model = SentenceTransformer("all-MiniLM-L6-v2")
        client = chromadb.PersistentClient(path="./literature/vectordb")
        _vdb_collection = client.get_collection("lsr_literature")
        print(f"  Vector DB loaded: {_vdb_collection.count():,} chunks")

@app.route("/search", methods=["POST"])
def search_literature():
    """Search literature corpus. POST: {query, n, streams}"""
    _load_vdb()
    data    = request.get_json()
    query   = data.get("query", "")
    n       = data.get("n", 5)
    streams = data.get("streams", None)
    if not query:
        return jsonify({"error": "query required"}), 400
    embedding = _vdb_model.encode([query]).tolist()
    kwargs = dict(query_embeddings=embedding, n_results=n,
                  include=["documents","metadatas","distances"])
    if streams:
        kwargs["where"] = {"stream": {"$in": streams}}
    results = _vdb_collection.query(**kwargs)
    passages = [
        {"text": doc, "filename": meta["filename"],
         "stream": meta["stream"], "similarity": round(1-dist, 3)}
        for doc, meta, dist in zip(results["documents"][0],
                                    results["metadatas"][0],
                                    results["distances"][0])
    ]
    return jsonify({"query": query, "results": passages})

@app.route("/evidence/<gate>", methods=["GET"])
def get_evidence_brief(gate):
    """Return pre-built evidence brief for a gate (G1-G7)."""
    brief_dir = Path("./literature/briefs")
    matches = list(brief_dir.glob(f"{gate.upper()}*.md")) + \\
              list(brief_dir.glob(f"{gate.lower()}*.md"))
    if not matches:
        return jsonify({"error": f"No brief found for gate {gate}"}), 404
    with open(matches[0], "r", encoding="utf-8") as f:
        content = f.read()
    return jsonify({"gate": gate, "brief": content, "source": str(matches[0])})

# ── End vector DB module ──────────────────────────────────────────────────────
'''

def patch_backend():
    if not BACKEND_PATH.exists():
        print(f"  Backend not found at {BACKEND_PATH}")
        print("  Creating standalone search server instead...")
        create_standalone()
        return

    content = BACKEND_PATH.read_text(encoding="utf-8")
    if "search_literature" in content:
        print("  Backend already patched.")
        return

    # Insert before the last if __name__ == block
    insert_point = content.rfind('if __name__')
    if insert_point == -1:
        content += SEARCH_MODULE
    else:
        content = content[:insert_point] + SEARCH_MODULE + "\n" + content[insert_point:]

    BACKEND_PATH.write_text(content, encoding="utf-8")
    print(f"  ✓ Patched: {BACKEND_PATH}")


def create_standalone():
    """Create a standalone search server if lsr_backend.py not found."""
    code = f'''#!/usr/bin/env python3
"""
lsr_search_server.py — Standalone literature search server
Run: python lsr_search_server.py
Then POST to http://localhost:5001/search
"""
from flask import Flask, request, jsonify
from pathlib import Path
{SEARCH_MODULE.replace("@app.", "@app.").replace("app = ", "")}

app = Flask(__name__)

# Re-register routes with this app instance
@app.route("/search", methods=["POST"])
def search_literature_standalone():
    _load_vdb()
    data    = request.get_json()
    query   = data.get("query", "")
    n       = data.get("n", 5)
    streams = data.get("streams", None)
    if not query:
        return jsonify({{"error": "query required"}}), 400
    embedding = _vdb_model.encode([query]).tolist()
    kwargs = dict(query_embeddings=embedding, n_results=n,
                  include=["documents","metadatas","distances"])
    if streams:
        kwargs["where"] = {{"stream": {{"$in": streams}}}}
    results = _vdb_collection.query(**kwargs)
    passages = [
        {{"text": doc, "filename": meta["filename"],
         "stream": meta["stream"], "similarity": round(1-dist, 3)}}
        for doc, meta, dist in zip(results["documents"][0],
                                    results["metadatas"][0],
                                    results["distances"][0])
    ]
    return jsonify({{"query": query, "results": passages}})

if __name__ == "__main__":
    app.run(port=5001, debug=False)
    print("Search server running at http://localhost:5001/search")
'''
    out = Path("./lsr_search_server.py")
    out.write_text(code, encoding="utf-8")
    print(f"  ✓ Created standalone: {out}")


def test_endpoints():
    import requests
    print("Testing search endpoint...")
    try:
        r = requests.post("http://localhost:5001/search",
                          json={"query": "quality at entry SIDS outcomes", "n": 3},
                          timeout=30)
        data = r.json()
        print(f"  Results: {len(data.get('results', []))}")
        for p in data.get("results", []):
            print(f"    {p['filename']} (sim: {p['similarity']})")
        print("  ✅ Search working.")
    except Exception as e:
        print(f"  ✗ {e} — is the server running?")


def main():
    parser = __import__("argparse").ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if args.test:
        test_endpoints()
        return

    if not DB_DIR.exists():
        print("Vector DB not found. Run 1_ingest_literature.py first.")
        sys.exit(1)

    print("Wiring vector DB into backend...")
    patch_backend()
    print("\n✅ Done. To use:")
    print("   Start backend: python lsr_backend.py")
    print("   Search: POST http://localhost:5000/search  {query: '...', n: 5}")
    print("   Evidence: GET  http://localhost:5000/evidence/G1")

if __name__ == "__main__":
    main()
