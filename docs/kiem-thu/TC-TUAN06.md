# Test case bổ sung Tuần 06

## 1. Bằng chứng kiểm thử tự động

- Ngày chạy Unit Test: 15/08/2026
- Tested commit: `5e9d478`
- Kết quả: `15 passed`
- OpenAI trong Unit Test: mock, không gọi provider thật
- GitHub Actions workflow: `Backend CI`
- CI workflow commit: `ebd92a5`; latest verified run: `5e9d478`
- Job: `backend-quality`
- CI result: PASS

## 2. TC-06 - Luồng chính và ngoại lệ

### UC01 - Đăng nhập
- TC-AUTH-003: đăng nhập thành công - chưa chạy manual
- TC-AUTH-004: mật khẩu sai - chưa chạy manual
- TC-AUTH-001: khóa tài khoản - đã có ở Tuần 05, Unit Test PASS

### UC05 - Nhập Requirement
- TC-REQ-002: tạo Requirement hợp lệ - chưa chạy manual
- TC-REQ-003: module không tồn tại - Unit Test PASS
- TC-REQ-001: content quá ngắn - đã có ở Tuần 05

### UC02 - Quản lý User
- TC-USER-001: Admin tạo User hợp lệ - chưa chạy manual
- TC-USER-002: email trùng - Unit Test PASS
- TC-USER-003: QA tạo User - Unit Test PASS

### UC06 - Generate Test Case
- TC-GEN-001: output hợp lệ lưu DRAFT - Unit Test PASS, AI mock
- TC-GEN-002: QA không được generate Requirement người khác - Unit Test PASS
- TC-GEN-003: AI output sai schema không được lưu - Unit Test PASS

## 3. TC-11 - Negative Test

### Login
- TC-AUTH-005: thiếu email
- TC-AUTH-006: email sai định dạng
- TC-AUTH-007: thiếu password
- TC-AUTH-008: password rỗng
- TC-AUTH-009: password > 128 ký tự
- TC-AUTH-010: gửi field ngoài schema

### Requirement
- TC-REQ-004: thiếu module_id
- TC-REQ-005: module_id = 0
- TC-REQ-006: module_id < 0
- TC-REQ-007: thiếu content
- TC-REQ-008: content < 20 ký tự
- TC-REQ-009: content > 50000 ký tự
- TC-REQ-010: acceptance_criteria > 20000 ký tự
- TC-REQ-011: gửi field ngoài schema

### Create User
- TC-USER-004: thiếu email
- TC-USER-005: email sai định dạng
- TC-USER-006: thiếu password
- TC-USER-007: password < 10 ký tự
- TC-USER-008: password > 128 ký tự
- TC-USER-009: role không thuộc UserRole
- TC-USER-010: email trùng
- TC-USER-011: gửi field ngoài schema

> Các trường hợp chưa chạy manual giữ trạng thái Chưa chạy, không ghi PASS khi chưa có bằng chứng.

## 4. TC-12 - Authorization Testing

| Tình huống | Kết quả |
|---|---|
| QA gọi Create User chỉ dành cho Admin | PASS - Unit Test |
| QA generate từ Requirement của người khác | PASS - Unit Test |
| MANAGER tạo Requirement chỉ dành cho QA | PASS - Unit Test |
| MANAGER truy cập record không thuộc quyền | Chưa có bằng chứng |
| ADMIN gọi endpoint sai quyền | Chưa có bằng chứng |

## 5. Ghi chú

- Không ghi OpenAI provider thật là PASS vì lần gọi thật còn bị giới hạn credit.
- Unit Test AI sử dụng mock.
- Manual test chưa chạy giữ trạng thái `Chưa chạy`.

---

## AP-08 - Background Job cho AI Generation

### TC-JOB-001 - Submit Generation Job hợp lệ

- Loại kiểm thử: Unit Test
- Tiền điều kiện: QA sở hữu Requirement.
- Hành động: Gửi yêu cầu sinh Test Case.
- Kết quả mong đợi:
  - Generation Job được tạo với trạng thái `QUEUED`.
  - Rate limit được kiểm tra.
  - Job được enqueue đúng `job_id`.
  - Không chờ OpenAI hoàn thành trong HTTP request.
- Test tự động: `test_submit_generation_creates_queued_job_and_enqueues`
- Kết quả: PASS - 15/08/2026, commit `5e9d478` (CI xanh).

### TC-JOB-002 - QA submit Requirement của người khác

- Loại kiểm thử: Unit Test / Authorization
- Tiền điều kiện: Requirement thuộc QA khác.
- Hành động: QA hiện tại yêu cầu sinh Test Case.
- Kết quả mong đợi:
  - Trả lỗi quyền `FORBIDDEN_RECORD`.
  - Không tạo Generation Job.
  - Không enqueue task.
- Test tự động: `test_submit_other_users_requirement_is_forbidden`
- Kết quả: PASS - 15/08/2026, commit `5e9d478` (CI xanh).

### TC-JOB-003 - QA xem Generation Job của người khác

- Loại kiểm thử: Unit Test / Record-level Authorization
- Tiền điều kiện: Generation Job thuộc QA khác.
- Hành động: QA hiện tại lấy trạng thái job.
- Kết quả mong đợi:
  - Trả `FORBIDDEN_RECORD`.
  - Không cho đọc trạng thái job của người khác.
- Test tự động: `test_get_other_users_job_is_forbidden`
- Kết quả: PASS - 15/08/2026, commit `5e9d478` (CI xanh).

### TC-JOB-004 - Queue không khả dụng

- Loại kiểm thử: Unit Test / Error Handling
- Tiền điều kiện: Broker/queue phát sinh lỗi khi enqueue.
- Hành động: Submit Generation Job.
- Kết quả mong đợi:
  - Job chuyển sang `FAILED`.
  - Error code là `GENERATION_QUEUE_UNAVAILABLE`.
  - Không ghi nhận generation thành công.
- Test tự động: `test_queue_failure_marks_job_failed`
- Kết quả: PASS - 15/08/2026, commit `5e9d478` (CI xanh).

### Kết quả AP-08

- 4/4 Unit Test AP-08: PASS.
- Tổng Unit Test backend: 15/15 PASS.
- RabbitMQ/Celery worker integration chưa chạy trên local.
- Integration test cho luồng nghiệp vụ chính theo lộ trình quy định bắt đầu bắt buộc ở Tuần 8.
