"""Test cho eval-kit — chạy từ root repo: python3 tests/test_eval_kit.py

Hai tầng:
- Offline (mặc định, không cần API key): normalize/retrieve/parse/slide context,
  vòng tool-calling với chat GIẢ (mock), judge prompt, cost estimate.
- Live (EVAL_LIVE=1 python3 tests/test_eval_kit.py): gọi gateway thật 3 câu để chứng
  minh vòng tool-calling chạy được với model thật.
"""
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "eval"))    # judge, run_eval, tracing
sys.path.insert(0, os.path.join(_ROOT, "tutor"))   # tutor

import tutor

PASS, FAIL = 0, 0

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  ok  %s" % name)
    else:
        FAIL += 1
        print("  FAIL %s  %s" % (name, detail))

print("== Tầng 1: text utils ==")
check("normalize bỏ dấu", tutor.normalize("Câu hỏi Đắc") == "cau hoi dac")
check("tokens tách từ", tutor.tokens("LLM judge là gì?") == ["llm", "judge", "là", "gì"] or
      tutor.tokens("LLM judge la gi?") == ["llm", "judge", "la", "gi"])
check("slugify heading", tutor.slugify("Types of Graders for Agents") == "types-of-graders-for-agents")

print("== Tầng 2: corpus & retrieve ==")
sections = tutor.load_corpus()
check("corpus có sections", len(sections) > 50, "có %d sections" % len(sections))
doc_ids = {s["doc_id"] for s in sections}
check("đủ 18 docs", len(doc_ids) == 18, "có %d doc_id" % len(doc_ids))
hits = tutor.retrieve_corpus("calibration judge là gì")
check("retrieve calibration ra slide deck", any(s["doc_id"] == "slide-day19-20" for s in hits),
      str([(s["doc_id"], s["section_id"]) for s in hits]))
hits2 = tutor.retrieve_corpus("context richness user input grid")
check("retrieve input grid trúng s22/s23", any(s["section_id"] in ("s27", "s29") for s in hits2),
      str([(s["doc_id"], s["section_id"]) for s in hits2]))
check("retrieve câu vô nghĩa không crash", tutor.retrieve_corpus("asds lkkljl") == [])

print("== Tầng 3: kb_search local (đúng shape platform) ==")
r = tutor.kb_search_local("confusion matrix judge", max_results=3)
check("kb_search shape", r["tool"] == "kb_search" and isinstance(r["results"], list)
      and r["source_count"] == len(r["results"]))
check("kb_search tôn trọng max_results", r["source_count"] <= 3)
check("kb_search kết quả đủ field", all(set(x) == {"doc_id", "section_id", "text"} for x in r["results"]))

print("== Tầng 4: parse JSON output ==")
check("parse JSON sạch", tutor.parse_json_content('{"a": 1}') == {"a": 1})
check("parse JSON bọc fence", tutor.parse_json_content('```json\n{"a": 1}\n```') == {"a": 1})
broken = tutor.parse_json_content('{"a": "cắt giữa chừng...')
check("JSON vỡ -> _parse_error không raise", broken.get("_parse_error") is True and "raw" in broken)
check("không có JSON -> _parse_error", tutor.parse_json_content("không có gì hết").get("_parse_error") is True)
# Regression: deepseek nhả xuống dòng THẬT giữa string value (đã gặp live 20/08)
raw_nl = tutor.parse_json_content('{"scope": "in_scope", "answer": "dòng 1\ndòng 2"}')
check("JSON có newline thật trong string -> parse lỏng được",
      raw_nl.get("answer") == "dòng 1\ndòng 2" and not raw_nl.get("_parse_error"))
really_broken = tutor.parse_json_content('{"a": 1, "b": }')
check("JSON sai cú pháp thật -> vẫn _parse_error", really_broken.get("_parse_error") is True)

print("== Tầng 5: slide context ==")
check("slide None -> rỗng", tutor.format_slide_context(None) == "")
ctx = tutor.format_slide_context({"id": "s51", "title": "T", "keyword": "calibration"})
check("slide đầy đủ", 's51' in ctx and '"calibration"' in ctx and "Ngữ cảnh" in ctx)
ctx2 = tutor.format_slide_context({"id": "s12", "title": "T", "keyword": None})
check("slide không keyword", 's12' in ctx2 and "từ khoá" not in ctx2)

print("== Tầng 5b: resolve_provider ==")
import importlib
saved_base = tutor.BASE_URL
saved_ds_key = os.environ.get("DEEPSEEK_API_KEY")
tutor.BASE_URL = None
os.environ["DEEPSEEK_API_KEY"] = "test-key-ds"
b, k, m = tutor.resolve_provider("deepseek/deepseek-v4-flash")
check("deepseek direct: base + strip prefix",
      b == "https://api.deepseek.com/v1" and m == "deepseek-v4-flash" and k == "test-key-ds")
b, k, m = tutor.resolve_provider("openai/gpt-4o-mini")
check("openai direct", b == "https://api.openai.com/v1" and m == "gpt-4o-mini")
b, k, m = tutor.resolve_provider("gemini/gemini-3.1-flash-lite")
check("gemini direct", "generativelanguage.googleapis.com" in b and m == "gemini-3.1-flash-lite")
b, k, m = tutor.resolve_provider("openrouter/anthropic/claude-x")
check("openrouter giữ nguyên id 2 đoạn", m == "anthropic/claude-x" and "openrouter.ai" in b)
tutor.BASE_URL = "https://gw.example/v1"
os.environ["EVAL_API_KEY"] = "gw-key"
b, k, m = tutor.resolve_provider("deepseek/deepseek-v4-flash")
check("gateway mode: giữ nguyên model id + EVAL_API_KEY",
      b == "https://gw.example/v1" and m == "deepseek/deepseek-v4-flash" and k == "gw-key")
try:
    tutor.BASE_URL = None
    tutor.resolve_provider("vendor-la/model-x")
    check("provider lạ -> báo lỗi rõ", False)
except RuntimeError as e:
    check("provider lạ -> báo lỗi rõ", "EVAL_BASE_URL" in str(e))
tutor.BASE_URL = saved_base
# dọn env test — nếu không EVAL_API_KEY/DEEPSEEK_API_KEY giả sẽ làm live test 401
os.environ.pop("EVAL_API_KEY", None)
if saved_ds_key is not None:
    os.environ["DEEPSEEK_API_KEY"] = saved_ds_key

print("== Tầng 6: vòng tool-calling (chat giả) ==")
def fake_chat_factory(responses):
    it = iter(responses)
    def fake(messages, **kwargs):
        return ({"choices": [{"message": next(it), "finish_reason": "stop"}],
                 "usage": {"prompt_tokens": 10, "completion_tokens": 5}}, 0.01)
    return fake

# Kịch bản A: model gọi kb_search một lần rồi trả JSON hợp lệ
final_json = json.dumps({"scope": "in_scope", "answer": "Trả lời", "sources": [],
                         "followup_questions": ["a?", "b?", "c?"]}, ensure_ascii=False)
tutor.chat = fake_chat_factory([
    {"role": "assistant", "content": None,
     "tool_calls": [{"id": "c1", "type": "function",
                     "function": {"name": "kb_search",
                                  "arguments": '{"query": "trace codes"}'}}]},
    {"role": "assistant", "content": final_json},
])
out, meta = tutor.call_tutor("trace codes là gì ạ")
check("loop: answer parse được", out.get("scope") == "in_scope", str(out)[:80])
check("loop: ghi nhận tool call", meta["tool_calls"] and "trace codes" in meta["tool_calls"][0]["query"])
check("loop: retrieved không rỗng", len(meta["retrieved"]) > 0)
check("loop: usage cộng dồn 2 vòng", meta["usage"]["prompt_tokens"] == 20)
check("loop: steps = 2", meta["steps"] == 2)

# Kịch bản B: model gọi tool lạ -> nhận error, rồi vẫn trả lời được
tutor.chat = fake_chat_factory([
    {"role": "assistant", "content": None,
     "tool_calls": [{"id": "c1", "type": "function",
                     "function": {"name": "hack_system", "arguments": "{}"}}]},
    {"role": "assistant", "content": final_json},
])
out, meta = tutor.call_tutor("test")
check("tool lạ không làm chết vòng lặp", out.get("scope") == "in_scope")

# Kịch bản C: model cứ gọi tool mãi -> vòng cuối rút tools, ép trả lời
def chat_stubborn(messages, **kwargs):
    if kwargs.get("tools"):
        return ({"choices": [{"message": {"role": "assistant", "content": None,
                "tool_calls": [{"id": "c", "type": "function",
                                "function": {"name": "kb_search", "arguments": '{"query":"x"}'}}]},
                "finish_reason": "tool_calls"}], "usage": {}}, 0.01)
    return ({"choices": [{"message": {"role": "assistant", "content": final_json},
                         "finish_reason": "stop"}], "usage": {}}, 0.01)
tutor.chat = chat_stubborn
out, meta = tutor.call_tutor("test vòng lặp vô hạn")
check("cap max_steps vẫn có output", out.get("scope") == "in_scope")
check("cap max_steps đúng số vòng", meta["steps"] == 6)

# Kịch bản D: slide context đi vào user message thật
captured = {}
def chat_capture(messages, **kwargs):
    captured["user"] = messages[1]["content"]
    return ({"choices": [{"message": {"role": "assistant", "content": final_json},
                         "finish_reason": "stop"}], "usage": {}}, 0.01)
tutor.chat = chat_capture
tutor.call_tutor("giải thích đoạn này", slide={"id": "s22", "title": "User Input Grid",
                                               "keyword": "context richness"})
check("slide context trong user message", "đang xem slide s22" in captured["user"])

import importlib
importlib.reload(tutor)  # trả lại chat thật

print("== Tầng 7: judge & report helpers ==")
import judge as judge_mod
rec = {"scenario_id": "q1", "input": "câu hỏi",
       "slide": {"id": "s22", "title": "T", "keyword": "k"},
       "output": {"answer": "a", "sources": []}}
p = judge_mod.build_judge_prompt(rec, "{{input}}||{{answer}}||{{sources}}")
check("judge prompt có slide context", "đang xem slide s22" in p)
rec2 = {"scenario_id": "q2", "input": "câu hỏi 2", "output": {"answer": "a", "sources": []}}
p2 = judge_mod.build_judge_prompt(rec2, "{{input}}")
check("judge prompt không slide thì sạch", "Ngữ cảnh" not in p2)

from run_eval import estimate_cost_usd
check("cost deepseek", estimate_cost_usd("deepseek/deepseek-v4-flash",
      {"prompt_tokens": 1_000_000, "completion_tokens": 1_000_000}) == 1.76)
check("cost model lạ -> None", estimate_cost_usd("x/y", {"prompt_tokens": 1}) is None)

print("== Tầng 7b: tracing backend ==")
import importlib.util
import tracing
for k in ("BRAINTRUST_API_KEY", "LANGSMITH_API_KEY", "LANGCHAIN_API_KEY"):
    os.environ.pop(k, None)
t0 = tracing.init_tracer()
check("không key -> noop", t0.backend is None)
try:
    t0.log_run(name="x", inputs={}, outputs={})
    t0.flush()
    check("noop log_run/flush không raise", True)
except Exception as e:
    check("noop log_run/flush không raise", False, str(e))

has_ls = importlib.util.find_spec("langsmith") is not None
has_bt = importlib.util.find_spec("braintrust") is not None
os.environ["LANGSMITH_API_KEY"] = "lsv2_pt_fake"
t1 = tracing.init_tracer()
check("LANGSMITH_API_KEY -> langsmith" + ("" if has_ls else " (bỏ qua: chưa pip install)"),
      t1.backend == "langsmith" if has_ls else t1.backend is None)
if has_ls:
    try:  # key giả: chỉ warn-once, không được raise làm chết eval
        t1.log_run(name="x", inputs={}, outputs={})
        t1.flush()
        check("langsmith lỗi chỉ warn không raise", True)
    except Exception as e:
        check("langsmith lỗi chỉ warn không raise", False, str(e))
os.environ["BRAINTRUST_API_KEY"] = "sk-fake"
t2 = tracing.init_tracer()
check("braintrust ưu tiên hơn langsmith" + ("" if has_bt else " (bỏ qua: chưa pip install)"),
      t2.backend == "braintrust" if has_bt else t2.backend is None)
for k in ("BRAINTRUST_API_KEY", "LANGSMITH_API_KEY"):
    os.environ.pop(k, None)

if os.environ.get("EVAL_LIVE") == "1":
    print("== Tầng 8: LIVE — gateway thật, model thật ==")
    for q in ["calibration là gì ạ", "cuối tuần này đà lạt có mưa không", "giải thích đoạn này"]:
        slide = {"id": "s22", "title": "User Input Grid", "keyword": "context richness"} if q.startswith("giải") else None
        out, meta = tutor.call_tutor(q, slide=slide)
        ok_contract = out.get("scope") in ("in_scope", "out_of_scope") and \
                      isinstance(out.get("followup_questions"), list) and \
                      not out.get("_parse_error")
        check("live: %s" % q[:30], ok_contract, str(out)[:100])
        print("       scope=%s steps=%s tools=%d" % (out.get("scope"), meta["steps"], len(meta["tool_calls"])))
else:
    print("== Tầng 8 (live) bỏ qua — bật bằng: EVAL_LIVE=1 python3 tests/test_eval_kit.py ==")

print("\nKết quả: %d pass, %d fail" % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
