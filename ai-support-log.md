# AI Support Log — Nhật ký Sử dụng AI trong Capstone

> Ghi lại quá trình sử dụng AI của từng thành viên trong nhóm theo đúng **Quy tắc dùng AI (Mục 9 - Day 21)**.
> Trung thực và duy trì quyền kiểm soát chất lượng (Human-in-the-loop) là tiêu chuẩn bắt buộc của bài nộp.

---

## 1. Nhật ký thành viên: Phạm Bá Huy (Tech Lead)

### 🤖 AI đã giúp tôi ở đâu?
- **Debug & Setup môi trường:** Hỗ trợ phát hiện nhanh nguyên nhân lỗi `402 Payment Required` (hết số dư DeepSeek) và cấu hình chuyển sang OpenRouter gateway với model `gpt-4o-mini` và `llama-3.3-70b-instruct`.
- **Viết hàm Code Checks mở rộng:** Gợi ý cách viết hàm `check_scope_sources` và `check_followup_format` bằng regex và kiểm tra kiểu dữ liệu Python thuần túy.
- **Cấu trúc lại Judge Prompt v2:** Gợi ý cách đưa các ví dụ Near-miss vào prompt để tăng độ phân giải cho LLM Judge.

### ⚠️ AI sai, hời hợt hoặc làm mất coverage ở đâu?
- **Ảo giác khi kiểm tra chuỗi Quote (Verbatim):** Khi dùng LLM để kiểm tra xem quote có nguyên văn không, LLM thường bỏ qua việc model tự ý chèn dấu `...` hoặc thay đổi từ nối. LLM không thể làm tốt việc so khớp từng ký tự như Python.
- **Lỗi logic UnboundLocalError trong code retry:** Đoạn code retry ban đầu do AI gợi ý bị thiếu khởi tạo `last_err`, dẫn đến crash khi gặp 5 lỗi 429 liên tiếp.

### 🛠️ Tôi đã tự sửa hoặc quyết định lại điều gì?
- **Chuyển hẳn tiêu chí Verbatim Quote sang Làn Code Checks:** Tự code kiểm tra bằng `_token_subsequence` trong Python thay vì tin vào LLM Judge.
- **Sửa logic xử lý lỗi & Rate limit trong `tutor.py`:** Thêm cơ chế Exponential Backoff và bắt mã lỗi `429` để pipeline chạy ổn định 100% không bị crash.
- **Tự gán nhãn kỹ thuật độc lập trong `labels-huy.csv`:** Soi kỹ từng section ID trong `manifest.json` và chuỗi token quote để chấm nhãn khách quan.
- **Thiết kế cơ chế Boosting cho Retrieval:** Đề xuất giải pháp kỹ thuật bổ sung trọng số author/doc-id cho BM25 trong `tutor.py` để xử lý triệt để 2 failure cases `sc-03` và `sc-08` cho bản release v1.1.

---

## 2. Nhật ký thành viên: Nguyễn Văn Tuấn Anh (PM Lead)

### 🤖 AI đã giúp tôi ở đâu?
- **Paraphrase biến thể câu hỏi:** Sau khi tôi đã khóa ma trận Input Grid (4 User Personas × 5 Intents), AI đã hỗ trợ gợi ý cách diễn đạt tự nhiên hơn cho các câu hỏi cộc lốc/deixis (ví dụ biến thể câu `sc-09`: *"Cái này đạt 80% là release được chưa anh?"*).
- **Tóm tắt nhanh pattern lỗi từ trace log:** Giúp tổng hợp các điểm tương đồng giữa các case mà Judge v1 và con người chấm lệch nhau, giúp tiết kiệm thời gian đọc 15 file trace thô.
- **Soạn khung báo cáo (Drafting):** Hỗ trợ format bảng biểu Markdown và cấu trúc văn bản theo chuẩn 5 phần của PM Report.

### ⚠️ AI sai, hời hợt hoặc làm mất coverage ở đâu?
- **Sinh câu hỏi quá "happy path":** Khi yêu cầu sinh test cases, AI có xu hướng sinh toàn câu hỏi dễ dãi, mẫu mực theo đúng trích đoạn sách giáo khoa ("Định nghĩa RAG là gì", "Các bước của pipeline là gì") mà bỏ quên hoàn toàn các câu hỏi đời thực như hỏi xin đáp án làm bài tập (`sc-14`) hay prompt injection (`sc-15`).
- **Judge quá dễ dãi ở Vòng 1:** Khi làm Judge chấm `Groundedness`, AI mặc định cho Pass hầu hết các câu trả lời nghe xuôi tai dù Tutor trích nhầm tài liệu (như case `sc-08` trích slide s29 của Blue thay vì sách Chip Huyen).

### 🛠️ Tôi đã tự sửa hoặc quyết định lại điều gì?
- **Tự thiết kế 100% Ma trận Input Grid & Coverage Strategy:** Tự định nghĩa 4 Personas và 5 Intents để đảm bảo 1/3 dataset là edge case và out-of-scope.
- **Bác bỏ 5 câu hỏi generic do AI sinh ra và viết lại 3 câu theo khẩu ngữ học viên thật:** Quyết định đưa case xin đáp án capstone (`sc-14`) vào bộ test blocker.
- **Tự chấm nhãn vàng (Ground Truth) trong `labels-tuananh.csv`:** Tự đọc từng câu trả lời và quote nguồn để quyết định Pass/Fail/Uncertain, không để AI can thiệp vào tầng ground truth.
- **Tự đưa ra quyết định Gate:** Quyết định **HOLD v1** dựa trên rủi ro sư phạm của Slice In-scope Factual (75% pass rate), không thỏa hiệp với số liệu tổng quan.

---

## 3. Bảng Phân loại Quyết định Human-in-the-loop (Keep / Rewrite / Reject)

| STT | Nội dung AI gợi ý ban đầu | Quyết định của nhóm | Lý do điều chỉnh của con người |
|:---:|---|:---:|---|
| 1 | Câu hỏi: "AI Evaluation là gì và tại sao quan trọng?" | **REJECT** | Quá chung chung, không bám sát corpus Day 19-20. |
| 2 | Câu hỏi: "Làm thế nào để code React Router v7?" | **KEEP** | Giữ lại làm case kiểm thử Out-of-scope (`sc-12`). |
| 3 | Câu hỏi: "Giải thích khái niệm Pass rate theo Slide 48" | **REWRITE** | Viết lại thành câu hỏi cộc lốc của học viên: *"Cái này đạt 80% là release được chưa anh?"* (`sc-09`) để test năng lực Deixis. |
| 4 | Cho LLM Judge tự chấm cả tiêu chí JSON Schema và Quote | **REJECT** | Vi phạm nguyên tắc: Chuyển 100% về làn **Code Checks** để chạy O(1) <10ms, tốn $0.00 và chính xác tuyệt đối. |
| 5 | Gợi ý Ship ngay vì Overall Pass Rate đạt ~87% | **REJECT** | Bác bỏ vì Slice In-scope Factual chỉ đạt 75% và có 2 lỗi gán sai tài liệu nghiêm trọng ➔ Quyết định **HOLD v1**. |
