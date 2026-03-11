#!/usr/bin/env python3
"""
1_ingest_literature.py
======================
Reads all PDFs and DOCXs from literature/raw/<stream>/
Chunks them into passages and stores in a local ChromaDB vector database.

USAGE:
  python 1_ingest_literature.py              # ingest everything
  python 1_ingest_literature.py --stream s01 # ingest one stream only
  python 1_ingest_literature.py --reset      # wipe DB and start fresh

REQUIREMENTS:
  pip install chromadb sentence-transformers pypdf python-docx tqdm

OUTPUT:
  ./literature/vectordb/   (ChromaDB database files)
"""

import os
import sys
import argparse
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
RAW_DIR = Path(os.environ.get("LIT_DATA_DIR", "./literature/raw"))
DB_DIR  = Path("./literature/vectordb")
CHUNK_SIZE    = 800   # characters per chunk
CHUNK_OVERLAP = 100   # overlap between chunks
BATCH_SIZE    = 50    # documents per ChromaDB upsert

STREAMS = ["s01","s02","s03","s04","s05","s06","s07","s08","s09","s10",
           "s11","s12","s13","s14","s15","s16","s17","s18","s19","s20",
           "s21","s22","s26","supervisor","synthesis"]

def check_deps():
    missing = []
    for pkg in ["chromadb","sentence_transformers","pypdf","docx","tqdm"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print("Missing packages. Run:")
        pkgs = "chromadb sentence-transformers pypdf python-docx tqdm"
        print(f"  pip install {pkgs}")
        sys.exit(1)

def extract_pdf(path):
    from pypdf import PdfReader
    try:
        reader = PdfReader(str(path))
        return "\n".join(p.extract_text() or "" for p in reader.pages)
    except Exception as e:
        print(f"    ⚠ PDF error {path.name}: {e}")
        return ""

def extract_docx(path):
    from docx import Document
    try:
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        print(f"    ⚠ DOCX error {path.name}: {e}")
        return ""

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c.strip() for c in chunks if len(c.strip()) > 100]

def ingest(stream_filter=None, reset=False):
    check_deps()
    import chromadb
    from sentence_transformers import SentenceTransformer
    from tqdm import tqdm

    DB_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    client = chromadb.PersistentClient(path=str(DB_DIR))

    if reset:
        print("Resetting database...")
        try:
            client.delete_collection("lsr_literature")
        except:
            pass

    collection = client.get_or_create_collection(
        name="lsr_literature",
        metadata={"hnsw:space": "cosine"}
    )

    streams = [stream_filter] if stream_filter else STREAMS
    total_chunks = 0
    total_files  = 0

    for stream in streams:
        stream_dir = RAW_DIR / stream
        if not stream_dir.exists():
            print(f"  ⚠ Stream dir not found: {stream_dir}")
            continue

        files = list(stream_dir.iterdir())
        files = [f for f in files if f.suffix.lower() in (".pdf", ".docx", ".doc")]
        if not files:
            print(f"  [{stream.upper()}] no files")
            continue

        print(f"\n  [{stream.upper()}] {len(files)} files")

        for fpath in tqdm(files, desc=f"  {stream}", leave=False):
            if fpath.suffix.lower() == ".pdf":
                text = extract_pdf(fpath)
            else:
                text = extract_docx(fpath)

            if not text.strip():
                continue

            chunks = chunk_text(text)
            if not chunks:
                continue

            # Embed in batches
            for i in range(0, len(chunks), BATCH_SIZE):
                batch = chunks[i:i+BATCH_SIZE]
                embeddings = model.encode(batch).tolist()
                ids = [f"{stream}::{fpath.name}::chunk{i+j}" for j, _ in enumerate(batch)]
                metas = [{"stream": stream, "filename": fpath.name, "chunk": i+j} for j, _ in enumerate(batch)]
                collection.upsert(documents=batch, embeddings=embeddings, ids=ids, metadatas=metas)

            total_chunks += len(chunks)
            total_files  += 1

    print(f"\n  ✅ Ingestion complete")
    print(f"     Files processed : {total_files}")
    print(f"     Chunks stored   : {total_chunks}")
    print(f"     DB location     : {DB_DIR.resolve()}")
    print(f"\n  Run: python 2_test_retrieval.py")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stream", type=str, help="Ingest one stream only")
    parser.add_argument("--reset",  action="store_true", help="Wipe DB and start fresh")
    args = parser.parse_args()
    ingest(stream_filter=args.stream, reset=args.reset)
