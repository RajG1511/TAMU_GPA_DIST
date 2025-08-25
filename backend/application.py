from fastapi import FastAPI, Depends, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Dict, Any
import os, json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ---------- DB URLs ----------
RDS_DATABASE_URL = os.getenv("RDS_DATABASE_URL")   # MySQL (RDS)
VEC_DATABASE_URL = os.getenv("VEC_DATABASE_URL")   # Postgres (Neon)

if not RDS_DATABASE_URL:
    raise Exception("RDS_DATABASE_URL is not set.")
if not VEC_DATABASE_URL:
    raise Exception("VEC_DATABASE_URL is not set.")

# ---------- OpenAI ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBED_MODEL    = os.getenv("EMBED_MODEL", "text-embedding-3-small")
CHAT_MODEL     = os.getenv("CHAT_MODEL", "gpt-4o-mini")
oa_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ---------- Engines & Sessions ----------
# RDS (MySQL)
rds_engine = create_engine(RDS_DATABASE_URL, pool_pre_ping=True, echo=False)
RdsSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=rds_engine)

# Neon (Postgres with pgvector)
vec_engine = create_engine(VEC_DATABASE_URL, pool_pre_ping=True, echo=False)
VecSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=vec_engine)

def get_rds_session():
    db = RdsSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_vec_session():
    db = VecSessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="A&M Grade Data Insights")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000", 
        "https://tamu-gpa-dist-e87h-git-rag-integration-rajg1511s-projects.vercel.app",
        "https://tamu-gpa-dist.vercel.app",
        "https://*.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- tiny helpers ----------
def _vec_literal(v: List[float]) -> str:
    return "[" + ",".join(f"{float(x):.8f}" for x in v) + "]"

def _embed(text: str) -> List[float]:
    if not oa_client:
        raise HTTPException(500, "OPENAI_API_KEY not configured")
    resp = oa_client.embeddings.create(model=EMBED_MODEL, input=text)
    return resp.data[0].embedding

# ===========================================================================
# HEALTH
# ===========================================================================
@app.get("/health")
def health():
    # check both DBs
    try:
        with rds_engine.connect() as c:
            c.execute(text("SELECT 1"))
        with vec_engine.connect() as c:
            c.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(500, f"health check failed: {e}")
    return {"status": "OK", "rds": "ok", "vec": "ok"}

# ===========================================================================
# EXISTING ENDPOINTS — use RDS (MySQL)
# ===========================================================================
@app.get("/grades/trends")
def get_gpa_trends_for_course(course_name: str, db: Session = Depends(get_rds_session)):
    query = text("""
    SELECT 
      t.semester,
      t.year,
      i.instructor_name,
      SUM(g.gpa * g.total) / SUM(g.total) AS avg_gpa
    FROM grades g
    JOIN sections s       ON g.section_id = s.section_id
    JOIN course_names cn  ON s.course_id  = cn.course_id
    JOIN instructors i    ON s.instructor_id = i.instructor_id
    JOIN terms t          ON s.term_id = t.term_id
    WHERE cn.course_name = :course_name
    GROUP BY t.semester, t.year, i.instructor_name
    ORDER BY t.year,
             CASE
               WHEN t.semester = 'SPRING' THEN 1
               WHEN t.semester = 'SUMMER' THEN 2
               WHEN t.semester = 'FALL'   THEN 3
               ELSE 4
             END;
    """)
    rows = db.execute(query, {"course_name": course_name}).fetchall()
    return [
        {
            "semester": r.semester,
            "year": r.year,
            "instructor_name": r.instructor_name,
            "avg_gpa": float(r.avg_gpa) if r.avg_gpa is not None else None
        }
        for r in rows
    ]

@app.get("/")
def read_root():
    return {"message": "Welcome to the Grade Distribution API!"}

@app.get("/insights/avg_gpa_top10_by_dept")
def avg_gpa_top10_by_department(
    department: str = Query(..., description="Department code, e.g. 'CSCE'"),
    db: Session = Depends(get_rds_session)
):
    sql = text("""
    SELECT cn.course_name, AVG(g.gpa) as avg_gpa
    FROM grades g
    JOIN sections s on g.section_id = s.section_id
    JOIN course_names cn on s.course_id = cn.course_id
    WHERE cn.course_name LIKE :deptPrefix
    GROUP BY cn.course_name
    ORDER BY AVG(g.gpa) DESC
    """)
    rows = db.execute(sql, {"deptPrefix": f"{department}%"}).fetchall()
    return [{"course_name": r.course_name, "avg_gpa": float(r.avg_gpa) if r.avg_gpa else None} for r in rows]

@app.get("/insights/proportion_by_department")
def proportion_by_department(db: Session = Depends(get_rds_session)):
    sql = text("""
    SELECT LEFT(course_name, LOCATE('-', course_name) - 1) as dept_code,
           COUNT(*) as course_count
    FROM course_names
    WHERE LOCATE('-', course_name) > 0
    GROUP BY dept_code
    ORDER BY course_count DESC
    """)
    rows = db.execute(sql).fetchall()
    return [{"department": r.dept_code, "count": int(r.course_count)} for r in rows]

@app.get("/insights/scatter_gpa_class_size")
def scatter_gpa_class_size(db: Session = Depends(get_rds_session)):
    sql = text("""
    SELECT 
      s.section_id,
      AVG(g.gpa) as avg_gpa,
      AVG(g.total) as avg_class_size
    FROM grades g
    JOIN sections s ON g.section_id = s.section_id
    GROUP BY s.section_id
    HAVING avg_class_size IS NOT NULL
    ORDER BY s.section_id
    LIMIT 200
    """)
    rows = db.execute(sql).fetchall()
    return [{
        "section_id": r.section_id,
        "avg_gpa": float(r.avg_gpa) if r.avg_gpa else None,
        "avg_class_size": float(r.avg_class_size) if r.avg_class_size else None
    } for r in rows]

@app.get("/insights/avg_gpa_by_department")
def avg_gpa_by_department(db: Session = Depends(get_rds_session)):
    sql = text("""
    SELECT LEFT(cn.course_name, LOCATE('-', cn.course_name) - 1) as dept_code,
           AVG(g.gpa) as avg_gpa
    FROM course_names cn
    JOIN sections s ON s.course_id = cn.course_id
    JOIN grades g   ON g.section_id = s.section_id
    WHERE LOCATE('-', cn.course_name) > 0
    GROUP BY dept_code
    ORDER BY avg_gpa DESC
    """)
    rows = db.execute(sql).fetchall()
    return [{"department": r.dept_code, "avg_gpa": float(r.avg_gpa) if r.avg_gpa else None} for r in rows]

@app.get("/courses", response_model=List[str])
def get_course_suggestions(
    prefix: str = Query("", description="Course name prefix, e.g. 'ENGR'"),
    limit: int = Query(10, ge=1, le=50, description="Max number of suggestions"),
    db: Session = Depends(get_rds_session)
):
    sql = text("""
        SELECT course_name
        FROM course_names
        WHERE course_name LIKE :prefix
        ORDER BY course_name
        LIMIT :limit
    """)
    rows = db.execute(sql, {"prefix": f"{prefix}%", "limit": limit}).fetchall()
    return [r.course_name for r in rows]

# ===========================================================================
# NEW RAG ENDPOINTS — use Neon (Postgres with pgvector)
# ===========================================================================
@app.post("/rag/search")
def rag_search(
    body: Dict[str, Any] = Body(...),
    db: Session = Depends(get_vec_session)
):
    """
    Body:
      q (str, required)
      top_k (int, default 8)
      subject (str|None)
      undergrad_only (bool, default False) -> filters number < 500 if present
      min_n (int, default 0)
      recent_re (str|None) regex on term (e.g. '^(2023|2024)')
    """
    q = body.get("q", "").strip()
    if not q:
        raise HTTPException(400, "q is required")

    top_k     = int(body.get("top_k", 8))
    subject   = (body.get("subject") or "").strip().upper() or None
    undergrad = bool(body.get("undergrad_only", False))
    min_n     = int(body.get("min_n", 0))
    recent_re = body.get("recent_re")

    q_vec = _embed(q)

    filters = []
    params = {
        "embed": _vec_literal(q_vec),
        "k": top_k,
    }
    if subject:
        filters.append("(metadata->>'subject') = :subject")
        params["subject"] = subject
    if undergrad:
        filters.append("(metadata->>'number') ~ '^[0-9]+$' AND (metadata->>'number')::int < 500")
    if min_n > 0:
        filters.append("((metadata->>'n') IS NULL) OR ((metadata->>'n')::int >= :min_n)")
        params["min_n"] = min_n
    if recent_re:
        filters.append("((metadata->>'term') IS NULL) OR ((metadata->>'term') ~ :recent_re)")
        params["recent_re"] = recent_re

    where_clause = "WHERE " + " AND ".join(filters) if filters else ""
    sql = text(f"""
        SELECT
          doc_id,
          LEFT(content, 160) AS preview,
          metadata,
          embedding <=> :embed::vector AS score
        FROM rag_docs
        {where_clause}
        ORDER BY embedding <=> :embed::vector
        LIMIT :k
    """)
    rows = db.execute(sql, params).mappings().all()
    return {
        "count": len(rows),
        "results": [
            {
                "doc_id": r["doc_id"],
                "preview": r["preview"],
                "metadata": json.loads(r["metadata"]) if isinstance(r["metadata"], str) else r["metadata"],
                "score": float(r["score"]),
            }
            for r in rows
        ],
    }

@app.post("/rag/advise")
def rag_advise(
    body: Dict[str, Any] = Body(...),
    db: Session = Depends(get_vec_session)
):
    if not oa_client:
        raise HTTPException(500, "OPENAI_API_KEY not configured")
    # reuse retrieval
    search = rag_search(body, db)
    hits = search["results"]

    def brief(r):
        m = r["metadata"] or {}
        title = m.get("course_id") or f"{m.get('subject','?')} {m.get('number','?')}"
        xs = []
        if "mean_gpa" in m: xs.append(f"mean_gpa={m['mean_gpa']:.3f}")
        if "pct_a"   in m: xs.append(f"pct_a={m['pct_a']:.2f}")
        if "n"       in m: xs.append(f"n={m['n']}")
        if "term"    in m: xs.append(f"term={m['term']}")
        return f"{title} | {'; '.join(xs)} | PREVIEW: {r['preview']}"

    ctx_blob = "\n".join(brief(r) for r in hits)
    user_q = body.get("q", "")

    messages = [
        {"role": "system",
         "content": ("You are an academic advisor for Texas A&M. "
                     "Use only the provided context. Prefer higher mean_gpa and pct_a "
                     "with adequate enrollment (n>=25). Include course_id(s) when recommending.")
        },
        {"role": "user", "content": f"Question: {user_q}\n\nContext:\n{ctx_blob}"}
    ]
    resp = oa_client.chat.completions.create(model=CHAT_MODEL, messages=messages, temperature=0.2)
    return {"answer": resp.choices[0].message.content, "sources": hits}
