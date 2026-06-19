# ClassLens — 模考診斷與家長報告 (Mock-Exam Diagnostics for Cram Schools)

> A data system that turns the answer-sheet data a cram school (or an independent
> tutor) **already collects** into a **personalised study plan for each student** —
> the weak-but-heavily-tested topics ranked by payoff, a two-week practice
> sequence, and an **estimated attainable lift** (an explainable opportunity
> estimate, not a validated prediction). That personalised recommendation is
> the sellable value: a school uses it to recruit and retain (show parents exactly
> what to work on and the expected gain), and a solo tutor can use it with a single
> student. The teacher keeps the teaching; the system does the routine diagnosis,
> recommendation, and report-writing.

**Big Data Systems — Final Project (Spring 2026, NTU)**
Repo: https://github.com/petercechung/classlens · Report: `report/b12902013.pdf` · Live demo: https://classlens.cechung.com (teacher dashboard; `/student.html` = student portal)

---

## What it does (ingestion → storage → processing → delivery)

| Stage | File | What happens |
|-------|------|--------------|
| **Ingestion** | `src/ingest.py` | Load weekly mock-exam answer sheets (CSV: students, item bank, responses) into a store. |
| **Storage** | SQLite (`data/classlens.db`) | Relational store; same schema/queries map directly to Postgres / a columnar warehouse at scale (see `ARCHITECTURE.md`). |
| **Processing** | `src/process.py` | Difficulty-weighted **topic mastery**, **class heatmap**, **cohort percentile**, **term trend**, and the core output — a **personalised study plan** (topics ranked by gap × exam-weight) with an **estimated attainable lift** (explainable opportunity estimate, not a validated prediction). |
| **Delivery** | `src/deliver.py` → `public/` | A teacher **dashboard** (`index.html`), a **student/parent portal** (`student.html`, pick identity → own report), and the printable **personalised report** (`report.html?student=<id>`) — works for a single tutored student too. Static + deployable. |

The diagnostic model is a light **IRT-style** scheme: getting a *hard* item right
counts more than an easy one, so the system recovers each student's true weak
topics instead of just ranking raw scores.

## Quick start

```bash
cd classlens
python3 run.py                       # generate -> ingest -> process -> deliver
cd public && python3 -m http.server 8000   # serve (fetch() needs http, not file://)
# open http://localhost:8000  -> teacher dashboard
```

`run.py` is idempotent. To regenerate fresh synthetic data: `python3 run.py --regen`.

> **Note:** some networked/FUSE-mounted folders cannot lock SQLite. If you hit a
> `disk I/O error`, point the DB at local disk:
> `CLASSLENS_DB=/tmp/classlens.db python3 run.py`

## Import your own data (low friction)

Schools/tutors don't have a clean long-format table — they have a card-reader
(讀卡機) / Excel export: one row per student, one column per question, cells =
the chosen answer (or a correct/incorrect mark), plus a one-row answer key.
`src/import_data.py` converts exactly that into the pipeline's inputs. **Item
difficulty is computed automatically** from the pass rate; the only one-time
input is a `question → topic` map (or a 詳解).

```bash
python3 src/import_data.py \
  --responses data/samples/responses_wide.csv \
  --key       data/samples/answer_key.csv \
  --itemmap   data/samples/item_topics.csv \
  --exam MOCK01            # add --append for a 2nd/3rd mock exam
python3 run.py             # then ingest -> process -> deliver
```

See `data/samples/` for the exact three-file format. Accepts `.csv` and `.xlsx`.
If the cells are already correct/incorrect marks (O/X, 1/0, ✓), omit `--key`.

## Reproducing the demo data

`data/generate_synthetic.py` simulates 3 classes × 25 students answering three
40-item mock exams. Each student has a latent ability per topic plus a term-long
improvement drift; responses are drawn from `P(correct)=sigmoid(ability − difficulty)`.
This produces realistic weak-topic structure for the engine to recover. Replace
`data/raw/*.csv` with a real school's exports to run on live data — the schema is
documented in `ingest.py`.

## Deploy (read-only demo)

`public/` is fully static (reads `data.json` at runtime, charts via Chart.js CDN).
Deploy the folder to Vercel / Render / GitHub Pages:

```bash
cd public && npx vercel deploy --prod   # or drag the folder into any static host
```

## Repo layout

```
classlens/
  run.py                     # end-to-end pipeline
  data/generate_synthetic.py # reproducible demo data
  data/raw/*.csv             # ingestion inputs (students, items, responses)
  src/ingest.py              # ingestion + SQLite storage
  src/process.py             # diagnostic engine (the core IP)
  src/deliver.py             # dashboard + parent-report renderer
  public/                    # generated static demo (index.html, report.html, data.json)
  ARCHITECTURE.md            # end-to-end design + scale story
```

## License / attribution
Synthetic data only; no real student data is included. Charts: Chart.js (MIT).
