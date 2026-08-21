"""Code checks — kiểm tra results.jsonl bằng rule thuần Python (không tốn API).

Đây là làn "Code check" của bài lab: những tiêu chí viết được thành rule thì kiểm
bằng code — nhanh, rẻ, khách quan, chạy lại bao nhiêu lần cũng được.

Chạy:  python3 eval/code_checks.py            # in bảng pass/fail từng check từng row
Mở rộng: thêm hàm check_* mới của riêng nhóm (xem 3 hàm mẫu dưới).
"""
import json
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# tutor.py nằm ở tutor/ (khu vực sản phẩm) — thêm vào sys.path để import được
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tutor"))

import tutor  # dùng lại load_corpus

EXPECTED_FIELDS = {"scope", "answer", "sources", "followup_questions"}


def check_schema(rec):
    """Output parse được và đủ 4 field đúng contract."""
    out = rec.get("output") or {}
    if out.get("_parse_error"):
        return False, "JSON không parse được (xem raw_content)"
    missing = EXPECTED_FIELDS - set(out)
    if missing:
        return False, "thiếu field: " + ", ".join(sorted(missing))
    return True, None


def check_citation_exists(rec, valid_ids):
    """Mọi doc_id/section_id trong sources phải tồn tại thật trong corpus."""
    out = rec.get("output") or {}
    if out.get("_parse_error"):
        return None, "bỏ qua (JSON vỡ)"
    for s in out.get("sources") or []:
        key = (s.get("doc_id"), s.get("section_id"))
        if key not in valid_ids:
            return False, f'nguồn không tồn tại: {key[0]}#{key[1]}'
    return True, None


def _token_subsequence(needle, haystack):
    """True nếu chuỗi token của needle xuất hiện liên tiếp trong haystack."""
    if not needle:
        return True
    n = len(needle)
    return any(haystack[i:i + n] == needle for i in range(len(haystack) - n + 1))


def check_quote_verbatim(rec, section_tokens):
    """Quote phải nằm trong section đã cite — so theo chuỗi token (bỏ dấu, lowercase,
    bỏ mọi dấu câu/khoảng trắng) nên khác biệt gạch ngang/ngoặc kép không tính là sai."""
    out = rec.get("output") or {}
    if out.get("_parse_error"):
        return None, "bỏ qua (JSON vỡ)"
    for s in out.get("sources") or []:
        tokens = section_tokens.get((s.get("doc_id"), s.get("section_id")), [])
        quote_tokens = tutor.tokens(s.get("quote") or "")
        if quote_tokens and not _token_subsequence(quote_tokens, tokens):
            return False, f'quote không khớp section {s.get("section_id")}: "{(s.get("quote") or "")[:40]}..."'
    return True, None


def check_scope_sources(rec):
    """Quy tắc contract: out_of_scope thì sources = []; in_scope thì sources >= 1."""
    out = rec.get("output") or {}
    if out.get("_parse_error"):
        return None, "bỏ qua (JSON vỡ)"
    scope = out.get("scope")
    sources = out.get("sources") or []
    if scope == "out_of_scope" and len(sources) > 0:
        return False, f"out_of_scope nhưng sources không rỗng ({len(sources)} nguồn)"
    if scope == "in_scope" and len(sources) == 0:
        return False, "in_scope nhưng sources rỗng (thiếu nguồn trích dẫn)"
    return True, None


def check_followup_format(rec):
    """Quy tắc sư phạm: followup_questions phải gồm đúng 3 câu hỏi không rỗng."""
    out = rec.get("output") or {}
    if out.get("_parse_error"):
        return None, "bỏ qua (JSON vỡ)"
    fu = out.get("followup_questions")
    if not isinstance(fu, list):
        return False, "followup_questions không phải dạng list"
    if len(fu) != 3:
        return False, f"yêu cầu đúng 3 câu hỏi followup, nhận được {len(fu)}"
    if any(not isinstance(q, str) or not q.strip() for q in fu):
        return False, "chứa câu hỏi rỗng trong followup_questions"
    return True, None


CHECKS = [  # 3 check chuẩn + 2 check mở rộng của nhóm
    ("schema_valid", check_schema),
    ("scope_sources_match", check_scope_sources),
    ("followup_count_3", check_followup_format),
    ("citation_exists", check_citation_exists),
    ("quote_verbatim", check_quote_verbatim),
]


def main(path="results.jsonl"):
    if not os.path.exists(path):
        raise SystemExit("Không thấy %s — chạy python3 eval/run_eval.py trước." % path)
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]

    sections = tutor.load_corpus()
    valid_ids = {(s["doc_id"], s["section_id"]) for s in sections}
    section_tokens = {(s["doc_id"], s["section_id"]): tutor.tokens(s["text"]) for s in sections}

    totals = {name: [0, 0] for name, _ in CHECKS}  # [pass, fail] (skip không đếm)
    for rec in rows:
        sid = rec.get("scenario_id", "?")
        line = [sid]
        for name, fn in CHECKS:
            if fn in (check_schema, check_scope_sources, check_followup_format):
                ok, reason = fn(rec)
            elif fn is check_citation_exists:
                ok, reason = fn(rec, valid_ids)
            else:
                ok, reason = fn(rec, section_tokens)
            if ok is None:
                line.append(f"{name}: skip")
                continue
            totals[name][0 if ok else 1] += 1
            line.append(f"{name}: {'pass' if ok else 'FAIL — ' + str(reason)}")
        print(" | ".join(line))

    print("\nTổng kết:")
    for name, (p, f) in totals.items():
        print(f"  {name}: {p} pass / {f} fail")


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "results.jsonl")
