# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`; Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: `response_sent.latency_ms`, mục tiêu P95 không quá 3000 ms.
- Điều kiện và thời gian duy trì: P95 latency vượt 3000 ms liên tục trong 5 phút.
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn để nhận câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. **Metrics:** xác nhận P95/P99 tăng trên dashboard và ghi lại khoảng thời gian.
  2. **Logs:** lọc `response_sent` trong khoảng đó, chọn latency cao và ghi `correlation_id`.
  3. **Traces:** mở trace cùng `correlation_id`, so sánh thời gian của retrieval và generation.
- Mitigation tạm thời: nếu generation tăng sau đổi prompt, rollback label `production`; nếu retrieval chậm, tắt practice incident hoặc khôi phục dịch vụ retrieval. Chỉ chọn hành động khớp với trace.
- Owner: `student-2A202602884`

## Alert 2

- Tên: `HighRequestErrorRate`
- Severity: `critical`; Duration: `3m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: tỷ lệ request lỗi; guardrail tối đa 2%.
- Điều kiện và thời gian duy trì: `request_failed / request_received > 2%` liên tục trong 3 phút.
- Ảnh hưởng tới người dùng: một phần request không nhận được câu trả lời thành công.
- Ba bước kiểm tra đầu tiên:
  1. **Metrics:** kiểm tra error rate và thời điểm bắt đầu tăng.
  2. **Logs:** lọc event `request_failed`, nhóm theo `error_type`, lấy một `correlation_id`.
  3. **Traces:** mở trace tương ứng, xem span nào báo lỗi hoặc có trạng thái bất thường.
- Mitigation tạm thời: rollback prompt nếu lỗi bắt đầu sau khi promote; nếu trace xác nhận retrieval fail, khôi phục nguồn dữ liệu hoặc tắt practice incident. Không retry hàng loạt trước khi xác định lỗi.
- Owner: `student-2A202602884`

## Alert 3

- Tên: `LowRetrievalSuccess`
- Severity: `warning`; Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: tỷ lệ `tool_success == true`; guardrail tối thiểu 90%.
- Điều kiện và thời gian duy trì: retrieval success dưới 90% trong 5 phút, tính trên mọi event có `tool_success`.
- Ảnh hưởng tới người dùng: câu trả lời có thể thiếu tài liệu phù hợp hoặc chuyển sang nội dung dự phòng.
- Ba bước kiểm tra đầu tiên:
  1. **Metrics:** xác nhận retrieval success giảm và kiểm tra error rate cùng thời điểm.
  2. **Logs:** xem cả `response_sent` và `request_failed` có `tool_success`, sau đó lấy `correlation_id` của một request thất bại.
  3. **Traces:** mở trace tương ứng, kiểm tra span retrieval, thời gian và trạng thái.
- Mitigation tạm thời: khôi phục index/nguồn tài liệu nếu span xác nhận lỗi retrieval; tắt practice incident nếu đang bật. Theo dõi lại retrieval success sau mitigation.
- Owner: `student-2A202602884`
