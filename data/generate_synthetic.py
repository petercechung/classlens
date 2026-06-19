"""
Generate realistic synthetic mock-exam (模考) data for a high-school cram school.

This stands in for the data a cram school ALREADY collects every week
(answer sheets / 答案卡) but currently throws away after computing a raw score.

Output (written to data/raw/):
    students.csv   student_id, name, class_id
    items.csv      item_id, exam_id, topic, difficulty, max_score
    responses.csv  student_id, exam_id, item_id, is_correct, score

The response model is a simple Item Response Theory (IRT) style logistic:
    P(correct) = sigmoid( ability(student, topic) - difficulty(item) )
so weak students systematically miss hard items in their weak topics,
which is exactly the structure the diagnostic engine must recover.
"""
import csv
import math
import os
import random

random.seed(42)

OUT = os.path.join(os.path.dirname(__file__), "raw")
os.makedirs(OUT, exist_ok=True)

# --- exam design: 高三 數學A, three mock exams across a term ---------------
EXAMS = ["MOCK01", "MOCK02", "MOCK03"]          # chronological
TOPICS = [
    "多項式函數", "指數與對數", "三角函數", "數列與級數",
    "排列組合", "機率與統計", "平面向量", "空間向量",
]
CLASSES = ["A班", "B班", "C班"]
STUDENTS_PER_CLASS = 25
ITEMS_PER_EXAM = 40

GIVEN_NAMES = ["承翰","宇翔","詩涵","欣怡","冠廷","雅婷","柏宇","思妤","品妍","彥廷",
               "佳穎","俊傑","怡君","志豪","靜宜","建宏","美玲","家豪","婉婷","哲瑋",
               "淑芬","昱安","郁婷","信宏","曉涵","柏翰","若涵","俊宏","佩珊","冠勳"]
SURNAMES = ["陳","林","黃","張","李","王","吳","劉","蔡","楊","許","鄭","謝","郭","洪"]


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def make_students():
    students = []
    sid = 1001
    for class_id in CLASSES:
        # each class has a slightly different baseline ability
        class_base = {"A班": 0.6, "B班": 0.0, "C班": -0.5}[class_id]
        for _ in range(STUDENTS_PER_CLASS):
            name = random.choice(SURNAMES) + random.choice(GIVEN_NAMES)
            # latent ability per topic (this is the ground truth we try to recover)
            ability = {t: random.gauss(class_base, 0.8) for t in TOPICS}
            # term-long drift: students improve a bit over the three exams
            drift = random.uniform(0.05, 0.35)
            students.append({
                "student_id": f"S{sid}", "name": name, "class_id": class_id,
                "_ability": ability, "_drift": drift,
            })
            sid += 1
    return students


def make_items():
    items = []
    iid = 1
    for exam_id in EXAMS:
        for _ in range(ITEMS_PER_EXAM):
            topic = random.choice(TOPICS)
            difficulty = round(random.uniform(-1.2, 1.2), 3)   # IRT difficulty
            items.append({
                "item_id": f"{exam_id}-Q{iid:03d}", "exam_id": exam_id,
                "topic": topic, "difficulty": difficulty, "max_score": 5,
            })
            iid += 1
    return items


def make_responses(students, items):
    rows = []
    for s in students:
        for exam_idx, exam_id in enumerate(EXAMS):
            for it in [i for i in items if i["exam_id"] == exam_id]:
                ability = s["_ability"][it["topic"]] + s["_drift"] * exam_idx
                p = sigmoid(ability - it["difficulty"])
                is_correct = 1 if random.random() < p else 0
                rows.append({
                    "student_id": s["student_id"], "exam_id": exam_id,
                    "item_id": it["item_id"], "is_correct": is_correct,
                    "score": it["max_score"] if is_correct else 0,
                })
    return rows


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fields})


def main():
    students = make_students()
    items = make_items()
    responses = make_responses(students, items)

    write_csv(os.path.join(OUT, "students.csv"), students,
              ["student_id", "name", "class_id"])
    write_csv(os.path.join(OUT, "items.csv"), items,
              ["item_id", "exam_id", "topic", "difficulty", "max_score"])
    write_csv(os.path.join(OUT, "responses.csv"), responses,
              ["student_id", "exam_id", "item_id", "is_correct", "score"])

    print(f"Wrote {len(students)} students, {len(items)} items, "
          f"{len(responses)} responses to {OUT}")


if __name__ == "__main__":
    main()
