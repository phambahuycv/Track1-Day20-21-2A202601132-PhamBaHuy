# AI Support Log

> Ghi lại bạn đã dùng AI (ChatGPT/Claude/Kimi...) ở những bước nào khi làm deliverables.
> Trung thực là một phần của bài nộp — không ai làm một mình, quan trọng là bạn giữ
> quyền kiểm soát chất lượng.

| # | Bước | AI dùng để làm gì | Bạn kiểm chứng kết quả thế nào |
|---|------|-------------------|-------------------------------|
| 1 | Setup môi trường & Debug API | Hỗ trợ phát hiện lỗi 402/429 khi chạy model trực tiếp, chuyển hướng sang OpenRouter gateway | Test kết nối API trực tiếp bằng script python, xác nhận 200 OK |
| 2 | Phase 1: Input Grid & Dataset generation | Gợi ý 20 câu hỏi tiềm năng dựa trên danh sách tài liệu corpus | Rà soát từng câu với corpus thật, loại bỏ 5 câu rác/lệch đề, viết lại 3 câu theo khẩu ngữ học viên Việt Nam, giữ 15 câu |
| 3 | Phase 2 & 4: Rubric & Judge Calibration | Hỗ trợ phân tích failure cases trong report.html | Tự đọc và đối chiếu từng trace, tự gán nhãn ground truth vào `labels.csv` |

- **Phần nào AI gợi ý mà bạn bác bỏ? Vì sao?**
  - Bác bỏ các câu hỏi quá chung chung mà AI sinh ra ("AI là gì", "Machine learning là gì", "Cách code frontend React") vì không phục vụ đúng mục tiêu đánh giá khóa học AI Evaluation (Day 19-20).
  - Bác bỏ câu hỏi dịch máy tiếng Anh thô cứng, viết lại thành câu hỏi cộc lốc/ngữ cảnh thực tế của học viên trong lớp.
- **Phần nào bạn hoàn toàn tự làm?**
  - Thiết kế ma trận Input Grid theo 2 trục (User Persona × Intent).
  - Đọc output, gán nhãn người (`labels.csv`) và quyết định tiêu chí chấp nhận cho sản phẩm.
