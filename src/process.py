"""
Processing layer -- the diagnostic engine (the product's core IP).

From raw correct/incorrect responses it derives, per the rubric's
"processing" stage:

  1. Topic mastery per student   -- difficulty-weighted, so getting hard items
                                    right counts more than easy ones.
  2. Class weakness heatmap      -- mean mastery per topic per class.
  3. Cohort percentile           -- where each student ranks.
  4. Term trend                  -- mastery trajectory across the mock exams,
                                    so the parent report can show progress.
  5. Targeted recommendations    -- each student's weakest topics + practice.

The AI/automation does this routine diagnosis; the teacher keeps the teaching.
"""
import json
import os
import sqlite3

DB = os.environ.get(
    "CLASSLENS_DB",
    os.path.join(os.path.dirname(__file__), "..", "data", "classlens.db"))
OUT = os.path.join(os.path.dirname(__file__), "..", "public", "data.json")

# static practice catalogue: weakest topic -> what to assign next
PRACTICE = {
    "多項式函數": "多項式除法與餘式定理 8 題 + 函數圖形 4 題",
    "指數與對數": "對數律混合計算 10 題 + 指對數方程式 5 題",
    "三角函數": "和差角與倍角公式 10 題 + 正餘弦定理應用 5 題",
    "數列與級數": "等差等比綜合 8 題 + 數學歸納法 4 題",
    "排列組合": "重複排列與組合 10 題 + 二項式定理 5 題",
    "機率與統計": "條件機率 8 題 + 期望值與變異數 6 題",
    "平面向量": "內積與夾角 8 題 + 向量分解 5 題",
    "空間向量": "外積與平面方程式 8 題 + 直線與平面關係 5 題",
}


def _rows(con, q, args=()):
    cur = con.execute(q, args)
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def topic_mastery(con):
    """Difficulty-weighted mastery in [0,100] per (student, exam, topic).

    weight = 1 + difficulty offset so harder items contribute more.
    """
    q = """
    SELECT r.student_id, r.exam_id, i.topic,
           SUM(r.is_correct * (1.5 + i.difficulty)) AS got,
           SUM(1.5 + i.difficulty)                  AS pos
    FROM responses r JOIN items i ON r.item_id = i.item_id
    GROUP BY r.student_id, r.exam_id, i.topic
    """
    out = {}
    for row in _rows(con, q):
        mastery = 100.0 * row["got"] / row["pos"] if row["pos"] else 0.0
        out.setdefault(row["student_id"], {}).setdefault(
            row["exam_id"], {})[row["topic"]] = round(mastery, 1)
    return out


def overall_by_exam(con):
    """Difficulty-adjusted overall score per (student, exam), 0-100."""
    q = """
    SELECT r.student_id, r.exam_id,
           SUM(r.is_correct * (1.5 + i.difficulty)) AS got,
           SUM(1.5 + i.difficulty)                  AS pos
    FROM responses r JOIN items i ON r.item_id = i.item_id
    GROUP BY r.student_id, r.exam_id
    """
    out = {}
    for row in _rows(con, q):
        s = 100.0 * row["got"] / row["pos"] if row["pos"] else 0.0
        out.setdefault(row["student_id"], {})[row["exam_id"]] = round(s, 1)
    return out


def percentile(scores_latest):
    """Cohort percentile from latest-exam overall scores."""
    vals = sorted(scores_latest.values())
    n = len(vals)
    out = {}
    for sid, sc in scores_latest.items():
        below = sum(1 for v in vals if v < sc)
        out[sid] = round(100.0 * below / max(n - 1, 1))
    return out


def topic_weights(con, latest):
    """How much each topic 'matters' on the exam = its share of items
    (frequency proxy). Used to prioritise recommendations by payoff."""
    q = """SELECT topic, COUNT(*) AS n FROM items
           WHERE exam_id = ? GROUP BY topic"""
    rows = _rows(con, q, (latest,))
    total = sum(r["n"] for r in rows) or 1
    return {r["topic"]: r["n"] / total for r in rows}


def study_plan(mastery_latest, weights):
    """Personalised, prioritised plan: target the weak topics that are also
    heavily tested (highest gap x exam-weight). `est_gain` is an EXPLAINABLE
    HEURISTIC (raise a topic by a capped step toward a target, weighted by its
    exam share) -- an opportunity estimate, NOT a validated prediction."""
    rows = []
    for t, m in mastery_latest.items():
        w = weights.get(t, 0.0)
        target = min(m + 25.0, 90.0)          # an achievable term target
        if target <= m:                        # already mastered -> skip
            continue
        gap = 100.0 - m
        est_gain = round((target - m) * w, 1)  # contribution to overall score
        if est_gain <= 0:
            continue
        rows.append({"topic": t, "mastery": m, "weight_pct": round(w * 100, 1),
                     "target": round(target, 1), "est_gain": est_gain,
                     "priority": gap * w})
    rows.sort(key=lambda r: r["priority"], reverse=True)
    plan = rows[:4]
    for i, r in enumerate(plan):
        r["week"] = (i // 2) + 1               # sequence into a 2-week plan
        r["practice"] = PRACTICE.get(r["topic"], "")
        del r["priority"]
    return plan


def build():
    con = sqlite3.connect(DB)
    students = {s["student_id"]: s for s in _rows(con, "SELECT * FROM students")}
    exams = [r["exam_id"] for r in
             _rows(con, "SELECT DISTINCT exam_id FROM items ORDER BY exam_id")]
    topics = [r["topic"] for r in
              _rows(con, "SELECT DISTINCT topic FROM items ORDER BY topic")]
    latest = exams[-1]
    weights = topic_weights(con, latest)

    mastery = topic_mastery(con)
    overall = overall_by_exam(con)
    latest_scores = {sid: overall[sid][latest] for sid in overall
                     if latest in overall[sid]}
    pct = percentile(latest_scores)

    # per-student record
    student_records = {}
    for sid, s in students.items():
        m_latest = mastery.get(sid, {}).get(latest, {})
        weakest = sorted(m_latest.items(), key=lambda kv: kv[1])[:3]
        trend = [overall.get(sid, {}).get(e) for e in exams]
        plan = study_plan(m_latest, weights)
        projected = round((latest_scores.get(sid) or 0)
                          + sum(p["est_gain"] for p in plan), 1)
        student_records[sid] = {
            "student_id": sid, "name": s["name"], "class_id": s["class_id"],
            "score_latest": latest_scores.get(sid),
            "percentile": pct.get(sid),
            "projected_score": projected,
            "trend": trend,
            "mastery_latest": m_latest,
            "mastery_history": mastery.get(sid, {}),
            "weak_topics": [t for t, _ in weakest],
            "study_plan": plan,
        }

    # class-level weakness heatmap (mean mastery per topic, latest exam)
    classes = {}
    for cls in sorted({s["class_id"] for s in students.values()}):
        members = [sid for sid, s in students.items() if s["class_id"] == cls]
        heat = {}
        for t in topics:
            vals = [mastery.get(sid, {}).get(latest, {}).get(t)
                    for sid in members]
            vals = [v for v in vals if v is not None]
            heat[t] = round(sum(vals) / len(vals), 1) if vals else None
        weakest_class = sorted(heat.items(), key=lambda kv: kv[1])[:3]
        classes[cls] = {
            "class_id": cls, "n_students": len(members),
            "heatmap": heat,
            "weakest_topics": [t for t, _ in weakest_class],
            "avg_score": round(
                sum(latest_scores[sid] for sid in members) / len(members), 1),
            "students": sorted(
                members, key=lambda sid: latest_scores.get(sid, 0),
                reverse=True),
        }

    payload = {
        "generated_for": "升學型補習班 模考診斷 Demo",
        "exams": exams, "topics": topics, "latest_exam": latest,
        "classes": classes, "students": student_records,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    con.close()
    print(f"Processed -> {len(student_records)} students, "
          f"{len(classes)} classes, {len(topics)} topics  "
          f"(json: {os.path.relpath(OUT)})")
    return payload


if __name__ == "__main__":
    build()
