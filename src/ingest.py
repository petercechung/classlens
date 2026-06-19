"""
Ingestion + storage layer.

Loads the raw answer-sheet CSVs into a SQLite store. SQLite stands in for the
production warehouse; the schema and access patterns are identical to what you
would run on Postgres / a columnar warehouse at scale (see ARCHITECTURE.md).
"""
import csv
import os
import sqlite3

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
# DB path is overridable via env (some networked/FUSE mounts can't lock SQLite).
DB = os.environ.get(
    "CLASSLENS_DB",
    os.path.join(os.path.dirname(__file__), "..", "data", "classlens.db"))

SCHEMA = """
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS responses;

CREATE TABLE students (
    student_id TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    class_id   TEXT NOT NULL
);
CREATE TABLE items (
    item_id    TEXT PRIMARY KEY,
    exam_id    TEXT NOT NULL,
    topic      TEXT NOT NULL,
    difficulty REAL NOT NULL,
    max_score  INTEGER NOT NULL
);
CREATE TABLE responses (
    student_id TEXT NOT NULL,
    exam_id    TEXT NOT NULL,
    item_id    TEXT NOT NULL,
    is_correct INTEGER NOT NULL,
    score      INTEGER NOT NULL,
    PRIMARY KEY (student_id, item_id)
);
CREATE INDEX idx_resp_student ON responses(student_id);
CREATE INDEX idx_resp_exam    ON responses(exam_id);
CREATE INDEX idx_item_topic   ON items(topic);
"""


def _load_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ingest():
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)

    students = _load_csv(os.path.join(RAW, "students.csv"))
    items = _load_csv(os.path.join(RAW, "items.csv"))
    responses = _load_csv(os.path.join(RAW, "responses.csv"))

    con.executemany(
        "INSERT INTO students VALUES (:student_id,:name,:class_id)", students)
    con.executemany(
        "INSERT INTO items VALUES "
        "(:item_id,:exam_id,:topic,:difficulty,:max_score)", items)
    con.executemany(
        "INSERT INTO responses VALUES "
        "(:student_id,:exam_id,:item_id,:is_correct,:score)", responses)
    con.commit()

    n = lambda t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"Ingested -> students={n('students')} items={n('items')} "
          f"responses={n('responses')}  (db: {os.path.relpath(DB)})")
    con.close()
    return DB


if __name__ == "__main__":
    ingest()
