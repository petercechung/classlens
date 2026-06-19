"""
Delivery layer.

Writes two static, deployable files into public/ (which already contains the
processed data.json):

    index.html    Teacher dashboard  -- class weakness heatmap, ranked students,
                                        weakest topics, links to parent reports.
    report.html   Parent report      -- ?student=<id>; radar of topic mastery,
                                        term trend, strengths/weaknesses,
                                        targeted practice. Print-friendly.

Both are static + read data.json at runtime, so the whole /public folder can be
dropped on Vercel/Render/GitHub Pages as a read-only demo.
"""
import os

PUB = os.path.join(os.path.dirname(__file__), "..", "public")

DASHBOARD = r"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ClassLens · 教師診斷後台</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
 :root{--bg:#0f172a;--card:#1e293b;--ink:#e2e8f0;--mut:#94a3b8;--accent:#38bdf8;--bad:#f87171;--ok:#4ade80}
 *{box-sizing:border-box} body{margin:0;font-family:-apple-system,"Noto Sans TC",sans-serif;background:#f1f5f9;color:#0f172a}
 header{background:var(--bg);color:#fff;padding:18px 24px}
 header h1{margin:0;font-size:20px} header p{margin:4px 0 0;color:var(--mut);font-size:13px}
 .wrap{max-width:1100px;margin:0 auto;padding:20px}
 .tabs{display:flex;gap:8px;margin:16px 0}
 .tabs button{border:0;padding:8px 16px;border-radius:8px;background:#e2e8f0;cursor:pointer;font-size:14px}
 .tabs button.active{background:#0f172a;color:#fff}
 .kpis{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px}
 .kpi{background:#fff;border-radius:12px;padding:14px 18px;box-shadow:0 1px 3px rgba(0,0,0,.08);flex:1;min-width:150px}
 .kpi b{font-size:24px} .kpi span{color:#64748b;font-size:13px;display:block}
 .card{background:#fff;border-radius:12px;padding:18px;box-shadow:0 1px 3px rgba(0,0,0,.08);margin-bottom:16px}
 .card h2{margin:0 0 12px;font-size:16px}
 table{width:100%;border-collapse:collapse;font-size:14px}
 th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #eef2f7}
 th{color:#64748b;font-weight:600}
 .chip{display:inline-block;background:#fee2e2;color:#b91c1c;padding:2px 8px;border-radius:999px;font-size:12px;margin:2px}
 a.btn{color:#0369a1;text-decoration:none;font-weight:600}
 .heatcell{padding:8px;border-radius:6px;text-align:center;color:#0f172a;font-size:13px}
</style></head>
<body>
<header><h1>ClassLens · 模考診斷後台</h1>
<p>把你已經在收的答案卡，變成留得住學生、說服得了家長的診斷 — 教學交給老師，診斷交給系統。
<a href="student.html" style="color:#38bdf8;margin-left:8px;text-decoration:none">學生入口 →</a></p></header>
<div class="wrap">
 <div class="tabs" id="tabs"></div>
 <div class="kpis" id="kpis"></div>
 <div class="card"><h2>單元弱點熱圖（最近一次模考，平均掌握度 %）</h2>
   <div id="heat"></div></div>
 <div class="card"><h2>班級弱點 Top 3（建議下週補強）</h2><div id="weak"></div></div>
 <div class="card"><h2>學生名單（依難度校正分數排序）</h2>
   <table><thead><tr><th>排名</th><th>姓名</th><th>校正分數</th><th>百分位</th><th>預期提分</th><th>最弱單元</th><th>個人化建議書</th></tr></thead>
   <tbody id="rows"></tbody></table></div>
</div>
<script>
let DATA, current;
fetch('data.json').then(r=>r.json()).then(d=>{DATA=d;current=Object.keys(d.classes)[0];render();});
function color(v){if(v==null)return '#f1f5f9';const t=Math.max(0,Math.min(100,v))/100;
  const r=Math.round(248-(248-74)*t),g=Math.round(113+(222-113)*t),b=Math.round(113+(128-113)*t);
  return `rgb(${r},${g},${b})`;}
function render(){
  const tabs=document.getElementById('tabs');tabs.innerHTML='';
  Object.keys(DATA.classes).forEach(c=>{const b=document.createElement('button');
    b.textContent=c;b.className=c===current?'active':'';b.onclick=()=>{current=c;render();};tabs.appendChild(b);});
  const cls=DATA.classes[current];
  document.getElementById('kpis').innerHTML=
    `<div class="kpi"><b>${cls.n_students}</b><span>學生人數</span></div>
     <div class="kpi"><b>${cls.avg_score}</b><span>班級平均（校正分數）</span></div>
     <div class="kpi"><b>${cls.weakest_topics[0]}</b><span>全班最弱單元</span></div>`;
  // heatmap
  let h='<table><tr>'+DATA.topics.map(t=>`<th style="font-size:12px">${t}</th>`).join('')+'</tr><tr>';
  h+=DATA.topics.map(t=>{const v=cls.heatmap[t];
    return `<td><div class="heatcell" style="background:${color(v)}">${v==null?'–':v}</div></td>`;}).join('');
  h+='</tr></table>';document.getElementById('heat').innerHTML=h;
  document.getElementById('weak').innerHTML=cls.weakest_topics.map(t=>`<span class="chip">${t}</span>`).join(' ');
  // rows
  document.getElementById('rows').innerHTML=cls.students.map((sid,i)=>{const s=DATA.students[sid];
    const gain=(s.projected_score-s.score_latest).toFixed(1);
    return `<tr><td>${i+1}</td><td>${s.name}</td><td>${s.score_latest}</td><td>${s.percentile}%</td>
      <td style="color:#15803d;font-weight:600">+${gain}</td>
      <td>${s.weak_topics.map(t=>`<span class="chip">${t}</span>`).join('')}</td>
      <td><a class="btn" href="report.html?student=${sid}" target="_blank">開啟 ↗</a></td></tr>`;}).join('');
}
</script></body></html>
"""

REPORT = r"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ClassLens · 學習診斷報告</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
 body{margin:0;font-family:-apple-system,"Noto Sans TC",sans-serif;background:#f1f5f9;color:#0f172a}
 .sheet{max-width:760px;margin:24px auto;background:#fff;border-radius:14px;padding:32px;box-shadow:0 2px 10px rgba(0,0,0,.08)}
 .top{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:3px solid #0f172a;padding-bottom:12px}
 .top h1{margin:0;font-size:22px} .top .meta{color:#64748b;font-size:13px;text-align:right}
 .grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:20px}
 .panel h3{margin:0 0 8px;font-size:15px;color:#0f172a}
 .summary{background:#f0f9ff;border-left:4px solid #38bdf8;padding:12px 14px;border-radius:6px;margin-top:18px;font-size:14px;line-height:1.7}
 .rec{margin-top:18px} .rec h3{font-size:15px;margin:0 0 8px}
 .rec li{margin-bottom:6px;font-size:14px}
 .good{color:#15803d;font-weight:600}.bad{color:#b91c1c;font-weight:600}
 .proj{display:flex;align-items:center;gap:16px;margin-top:18px;background:#0f172a;color:#fff;border-radius:10px;padding:14px 18px}
 .proj div span{display:block;font-size:12px;color:#94a3b8}.proj div b{font-size:26px}
 .proj .arrow{font-size:24px;color:#38bdf8}
 .proj .up{margin-left:auto;background:#15803d;padding:8px 14px;border-radius:8px;font-weight:700}
 table.plan{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}
 table.plan th,table.plan td{border-bottom:1px solid #eef2f7;padding:6px 8px;text-align:left}
 table.plan th{color:#64748b;font-weight:600;font-size:12px}
 .note{margin-top:18px;border:1px dashed #cbd5e1;border-radius:8px;padding:12px;color:#64748b;font-size:13px}
 @media print{body{background:#fff}.sheet{box-shadow:none;margin:0}}
</style></head>
<body><div class="sheet" id="sheet">載入中…</div>
<script>
const sid=new URLSearchParams(location.search).get('student');
fetch('data.json').then(r=>r.json()).then(d=>{
  const s=d.students[sid]; if(!s){document.getElementById('sheet').textContent='找不到學生';return;}
  const topics=d.topics, mast=s.mastery_latest;
  const strengths=Object.entries(mast).sort((a,b)=>b[1]-a[1]).slice(0,2).map(x=>x[0]);
  const gain=(s.projected_score-s.score_latest).toFixed(1);
  document.getElementById('sheet').innerHTML=`
   <div class="top"><div><h1>個人化學習診斷與建議書</h1>
     <div style="color:#64748b;font-size:14px">${s.name}　${s.class_id}</div></div>
     <div class="meta">ClassLens 模考診斷<br>最近一次：${d.latest_exam}<br>班級百分位：第 ${s.percentile} 百分位</div></div>
   <div class="proj">
     <div><span>目前校正分數</span><b>${s.score_latest}</b></div>
     <div class="arrow">→</div>
     <div><span>依建議練習後預期</span><b class="good">${s.projected_score}</b></div>
     <div class="up">預期可提升 +${gain} 分</div>
   </div>
   <div class="grid">
     <div class="panel"><h3>單元掌握度</h3><canvas id="radar" height="240"></canvas></div>
     <div class="panel"><h3>三次模考成績趨勢</h3><canvas id="trend" height="240"></canvas></div>
   </div>
   <div class="summary">優勢單元：<span class="good">${strengths.join('、')}</span>；
     最該補強：<span class="bad">${s.weak_topics.join('、')}</span>。成績趨勢${trendWord(s.trend)}。
     下方為依「弱點 × 考試比重」排序的<b>個人化兩週學習計畫</b>，預估若完成可提升約 <b>${gain}</b> 分。</div>
   <div class="rec"><h3>個人化學習計畫（先做 CP 值最高的）</h3>
   <table class="plan"><thead><tr><th>週次</th><th>單元</th><th>目前</th><th>考試比重</th><th>目標</th><th>預期貢獻</th><th>建議練習</th></tr></thead><tbody>
     ${s.study_plan.map(r=>`<tr><td>W${r.week}</td><td><b>${r.topic}</b></td><td>${r.mastery}</td>
       <td>${r.weight_pct}%</td><td>${r.target}</td><td class="good">+${r.est_gain}</td><td>${r.practice}</td></tr>`).join('')}
   </tbody></table></div>
   <div class="note">導師評語：____________________________________________（由老師補充；系統只負責診斷、建議與排版，教學judgment仍由老師掌握）</div>`;
  new Chart(document.getElementById('radar'),{type:'radar',
    data:{labels:topics,datasets:[{label:'掌握度',data:topics.map(t=>mast[t]??0),
      backgroundColor:'rgba(56,189,248,.2)',borderColor:'#0284c7',pointBackgroundColor:'#0284c7'}]},
    options:{scales:{r:{min:0,max:100,ticks:{stepSize:25}}},plugins:{legend:{display:false}}}});
  new Chart(document.getElementById('trend'),{type:'line',
    data:{labels:d.exams,datasets:[{label:'校正分數',data:s.trend,borderColor:'#0284c7',
      backgroundColor:'rgba(56,189,248,.2)',fill:true,tension:.3}]},
    options:{scales:{y:{min:0,max:100}},plugins:{legend:{display:false}}}});
});
function trendWord(t){const v=t.filter(x=>x!=null);if(v.length<2)return '尚需更多次模考觀察';
  const d=v[v.length-1]-v[0];return d>3?'穩定進步（↑ '+d.toFixed(1)+' 分）':d<-3?'近期下滑，需注意':'大致持平';}
</script></body></html>
"""


STUDENT = r"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ClassLens · 學生個人化學習報告</title>
<style>
 body{margin:0;font-family:-apple-system,"Noto Sans TC",sans-serif;background:#f1f5f9;color:#0f172a}
 header{background:#0f172a;color:#fff;padding:18px 24px}
 header h1{margin:0;font-size:20px} header p{margin:4px 0 0;color:#94a3b8;font-size:13px}
 .wrap{max-width:560px;margin:40px auto;padding:0 20px}
 .card{background:#fff;border-radius:14px;padding:28px;box-shadow:0 2px 10px rgba(0,0,0,.06)}
 .card h2{margin:0 0 4px;font-size:18px}.card .sub{color:#64748b;font-size:13px;margin-bottom:20px}
 label{display:block;font-size:13px;color:#475569;margin:14px 0 6px;font-weight:600}
 select,button{width:100%;font-size:15px;padding:11px 12px;border-radius:9px;border:1px solid #cbd5e1;background:#fff}
 button{margin-top:22px;background:#0284c7;color:#fff;border:0;font-weight:700;cursor:pointer}
 button:disabled{background:#cbd5e1;cursor:not-allowed}
 .tabs{display:flex;gap:8px;flex-wrap:wrap}
 .tabs button{width:auto;margin:0;padding:7px 14px;background:#e2e8f0;color:#0f172a;font-weight:500;font-size:14px}
 .tabs button.active{background:#0f172a;color:#fff}
 .note{margin-top:18px;color:#94a3b8;font-size:12px;line-height:1.6}
</style></head>
<body>
<header><h1>ClassLens · 學生個人化學習報告</h1>
<p>選擇你的班級與姓名，查看你的弱點診斷與兩週學習計畫。</p></header>
<div class="wrap"><div class="card">
  <h2>查看我的學習報告</h2>
  <div class="sub">輸入身分後，系統會給你一份專屬的個人化建議。</div>
  <label>班級</label><div class="tabs" id="tabs"></div>
  <label>姓名</label><select id="stu"></select>
  <button id="go" disabled>查看我的個人化報告 →</button>
  <div class="note">示範版可自由選擇姓名；正式版需以帳號登入，學生僅能查看本人報告（符合個資保護）。</div>
</div></div>
<script>
let DATA, cls;
fetch('data.json').then(r=>r.json()).then(d=>{DATA=d;cls=Object.keys(d.classes)[0];render();});
function render(){
  const tabs=document.getElementById('tabs');tabs.innerHTML='';
  Object.keys(DATA.classes).forEach(c=>{const b=document.createElement('button');
    b.textContent=c;b.className=c===cls?'active':'';b.onclick=()=>{cls=c;render();};tabs.appendChild(b);});
  const sel=document.getElementById('stu');
  const ids=DATA.classes[cls].students.slice().sort((a,b)=>DATA.students[a].name.localeCompare(DATA.students[b].name));
  sel.innerHTML='<option value="">— 請選擇 —</option>'+ids.map(id=>`<option value="${id}">${DATA.students[id].name}</option>`).join('');
  const go=document.getElementById('go');
  sel.onchange=()=>{go.disabled=!sel.value;};
  go.onclick=()=>{if(sel.value)location.href='report.html?student='+sel.value;};
  go.disabled=true;
}
</script></body></html>
"""


def write():
    os.makedirs(PUB, exist_ok=True)
    with open(os.path.join(PUB, "index.html"), "w", encoding="utf-8") as f:
        f.write(DASHBOARD)
    with open(os.path.join(PUB, "report.html"), "w", encoding="utf-8") as f:
        f.write(REPORT)
    with open(os.path.join(PUB, "student.html"), "w", encoding="utf-8") as f:
        f.write(STUDENT)
    print(f"Delivered -> index.html, report.html, student.html "
          f"(dir: {os.path.relpath(PUB)})")


if __name__ == "__main__":
    write()
