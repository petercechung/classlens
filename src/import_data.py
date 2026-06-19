"""
Low-friction importer: ingest the data a school / tutor ALREADY has.

Real schools don't have a clean long-format table with item difficulties. What
they have is a card-reader (讀卡機) / Excel export of an answer sheet:

    one row per student, one column per question, cells = the chosen answer
    (A/B/C/D) or a correct/incorrect mark — plus a one-row answer key.

This script converts that into the canonical data/raw/{students,items,responses}
.csv that the pipeline consumes. The only thing the teacher must supply once is
a question -> topic map (or a 詳解). **Item difficulty is computed automatically**
from the data (the empirical pass rate), so nothing extra is needed.

Usage:
    python3 src/import_data.py \
        --responses data/samples/responses_wide.csv \
        --key       data/samples/answer_key.csv \
        --itemmap   data/samples/item_topics.csv \
        --exam MOCK01
    python3 run.py            # then ingest -> process -> deliver
"""
import argparse
import csv
import math
import os

import pandas as pd

HERE = os.path.dirname(__file__)
RAW = os.path.join(HERE, "..", "data", "raw")

CORRECT_TOKENS = {"1", "o", "O", "✓", "對", "v", "V", "T", "true", "correct"}
WRONG_TOKENS = {"0", "x", "X", "✗", "錯", "f", "F", "false", "wrong", ""}


def _read(path):
    if path.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(path, dtype=str)
    return pd.read_csv(path, dtype=str)


def _difficulty(pass_rate):
    """Empirical IRT-style difficulty from pass rate (higher = harder)."""
    p = min(max(pass_rate, 0.02), 0.98)
    return round(max(-1.5, min(1.5, -math.log(p / (1 - p)))), 3)


def load(responses, key, itemmap, exam):
    rdf = _read(responses)
    cols = list(rdf.columns)
    id_col = cols[0]
    class_col = next((c for c in cols if c.lower() in
                      ("class", "班級", "班別", "group")), None)
    qcols = [c for c in cols[1:] if c != class_col]

    # answer key (optional): question -> correct answer
    key_map = {}
    if key:
        kdf = _read(key)
        kc = list(kdf.columns)
        key_map = {str(r[kc[0]]).strip(): str(r[kc[1]]).strip()
                   for _, r in kdf.iterrows()}

    # item -> topic / difficulty / max_score
    idf = _read(itemmap)
    ic = {c.lower(): c for c in idf.columns}
    qk, tk = ic.get("question"), ic.get("topic")
    dk, mk = ic.get("difficulty"), ic.get("max_score")
    topic_of, diff_of, max_of = {}, {}, {}
    for _, r in idf.iterrows():
        q = str(r[qk]).strip()
        topic_of[q] = str(r[tk]).strip()
        if dk and pd.notna(r[dk]):
            diff_of[q] = float(r[dk])
        max_of[q] = int(float(r[mk])) if mk and pd.notna(r[mk]) else 5

    # build responses (long) + per-item correctness for difficulty
    students, responses, correct_count, seen = [], [], {}, {}
    for _, row in rdf.iterrows():
        sid = str(row[id_col]).strip()
        cls = str(row[class_col]).strip() if class_col else "預設班"
        students.append({"student_id": sid, "name": sid, "class_id": cls})
        for q in qcols:
            cell = "" if pd.isna(row[q]) else str(row[q]).strip()
            if q in key_map:                       # answers + key
                is_c = 1 if cell and cell.upper() == key_map[q].upper() else 0
            elif cell in CORRECT_TOKENS:           # correctness mark
                is_c = 1
            elif cell in WRONG_TOKENS:
                is_c = 0
            else:                                  # unknown -> treat blank wrong
                is_c = 0
            responses.append({"student_id": sid, "exam_id": exam, "item_id": q,
                              "is_correct": is_c,
                              "score": max_of.get(q, 5) if is_c else 0})
            correct_count[q] = correct_count.get(q, 0) + is_c
            seen[q] = seen.get(q, 0) + 1

    # items (difficulty auto-computed if not supplied)
    items = []
    for q in qcols:
        if q not in topic_of:
            raise SystemExit(f"Question '{q}' missing from item map ({itemmap})")
        diff = diff_of.get(q)
        if diff is None:
            diff = _difficulty(correct_count[q] / max(seen[q], 1))
        items.append({"item_id": q, "exam_id": exam, "topic": topic_of[q],
                      "difficulty": diff, "max_score": max_of.get(q, 5)})
    return students, items, responses


def _write(path, rows, fields, append=False):
    mode = "a" if append and os.path.exists(path) else "w"
    with open(path, mode, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if mode == "w":
            w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fields})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--responses", required=True)
    ap.add_argument("--key", default=None)
    ap.add_argument("--itemmap", required=True)
    ap.add_argument("--exam", default="MOCK01")
    ap.add_argument("--append", action="store_true",
                    help="append this exam to existing raw (for >1 mock exam)")
    a = ap.parse_args()
    os.makedirs(RAW, exist_ok=True)

    students, items, responses = load(a.responses, a.key, a.itemmap, a.exam)
    # students table: de-dup if appending
    spath = os.path.join(RAW, "students.csv")
    if a.append and os.path.exists(spath):
        have = {r["student_id"] for r in csv.DictReader(open(spath, encoding="utf-8"))}
        students = [s for s in students if s["student_id"] not in have]
    _write(spath, students, ["student_id", "name", "class_id"], a.append)
    _write(os.path.join(RAW, "items.csv"), items,
           ["item_id", "exam_id", "topic", "difficulty", "max_score"], a.append)
    _write(os.path.join(RAW, "responses.csv"), responses,
           ["student_id", "exam_id", "item_id", "is_correct", "score"], a.append)
    print(f"Imported exam {a.exam}: {len(set(r['student_id'] for r in responses))} "
          f"students, {len(items)} items, {len(responses)} responses "
          f"(difficulty auto-computed where absent). Now run: python3 run.py")


if __name__ == "__main__":
    main()
