# Tuần 08 - Integration Test và hoàn thiện luồng nghiệp vụ chính

## 1. Công việc đã thực hiện

- Bổ sung integration test cho các luồng nghiệp vụ chính.
- Bổ sung integration cho AI generation.
- Bổ sung integration cho Module / Tag / Coverage.
- Bổ sung integration cho Version History / Compare / Restore.
- Bổ sung test database cho backend integration test.
- Sửa PF-01 để tránh query lặp trong loop.
- Sửa PF-05 cho phần persistence theo batch.
- Refactor các file và function vượt giới hạn AR-04.
- Cập nhật GitHub Actions để chạy trên weekly branch.
- Sửa lỗi generation job có thể bị giữ ở trạng thái RUNNING.
- Sửa lỗi Celery worker thiếu ORM model registration.
- Thực hiện manual smoke test các luồng chính.
- Kiểm tra Export CSV và XLSX bằng dữ liệu thật.

## 2. Kết quả kiểm thử

- Integration: `15 passed, 1 warning`.
- Toàn bộ backend: `105 passed, 1 warning`.
- AR-04: PASS.
- Backend health: HTTP 200.
- RabbitMQ: ping thành công.
- Celery: worker phản hồi pong.
- Real AI retest: sinh 6 Test Case DRAFT thành công.
- Human-in-the-loop:
  - DRAFT v1 -> IN_REVIEW v2.
  - IN_REVIEW v2 -> APPROVED v3.
- Coverage: 1/1 Requirement có Test Case.
- Export CSV: PASS.
- Export XLSX: PASS.
- Duplicate candidate và Version History hiển thị đúng trên frontend.
- Swagger/OpenAPI hoạt động tại `/docs`.

## 3. Integration flow đã bổ sung

Các integration test sử dụng FastAPI application và database
`testcase_ai_test`.

Các luồng chính được kiểm tra gồm:

- Authentication.
- Requirement và record-level authorization.
- BR-08 Requirement revalidation.
- AI generation job.
- Human-in-the-loop review / approve.
- Duplicate merge.
- Export.
- Module / Tag / Coverage.
- Version History / Compare / Restore.

External provider và queue boundary được mock ở nơi phù hợp để automated
test không phụ thuộc OpenAI thật hoặc RabbitMQ trong CI.

## 4. Defect và regression

Các lỗi quan trọng đã được xử lý trong Tuần 08:

- Issue #21: Generation job có thể giữ trạng thái RUNNING.
- Issue #22: Celery worker thiếu đăng ký ORM model Module.

Sau khi sửa, regression test và full backend suite đều PASS.

## 5. Tài liệu kiểm thử

- Kết quả Tuần 08: `docs/kiem-thu/TC-TUAN08.md`.
- Traceability matrix: `docs/kiem-thu/matran-truyvet.md`.
- Các Test Case Tuần 05-07 tiếp tục được tái sử dụng, không tạo mã Test Case
  mới khi đã có Test Case tương đương.

## 6. Phần còn lại

- Một số manual Test Case chưa được chạy đầy đủ.
- Loading / Empty / Error frontend chưa được kiểm tra toàn bộ.
- Lượt kiểm thử thứ 2 thực hiện ở Tuần 09.
- Gold Set >= 20 và các KPI AI đầy đủ chưa được đo.
- Docker Compose chưa triển khai; DP-02 là hạng mục khuyến nghị.

