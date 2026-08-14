# Nhật ký Tuần 06

## 1. Đã làm

- Sửa lỗi Unit Test phụ thuộc `.env` tại thời điểm import module.
- Bổ sung regression test chống tái phát lỗi import-time settings.
- Ghi nhận defect GitHub Issue #6, Severity Major; fix tại commit `a40e8ce`, retest PASS và đóng Issue.
- Kiểm tra `.env`: file `.env` thật không được Git track; `.env.example` được commit.
- Cập nhật ma trận truy vết theo kết quả kiểm thử thực tế.
- Bổ sung `database/schema.sql` từ Alembic migration hiện có.
- Thêm GitHub Actions workflow `Backend CI`; job `backend-quality` đã chạy PASS ở commit trước.
- Cấu hình ruleset `Protect main` yêu cầu Pull Request và status check.
- Bổ sung `TC-TUAN06.md` theo TC-06, TC-11 và TC-12.

### AP-08 - Background job cho tác vụ AI

- Refactor luồng sinh Test Case theo hướng background job để không giữ HTTP request chờ OpenAI xử lý xong.
- Bổ sung Celery 5.6 cho cơ chế background job.
- Cấu hình Celery để sử dụng RabbitMQ làm message broker thông qua biến môi trường `CELERY_BROKER_URL`.
- Bổ sung `GenerationJob` để theo dõi trạng thái tác vụ sinh Test Case.
- Bổ sung migration `0002_week06_generation_jobs.py`.
- Generation Job có các trạng thái:
  - `QUEUED`
  - `RUNNING`
  - `COMPLETED`
  - `FAILED`
- Bổ sung `GenerationJobRepository` để truy xuất và cập nhật Generation Job trong database.
- Bổ sung `GenerationJobService` để xử lý submit job, kiểm tra quyền và lấy trạng thái job.
- Bổ sung task queue adapter, Celery app và Celery worker.
- Rate limit và kiểm tra quyền theo Requirement được thực hiện trước khi enqueue.
- POST `/api/v1/requirements/{requirement_id}/test-cases` chuyển sang trả HTTP `202 Accepted`.
- API trả Generation Job thay vì giữ request chờ OpenAI hoàn thành.
- Bổ sung GET `/api/v1/generation-jobs/{job_id}` để client polling trạng thái Generation Job.
- Quyền truy cập Generation Job được kiểm tra theo `created_by` để hạn chế truy cập record của người dùng khác.
- Worker tiếp tục sử dụng `OpenAIAdapter` cho phần gọi AI.
- Structured Output/Pydantic tiếp tục kiểm tra cấu trúc dữ liệu AI trả về.
- Test Case do AI sinh vẫn chỉ được lưu ở trạng thái `DRAFT`.
- Generation vẫn ghi `AuditLog` trong transaction nghiệp vụ.
- Bổ sung Unit Test cho:
  - submit generation job hợp lệ;
  - tạo job ở trạng thái `QUEUED`;
  - enqueue đúng job;
  - QA không được submit Requirement của người khác;
  - QA không được xem Generation Job của người khác;
  - queue lỗi thì Generation Job chuyển sang `FAILED`.

## 2. Kết quả kiểm thử

- Python compile: PASS.
- Ruff check: PASS.
- Ruff format check: PASS.
- Tổng Unit Test hiện tại: 15/15 PASS.
- 4 Unit Test mới cho Generation Job/AP-08: PASS.
- Regression test import-time settings: PASS.
- Unit Test phần OpenAI sử dụng mock, không gọi provider thật.
- Celery version trên môi trường local: 5.6.3.
- GitHub Actions Backend CI đã PASS ở commit trước.
- Migration `0002_week06_generation_jobs.py` đã được bổ sung.

## 3. Chưa chạy manual / integration

- Chưa chạy RabbitMQ broker thật trên local vì máy hiện chưa cài Docker/RabbitMQ.
- Chưa chạy Celery worker kết nối RabbitMQ để kiểm thử end-to-end.
- Chưa có bằng chứng Swagger cho chuỗi:
  POST `202 Accepted` -> RabbitMQ -> Celery worker -> GET trạng thái Generation Job.
- `database/schema.sql` đã được regenerate sau migration `0002_week06_generation_jobs.py` và đã có bảng `generation_jobs`.
- Một số manual test trong `TC-TUAN06.md` vẫn ở trạng thái chưa chạy.
- OpenAI provider thật hiện còn phụ thuộc API credit; Unit Test tiếp tục mock OpenAI theo quy định.

## 4. Câu hỏi cho GVHD

Em đã refactor AP-08 theo hướng background job: sử dụng Celery, cấu hình RabbitMQ làm message broker, POST generate trả HTTP 202 và bổ sung endpoint polling trạng thái Generation Job. Phần code, Ruff và Unit Test hiện đã PASS 15/15, trong đó có 4 Unit Test cho luồng Generation Job.

Tuy nhiên, em chưa kiểm thử integration thực tế với RabbitMQ + Celery worker trên local do môi trường máy hiện chưa cài RabbitMQ/Docker.

Cho em hỏi cách thiết kế hiện tại đã đúng hướng AP-08 chưa, và ở giai đoạn Tuần 06 thầy yêu cầu phải có bằng chứng chạy integration RabbitMQ/Celery thực tế hay phần code + Unit Test + cấu trúc queue/job status như hiện tại là đủ ạ?

## 5. Tự kiểm

- [x] Không commit `.env` hoặc secret thật
- [x] `.env.example` có cấu hình broker mẫu
- [x] Unit Test không phụ thuộc OpenAI API key thật
- [x] Regression test cho defect Major
- [x] Python compile PASS
- [x] Ruff check PASS
- [x] Ruff format PASS
- [x] Unit Test 15/15 PASS
- [x] Có Unit Test riêng cho AP-08
- [x] Có GitHub CI
- [x] Có `TC-TUAN06.md`
- [x] Ma trận truy vết đã cập nhật
- [x] Có migration `0002_week06_generation_jobs.py`
- [x] AP-08 đã có queue abstraction + Generation Job + HTTP 202 + polling API + Unit Test
- [x] Regenerate `database/schema.sql` sau migration 0002
- [ ] Integration RabbitMQ + Celery worker
- [ ] Swagger POST 202 + GET Generation Job status
