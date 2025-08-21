# scrape_tamu_catalog_resilient.py
import re, os, json, time, uuid, datetime as dt, random
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

BASE = "https://catalog.tamu.edu/undergraduate/course-descriptions/"
HEADERS = {"User-Agent": "TAMU-GPA-RAG/1.1 (+github.com/RajG1511/TAMU_GPA_DIST)"}
OUT_DIR = Path("out"); (OUT_DIR / "by_subject").mkdir(parents=True, exist_ok=True)

# ---------- NEW: hardened session with retries ----------
def make_session():
    s = requests.Session()
    retry = Retry(
        total=6,                # total tries (1 original + 5 retries)
        connect=6,
        read=6,
        backoff_factor=0.8,     # 0.8s, 1.6s, 3.2s, ...
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],  # only retry GET
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update(HEADERS)
    return s

def get(url, session, timeout=30):
    r = session.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text

def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def extract_subject_links(index_html: str, base_url: str):
    soup = BeautifulSoup(index_html, "html.parser")
    pattern = re.compile(r"^/undergraduate/course-descriptions/[^/]+/?$")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if pattern.match(href):
            links.append(urljoin(base_url, href))
    seen = set(); out = []
    for u in links:
        if u not in seen and u.rstrip("/") != BASE.rstrip("/"):
            seen.add(u); out.append(u)
    return out

def build_rag_text(title_raw: str, desc_text: str, credits_raw: str, prerequisites: str) -> str:
    bits = [title_raw]
    if credits_raw:
        bits.append(f"Credits: {credits_raw.replace('Credits', '').strip()}")
    desc_core = re.sub(r"Credits?\s+[0-9]+(?:\s*to\s*[0-9]+)?(?:\s*or\s*[0-9]+)?\.?", "", desc_text, flags=re.I)
    desc_core = normalize_ws(desc_core)
    if desc_core:
        bits.append(f"Overview: {desc_core}")
    if prerequisites:
        bits.append(f"Prerequisite: {prerequisites}")
    return " ".join(bits).strip()

def parse_subject_page(html_text: str, subj_url: str):
    soup = BeautifulSoup(html_text, "html.parser")
    title_el = soup.select_one("h1.page-title")
    subject_page_title = normalize_ws(title_el.get_text(" ", strip=True) if title_el else "")
    blocks = soup.select("div.courseblock")
    out = []
    for blk in blocks:
        h2 = blk.select_one("h2.courseblocktitle")
        p  = blk.select_one("p.courseblockdesc")
        if not h2 or not p:
            continue
        title_raw = normalize_ws(h2.get_text(" ", strip=True))
        desc_text = normalize_ws(p.get_text(" ", strip=True))
        hours_span = blk.select_one("span.hours")
        credits_raw = normalize_ws(hours_span.get_text(" ", strip=True)) if hours_span else ""
        prereq_match = re.search(r"(?:Prerequisite|Prerequisites)\s*:\s*(.+?)(?=$)", desc_text)
        prerequisites = normalize_ws(prereq_match.group(1).rstrip(" .")) + "." if prereq_match else ""
        m = re.match(r"^([A-Z&]{2,})\s+(\d+[A-Z]?)\s+(.*)$", title_raw)
        subject, number, course_title = ("", "", title_raw)
        if m:
            subject, number, course_title = m.group(1), m.group(2), m.group(3).strip()
        course_id = f"{subject} {number}".strip() if subject and number else title_raw
        out.append({
            "id": f"{subject}-{number}" if subject and number else str(uuid.uuid4()),
            "text": build_rag_text(title_raw, desc_text, credits_raw, prerequisites),
            "metadata": {
                "doc_type": "course",
                "subject": subject or None,
                "number": number or None,
                "course_id": course_id,
                "title": course_title or title_raw,
                "credits_raw": credits_raw or None,
                "prerequisites": prerequisites or None,
                "subject_page_title": subject_page_title or None,
                "source_url": subj_url,
                "last_crawled": dt.date.today().isoformat()
            }
        })
    return out

def write_jsonl(path: Path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def main():
    session = make_session()
    print(f"Fetching index: {BASE}")
    idx_html = get(BASE, session)
    subject_links = extract_subject_links(idx_html, BASE)
    print(f"Found {len(subject_links)} subject pages.")
    all_recs = []

    for i, subj_url in enumerate(subject_links, 1):
        print(f"[{i}/{len(subject_links)}] {subj_url}")
        # Skip if already scraped (resume support)
        slug = urlparse(subj_url).path.rstrip("/").split("/")[-1]
        subj_out = OUT_DIR / "by_subject" / f"{slug}.jsonl"
        if subj_out.exists():
            print("  [SKIP] already scraped")
            with subj_out.open("r", encoding="utf-8") as f:
                all_recs.extend(json.loads(line) for line in f)
            continue

        # Robust fetch with a last-chance local retry loop for connection resets
        tries = 0
        while True:
            tries += 1
            try:
                html_text = get(subj_url, session)
                break
            except requests.exceptions.RequestException as e:
                if tries <= 4:
                    wait = round(1.0 * (2 ** (tries - 1)) + random.uniform(0, 0.5), 2)
                    print(f"  [RETRY {tries}] {e.__class__.__name__}: {e}. Sleeping {wait}s…")
                    time.sleep(wait)
                    continue
                else:
                    print(f"  [FAIL] {subj_url} after {tries-1} retries. Skipping.")
                    html_text = None
                    break

        if not html_text:
            continue

        recs = parse_subject_page(html_text, subj_url)
        write_jsonl(subj_out, recs)
        print(f"  [OK] {len(recs)} courses")
        all_recs.extend(recs)

        # polite jitter + occasional longer pause
        time.sleep(0.6 + random.random() * 0.6)
        if i % 25 == 0:
            time.sleep(3)

    write_jsonl(OUT_DIR / "courses.jsonl", all_recs)
    print(f"\nDone. Wrote {len(all_recs)} total courses -> {OUT_DIR/'courses.jsonl'}")

if __name__ == "__main__":
    main()
