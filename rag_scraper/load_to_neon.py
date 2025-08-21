from __future__ import annotations
import os, json, time, hashlib
from pathlib import Path
from typing import List, Dict, Any, Iterable

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
from openai import OpenAI, RateLimitError, APIError
from tqdm import tqdm

# ---------- config ----------
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
DATABASE_URL   = os.environ["DATABASE_URL"]
EMBED_MODEL    = os.getenv("EMBED_MODEL", "text-embedding-3-small")

DATA_FILES = [
    ROOT / "out/courses.jsonl",
    ROOT / "out/grades_sections.jsonl",
    ROOT / "out/grades_aggregates.jsonl",
]

BATCH = 64  # drop to 32/16 if you want lighter inserts
client = OpenAI(api_key=OPENAI_API_KEY)

# ---------- helpers ----------
def to_vector_literal(vec: List[float]) -> str:
    """pgvector literal: '[v1,v2,...]' as text (cast to ::vector in SQL)."""
    return "[" + ",".join(f"{float(x):.8f}" for x in vec) + "]"

def embed_with_retries(texts: List[str], max_retries: int = 6) -> List[List[float]]:
    delay = 2.0
    for _ in range(max_retries):
        try:
            resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
            return [d.embedding for d in resp.data]
        except (RateLimitError, APIError) as e:
            print(f"[OpenAI] {e}; retrying in {delay:.1f}s")
            time.sleep(delay)
            delay = min(60, delay * 2)
    raise RuntimeError("Too many embedding failures; check quota/billing.")

def stable_doc_id(meta: Dict[str, Any], content: str) -> str:
    """Use JSONL 'id' if present; otherwise make a stable hash from content + key metadata."""
    if meta and meta.get("id"):
        return str(meta["id"])
    h = hashlib.sha1()
    h.update(content.encode("utf-8"))
    for k in ("doc_type", "subject", "number", "course_id", "term", "instructor"):
        v = meta.get(k) if meta else None
        if v:
            h.update(str(v).encode("utf-8"))
    return f"auto-{h.hexdigest()[:16]}"

def read_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): 
                continue
            obj = json.loads(line)
            text = obj.get("text", "")
            meta = obj.get("metadata", {}) or {}
            # keep original source id in metadata for traceability
            if "id" in obj and "id" not in meta:
                meta["id"] = obj["id"]
            doc_id = stable_doc_id(meta, text)
            yield {"doc_id": doc_id, "content": text, "metadata": meta}

def load_all_docs() -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for p in DATA_FILES:
        if p.exists():
            print(f"[READ] {p}")
            docs.extend(read_jsonl(p))
        else:
            print(f"[WARN] missing {p}, skipping")
    return docs

def upsert_batch(conn, rows: List[Dict[str, Any]]):
    """
    Idempotent UPSERT on doc_id; stores full content + metadata + embedding.
    """
    values = [
        (
            r["doc_id"],
            r["content"],
            json.dumps(r["metadata"]),
            to_vector_literal(r["embedding"]),
        )
        for r in rows
    ]
    with conn, conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO rag_docs (doc_id, content, metadata, embedding)
            VALUES %s
            ON CONFLICT (doc_id) DO UPDATE SET
              content   = EXCLUDED.content,
              metadata  = EXCLUDED.metadata,
              embedding = EXCLUDED.embedding;
            """,
            values,
            template="(%s, %s, %s::jsonb, %s::vector)"
        )

# ---------- main ----------
def main():
    docs = load_all_docs()
    if not docs:
        print("No documents found under /out. Nothing to do.")
        return

    # connect once
    conn = psycopg2.connect(DATABASE_URL)

    total = 0
    for i in tqdm(range(0, len(docs), BATCH), desc="Embedding+Upserting"):
        chunk = docs[i:i+BATCH]
        # embed content text
        embs = embed_with_retries([d["content"] for d in chunk])
        for d, e in zip(chunk, embs):
            d["embedding"] = e
        # upsert
        upsert_batch(conn, chunk)
        total += len(chunk)

    # sanity
    with conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM rag_docs;")
        n = cur.fetchone()[0]
    conn.close()
    print(f"[DONE] Upserted {total}. Table row count: {n}")

if __name__ == "__main__":
    main()
