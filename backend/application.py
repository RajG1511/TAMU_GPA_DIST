# main.py

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL is not set. Please set it as an environment variable.")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="A&M Grade Data Insights")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust if using 127.0.0.1 or in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------------------------------
# EXISTING ENDPOINTS
# --------------------------------------------------------------------------

@app.get("/health")
def health_check(db: Session = Depends(get_db_session)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "OK", "db_connection": "successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/grades/trends")
def get_gpa_trends_for_course(course_name: str, db: Session = Depends(get_db_session)):
    """
    Example existing endpoint that returns average GPA by semester+year+instructor
    for a given course_name. 
    """
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
    results = []
    for r in rows:
        results.append({
            "semester": r.semester,
            "year": r.year,
            "instructor_name": r.instructor_name,
            "avg_gpa": float(r.avg_gpa) if r.avg_gpa is not None else None
        })
    return results


@app.get("/")
def read_root():
    return {"message": "Welcome to the Grade Distribution API!"}


# --------------------------------------------------------------------------
# NEW ENDPOINTS FOR INSIGHTS
# --------------------------------------------------------------------------

@app.get("/insights/avg_gpa_top10_by_dept")
def avg_gpa_top10_by_department(
    department: str = Query(..., description="Department code, e.g. 'CSCE'")
    , db: Session = Depends(get_db_session)
):
    """
    Bar Chart:
    "avg gpa vs course top 10 by department"
    Return top 10 courses in a given department by avg_gpa.
    """
    # EXAMPLE query: adjust your real columns/tables as needed
    sql = text("""
    SELECT cn.course_name, AVG(g.gpa) as avg_gpa
    FROM grades g
    JOIN sections s on g.section_id = s.section_id
    JOIN course_names cn on s.course_id = cn.course_id
    WHERE cn.course_name LIKE :deptPrefix
    GROUP BY cn.course_name
    ORDER BY AVG(g.gpa) DESC
    """)
    # E.g. if dept = 'CSCE', we do 'CSCE%' to match 'CSCE-101' etc.
    param = {"deptPrefix": f"{department}%"}

    rows = db.execute(sql, param).fetchall()
    results = []
    for row in rows:
        results.append({
            "course_name": row.course_name,
            "avg_gpa": float(row.avg_gpa) if row.avg_gpa else None
        })
    return results


@app.get("/insights/proportion_by_department")
def proportion_by_department(db: Session = Depends(get_db_session)):
    """
    Pie Chart:
    "proportion of courses offered by each department"
    Return department -> count_of_courses or something similar
    for a pie chart.
    """
    sql = text("""
    SELECT LEFT(course_name, LOCATE('-', course_name) - 1) as dept_code,
           COUNT(*) as course_count
    FROM course_names
    WHERE LOCATE('-', course_name) > 0
    GROUP BY dept_code
    ORDER BY course_count DESC
    """)
    rows = db.execute(sql).fetchall()
    results = []
    for row in rows:
        results.append({
            "department": row.dept_code,
            "count": int(row.course_count)
        })
    return results


@app.get("/insights/scatter_gpa_class_size")
def scatter_gpa_class_size(db: Session = Depends(get_db_session)):
    """
    Scatter Plot:
    "avg gpa vs class size"
    Return each course or section, with an X = average class size, Y = average GPA
    For demonstration, we'll do something simplistic.
    """
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
    results = []
    for row in rows:
        results.append({
            "section_id": row.section_id,
            "avg_gpa": float(row.avg_gpa) if row.avg_gpa else None,
            "avg_class_size": float(row.avg_class_size) if row.avg_class_size else None
        })
    return results


@app.get("/insights/avg_gpa_by_department")
def avg_gpa_by_department(db: Session = Depends(get_db_session)):
    """
    Bar Chart:
    "avg gpa vs department"
    Return dept_code -> avg_gpa
    """
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
    results = []
    for row in rows:
        results.append({
            "department": row.dept_code,
            "avg_gpa": float(row.avg_gpa) if row.avg_gpa else None
        })
    return results

@app.get("/courses", response_model=list[str])
def get_course_suggestions(
    prefix: str = Query("", description="Course name prefix, e.g. 'ENGR'"),
    limit: int = Query(10, ge=1, le=50, description="Max number of suggestions"),
    db: Session = Depends(get_db_session)
):
    """
    Returns up to `limit` course_name strings that start with `prefix`.
    """
    sql = text("""
        SELECT course_name
        FROM course_names
        WHERE course_name LIKE :prefix
        ORDER BY course_name
        LIMIT :limit
    """)
    rows = db.execute(sql, {"prefix": f"{prefix}%", "limit": limit}).fetchall()
    return [r.course_name for r in rows]