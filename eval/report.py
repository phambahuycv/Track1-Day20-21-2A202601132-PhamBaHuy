"""Sinh report.html TĨNH (1 file, mở bằng double-click, không cần server/mạng).

Đọc results.jsonl + verdicts.jsonl + labels.csv, nhúng toàn bộ dữ liệu vào HTML.
Nhãn pass/fail/uncertain KÈM NOTE NGẮN bấm/nhập trong report, lưu vào localStorage
của trình duyệt (dạng {label, note}; đọc được cả bản cũ lưu string thuần);
nút "Export labels.csv" tải về CSV 3 cột scenario_id,label,note để đưa lại cho
judge.py so agreement.
"""
import csv, json, os, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def read_labels(path="labels.csv"):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return {r["scenario_id"]: r.get("label", "").strip()
                for r in csv.DictReader(f) if r.get("scenario_id")}

def main():
    results = read_jsonl("results.jsonl")
    verdicts = {v["scenario_id"]: v for v in read_jsonl("verdicts.jsonl")}
    labels = read_labels()
    if not results:
        print("Chưa có results.jsonl — report sẽ trống. Chạy python3 eval/run_eval.py trước.")
    # Gộp 3 nguồn thành 1 list row để nhúng vào HTML
    rows = []
    for r in results:
        sid = r.get("scenario_id", "?")
        rows.append({"scenario_id": sid, "input": r.get("input", ""),
                     "slide": r.get("slide"),
                     "output": r.get("output"), "error": r.get("error"),
                     "raw_content": r.get("raw_content", ""),
                     "latency_s": r.get("latency_s"), "cost_usd": r.get("cost_usd"),
                     "verdict": verdicts.get(sid, {}).get("verdict"),
                     "rationale": verdicts.get(sid, {}).get("rationale", ""),
                     "human_label": labels.get(sid, "")})
    html = TEMPLATE.replace("__DATA__", json.dumps(rows, ensure_ascii=False))
    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Đã sinh report.html (%d dòng dữ liệu). Mở bằng: open report.html" % len(rows))

# Giao diện: mọi logic render/lọc/gán nhãn chạy hoàn toàn trong trình duyệt.
TEMPLATE = """<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Eval report — AI Tutor</title><style>
body{font-family:-apple-system,system-ui,sans-serif;margin:0;background:#f6f7f9;color:#222}
header{position:sticky;top:0;background:#fff;border-bottom:1px solid #e2e4e8;padding:10px 16px;display:flex;gap:10px;flex-wrap:wrap;align-items:center;z-index:9}
h1{font-size:16px;margin:0 12px 0 0}
select,button{font-size:13px;padding:5px 10px;border:1px solid #ccd;border-radius:6px;background:#fff;cursor:pointer}
main{max-width:960px;margin:16px auto;padding:0 12px}
.card{background:#fff;border:1px solid #e2e4e8;border-radius:10px;padding:14px;margin-bottom:14px}
.q{font-weight:600;margin-bottom:8px}
.meta{font-size:12px;color:#778;margin-bottom:8px}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:12px;font-weight:600}
.pass{background:#e3f5e9;color:#176b36}.fail{background:#fde8e8;color:#a32727}.uncertain{background:#fdf3dc;color:#8a6100}
.src{font-size:13px;background:#f4f6f8;border-left:3px solid #9db4c8;padding:6px 10px;margin:6px 0;border-radius:0 6px 6px 0}
.src code{color:#356}
.fu{margin:4px 0 4px 18px;font-size:14px}
.raw{display:none;white-space:pre-wrap;background:#1d1f24;color:#d6dce4;font-size:12px;padding:10px;border-radius:8px;overflow:auto;max-height:320px}
.lbl button.on{background:#223;color:#fff;border-color:#223}
.note{font-size:12px;padding:4px 8px;border:1px solid #ccd;border-radius:6px;width:230px}
.rat{font-size:13px;color:#555;margin-top:6px}
</style></head><body>
<header><h1>Eval report — AI Tutor</h1>
Lọc verdict: <select id="flt"><option value="">Tất cả</option><option>pass</option><option>fail</option><option>uncertain</option><option value="none">(chưa chấm)</option></select>
<button onclick="exportCsv()">Export labels.csv</button><span id="stat"></span></header>
<main id="list"></main>
<script>
var ROWS=__DATA__, KEY="evalkit-labels";
var saved={};try{saved=JSON.parse(localStorage.getItem(KEY)||"{}")}catch(e){}
// tương thích ngược: bản cũ lưu value là string label thuần -> coi như {label, note:""}
function norm(v){return typeof v=="string"?{label:v,note:""}:(v||{label:"",note:""})}
function cur(sid,human){var s=saved[sid];return s?norm(s):{label:human||"",note:""}}
function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function badge(v){return v?'<span class="badge '+v+'">judge: '+v+'</span>':'<span class="badge">chưa chấm</span>'}
function render(){
 var f=document.getElementById("flt").value,el=document.getElementById("list"),h="",n=0;
 ROWS.forEach(function(r,i){
  if(f&&((f=="none"&&r.verdict)||(f!="none"&&r.verdict!=f)))return;n++;
  var o=r.output||{},c=cur(r.scenario_id,r.human_label),lbl=c.label;
  h+='<div class="card"><div class="meta">'+esc(r.scenario_id)+' &middot; '+esc(o.scope||"")+
  (r.latency_s!=null?' &middot; '+r.latency_s+'s':'')+(r.cost_usd!=null?' &middot; ~$'+r.cost_usd:'')+'</div>';
  if(r.slide)h+='<div class="meta" style="color:#346">Đang xem slide '+esc(r.slide.id)+' — '+esc(r.slide.title)+(r.slide.keyword?' &middot; từ khoá: <b>'+esc(r.slide.keyword)+'</b>':'')+'</div>';
  h+='<div class="q">'+esc(r.input)+'</div>';
  if(r.error)h+='<div class="badge fail">lỗi chạy</div><div class="rat">'+esc(r.error)+'</div>';
  else{h+='<div>'+esc(o.answer||"(không parse được answer)")+'</div>';
   (o.sources||[]).forEach(function(s){h+='<div class="src"><code>'+esc(s.doc_id)+'#'+esc(s.section_id)+'</code> — “'+esc(s.quote)+'”</div>'});
   if(o.followup_questions)h+='<div style="margin-top:6px"><b>Gợi ý hỏi tiếp:</b></div>'+o.followup_questions.map(function(q){return '<div class="fu">• '+esc(q)+'</div>'}).join("");}
  h+='<div style="margin-top:10px">'+badge(r.verdict)+' <span class="rat">'+esc(r.rationale)+'</span></div>'+
  '<div class="lbl" style="margin-top:8px">Nhãn người: '+["pass","fail","uncertain"].map(function(v){
   return '<button data-i="'+i+'" data-v="'+v+'" class="'+(lbl==v?"on":"")+'" onclick="setLabel(this)">'+v+'</button>'}).join(" ")+
  ' <input type="text" class="note" data-i="'+i+'" placeholder="note ngắn (vd: fail vì citation)" value="'+esc(c.note)+'" onchange="setNote(this)">'+
  ' <button data-i="'+i+'" onclick="raw(this)">xem raw</button></div>'+
  '<div class="raw">'+esc(r.raw_content||JSON.stringify(o,null,2))+'</div></div>';});
 el.innerHTML=h||"<p>Không có dòng nào khớp bộ lọc.</p>";
 document.getElementById("stat").textContent=n+"/"+ROWS.length+" dòng";}
function setLabel(b){var r=ROWS[b.dataset.i],c=cur(r.scenario_id,r.human_label);
 if(c.label==b.dataset.v){if(c.note)saved[r.scenario_id]={label:"",note:c.note};else delete saved[r.scenario_id]}
 else saved[r.scenario_id]={label:b.dataset.v,note:c.note};
 localStorage.setItem(KEY,JSON.stringify(saved));render();}
function setNote(inp){var r=ROWS[inp.dataset.i],c=cur(r.scenario_id,r.human_label),n=inp.value.trim();
 if(!n&&!c.label)delete saved[r.scenario_id];else saved[r.scenario_id]={label:c.label,note:n};
 localStorage.setItem(KEY,JSON.stringify(saved));}
function raw(b){var d=b.closest(".card").querySelector(".raw");d.style.display=d.style.display=="block"?"none":"block";}
function exportCsv(){var s="scenario_id,label,note\\n";
 function q(x){return '"'+String(x==null?"":x).replace(/"/g,'""')+'"'}
 ROWS.forEach(function(r){var c=cur(r.scenario_id,r.human_label);
  s+=q(r.scenario_id)+","+q(c.label)+","+q(c.note)+"\\n"});
 var a=document.createElement("a");a.href=URL.createObjectURL(new Blob([s],{type:"text/csv"}));
 a.download="labels.csv";a.click();}
document.getElementById("flt").onchange=render;render();
</script></body></html>"""

if __name__ == "__main__":
    main()
