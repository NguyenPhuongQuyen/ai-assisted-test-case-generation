# Kết quả kiểm thử Tuần 09

## 1. Mục tiêu

Tuần 09 tập trung vào regression, kiểm thử end-to-end với provider thật,
hoàn thiện Gold Set, kiểm tra CI và thực hiện lượt kiểm thử thứ 2.

Không ghi nhận `128/128 PASS` vì không có bằng chứng thực thi thủ công
toàn bộ 128 mã Test Case đã thiết kế.

## 2. Automated regression

### Backend

- Unit + Integration: **108 PASS, 1 warning**
- Integration subset: **16 PASS, 1 warning**
- Warning còn lại là `StarletteDeprecationWarning`, không làm test fail.
- Integration test sử dụng database riêng `testcase_ai_test`.
- Database demo/dev tiếp tục sử dụng `testcase_ai`.

### Frontend

- ESLint: **PASS**
- Next.js production build: **PASS**
- `git diff --check`: **PASS**

### CI

GitHub Actions `Project CI` đã chạy xanh trên nhánh `tuan-09`.

## 3. Manual / End-to-End regression

Các luồng đại diện đã thực thi và PASS:

| Nhóm | Kết quả |
|---|---|
| QA login và role navigation | PASS |
| Tạo Requirement | PASS |
| Mở lại Requirement đã lưu trên UI | PASS |
| Cập nhật Requirement | PASS |
| AI generation QUEUED -> COMPLETED | PASS |
| AI sinh Test Case trạng thái DRAFT | PASS |
| DRAFT -> IN_REVIEW -> APPROVED | PASS |
| APPROVED -> EXPORTED | PASS |
| DRAFT -> IN_REVIEW -> NEEDS_FIX | PASS |
| DRAFT -> IN_REVIEW -> REJECTED | PASS |
| Duplicate Detection | PASS |
| Version History / Compare | PASS |
| Version Restore | PASS |
| Coverage | PASS |
| Export CSV | PASS |
| Export XLSX | PASS |
| Manager tạo Module | PASS |
| Manager đổi tên Module | PASS |
| Admin tạo user | PASS |
| Admin đổi role | PASS |
| Admin vô hiệu hóa user | PASS |
| User bị vô hiệu hóa không đăng nhập được | PASS |
| Prompt/Model version hiển thị | PASS |
| BR-08 Requirement thay đổi -> Test Case cần review lại | PASS |

## 4. Gold Set - OpenAI API thật

Gold Set gồm 20 requirement.

Luồng chạy:

`Gold Set -> FastAPI -> RabbitMQ -> Celery -> OpenAI API -> Schema Validation -> PostgreSQL`

Kết quả:

| KPI | Kết quả |
|---|---:|
| Generation Success Rate | 20/20 (100%) |
| Schema Valid Rate | 20/20 (100%) |
| Full Coverage Rate | 15/20 (75%) |
| Requirements đạt Partial Coverage | 5/20 (25%) |
| Coverage Failure | 0/20 (0%) |
| At-least-partial Coverage | 20/20 (100%) |
| Technique Match Rate | 20/20 (100%) |
| No Hallucination Rate | 20/20 (100%) |
| Tổng Test Case AI sinh | 110 |
| Trung bình Test Case / Requirement | 5.5 |

Trong lần chạy đầu, GS11-GS20 nhận HTTP 429 do rate limiter của ứng dụng
đạt giới hạn 10 generation request / 300 giây. Đây là hành vi đúng theo
thiết kế, không được ghi nhận là defect. Sau khi sliding-window reset,
các mẫu được retry trên cùng Requirement và hoàn thành 20/20.

Chi tiết:
- `docs/kiem-thu/gold-set.csv`
- `docs/kiem-thu/gold-set-results.csv`
- `docs/kiem-thu/gold-set-evidence.jsonl`
- `docs/kiem-thu/gold-set-report.md`

## 5. Defect Tuần 09

### DF-T09-01 / Issue #24 - Celery worker lỗi event loop khi xử lý nhiều generation job

- Severity: **Major**
- Thành phần: Celery / SQLAlchemy async / asyncpg
- Hiện tượng: worker có thể lỗi khi cached async engine được tái sử dụng
  qua các event loop khác nhau trên Windows.
- Nguyên nhân: mỗi lần `asyncio.run()` tạo một event loop mới trong khi
  async database resources được tái sử dụng.
- Fix: worker dùng persistent `asyncio.Runner`.
- Fix commit: `10b9ea0`
- Regression:
  - focused Celery task test: **2 PASS**
  - full backend regression sau fix: **PASS**
  - E2E RabbitMQ/Celery/OpenAI chạy thật: **PASS**
- Trạng thái: **RETEST PASS - READY TO CLOSE**

### DF-T09-02 / Issue #25 - Integration test chưa tách hoàn toàn khỏi database demo

- Severity: **Major**
- Thành phần: Test isolation / PostgreSQL
- Rủi ro: fixture integration có thao tác reset dữ liệu, do đó không được
  phép chạy trên database demo.
- Fix:
  - demo/dev sử dụng `testcase_ai`;
  - integration sử dụng riêng `testcase_ai_test`;
  - lệnh test truyền `DATABASE_URL` test riêng.
- Fix/documentation commit: `1088e72`
- Regression:
  - Integration: **15 PASS**
  - Full backend: **108 PASS**
  - `.env` vẫn trỏ về `testcase_ai`.
- Trạng thái: **RETEST PASS - READY TO CLOSE**

### DF-T09-03 / Issue #26 - Không thể mở lại Requirement cũ từ giao diện QA

- Severity: **Major**
- Thành phần: Frontend / Requirement API
- Hiện tượng: sau khi rời workspace, QA không thể chọn lại Requirement đã
  lưu để cập nhật; form chỉ giữ Requirement vừa tạo trong phiên.
- Fix:
  - bổ sung API list Requirement theo Module và QA owner;
  - bổ sung dropdown `Requirement đã lưu`;
  - chọn Requirement tự load SRS, Acceptance Criteria và lock_version.
- Fix commit: `0064144`
- Regression:
  - Backend Ruff: **PASS**
  - Frontend ESLint: **PASS**
  - Frontend build: **PASS**
  - Full backend: **108 PASS**
  - Integration regression mở lại Requirement đã lưu: **PASS**
  - Manual mở lại `REQ #5`: **PASS**
- Trạng thái: **RETEST PASS - READY TO CLOSE**

## 6. So sánh hai lượt kiểm thử

| Hạng mục | Lượt 1 - Tuần 08 | Lượt 2 - Tuần 09 |
|---|---|---|
| Full backend automated suite | 105 PASS | 108 PASS |
| Integration suite | 15 PASS | 16 PASS |
| Manual luồng chính | Smoke PASS, còn NOT RUN | Regression đại diện PASS |
| BR-08 manual | Có bằng chứng | PASS lại bằng API/UI |
| Version Restore manual | Chưa thực hiện lại | PASS |
| Admin/User flow | Chưa đầy đủ | PASS |
| Requirement reopen/edit UI | Chưa có | PASS sau fix |
| RabbitMQ/Celery/OpenAI E2E | Có luồng cơ bản | PASS với Gold Set 20/20 |
| Gold Set >=20 | Chưa đo | HOÀN THÀNH |
| AI KPI | Chưa đo | Đã đo |
| CI | PASS | PASS |

## 7. Kết luận lượt 2

Lượt kiểm thử thứ 2 xác nhận các regression chính của hệ thống sau khi sửa
defect. Automated backend đạt 108 PASS; frontend lint/build và CI đều PASS.

Gold Set sử dụng OpenAI API thật hoàn thành 20/20 generation và tạo 110
Test Case. Full Coverage Rate đạt 75%; 5 mẫu còn lại đạt PARTIAL và không có
mẫu Coverage FAIL. Kết quả này tiếp tục cho thấy Human-in-the-loop là cần
thiết trước khi Test Case được APPROVED.

Các raw Newman report có chứa token runtime nên không được commit vào repository.
