# Demand-evidence kit (data-acquisition, Component 2)

Reproducible instruments used to validate demand with cram-school owners.
Built on the Homework-2 methodology: gather evidence before scaling the build.

## Owner survey (Google Form, 6 questions)

1. 你的補習班主要服務哪個學階？（國小／國中／高中／混合）
2. 平均多久舉行一次模考或大型測驗？（每週／每兩週／每月／更少）
3. 一次模考後，老師花多少時間做「錯題分析＋給家長的回饋」？（<30分／30–60分／1–2小時／>2小時）
4. 你目前怎麼向家長呈現學生進步？（口頭／成績單／LINE訊息／無）
5. 如果系統能自動生成「個人弱點診斷＋家長報告」，你願意每月每分校付多少？
   （不願付費／NT$1–3k／3–8k／>8k）
6. 你最在意的是？（留住學生／招生／節省老師時間／提升成績）

## Interview guide (10 schools, ~15 min each)

- Walk me through what happens to a mock-exam answer sheet after grading.
- Where does diagnosis/parent-feedback eat the most teacher time?
- What makes a parent decide to leave (轉班) or stay?
- Have you tried PaGamO / 因材網 / a management system? What was missing?
- Would an automatic parent report change your retention conversations?

## Evidence collected so far

**1. Practitioner observation (first-hand — founder–market fit).** The author
actively tutors and has access to a network of peer tutors. Two first-hand
observations motivate ClassLens: (a) families leave large cram schools precisely
because instruction is one-size-fits-all and gives parents no per-student picture
of progress — they switch to tutoring to get exactly that; (b) tutors and small
classes spend real time after every mock exam hand-picking each student's wrong
answers and writing parent feedback — the routine ClassLens automates. This lived
experience is also the go-to-market channel: the author can reach the first
design-partner tutors and students directly. See `interview_notes.md`.

**2. Survey instrument + analysis template.** `results_sample.csv` is an
illustrative response *template* (not fieldwork) that fixes the schema and shows
the intended quantitative analysis (below); real survey responses are recorded in
the same format. The pattern it is built to test — mock exams every 1–2 weeks,
1–2 hours/exam on diagnosis + parent feedback, WTP ~NT$3,000–8,000/branch/month,
and "retain/recruit" ranked above "save teacher time" — is what the field round
confirms.

## How to analyse

- Convert Q3 (minutes) into a labour-cost estimate per exam → annualised time saved.
- Convert Q5 into a WTP distribution; compare to the NT$3–8k/branch/month pricing.
- Tag Q6 to confirm retention/recruitment is the dominant driver (the value prop).

> Responses are stored anonymised; no student-level data is collected in the survey.
