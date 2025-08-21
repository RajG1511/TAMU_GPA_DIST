# verify_recs.py (psycopg2 named params fixed)
import os, json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
DATABASE_URL   = os.environ["DATABASE_URL"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
CHAT_MODEL     = os.getenv("CHAT_MODEL", "gpt-4o-mini")

client = OpenAI(api_key=OPENAI_API_KEY)

SUBJECT = "CSCE"
TOP_K   = 6

sql = """
WITH recent AS (
  SELECT
    (metadata->>'subject') AS subject,
    (metadata->>'number')  AS number,
    (metadata->>'term')    AS term,
    (metadata->>'n')::int  AS n,
    (metadata->>'mean_gpa')::float AS mean_gpa,
    (metadata->>'pct_a')::float     AS pct_a
  FROM rag_docs
  WHERE (metadata->>'doc_type') = 'grade_summary'
    AND (metadata->>'subject') = %(subject)s
    AND (metadata->>'term') ~ '^(2023|2024)'       -- only recent terms
    AND (metadata->>'n')::int >= 25                -- enough students
    AND (metadata->>'number') ~ '^[0-9]+$'         -- ensure course number is numeric
    AND (metadata->>'number')::int < 500           -- remove 500-level and above
),
per_course AS (
  SELECT
    subject, number,
    COUNT(*)                         AS sections,
    SUM(n)                           AS total_n,
    AVG(mean_gpa)                    AS avg_mean_gpa,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY mean_gpa) AS median_gpa,
    AVG(pct_a)                       AS avg_pct_a
  FROM recent
  GROUP BY subject, number
)
SELECT *
FROM per_course
WHERE total_n >= 60
ORDER BY avg_mean_gpa DESC, avg_pct_a DESC, total_n DESC
LIMIT %(k)s::int;
"""

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)
cur.execute(sql, {"subject": SUBJECT, "k": TOP_K})
rows = cur.fetchall()
cur.close(); conn.close()

if not rows:
    print("No rows matched. Loosen filters (term/N) or subject and retry.")
    raise SystemExit

print("CANDIDATES:")
for r in rows:
    print(r)

context = {
    "subject": SUBJECT,
    "candidates": [
        {
            "course_id": f"{r['subject']} {r['number']}",
            "avg_mean_gpa": round(r["avg_mean_gpa"], 3),
            "median_gpa": round(r["median_gpa"], 3),
            "avg_pct_a": round(r["avg_pct_a"], 3),
            "total_n": int(r["total_n"]),
            "sections": int(r["sections"]),
        }
        for r in rows
    ]
}

messages = [
    {"role": "system", "content":
     "You are an academic advisor. Only use the provided structured data. "
     "Recommend 2–3 courses that are relatively lighter graded. "
     "Prefer higher avg_mean_gpa and avg_pct_a, ignore any with total_n < 60. "
     "Never contradict the numbers. Cite course_ids in your bullets."},
    {"role": "user", "content": f"Here is the data:\n{json.dumps(context, indent=2)}"}
]

resp = client.chat.completions.create(
    model=CHAT_MODEL,
    messages=messages,
    temperature=0.2
)
print("\nANSWER:\n", resp.choices[0].message.content)
