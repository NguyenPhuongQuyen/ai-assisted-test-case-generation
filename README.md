# Công cụ sinh test case tự động từ đặc tả yêu cầu bằng AI

Đồ án ngành ITEC4401 - Đề tài #13.

## Công nghệ sử dụng

- Frontend: Next.js 16 + TypeScript
- Backend: FastAPI + Python
- Database: PostgreSQL + pgvector
- AI: OpenAI API
- Background job: Celery
- Message broker: RabbitMQ
- CI: GitHub Actions

## Kiến trúc

- Source nằm trong `src/`, tách rõ `frontend/` và `backend/`.
- Backend tổ chức theo feature và phân tầng:
  `Router -> Service -> Repository`.
- OpenAI/Embedding adapter nằm tại:
  `src/backend/app/common/ai/`.
- AI generation được xử lý nền bằng Celery + RabbitMQ.
- Frontend giao tiếp với backend qua REST API `/api/v1`.
- PostgreSQL lưu dữ liệu nghiệp vụ; pgvector hỗ trợ embedding và Duplicate Detection.

## pgvector và Duplicate Detection

Hệ thống sử dụng PostgreSQL `pgvector` để phát hiện các test case tương tự theo NC-05.

- Embedding model: `text-embedding-3-small`
- Số chiều embedding: `1536`
- Độ tương tự: cosine similarity
- Ngưỡng duplicate mặc định: `0.85`
- Vector index: HNSW với `vector_cosine_ops`
- Index trong database: `ix_test_cases_embedding_hnsw`
- Rebuild embedding: `PYTHONPATH=src/backend python src/backend/scripts/rebuild_embeddings.py --batch-size 50`

Migration `0004_week07_pgvector_duplicates` bật extension `vector`, thêm cột embedding và tạo HNSW index.

Lệnh rebuild sử dụng Embedding API nên yêu cầu cấu hình API key hợp lệ trong file `.env` cục bộ.

## Yêu cầu môi trường

- Python 3.11+
- Node.js 20.9+ (khuyến nghị Node 22 LTS)
- npm 10+
- PostgreSQL 15+ với pgvector
- RabbitMQ 4+

PostgreSQL, pgvector và RabbitMQ cần được cài đặt và chạy trước khi khởi động hệ thống.

## Chạy nhanh

Các lệnh dưới đây sử dụng Git Bash và chạy từ thư mục gốc repository.

### 1. Chuẩn bị backend

```bash
{ test -f .env || cp .env.example .env; } && \
python -m venv .venv && \
source .venv/Scripts/activate && \
python -m pip install -r src/backend/requirements.txt
```

Cập nhật các biến local cần thiết trong `.env`.

Không commit `.env`, API key, access token hoặc secret thật vào repository.

### 2. Migration và seed dữ liệu demo

```bash
source .venv/Scripts/activate && \
python -m alembic -c src/backend/alembic.ini upgrade head && \
PYTHONPATH=src/backend python src/backend/scripts/seed_demo.py
```

### 3. Chạy backend API

Mở một Git Bash:

```bash
source .venv/Scripts/activate && \
python -m uvicorn app.main:app \
  --reload \
  --app-dir src/backend \
  --host 127.0.0.1 \
  --port 8001
```

Backend:

```text
http://127.0.0.1:8001
```

Health check:

```text
http://127.0.0.1:8001/health
```

Swagger/OpenAPI:

```text
http://127.0.0.1:8001/docs
```

### 4. Chạy Celery worker

Đảm bảo RabbitMQ đang chạy.

Mở một Git Bash khác:

```bash
PYTHONPATH=src/backend \
./.venv/Scripts/python.exe \
  -m celery \
  -A app.worker.celery_app \
  worker \
  --loglevel=INFO \
  --pool=solo
```

Kiểm tra Celery worker:

```bash
PYTHONPATH=src/backend \
./.venv/Scripts/python.exe \
  -m celery \
  -A app.worker.celery_app \
  inspect ping
```

Kết quả mong đợi:

```text
-> testcase-worker@<hostname>: OK
    pong

1 node online.
```

### 5. Chạy frontend

Mở một Git Bash khác:

```bash
cd src/frontend && \
npm install && \
{ test -f .env.local || cp .env.example .env.local; } && \
npm run dev
```

`src/frontend/.env.example` và `.env.local` sử dụng:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001/api/v1
```

Frontend:

```text
http://localhost:3000
```

Sau khi chạy đầy đủ:

- Frontend: `http://localhost:3000`
- Backend: `http://127.0.0.1:8001`
- Health: `http://127.0.0.1:8001/health`
- Swagger: `http://127.0.0.1:8001/docs`

## Kiểm thử

### Backend

Từ thư mục gốc repository:

```bash
source .venv/Scripts/activate
```

Kiểm tra format:

```bash
python -m ruff format --check src/backend
```

Kiểm tra lint:

```bash
python -m ruff check src/backend
```

Chạy unit test:

```bash
PYTHONPATH=src/backend ./.venv/Scripts/python.exe -m pytest src/backend/tests/unit -q
```

### Integration Test

Integration test chỉ chạy trên database riêng:

```text
testcase_ai_test
```

Database demo/dev sử dụng:

```text
testcase_ai
```

Không chạy integration test trực tiếp trên database demo vì fixture integration có thao tác reset dữ liệu.

Trên Windows Git Bash, từ thư mục gốc repository:

```bash
DEMO_DATABASE_URL="$(grep '^DATABASE_URL=' .env | cut -d= -f2-)"
TEST_DATABASE_URL="${DEMO_DATABASE_URL/testcase_ai/testcase_ai_test}"

DATABASE_URL="$TEST_DATABASE_URL" \
PYTHONPATH=src/backend \
./.venv/Scripts/python.exe \
-m pytest src/backend/tests/integration -q
```

Chạy toàn bộ backend test trên database test:

```bash
DEMO_DATABASE_URL="$(grep '^DATABASE_URL=' .env | cut -d= -f2-)"
TEST_DATABASE_URL="${DEMO_DATABASE_URL/testcase_ai/testcase_ai_test}"

DATABASE_URL="$TEST_DATABASE_URL" \
PYTHONPATH=src/backend \
./.venv/Scripts/python.exe \
-m pytest src/backend/tests -q
```

Các boundary bên ngoài như LLM provider được mock trong automated test để unit/integration test không phụ thuộc mạng hoặc phát sinh chi phí API.

Kết quả kiểm thử gần nhất:

```text
Unit test: 92 passed
Integration test: 16 passed, 1 warning
Backend automated test: 108 passed, 1 warning
```

Warning còn lại là deprecation warning của FastAPI/Starlette TestClient và không làm test thất bại.

### Frontend

```bash
cd src/frontend
```

Kiểm tra format:

```bash
npm run format:check
```

Kiểm tra lint:

```bash
npm run lint
```

Kiểm tra build:

```bash
npm run build
```

## GitHub Actions

Workflow CI nằm tại:

```text
.github/workflows/ci.yml
```

GitHub Actions thực hiện kiểm tra backend và frontend khi push hoặc mở Pull Request.

Pull Request chỉ được merge khi các kiểm tra CI bắt buộc hoàn thành thành công.

## Tài khoản demo local

Sau khi chạy seed:

- Admin: `admin@example.com`
- Manager: `manager@example.com`
- QA: `qa@example.com`

Password lấy từ biến:

```text
DEMO_USER_PASSWORD
```

trong `.env`.

`.env.example` chỉ chứa giá trị mẫu vô hại phục vụ cài đặt local.

## Tài liệu kiểm thử hiện tại

- `docs/weekly/Tuan08.md`
- `docs/weekly/Tuan09.md`
- `docs/kiem-thu/TC-TUAN08.md`
- `docs/kiem-thu/TC-TUAN09.md`
- `docs/kiem-thu/gold-set-report.md`
- `docs/kiem-thu/matran-truyvet.md`
- `docs/assets/NGUON.md`

Chi tiết backend và database:

```text
src/backend/README.md
```

## Biến môi trường và bảo mật

- Không commit `.env`.
- Không commit API key.
- Không commit access token.
- Không commit database credential thật.
- `.env.example` chỉ chứa tên biến và giá trị mẫu vô hại.
- Secret dùng cho CI phải cấu hình thông qua GitHub Secrets.

## AI hỗ trợ

Skeleton ban đầu của dự án được xây dựng với sự hỗ trợ của ChatGPT (OpenAI) và sau đó được chỉnh sửa, tổ chức, kiểm thử và rà soát theo Quy định Code ITEC4401.
