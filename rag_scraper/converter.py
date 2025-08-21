# rag_scraper/converter.py
from __future__ import annotations
import os
import json
from pathlib import Path
from typing import Optional, Iterable, Dict, Any, Tuple

import pandas as pd

# ---------- Paths (resolve relative to repo root) ----------
ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "formatted_data"      # CSVs here
OUT_DIR = ROOT / "out"                # JSONL out here
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEASON_MAP = {"SPRING": "S", "SUMMER": "U", "FALL": "F"}

# Optional: set once to include a link in metadata; otherwise omitted
GRADE_SOURCE_URL = os.getenv("GRADE_SOURCE_URL", None)


def term_code(semester: Optional[str], year: Optional[str | int]) -> Optional[str]:
    if semester is None or year is None:
        return None
    s = str(semester).strip().upper()
    try:
        y = int(str(year).strip())
    except Exception:
        return None
    return f"{y}{SEASON_MAP.get(s, s[:1])}"


def parse_instructor(raw: Any) -> Tuple[Optional[str], str]:
    """
    Return (display_name, slug) from various forms:
      - "SMITH J"          -> "Smith J"
      - "SMITH, JOHN P"    -> "John P Smith"
      - "Alice Smith"      -> "Alice Smith"
      - NaN/None           -> (None, 'na')
    The slug is for stable IDs (lowercase, hyphenated).
    """
    if not isinstance(raw, str):
        return None, "na"
    s = raw.strip()
    if not s:
        return None, "na"

    s = s.replace("  ", " ").strip()

    # If there's a comma, treat as "Last, First [Middles]"
    if "," in s:
        last, firsts = s.split(",", 1)
        last = last.strip().title()
        firsts = " ".join(firsts.strip().title().split())
        disp = f"{firsts} {last}".strip()
    else:
        # No comma. Could be "SMITH J" or already "Alice Smith".
        parts = s.title().split()
        if len(parts) == 1:
            disp = parts[0]
        else:
            # Heuristic: if first part is all-caps and second is a single letter,
            # assume "Last Initial" -> "Last Initial" (already OK after title-case).
            disp = " ".join(parts)

    slug = "-".join(disp.lower().split())
    return disp, slug or "na"


def pct(num: float, den: float) -> float:
    return (num / den) if den and den > 0 else 0.0


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().upper() for c in df.columns]

    alias_map = {
        "DEPT": "DEPARTMENT",
        "SUBJECT": "DEPARTMENT",
        "COURSE_NUMBER": "COURSE",
        "COURSE NUM": "COURSE",
        "SECTION ID": "SECTION",
        "WITHDRAW": "W",
        "WITHDRAWALS": "W",
    }
    for old, new in alias_map.items():
        if old in df.columns and new not in df.columns:
            df.rename(columns={old: new}, inplace=True)

    needed = [
        "DEPARTMENT", "COURSE", "SECTION", "A", "B", "C", "D", "F", "GPA",
        "I", "S", "U", "Q", "X", "W", "TOTAL", "INSTRUCTOR", "COLLEGE",
        "SEMESTER", "YEAR"
    ]
    for c in needed:
        if c not in df.columns:
            if c in {"A","B","C","D","F","I","S","U","Q","X","W","TOTAL"}:
                df[c] = 0
            else:
                df[c] = None

    # numeric
    num_cols = ["A","B","C","D","F","I","S","U","Q","X","W","TOTAL","GPA"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    return df


def row_to_section_doc(r: pd.Series) -> Dict[str, Any]:
    n = float(r["TOTAL"])
    a, b, c_, d, f = (float(r[k]) for k in ["A", "B", "C", "D", "F"])

    # Withdrawals: prefer W if present; otherwise Q+X
    w = float(r.get("W", 0.0))
    if w == 0:
        w = float(r.get("Q", 0.0)) + float(r.get("X", 0.0))

    gpa = float(r["GPA"]) if r["GPA"] else None

    course_id = f"{str(r['DEPARTMENT']).strip()} {str(r['COURSE']).strip()}"
    subject = str(r["DEPARTMENT"]).strip()
    number = str(r["COURSE"]).strip()
    term = term_code(r["SEMESTER"], r["YEAR"])
    section = str(r["SECTION"]).strip()

    instr_disp, instr_slug = parse_instructor(r["INSTRUCTOR"])

    text = (
        f"{course_id} ({term or 'N/A'}, Section {section or 'N/A'}, "
        f"Instructor: {instr_disp or 'N/A'}) — N={int(n)}, "
        f"Mean GPA {gpa if gpa is not None else 'N/A'}. "
        f"A {pct(a,n):.0%}, B {pct(b,n):.0%}, C {pct(c_,n):.0%}, "
        f"D {pct(d,n):.0%}, F {pct(f,n):.0%}, Withdraw {pct(w,n):.0%}."
    )

    meta = {
        "doc_type": "grade_summary",
        "course_id": course_id,
        "subject": subject,
        "number": number,
        "section": section or None,
        "instructor": instr_disp,                 # full display name
        "instructor_last": (instr_disp.split()[-1] if instr_disp else None),
        "term": term,
        "n": int(n),
        "mean_gpa": gpa,
        "pct_a": pct(a, n),
        "pct_b": pct(b, n),
        "pct_c": pct(c_, n),
        "pct_d": pct(d, n),
        "pct_f": pct(f, n),
        "pct_w": pct(w, n),
        "source": "registrar_public",
    }
    if GRADE_SOURCE_URL:
        meta["source_url"] = GRADE_SOURCE_URL

    return {
        "id": f"{subject}-{number}-{section}-{term}-{instr_slug}",
        "text": text,
        "metadata": meta,
    }


def agg_group_to_doc(r: pd.Series) -> Dict[str, Any]:
    n = float(r["N"])
    a, b, c_, d, f = (float(r[k]) for k in ["A", "B", "C", "D", "F"])
    w = float(r.get("W", 0.0))
    if w == 0:
        w = float(r.get("Q", 0.0)) + float(r.get("X", 0.0))
    gpa = float(r["GPA"]) if pd.notna(r["GPA"]) else None

    course_id = r["COURSE_ID"]
    text = (
        f"{course_id} ({r['TERM'] or 'N/A'} — all sections) — N={int(n)}, "
        f"Mean GPA {gpa if gpa is not None else 'N/A'}. "
        f"A {pct(a,n):.0%}, B {pct(b,n):.0%}, C {pct(c_,n):.0%}, "
        f"D {pct(d,n):.0%}, F {pct(f,n):.0%}, Withdraw {pct(w,n):.0%}."
    )

    meta = {
        "doc_type": "grade_aggregate",
        "course_id": course_id,
        "subject": r["SUBJECT"],
        "number": r["NUMBER"],
        "term": r["TERM"],
        "n": int(n),
        "mean_gpa": gpa,
        "pct_a": pct(a, n),
        "pct_b": pct(b, n),
        "pct_c": pct(c_, n),
        "pct_d": pct(d, n),
        "pct_f": pct(f, n),
        "pct_w": pct(w, n),
        "source": "registrar_public",
    }
    if GRADE_SOURCE_URL:
        meta["source_url"] = GRADE_SOURCE_URL

    return {
        "id": f"{r['SUBJECT']}-{r['NUMBER']}-{r['TERM']}-aggregate",
        "text": text,
        "metadata": meta,
    }


def write_jsonl(path: Path, docs: Iterable[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")


def main():
    section_docs: list[Dict[str, Any]] = []
    agg_docs: list[Dict[str, Any]] = []

    csvs = sorted(IN_DIR.glob("*.csv"))
    if not csvs:
        print(f"[WARN] No CSVs found in {IN_DIR}")

    for csv in csvs:
        print(f"[READ] {csv.name}")
        df = pd.read_csv(csv, dtype=str)
        df = normalize_columns(df)

        # helper columns
        df["COURSE_ID"] = (
            df["DEPARTMENT"].astype(str).str.strip() + " " +
            df["COURSE"].astype(str).str.strip()
        )
        df["SUBJECT"] = df["DEPARTMENT"].astype(str).str.strip()
        df["NUMBER"] = df["COURSE"].astype(str).str.strip()
        df["TERM"] = [term_code(s, y) for s, y in zip(df["SEMESTER"], df["YEAR"])]

        # numeric again (since dtype=str on read)
        num_cols = ["A","B","C","D","F","I","S","U","Q","X","W","TOTAL","GPA"]
        for c in num_cols:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

        # per-section docs
        for _, r in df.iterrows():
            section_docs.append(row_to_section_doc(r))

        # aggregates
        grp = df.groupby(["COURSE_ID", "SUBJECT", "NUMBER", "TERM"], dropna=False).agg(
            N=("TOTAL", "sum"),
            A=("A", "sum"), B=("B", "sum"), C=("C", "sum"), D=("D", "sum"), F=("F", "sum"),
            Q=("Q", "sum"), X=("X", "sum"), W=("W", "sum"),
            GPA=("GPA", "mean"),
        ).reset_index()

        for _, r in grp.iterrows():
            agg_docs.append(agg_group_to_doc(r))

    write_jsonl(OUT_DIR / "grades_sections.jsonl", section_docs)
    write_jsonl(OUT_DIR / "grades_aggregates.jsonl", agg_docs)
    print(f"[DONE] Wrote {len(section_docs)} section docs and {len(agg_docs)} aggregate docs to {OUT_DIR}")


if __name__ == "__main__":
    main()
