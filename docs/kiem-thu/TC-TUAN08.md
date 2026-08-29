# Kết quả kiểm thử Tuần 08

## 1. Mục tiêu

Tuần 08 tập trung chạy integration test cho các luồng nghiệp vụ chính,
chạy lại toàn bộ automated test backend và thực hiện manual smoke test
trên hệ thống đang chạy local.

Các test case chưa có bằng chứng thực thi vẫn giữ trạng thái
`Chưa chạy` hoặc `NOT RUN`; không tự động đổi thành PASS.

## 2. Môi trường kiểm thử

- Branch: `tuan-08`
- Source commit dùng cho lượt automated test: `c9d574e`
- Backend: FastAPI
- Frontend: Next.js
- Database: PostgreSQL + pgvector
- Message broker: RabbitMQ
- Background worker: Celery
- Integration database: `testcase_ai_test`
- Backend local: `http://127.0.0.1:8001`
- Frontend local: `http://localhost:3000`

## 3. Kết quả automated test

| Hạng mục | Kết quả |
|---|---|
| Integration test | PASS - 15 passed, 1 warning |
| Toàn bộ backend test | PASS - 105 passed, 1 warning |
| AR-04 | PASS |
| QT-4 Module / Tag / Coverage | PASS |
| QT-6 Version History / Compare / Restore | PASS |

Warning còn lại là cảnh báo deprecation của Starlette TestClient/httpx,
không làm test thất bại.

Integration test sử dụng FastAPI application và test database thật.
Các external provider hoặc queue boundary được mock ở vị trí phù hợp để
CI không phụ thuộc dịch vụ ngoài hoặc phát sinh chi phí API.

## 4. Manual smoke test Tuần 08

| Luồng kiểm tra | Kết quả | Bằng chứng thực tế |
|---|---|---|
| Backend health | PASS | `/health` trả HTTP 200 |
| RabbitMQ | PASS | RabbitMQ diagnostics ping thành công |
| Celery worker | PASS | Worker phản hồi `pong`, 1 node online |
| Đăng nhập QA | PASS | QA truy cập được Requirement & AI workspace |
| Requirement UI | PASS | Module và form Requirement/SRS hiển thị bình thường |
| Real AI generation | PASS | Retest 27/08/2026: QUEUED -> RUNNING -> COMPLETED, sinh 6 Test Case DRAFT |
| Submit Review | PASS | TC #6 chuyển DRAFT v1 -> IN_REVIEW v2 |
| Manager Approve | PASS | TC #6 chuyển IN_REVIEW v2 -> APPROVED v3 |
| Module Coverage | PASS | 1/1 Requirement có Test Case, coverage hiển thị 100% |
| Export CSV | PASS | File 592 bytes, 13 cột, chứa dữ liệu Test Case APPROVED |
| Export XLSX | PASS | File 6046 bytes, sheet `Approved Test Cases`, 13 cột |
| Duplicate Detection | PASS | Hiển thị candidate similarity 91% và 89%, threshold 0.85 |
| Version History / Compare / Restore | PASS | Manual UI hiển thị v1, v2, v3 và nút Compare/Restore; Compare/Restore đã PASS ở integration test |
| Swagger / OpenAPI | PASS | `/docs` hiển thị các API `/api/v1` |

## 5. Kết quả kiểm thử lượt 1

Kho test hiện có 128 mã Test Case được thiết kế qua các tuần.

Lượt kiểm thử Tuần 08 hiện đã có bằng chứng cho:
- toàn bộ automated backend suite: 105 test PASS;
- integration suite: 15 test PASS;
- manual smoke test cho các luồng chính từ Requirement, AI generation,
  Human-in-the-loop, Coverage, Duplicate, Version đến Export.

Không ghi `128/128 PASS` vì một số Test Case manual chưa được chạy đầy đủ.

Các trường hợp Loading / Empty / Error của frontend và một số manual
boundary / Admin / User flow vẫn giữ `NOT RUN` hoặc `Chưa chạy`
nếu chưa có bằng chứng thực thi riêng.

## 6. Các chức năng chính đã được xác nhận

- Requirement create/update và phân quyền.
- AI background generation.
- Structured Test Case generation.
- Human-in-the-loop review và approve.
- Duplicate detection và merge ở integration level.
- Module, Tag và Coverage.
- Export CSV/XLSX.
- Version History, Compare và Restore ở integration level.
- BR-08: Requirement thay đổi làm Test Case cần review lại.
- Authentication và authorization cho các luồng chính.

## 7. Phần chưa hoàn thành trong lượt 1

- Chưa chạy thủ công toàn bộ 128 mã Test Case.
- FE Loading / Empty / Error chưa được thực thi đầy đủ.
- Một số boundary manual vẫn chưa chạy.
- Manual Restore không thực hiện lại trong smoke test để giữ dữ liệu demo;
  chức năng Restore đã có integration test PASS.
- Lượt kiểm thử thứ 2 thực hiện ở Tuần 09.
- Gold Set và các KPI AI đầy đủ chưa được đo trong Tuần 08.

