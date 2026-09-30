# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Bùi Quốc Việt
- **MSSV:** 2A202602884
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/vietbui000/K4-L3B-Day13-BuiQuocViet-2A202602884-Monitoring-LLMOps
- **Commit SHA cuối:** `<CẬP NHẬT SAU KHI COMMIT EVIDENCE CUỐI>`
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602884`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 (tính lại từ log CP0 đã lưu) | 100/100 | Không thiếu schema/context, 17+ correlation ID |
| `validate_dashboard.py` | Chưa ghi nhận output CP0 | 6/6 | Đủ sáu panel theo contract |
| `pytest` | Chưa ghi nhận output CP0 | 28 passed | Chạy bằng Python 3.13.3 |
| Số traces hợp lệ | Root-only, chưa đủ child observations | 37 trace trong 24 giờ | Có agent/retrieval/generation |
| Số PII leak | 0 trong log CP0 | 0 | Validator độc lập không phát hiện PII thô |
| Latency P95 / TTFT P95 | 2167.15 ms / 50 ms | 2653.25 ms / 50 ms | Kết quả cuối gồm challenge chậm; baseline CP3 là 153.1 ms |
| Retrieval success rate | Chưa có field đầy đủ | 100% | Tính trên mọi event có `tool_success` |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** middleware xóa context cũ, nhận `x-request-id` hoặc sinh `req-<8 hex>`, bind vào `structlog`, lưu trên request state, trả lại qua response header và truyền vào trace metadata.
- **Các metadata được ghi vào structured log:** `user_id_hash`, `session_id`, `feature`, `model`, `env`, timestamp, event, latency/TTFT, token, cost, quality và trạng thái retrieval.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` đệ quy qua string/dict/list/tuple và chạy trước processor ghi JSONL; user ID chỉ lưu dưới dạng hash 12 ký tự.
- **Cách kiểm chứng kết quả:** request PII giả `req-a11ce123` tạo log chứa đủ `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, `[REDACTED_CCCD]`, `[REDACTED_CREDIT_CARD]`; validator đạt 100/100 và 0 leak.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** workload được chạy từ repo cá nhân với API key của project `day13-k4-l3b-2A202602884`; session và correlation ID trong trace khớp log local.
- **Cấu trúc root/retrieval/generation observations:** trace `day13-agent-request` chứa `lab-agent-run` (agent), child `retrieval` và child `generation`; generation ghi model, input/output token và cost, không capture raw input/output.
- **Cách nối trace với log:** dùng metadata `correlation_id`; ví dụ incident log `req-1f9fcdbf` nối tới trace `31f7df1126a63cdb9a58c09dcbc44d5a`.
- **Prompt name:** `day13-chat` (Text prompt, đủ `{{feature}}`, `{{docs}}`, `{{message}}`).
- **Version/label baseline:** version 1, labels `baseline` và trạng thái cuối `production`.
- **Version/label candidate:** version 2, labels `candidate` và `latest`.
- **Trace ID của mỗi version:** baseline v1 `ee69888da5ea9ec477a90e39a62c0ee0`; candidate v2 `63379e7d33cdee2c4477afb39410ed3f`.
- **Cách promote và rollback `production`:** đã chuyển `production` sang v2 và tạo trace `4ce67f83240e14cec7984fbe5eb9adba`, sau đó chuyển lại v1 và tạo trace kiểm chứng `e8891020af6b39916ef0509b1dc19d5c`.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** dashboard local tại `http://127.0.0.1:8050` đọc `data/logs.jsonl`, refresh 30 giây, time range 60 phút; gồm Latency/TTFT, Traffic, Errors/Retrieval success, Cost, Tokens và Quality, mỗi panel có đơn vị và threshold.
- **SLO và lý do chọn:** 99.5% request trong 28 ngày phải thành công và có latency server không quá 3000 ms. CP0 có 10/10 response đạt ngưỡng, max 2173 ms; challenge P95 2653.8 ms chưa vi phạm SLO nhưng tăng rất lớn so với baseline 153.1 ms, cho thấy vẫn cần theo dõi regression và span retrieval riêng thay vì chỉ dựa vào một ngưỡng tổng.
- **Cách tính error budget:** error budget là `100% - 99.5% = 0.5%`; với 10,000 request, tối đa `10,000 × 0.005 = 50` request được phép lỗi hoặc chậm hơn 3000 ms.
- **Ba alert và runbook tương ứng:** `HighLatencyP95` (>3000 ms/5m), `HighRequestErrorRate` (>2%/3m) và `LowRetrievalSuccess` (<90%/5m); mỗi alert trỏ tới `docs/alerts.md#alert-1/2/3`, Slack `#k4-l3b-alerts`, owner `student-2A202602884`.

> Ví dụ cách viết error budget: "SLO 99.5% trong 28 ngày nghĩa là error budget 0.5%. Nếu workload có 10,000 request thì tối đa 50 request được phép lỗi hoặc chậm hơn ngưỡng SLO."

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`.
- **Khoảng thời gian điều tra:** 2026-09-30 04:36:26–04:36:37 UTC (11:36:26–11:36:37 Asia/Bangkok/Ho_Chi_Minh).
- **Triệu chứng từ metrics:** latency P95 tăng từ 153.1 ms ở baseline CP3 lên 2653.8 ms trong challenge; TTFT vẫn 50 ms, error rate 0% và retrieval success 100%.
- **Log line và correlation ID liên quan:** `response_sent` của `req-1f9fcdbf`, session `k4-l3b-challenge-s02`, `latency_ms=2654`, `ttft_ms=50`, `tool_success=true`.
- **Trace ID và span gây ảnh hưởng:** trace `31f7df1126a63cdb9a58c09dcbc44d5a`; `retrieval` observation `0bfefe5002728542` mất 2501 ms, trong khi `generation` observation `e10c9d2a81e70389` chỉ mất 152 ms.
- **Root cause:** retrieval bị tăng latency khoảng 2.5 giây; LLM generation, TTFT, lỗi và chất lượng không phải nguồn gây bất thường.
- **Fix action:** tắt incident `rag_slow`/khôi phục dịch vụ retrieval và xác nhận `/health` cho thấy mọi incident đều `false`.
- **Preventive measure:** alert latency P95, theo dõi riêng retrieval span duration, timeout/circuit breaker cho vector store và runbook bắt buộc điều tra Metrics → Logs → Traces trước khi rollback thành phần.

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** không capture raw prompt/output trong Langfuse; chỉ ghi preview đã scrub và metadata cần thiết để vẫn điều tra được mà giảm nguy cơ lộ PII.
- **Một lỗi/blocker đã gặp:** app ban đầu nhận 404 khi tải `day13-chat` với label `production`, nên trace dùng `local-fallback` thay vì managed prompt.
- **Cách tìm nguyên nhân và xử lý:** kiểm tra trực tiếp SDK xác nhận key/region hợp lệ nhưng prompt chưa tồn tại; tạo Text prompt v1/v2, thêm `baseline`/`candidate`, rồi kiểm tra lại từng label và trace.
- **Cách hiểu luồng Metrics → Logs → Traces:** metrics khoanh vùng thời gian và triệu chứng; logs chọn request cụ thể bằng correlation ID; trace của request đó phân rã latency theo span để kết luận root cause.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** version/label cho phép biết chính xác prompt của từng request và rollback không đổi code; token/cost phát hiện prompt phình to; SLO/error budget xác định mức suy giảm chấp nhận được.
- **Điều quan trọng nhất đã học:** không kết luận nguyên nhân từ một metric tổng; phải nối cùng request qua metric, structured log và trace.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** còn cần chụp và thêm evidence 01–14, cập nhật commit SHA cuối và tự nộp URL/SHA trên LMS.

## 9. Checklist trước khi nộp

- [x ] Kết quả và evidence thuộc commit SHA cuối.
- [x ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x ] Incident evidence nối đúng metric → log → trace.
- [x ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x ] Repository chạy lại được theo README.
- [x ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
