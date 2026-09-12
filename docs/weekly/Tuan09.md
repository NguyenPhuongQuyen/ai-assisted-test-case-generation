# Nhật ký Tuần 09

## 1. Công việc hoàn thành

- Hoàn thiện Newman smoke collection.
- Sửa Celery async worker trên Windows.
- Chạy RabbitMQ + Celery + FastAPI end-to-end.
- Tách database integration test khỏi database demo.
- Backend regression đạt 108 PASS.
- GitHub Actions Project CI PASS.
- Thực hiện manual regression cho QA / Manager / Admin.
- Kiểm thử BR-08 Requirement revalidation.
- Bổ sung khả năng mở lại Requirement đã lưu trên UI.
- Hoàn thiện Gold Set 20 requirement.
- Chạy OpenAI API thật cho toàn bộ Gold Set.
- AI generation hoàn thành 20/20, sinh 110 Test Case.
- Hoàn thiện KPI AI và lượt kiểm thử thứ 2.

## 2. Defect và regression

Tuần 09 xử lý ba defect:

1. DF-T09-01 / Issue #24 - Celery async event-loop issue - Major - RETEST PASS.
2. DF-T09-02 / Issue #25 - Integration/demo database isolation - Major - RETEST PASS.
3. DF-T09-03 / Issue #26 - Requirement cũ không mở lại được từ UI - Major - RETEST PASS.

HTTP 429 khi chạy quá 10 AI generation trong 300 giây là rate limiter hoạt
động đúng và không được phân loại là defect.

## 3. Kết quả kiểm thử

- Backend full suite: 108 PASS, 1 warning.
- Integration: 16 PASS, 1 warning.
- Frontend ESLint: PASS.
- Frontend production build: PASS.
- CI: PASS.
- Gold Set: 20/20 generation completed.
- Tổng Test Case AI sinh: 110.
- Full Coverage: 75%.
- Coverage Failure: 0%.
- Technique Match: 100%.
- No Hallucination: 100%.

Chi tiết xem `docs/kiem-thu/TC-TUAN09.md`.
