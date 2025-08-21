from __future__ import annotations
import os, time
from pathlib import Path
from typing import List

import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

# Optional: only needed if you want to embed a text question
USE_OPENAI = False

if USE_OPENAI:
    from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATABASE_URL   = os.environ["DATABASE_URL"]
EMBED_MODEL    = os.getenv("EMBED_MODEL", "text-embedding-3-small")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")  # only if USE_OPENAI

def to_vector_literal(vec: List[float]) -> str:
    # pgvector expects a string literal like: [0.1,0.2,...]
    return "[" + ",".join(f"{float(x):.8f}" for x in vec) + "]"

def get_query_vector_from_openai(q: str) -> List[float]:
    client = OpenAI(api_key=OPENAI_API_KEY)
    emb = client.embeddings.create(model=EMBED_MODEL, input=q).data[0].embedding
    return emb

def run_benchmark():
    conn = psycopg2.connect(DATABASE_URL)

    with conn, conn.cursor() as cur:
        # --- Choose query vector source ---

        if USE_OPENAI:
            # 1) use an embedded question as the query vector
            question = "What are the prereqs for CSCE 221?"
            print(f"[embed] '{question}' -> {EMBED_MODEL}")
            qv = get_query_vector_from_openai(question)
            qv_literal = to_vector_literal(qv)

            # Optional: set ANN runtime knobs (uncomment if you built indexes)
            # cur.execute("SET ivfflat.probes = %s;", (10,))
            # cur.execute("SET hnsw.ef_search = %s;", (40,))

            sql = """
                SELECT doc_id, metadata, left(content, 120) AS preview
                FROM rag_docs
                ORDER BY embedding <-> %s::vector
                LIMIT 8;
            """

            t0 = time.perf_counter()
            cur.execute(sql, (qv_literal,))
            rows = cur.fetchall()
            dt_ms = (time.perf_counter() - t0) * 1000
            print(f"[RESULTS] {len(rows)} rows in {dt_ms:.1f} ms")
            for i, r in enumerate(rows, 1):
                print(f"[{i}] {r[0]}  :: {r[2].replace('\\n',' ')}")

        else:
            # 2) use a random stored vector from your table (no OpenAI call)
            #    This is great to test raw DB speed.
            cur.execute("SELECT embedding FROM rag_docs ORDER BY random() LIMIT 1;")
            qv = cur.fetchone()[0]  # pgvector returns a Python list
            qv_literal = to_vector_literal(qv)

            # Optional ANN knobs:
            # cur.execute("SET ivfflat.probes = %s;", (10,))
            # cur.execute("SET hnsw.ef_search = %s;", (40,))

            sql = """
                SELECT doc_id, metadata, left(content, 120) AS preview
                FROM rag_docs
                ORDER BY embedding <-> %s::vector
                LIMIT 8;
            """
            t0 = time.perf_counter()
            cur.execute(sql, (qv_literal,))
            rows = cur.fetchall()
            dt_ms = (time.perf_counter() - t0) * 1000
            print(f"[RESULTS] {len(rows)} rows in {dt_ms:.1f} ms")
            for i, r in enumerate(rows, 1):
                print(f"[{i}] {r[0]}  :: {r[2].replace('\\n',' ')}")

    conn.close()

if __name__ == "__main__":
    run_benchmark()
