"""Build the final-project PDF report (b12902013.pdf) with reportlab.

Generates supporting figures from the real pipeline output, then assembles a
report addressing every required rubric component. English (per the rubric);
the Chinese product UI lives in the repo / live demo.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                Table, TableStyle, ListFlowable, ListItem,
                                HRFlowable)

HERE = os.path.dirname(__file__)
FIGS = os.path.join(HERE, "figs")
os.makedirs(FIGS, exist_ok=True)
# Resolve data.json across both layouts: inside the repo (classlens/report ->
# classlens/public) and the course working tree (BDA_final/report ->
# BDA_final/classlens/public).
_DATA_CANDIDATES = [
    os.path.join(HERE, "..", "public", "data.json"),
    os.path.join(HERE, "..", "classlens", "public", "data.json"),
]
DATA = next((p for p in _DATA_CANDIDATES if os.path.exists(p)),
            _DATA_CANDIDATES[0])
OUT = os.path.join(HERE, "b12902013.pdf")

GITHUB = "https://github.com/petercechung/classlens"
DEMO = "https://classlens.cechung.com"

EN = {
    "多項式函數": "Polynomials", "指數與對數": "Exp & Log",
    "三角函數": "Trigonometry", "數列與級數": "Sequences",
    "排列組合": "Perm & Comb", "機率與統計": "Prob & Stats",
    "平面向量": "Plane Vectors", "空間向量": "Space Vectors",
}


# ---------- figures -------------------------------------------------------
def fig_architecture():
    fig, ax = plt.subplots(figsize=(8.2, 2.4)); ax.axis("off")
    boxes = [
        (0.02, "Answer sheets\n(mock exams)\nCSV · OMR · app"),
        (0.225, "Ingestion +\nStorage\n(SQLite ->\nwarehouse)"),
        (0.43, "Diagnostic\nengine\nmastery · heatmap\npercentile · trend"),
        (0.635, "data.json"),
        (0.84, "Delivery\nDashboard +\nParent report"),
    ]
    for x, label in boxes:
        ax.add_patch(plt.Rectangle((x, 0.25), 0.155, 0.5, facecolor="#e0f2fe",
                     edgecolor="#0284c7", lw=1.5, transform=ax.transAxes))
        ax.text(x + 0.0775, 0.5, label, ha="center", va="center", fontsize=8,
                transform=ax.transAxes)
    for x in (0.175, 0.38, 0.585, 0.79):
        ax.annotate("", xy=(x + 0.05, 0.5), xytext=(x, 0.5),
                    xycoords=ax.transAxes, textcoords=ax.transAxes,
                    arrowprops=dict(arrowstyle="->", color="#334155", lw=1.5))
    fig.tight_layout()
    p = os.path.join(FIGS, "architecture.png")
    fig.savefig(p, dpi=160, bbox_inches="tight"); plt.close(fig)
    return p


def fig_diagnostics(d):
    sid = list(d["students"])[3]; s = d["students"][sid]
    topics = d["topics"]; labels = [EN[t] for t in topics]
    fig = plt.figure(figsize=(8.2, 3.0))
    ax = fig.add_subplot(1, 2, 1, polar=True)
    vals = [s["mastery_latest"].get(t, 0) for t in topics]
    ang = np.linspace(0, 2 * np.pi, len(topics), endpoint=False).tolist()
    ax.plot(ang + ang[:1], vals + vals[:1], color="#0284c7")
    ax.fill(ang + ang[:1], vals + vals[:1], alpha=0.2, color="#38bdf8")
    ax.set_xticks(ang); ax.set_xticklabels(labels, fontsize=6.5)
    ax.set_ylim(0, 100); ax.set_title("Topic mastery (one student)", fontsize=8)
    ax2 = fig.add_subplot(1, 2, 2)
    ax2.plot(d["exams"], s["trend"], marker="o", color="#0284c7")
    ax2.set_ylim(0, 100); ax2.set_ylabel("Adj. score"); ax2.grid(alpha=.3)
    ax2.set_title("Term trend across mock exams", fontsize=8)
    for sp in ["top", "right"]:
        ax2.spines[sp].set_visible(False)
    fig.tight_layout()
    p = os.path.join(FIGS, "diagnostics.png")
    fig.savefig(p, dpi=160, bbox_inches="tight"); plt.close(fig)
    return p


def fig_heatmap(d):
    classes = list(d["classes"]); topics = d["topics"]
    M = np.array([[d["classes"][c]["heatmap"][t] for t in topics]
                  for c in classes])
    fig, ax = plt.subplots(figsize=(8.2, 2.1))
    im = ax.imshow(M, cmap="RdYlGn", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(topics)))
    ax.set_xticklabels([EN[t] for t in topics], rotation=30, ha="right",
                        fontsize=7)
    ax.set_yticks(range(len(classes)))
    ax.set_yticklabels(["Class " + c.replace("班", "") for c in classes],
                       fontsize=8)
    for i in range(len(classes)):
        for j in range(len(topics)):
            ax.text(j, i, f"{M[i, j]:.0f}", ha="center", va="center",
                    fontsize=7)
    fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    fig.tight_layout()
    p = os.path.join(FIGS, "heatmap.png")
    fig.savefig(p, dpi=160, bbox_inches="tight"); plt.close(fig)
    return p


# ---------- document ------------------------------------------------------
def build():
    d = json.load(open(DATA, encoding="utf-8"))
    arch = fig_architecture(); diag = fig_diagnostics(d); heat = fig_heatmap(d)

    ss = getSampleStyleSheet()
    H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=14,
                        textColor=colors.HexColor("#0f172a"), spaceBefore=10,
                        spaceAfter=6)
    H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=11.5,
                        textColor=colors.HexColor("#0369a1"), spaceBefore=8,
                        spaceAfter=4)
    body = ParagraphStyle("body", parent=ss["BodyText"], fontSize=9.5,
                        leading=14, spaceAfter=5)
    small = ParagraphStyle("small", parent=body, fontSize=8.5, leading=12,
                        textColor=colors.HexColor("#475569"))
    title = ParagraphStyle("title", parent=ss["Title"], fontSize=20)

    def P(t): return Paragraph(t, body)
    def bullets(items, st=body):
        return ListFlowable([ListItem(Paragraph(i, st), leftIndent=8)
                             for i in items], bulletType="bullet",
                            start="•", leftIndent=10)

    E = []
    # ---- title ----
    E += [Spacer(1, 1.0 * cm),
          Paragraph("ClassLens", title),
          Paragraph("Turning Mock-Exam Data into Personalised Student Study "
                    "Plans a Cram School (or Tutor) Can Sell", H2),
          Spacer(1, 0.25 * cm),
          HRFlowable(width="100%", color=colors.HexColor("#0284c7")),
          Spacer(1, 0.25 * cm),
          P("<b>Big Data Systems &mdash; Final Project (Spring 2026, "
            "National Taiwan University)</b>"),
          P("Student ID: <b>b12902013</b>"),
          P(f"GitHub repository: <font color='#0369a1'>{GITHUB}</font>"),
          P(f"Live demo: <font color='#0369a1'>{DEMO}</font>"),
          P("Demo walkthrough: teacher dashboard "
            "(<font face='Courier'>/</font>), student portal "
            "(<font face='Courier'>/student.html</font>), and example report "
            "(<font face='Courier'>/report?student=S1004</font>)."),
          Spacer(1, 0.35 * cm),
          Paragraph("Executive summary", H2),
          P("Taiwanese cram schools (buxiban) run weekly mock exams and then "
            "discard the answer-level data after computing a raw score. "
            "<b>ClassLens</b> ingests that existing answer-sheet data and turns "
            "it into a <b>personalised study plan for each student</b>: the "
            "weak topics that are also heavily tested, ranked by payoff, with a "
            "two-week practice sequence and an <b>estimated attainable score "
            "lift</b> if the plan is followed &mdash; delivered as a print-ready "
            "report. "
            "Internal-efficiency framing (saving teacher time) is too weak a "
            "motivator on its own; the sellable value is the personalised "
            "recommendation, which a school uses to <b>recruit and retain</b> "
            "(showing parents exactly what their child should work on and the "
            "expected gain). The same per-student report works with no school at "
            "all, so an <b>independent tutor</b> can use it directly &mdash; "
            "which also seeds the first real data and demand evidence. The "
            "system does the routine diagnosis, recommendation and report-"
            "writing; the teacher keeps the teaching.")]

    # ---- 1 customer ----
    E += [Paragraph("1. Target customer", H1),
          P("<b>Primary customer:</b> owners / head teachers of <b>independent "
            "and small-chain, exam-focused cram schools serving junior- and "
            "senior-high students</b> &mdash; the segment that runs frequent "
            "mock exams and lives or dies on results and parent trust. <b>Beachhead "
            "/ design partner: independent tutors</b> (including the author's own "
            "tutoring students), who need no procurement decision and let the "
            "product prove value on day one."),
          P("<b>Why personalisation, not admin efficiency, is the wedge.</b> "
            "Saving a teacher an hour is a weak purchase trigger &mdash; teacher "
            "time is cheap and the pain is mild. What a school will pay for is a "
            "<b>per-student personalised plan with an explainable lift estimate</b>, "
            "because that is something it can put in front of parents to recruit "
            "and to justify staying enrolled. A peer-tutor interview reinforced "
            "this wedge: some students had left large cram schools for private "
            "tutoring because standardised large-class resources were not "
            "customised enough. The "
            "deliverable is therefore a sales/retention asset, not an internal "
            "report."),
          P("<b>Why this wedge.</b> Taiwan has roughly <b>12,500 academic "
            "(wenli) cram schools (~17,500 operating entities)</b>, an industry "
            "estimated at <b>NT$150&ndash;170 billion/year</b>, highly fragmented "
            "into tiny operators with budget but no data/IT team &mdash; the "
            "textbook SMB SaaS buyer. The junior/senior-high exam-prep slice is "
            "where exam stakes, parent willingness-to-pay and the value of "
            "diagnostics are all highest (the elementary majority is larger in "
            "headcount but lower in analytics need)."),
          P("<b>The job today.</b> Teachers cull wrong answers and write parent "
            "feedback by hand, or rely on a raw score. Walled content platforms "
            "(PaGamO, Yincai Net) only analyse <i>their own</i> question banks, "
            "not the school's own mock exams. ClassLens analyses the data the "
            "school already owns &mdash; the unserved gap."),
          P("<b>Secondary / expansion:</b> small-chain head offices (one rollout "
            "covers many branches) and a later admissions-portfolio "
            "(xuexi licheng) analytics module. Students/parents are the data "
            "source and the value delivered, <i>not</i> the direct payer.")]

    # ---- 2 demand ----
    E += [Paragraph("2. Evidence of demand and willingness to pay", H1),
          Paragraph("2.1 Data-acquisition process", H2),
          P("Following the Homework-2 methodology, demand is established from "
            "four sources:"),
          bullets([
            "<b>Public / market data:</b> Ministry-of-Interior and industry "
            "statistics on cram-school counts, sector value and per-capita "
            "tutoring spend (below).",
            "<b>Competitor pricing benchmarks:</b> existing tools' published "
            "prices, used as willingness-to-pay anchors.",
            "<b>A reproducible survey instrument (not yet a full field result):</b> "
            "a 6-question owner survey and a 10-school interview guide (in the "
            "repo, <font face='Courier'>survey/</font>) plus an illustrative "
            "response sample (<font face='Courier'>survey/results_sample.csv</font>) "
            "showing the intended analysis &mdash; minutes/exam spent on "
            "diagnosis and stated WTP. A full field round with the author's "
            "tutoring / cram-school contacts is the planned next step.",
            "<b>Practitioner workflow observation:</b> the author already works "
            "as an independent math tutor, so the first user observation is the "
            "author's own workflow: after a quiz, wrong answers must be grouped "
            "by topic, converted into next-practice advice and explained to "
            "students/parents (written up in the repo, "
            "<font face='Courier'>survey/interview_notes.md</font>). This "
            "validates the workflow pain, but on its own it is single-"
            "practitioner evidence rather than market proof &mdash; hence the "
            "survey instrument above for a wider round."]),
          P("The quantitative claims below therefore rest on the <i>real</i> "
            "public-market and competitor-pricing data; the survey instrument "
            "converts that into school-level willingness-to-pay once run."),
          Paragraph("2.2 Quantified demand signals", H2)]

    t1 = Table([
        ["Signal", "Value", "Source"],
        [Paragraph("Academic cram schools (2025)", small),
         Paragraph("~12,539", small), Paragraph("PTS", small)],
        [Paragraph("Sector value (estimate)", small),
         Paragraph("≈ NT$150 billion / yr", small), Paragraph("SEF", small)],
        [Paragraph("JH out-of-school / tutoring spend", small),
         Paragraph("≈ NT$71k / yr;<br/>tutoring ≈ NT$60k / yr", small),
         Paragraph("MOE via CNA", small)],
        [Paragraph("Tutoring-management SaaS pricing (WTP anchor)", small),
         Paragraph("NT$1,500–10,000 / mo", small),
         Paragraph("VibeAI / SchoolTracs", small)],
    ], colWidths=[7.0 * cm, 5.2 * cm, 3.2 * cm])
    t1.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f1f5f9")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    E += [t1, Spacer(1, 0.2 * cm),
          P("<b>Willingness to pay (pricing model).</b> B2B subscription priced "
            "per branch: <b>NT$3,000&ndash;8,000 / month / branch</b>, or per "
            "enrolled student per term. This sits inside an established budget "
            "line: tutoring-management systems (e.g. SchoolTracs and the systems "
            "surveyed by VibeAI) already charge schools roughly "
            "<b>NT$1,500&ndash;10,000 / month</b>, so schools are used to paying "
            "for back-office SaaS. The value is concrete: with per-student "
            "tutoring spend around NT$60,000/year, retaining a single student "
            "who would otherwise leave covers many months of subscription, and "
            "the personalised report doubles as a recruitment tool."),
          Paragraph("2.3 Why the author can test this wedge", H2),
          P("The author's tutoring work is useful as a <b>beachhead pilot</b>: "
            "it shows the routine workflow ClassLens automates (diagnose wrong "
            "answers, identify weak topics, write student/parent-facing next "
            "steps) and provides a low-friction first dataset. The peer-tutor "
            "interview adds <b>access</b>, not statistical proof: it points to "
            "students who already left large cram schools because customised "
            "resources were weak, giving the project a realistic first interview "
            "and pilot channel. The report therefore treats this as founder-"
            "market fit and early user access, while the pricing claim remains "
            "anchored by public market size and tutoring-management SaaS "
            "benchmarks.")]

    # ---- 3 system ----
    E += [Paragraph("3. System design", H1),
          P("ClassLens is a four-stage pipeline: <b>ingestion &rarr; storage "
            "&rarr; processing &rarr; delivery</b>."),
          Image(arch, width=16.5 * cm, height=4.8 * cm),
          Paragraph("3.1 Data sources &amp; ingestion (low friction)", H2),
          P("Adoption hinges on ingesting the data a school <i>already has</i>. "
            "Schools do not keep clean long-format tables; they have a "
            "card-reader (OMR) or Excel export: one row per student, one column "
            "per question, cells = the chosen answer (or a correct/incorrect "
            "mark), plus a one-row answer key. The importer "
            "(<font face='Courier'>import_data.py</font>) converts exactly that "
            "into the pipeline's inputs. Crucially, <b>item difficulty is "
            "computed automatically</b> from the empirical pass rate, so the only "
            "one-time input is a question&rarr;topic map (or an annotated answer "
            "key). This removes the main barrier to a teacher trying it on an "
            "existing exam.")]
    E += [P("No content lock-in: ClassLens analyses the school's own exams "
            "(unlike walled platforms that require their question bank).")]
    E += [
          Paragraph("3.2 Storage", H2),
          P("SQLite for the demo; the schema (students, items, responses) and "
            "the GROUP-BY aggregations are warehouse-agnostic. At scale, "
            "<font face='Courier'>responses</font> is the only large, "
            "append-only table, partitioned by (school, term)."),
          Paragraph("3.3 Processing &mdash; the diagnostic engine", H2),
          P("Mastery is <b>difficulty-weighted</b> (an IRT-style scheme): a "
            "correct answer on a hard item counts more, so the engine recovers a "
            "student's true weak topics rather than echoing the raw score. It "
            "computes topic mastery, a class weakness heatmap, cohort percentile "
            "and a term trend. The core output is a <b>personalised study "
            "plan</b>: topics are ranked by <i>gap x exam-weight</i> (a weak "
            "topic that is also heavily tested has the highest payoff) and "
            "sequenced into a two-week plan. Each topic carries an <b>estimated "
            "attainable lift</b> &mdash; an <i>explainable heuristic</i> (raise a "
            "weak topic by a capped step toward a target, weighted by its share "
            "of the exam), presented as an <b>opportunity estimate, not a "
            "validated prediction</b>. All metrics are explainable SQL "
            "aggregations + light Python: cheap, and easy for teachers and "
            "parents to trust."),
          Image(heat, width=16.5 * cm, height=4.2 * cm),
          Paragraph("<i>Figure: real pipeline output &mdash; class weakness "
            "heatmap across the three demo classes (mean mastery %, latest mock "
            "exam).</i>", small),
          Image(diag, width=16.5 * cm, height=6.0 * cm),
          Paragraph("<i>Figure: real pipeline output &mdash; one student's "
            "topic-mastery radar and term trend, as shown in the parent "
            "report.</i>", small),
          Paragraph("3.4 Delivery", H2),
          P("Three static views that read <font face='Courier'>data.json</font> "
            "at runtime: a <b>teacher dashboard</b> (class heatmap, ranked "
            "students, weak topics); a <b>student/parent portal</b> "
            "(<font face='Courier'>student.html</font>) where a student selects "
            "their identity and opens their own report &mdash; so the product is "
            "not teacher-only; and the <b>personalised report</b> itself "
            "(<font face='Courier'>report.html?student=ID</font>; radar, trend, "
            "two-week plan, estimated lift). In production the portal is "
            "login-gated so a student sees only their own report (PDPA). All "
            "deploy as a read-only static bundle (Vercel)."),
          Table([
              ["Route", "What the grader can verify"],
              [Paragraph("<font face='Courier'>/</font>", small),
               Paragraph("Teacher dashboard with class tabs, KPI cards, "
                         "weakness heatmap and ranked student list.", small)],
              [Paragraph("<font face='Courier'>/student.html</font>", small),
               Paragraph("Student/parent entry point for opening an individual "
                         "report without using the teacher dashboard.", small)],
              [Paragraph("<font face='Courier'>/report?student=S1004</font>",
                         small),
               Paragraph("Example personalised report with radar chart, trend "
                         "chart and two-week study plan.", small)],
          ], colWidths=[7.1 * cm, 8.3 * cm], style=TableStyle([
              ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
              ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
              ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
              ("FONTSIZE", (0, 0), (-1, -1), 8),
              ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
              ("VALIGN", (0, 0), (-1, -1), "TOP"),
              ("TOPPADDING", (0, 0), (-1, -1), 4),
              ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
          ])),
          Spacer(1, 0.15 * cm),
          Paragraph("3.5 Scalability &amp; cost", H2),
          P("The workload is bursty and batch-shaped: each exam upload triggers "
            "one diagnostic run, embarrassingly parallel by school/exam &mdash; "
            "no always-on streaming needed. At 100x (~100 branches, ~25k "
            "students, ~30M responses/term) the relational store moves to "
            "Postgres + object storage for raw scans; reports are pre-rendered "
            "on upload.")]

    # ---- 4 GTM ----
    gtm_rows = [
        ["Difficulty", "Why it is hard", "ClassLens mitigation"],
        [Paragraph("<b>Trust &amp; adoption</b>", small),
         Paragraph("Teachers and parents will not trust a black-box AI score, "
                   "especially if it claims a precise grade increase.", small),
         Paragraph("Run on the school's own exams; show topic mastery, exam "
                   "weight and the heuristic lift calculation. The teacher keeps "
                   "final judgment and can add comments.", small)],
        [Paragraph("<b>Data acquisition friction</b>", small),
         Paragraph("Small cram schools have messy Excel / OMR exports and do "
                   "not want to change their teaching system.", small),
         Paragraph("Importer accepts wide answer-sheet CSV/XLSX, computes "
                   "difficulty from pass rate and requires only a question-topic "
                   "map. One-class pilot can run from an existing exam.", small)],
        [Paragraph("<b>Privacy / PDPA</b>", small),
         Paragraph("Student performance data is sensitive and parents may object "
                   "to cross-school data resale.", small),
         Paragraph("Use anonymised student IDs, school-as-data-controller, "
                   "single-tenant or on-prem deployment for conservative schools "
                   "and no resale of student-level data.", small)],
        [Paragraph("<b>Cold start</b>", small),
         Paragraph("Without real school data, the product has little proof that "
                   "reports improve retention or parent conversations.", small),
         Paragraph("Start with the author's tutoring workflow and one design-"
                   "partner class; use before/after parent-report examples as "
                   "sales proof before scaling to 10-school interviews.", small)],
        [Paragraph("<b>Competition &amp; moat</b>", small),
         Paragraph("PaGamO / Yincai Net and management systems already exist; "
                   "large chains may build internal analytics.", small),
         Paragraph("Avoid competing as a content platform or admin system. The "
                   "wedge is analysing the school's own exams and turning that "
                   "data into parent-facing retention material for independents "
                   "and small chains.", small)],
        [Paragraph("<b>Unit economics</b>", small),
         Paragraph("Small branches have limited budgets, so heavy model or "
                   "support costs would break the business.", small),
         Paragraph("Batch processing on small append-only response tables keeps "
                   "marginal compute low. NT$3k-8k/month is justified if one "
                   "retained student covers months of subscription.", small)],
    ]
    E += [Paragraph("4. Go-to-market difficulties (bonus)", H1),
          P("The hardest part is not building the dashboard; it is making a "
            "small cram school trust, adopt and repeatedly pay for a diagnostic "
            "workflow. The table below maps the main promotion risks to concrete "
            "mitigations."),
          Table(gtm_rows, colWidths=[3.1 * cm, 6.1 * cm, 6.2 * cm],
                repeatRows=1,
                style=TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.4,
                     colors.HexColor("#cbd5e1")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                     [colors.white, colors.HexColor("#f8fafc")]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))]

    # ---- refs ----
    E += [Paragraph("References", H1),
          bullets([
            "PTS News Lab &mdash; cram-school counts (~12,539 academic cram "
            "schools, 2025). newslab.pts.org.tw/video/349",
            "SEF &mdash; tutoring sector value (≈ NT$150 billion / yr). "
            "sef.org.tw/article-1-129-12653",
            "CNA (citing MOE statistics) &mdash; junior-high out-of-school "
            "learning ≈ NT$71k/yr, tutoring ≈ NT$60k/yr per student. "
            "cna.com.tw/news/ahel/202201290059.aspx",
            "SchoolTracs &mdash; tutoring-centre management system (B2B SaaS WTP "
            "anchor). schooltracs.com/tw/",
            "VibeAI &mdash; tutoring-management system comparison; monthly fees "
            "≈ NT$1,500&ndash;10,000. vibeaico.com/blog/"
            "tutoring-management-system-comparison",
            "PaGamO Learning &mdash; competitor content platform / teacher "
            "backend. school.pagamo.org/product-and-service",
          ], small)]

    doc = SimpleDocTemplate(OUT, pagesize=A4, topMargin=1.6 * cm,
                            bottomMargin=1.5 * cm, leftMargin=2 * cm,
                            rightMargin=2 * cm,
                            title="ClassLens — BDA Final Project b12902013")
    doc.build(E)
    print(f"Built report -> {os.path.relpath(OUT)} "
          f"({os.path.getsize(OUT)//1024} KB)")


if __name__ == "__main__":
    build()
