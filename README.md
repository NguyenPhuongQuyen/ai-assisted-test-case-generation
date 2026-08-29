# Công cụ sinh test case tự động từ đặc tả yêu cầu bằng AI

Đồ án ngành ITEC4401 - Đề tài #13.

**Stack:** Next.js 16 + TypeScript, FastAPI + Python, PostgreSQL + pgvector, OpenAI API, Celery và RabbitMQ.

---

## Kiến trúc

- Source nằm trong `src/`, tách `frontend/` và `backend/` (AR-01).
- Backend tổ chức theo feature; luồng chính: Router -> Service -> Repository (AR-02, AR-03, AR-08).
- OpenAI/Embedding adapter nằm tại `src/backend/app/common/ai/` (AR-11).
- Business Rule được gắn mã BR tại Service khi có logic nghiệp vụ (DC-03).
- AI generation chạy background job qua Celery + RabbitMQ; HTTP submit trả `202 Accepted`.
- PostgreSQL lưu dữ liệu nghiệp vụ; pgvector hỗ trợ embedding và duplicate detection.
- Frontend giao tiếp với backend thông qua REST API tại `/api/v1`.

---

## Yêu cầu môi trường

- Python 3.11+
- Node.js 20.9+ (khuyến nghị Node 22 LTS)
- PostgreSQL 15+ với pgvector
- RabbitMQ 4+
- npm 10+

PostgreSQL, pgvector và RabbitMQ cần được chuẩn bị trước khi chạy hệ thống.

Hướng dẫn backend và database chi tiết nằm trong:

```text
src/backend/README.md
```

---

## Chạy nhanh

Các lệnh dưới đây dùng **Git Bash** và được chạy từ thư mục gốc repository.

### Lệnh 1 - Chuẩn bị backend

```bash
{ test -f .env || cp .env.example .env; } && \
python -m venv .venv && \
source .venv/Scripts/activate && \
python -m pip install -r src/backend/requirements.txt
```

File `.env` chỉ dùng ở môi trường local và **không được commit lên repository**.

---

### Lệnh 2 - Migration và seed dữ liệu demo

```bash
source .venv/Scripts/activate && \
python -m alembic -c src/backend/alembic.ini upgrade head && \
PYTHONPATH=src/backend python src/backend/scripts/seed_demo.py
```

Migration được quản lý bằng Alembic.

Seed demo tạo dữ liệu và các tài khoản phục vụ quá trình kiểm thử hệ thống.

---

### Lệnh 3 - Chạy backend API

Mở một Git Bash và chạy:

```bash
source .venv/Scripts/activate && \
python -m uvicorn app.main:app \
  --reload \
  --app-dir src/backend \
  --host 127.0.0.1 \
  --port 8001
```

Backend chạy tại:

```text
http://127.0.0.1:8001
```

Kiểm tra health:

```text
http://127.0.0.1:8001/health
```

Swagger/OpenAPI:

```text
http://127.0.0.1:8001/docs
```

---

### Lệnh 4 - Chạy Celery worker

Mở một Git Bash khác và chạy:

```bash
PYTHONPATH=src/backend \
./.venv/Scripts/python.exe \
  -m celery \
  -A app.worker.celery_app \
  worker \
  --loglevel=INFO \
  --pool=solo
```

Có thể kiểm tra worker bằng:

```bash
PYTHONPATH=src/backend \
./.venv/Scripts/python.exe \
  -m celery \
  -A app.worker.celery_app \
  inspect ping
```

Khi worker hoạt động bình thường, kết quả có dạng:

```text
-> testcase-worker@<hostname>: OK
    pong

1 node online.
```

---

### Lệnh 5 - Chạy frontend

Mở một Git Bash khác và chạy:

```bash
cd src/frontend && \
npm install && \
{ test -f .env.local || cp .env.example .env.local; } && \
npm run dev
```

Frontend chạy tại:

```text
http://localhost:3000
```

Frontend phải trỏ tới backend:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001/api/v1
```

Sau khi các service đã chạy:

- Frontend: `http://localhost:3000`
- Backend: `http://127.0.0.1:8001`
- Backend health: `http://127.0.0.1:8001/health`
- Swagger/OpenAPI: `http://127.0.0.1:8001/docs`

Nếu cần sử dụng OpenAI thật, cấu hình `OPENAI_API_KEY` hợp lệ trong `.env`.

**Không commit file `.env`, API key, access token hoặc secret thật vào repository.**

---

## Frontend Tuần 08

Frontend hiện có các workspace và chức năng theo role.

### QA

- Đăng nhập và sử dụng Bearer token.
- Nhập và cập nhật Requirement.
- Chọn Module cho Requirement.
- Submit AI generation.
- Theo dõi trạng thái Generation Job.
- Xem Test Case do AI sinh.
- Chỉnh sửa và gửi Test Case sang trạng thái review.

### QA / Manager

- Danh sách và chi tiết Test Case.
- Edit Test Case.
- Review Test Case.
- Approve.
- Request Fix.
- Reject.
- Duplicate candidate.
- Version History.
- Compare version.
- Restore version.
- Export CSV.
- Export XLSX.

Chỉ các Test Case đủ điều kiện nghiệp vụ mới được export.

Sau khi export thành công, Test Case đã xuất có thể chuyển sang trạng thái `EXPORTED`.

### Manager

- Quản lý Module.
- Quản lý Tag.
- Theo dõi Coverage và statistics.
- Duyệt Test Case.

### Admin

- Tạo User.
- Xem danh sách User.
- Cập nhật User.
- Vô hiệu hóa User.
- Quản lý Prompt/Model configuration có version.

Frontend có xử lý các data state chính.

Việc kiểm thử đầy đủ tất cả trường hợp Loading / Empty / Error tiếp tục được thực hiện trong lượt kiểm thử tiếp theo.

---

## AI Generation

Luồng sinh Test Case bằng AI:

```text
Requirement
    |
    v
FastAPI Backend
    |
    v
Generation Job
    |
    v
RabbitMQ
    |
    v
Celery Worker
    |
    v
LLM API
    |
    v
Structured Output Validation
    |
    v
Test Case DRAFT
```

Generation được xử lý dưới dạng background job để HTTP request không phải chờ toàn bộ thời gian gọi LLM.

Đầu ra AI được kiểm tra theo structured output/schema trước khi lưu.

Test Case do AI sinh không được sử dụng trực tiếp mà phải trải qua Human-in-the-loop review.

---

## Human-in-the-loop

Vòng đời chính của Test Case:

```text
DRAFT
  |
  v
IN_REVIEW
  |
  v
APPROVED
```

Ngoài luồng duyệt thành công, hệ thống hỗ trợ các trạng thái nghiệp vụ như request fix hoặc reject tùy trường hợp.

Trong manual smoke test Tuần 08 đã xác nhận luồng:

```text
DRAFT v1
   ->
IN_REVIEW v2
   ->
APPROVED v3
```

Version và Audit được ghi nhận trong các thao tác nghiệp vụ tương ứng.

---

## Version History

Hệ thống hỗ trợ:

- Lưu phiên bản Test Case.
- Xem lịch sử version.
- So sánh các version.
- Khôi phục version trước.
- Cập nhật trạng thái Test Case liên quan khi Requirement thay đổi theo BR-08.

Integration test cho Version History / Compare / Restore đã được bổ sung trong Tuần 08.

---

## Module, Tag và Coverage

Hệ thống tổ chức Requirement và Test Case theo Module.

Các chức năng chính gồm:

- Quản lý Module.
- Gắn Tag.
- Theo dõi số Requirement theo Module.
- Theo dõi số Test Case.
- Theo dõi Test Case đã APPROVED.
- Theo dõi Coverage.

Integration test cho Module / Tag / Coverage đã được bổ sung trong Tuần 08.

---

## Export Test Case

Hệ thống hỗ trợ hai định dạng export:

- CSV
- XLSX

Export chỉ áp dụng cho Test Case đủ điều kiện theo business rule và phân quyền.

Manual smoke test Tuần 08 đã xác nhận:

- Export CSV: PASS.
- Export XLSX: PASS.
- File export có 13 cột dữ liệu Test Case.

Các trường chính gồm:

```text
ID
Requirement ID
Module ID
Summary
Preconditions
Steps
Expected Result
Priority
Test Techniques
Review Note
Status
Created By
Created At
```

---

## Kiểm thử và chất lượng

### Backend

Chạy từ root repository:

```bash
python -m ruff format --check src/backend
python -m ruff check src/backend
python -m pytest -q
python -m pytest --cov=app --cov-report=term-missing
```

Kết quả kiểm thử Tuần 08:

```text
Integration test: 15 passed, 1 warning
Backend automated test: 105 passed, 1 warning
AR-04: PASS
```

Warning còn lại là deprecation warning và không làm test thất bại.

Integration test sử dụng application FastAPI và database test riêng:

```text
testcase_ai_test
```

Các external provider và queue boundary được mock ở vị trí phù hợp để automated test không phụ thuộc dịch vụ ngoài hoặc phát sinh chi phí API.

---

### Frontend

```bash
cd src/frontend

npm run format:check
npm run lint
npm run build
```

---

## Manual smoke test Tuần 08

Các luồng chính đã được kiểm tra:

- Backend `/health`: PASS - HTTP 200.
- RabbitMQ: PASS - ping thành công.
- Celery worker: PASS - phản hồi `pong`.
- QA Login: PASS.
- Requirement UI: PASS.
- Real AI Generation: PASS.
- Human-in-the-loop Submit Review: PASS.
- Manager Approve: PASS.
- Module Coverage: PASS.
- Export CSV: PASS.
- Export XLSX: PASS.
- Duplicate Detection: PASS.
- Version History: PASS.
- Swagger/OpenAPI: PASS.

Real AI retest đã xác nhận Generation Job:

```text
QUEUED -> RUNNING -> COMPLETED
```

và sinh thành công 6 Test Case ở trạng thái `DRAFT`.

---

## GitHub Actions / CI

GitHub Actions kiểm tra backend và frontend theo cấu hình:

```text
.github/workflows/ci.yml
```

CI thực hiện các bước kiểm tra chất lượng và automated test cho source code.

Backend integration test sử dụng database test riêng để không ảnh hưởng dữ liệu demo.

External LLM provider và queue boundary được mock trong automated test khi phù hợp, giúp CI không phụ thuộc OpenAI thật hoặc RabbitMQ thật.

Pull Request chỉ được merge khi các kiểm tra bắt buộc của CI hoàn thành thành công.

---

## pgvector / NC-05

Duplicate Detection sử dụng embedding kết hợp pgvector.

Cấu hình hiện tại:

- Embedding model mặc định: `text-embedding-3-small`
- Dimensions: `1536`
- Similarity threshold: `0.85`
- Index: HNSW với cosine distance

Rebuild toàn bộ embedding:

```bash
PYTHONPATH=src/backend \
python src/backend/scripts/rebuild_embeddings.py \
  --batch-size 50
```

Duplicate Detection sử dụng độ tương đồng để tìm các Test Case có nội dung gần nhau trước khi người dùng quyết định xử lý hoặc gộp.

Chi tiết backend:

```text
src/backend/README.md
```

---

## Database

Database chính:

```text
PostgreSQL + pgvector
```

Schema được quản lý thông qua Alembic migration.

Chạy migration:

```bash
source .venv/Scripts/activate

python -m alembic \
  -c src/backend/alembic.ini \
  upgrade head
```

Database integration test:

```text
testcase_ai_test
```

Database kiểm thử được tách khỏi database dùng cho demo.

---

## Seed dữ liệu demo

Chạy:

```bash
PYTHONPATH=src/backend \
python src/backend/scripts/seed_demo.py
```

Seed tạo dữ liệu cần thiết phục vụ demo và tài khoản cho các role chính.

---

## Tài khoản demo local

Sau khi chạy seed, có thể đăng nhập bằng các tài khoản sau:

| Role | Email | Password mặc định |
|---|---|---|
| Admin | `admin@example.com` | `Demo_Change_Me_123!` |
| Manager | `manager@example.com` | `Demo_Change_Me_123!` |
| QA | `qa@example.com` | `Demo_Change_Me_123!` |

Password trên là giá trị mặc định của `DEMO_USER_PASSWORD` trong `.env.example`.

Nếu thay đổi `DEMO_USER_PASSWORD` trong `.env` trước khi chạy seed, password của các tài khoản demo sẽ sử dụng giá trị mới đó.

Đây chỉ là credential phục vụ demo local, không sử dụng cho production.

---

## Tài liệu tiến độ Tuần 08

Tài liệu hiện tại:

- `docs/weekly/Tuan08.md`
- `docs/kiem-thu/TC-TUAN08.md`
- `docs/kiem-thu/matran-truyvet.md`

Các Test Case từ những tuần trước tiếp tục được tái sử dụng nếu vẫn còn phù hợp; không tạo mã Test Case mới khi đã có Test Case tương đương.

Kết quả manual test chưa có bằng chứng thực thi vẫn giữ trạng thái `NOT RUN` hoặc `Chưa chạy`.

Không ghi toàn bộ Test Case là PASS khi chưa chạy thực tế đầy đủ.

---

## Phần còn tiếp tục hoàn thiện

Sau Tuần 08, các nội dung tiếp tục được thực hiện gồm:

- Chạy đầy đủ các manual Test Case còn lại.
- Kiểm tra đầy đủ Loading / Empty / Error frontend.
- Kiểm tra thêm các boundary case.
- Hoàn thiện các manual Admin / User flow còn lại.
- Thực hiện lượt kiểm thử thứ 2 ở Tuần 09.
- Đo Gold Set và các KPI đánh giá chất lượng AI.
- Hoàn thiện báo cáo kiểm thử và đánh giá.

Docker Compose hiện chưa triển khai; đây là hạng mục mở rộng/khuyến nghị trong phiên bản hiện tại.

---

## Nguồn tham khảo / AI hỗ trợ

Skeleton ban đầu được xây dựng với sự hỗ trợ của ChatGPT (OpenAI) và sau đó được tổ chức, chỉnh sửa và kiểm thử theo Quy định Code ITEC4401.
