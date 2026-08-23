# Công cụ sinh test case tự động từ đặc tả yêu cầu bằng AI

Đồ án ngành ITEC4401 - Đề tài #13. Stack: Next.js 16 + TypeScript, FastAPI + Python, PostgreSQL + pgvector, OpenAI API, Celery và RabbitMQ.

## Kiến trúc

- Source nằm trong `src/`, tách `frontend/` và `backend/` (AR-01).
- Backend feature-based; Router -> Service -> Repository (AR-02, AR-03, AR-08).
- OpenAI/Embedding adapter nằm tại `src/backend/app/common/ai/` (AR-11).
- Business Rule được gắn mã BR tại Service khi có logic nghiệp vụ (DC-03).
- AI generation chạy background job qua Celery + RabbitMQ; HTTP submit trả `202 Accepted`.

## Yêu cầu môi trường

- Python 3.11+
- Node.js 20.9+ (khuyến nghị Node 22 LTS)
- PostgreSQL 15+ với pgvector
- RabbitMQ 4+
- npm 10+

PostgreSQL, pgvector và RabbitMQ cần được chuẩn bị trước khi chạy hệ thống.
Hướng dẫn database chi tiết nằm trong `src/backend/README.md`.

## Chạy nhanh

Các lệnh dưới đây dùng **Git Bash** và được chạy từ thư mục gốc repository.

### Lệnh 1 - Chuẩn bị backend

```bash
{ test -f .env || cp .env.example .env; } && python -m venv .venv && source .venv/Scripts/activate && python -m pip install -r src/backend/requirements.txt
```

### Lệnh 2 - Migration và seed dữ liệu demo

```bash
source .venv/Scripts/activate && python -m alembic -c src/backend/alembic.ini upgrade head && PYTHONPATH=src/backend python src/backend/scripts/seed_demo.py
```

### Lệnh 3 - Chạy backend API

Mở một Git Bash và chạy:

```bash
source .venv/Scripts/activate && python -m uvicorn app.main:app --reload --app-dir src/backend
```

### Lệnh 4 - Chạy Celery worker

Mở một Git Bash khác và chạy:

```bash
PYTHONPATH=src/backend ./.venv/Scripts/python.exe -m celery -A app.worker.celery_app worker --loglevel=INFO --pool=solo
```

### Lệnh 5 - Chạy frontend

Mở một Git Bash khác và chạy:

```bash
cd src/frontend && npm install && { test -f .env.local || cp .env.example .env.local; } && npm run dev
```

Sau khi các service đã chạy:

- Trang chủ: `http://localhost:3000`
- Swagger: `http://localhost:8000/docs`

Nếu cần sử dụng OpenAI thật, điền `OPENAI_API_KEY` hợp lệ trong `.env`.
Không commit file `.env`.

## Frontend Tuần 07

Frontend có các workspace theo role:

- Login và lưu Bearer token local.
- QA: nhập/cập nhật Requirement, submit AI generation, theo dõi Generation Job.
- QA/Manager: danh sách Test Case, edit, review, approve, request-fix, reject.
- Duplicate candidate bằng pgvector và lịch sử version/compare/restore.
- Manager: module, tags và coverage/statistics.
- QA/Manager: export CSV/XLSX các Test Case `APPROVED`; sau export thành công các Test Case đã xuất chuyển sang `EXPORTED`.
- Admin: tạo/list/cập nhật/vô hiệu hóa User và quản lý versioned Prompt/Model configuration.

Các màn hình có trạng thái loading, empty và error để đáp ứng FE-03.

## Kiểm thử và chất lượng

Backend, từ root repo:

```bash
python -m ruff format --check src/backend
python -m ruff check src/backend
python -m pytest -q
python -m pytest --cov=app --cov-report=term-missing
```

Frontend:

```bash
cd src/frontend
npm run format:check
npm run lint
npm run build
```

GitHub Actions kiểm tra backend và frontend theo cấu hình trong `.github/workflows/ci.yml`.

## pgvector / NC-05

- Embedding model mặc định: `text-embedding-3-small`.
- Dimensions: `1536`.
- Similarity threshold: `0.85`.
- Index: HNSW với cosine distance.
- Rebuild toàn bộ embedding:

```bash
PYTHONPATH=src/backend python src/backend/scripts/rebuild_embeddings.py --batch-size 50
```

Chi tiết cài đặt backend: `src/backend/README.md`.

## Tài khoản demo local

Sau khi chạy seed, có thể đăng nhập bằng các tài khoản sau:

| Role | Email | Password mặc định |
| --- | --- | --- |
| Admin | `admin@example.com` | `Demo_Change_Me_123!` |
| Manager | `manager@example.com` | `Demo_Change_Me_123!` |
| QA | `qa@example.com` | `Demo_Change_Me_123!` |

Password trên là giá trị mặc định của `DEMO_USER_PASSWORD` trong `.env.example`.

Nếu thay đổi `DEMO_USER_PASSWORD` trong `.env` trước khi chạy seed, password của các tài khoản demo sẽ sử dụng giá trị mới đó.

Đây chỉ là credential demo local, không sử dụng cho production.

## Tài liệu tiến độ

- `docs/weekly/Tuan07.md`
- `docs/kiem-thu/TC-TUAN07.md`
- `docs/kiem-thu/matran-truyvet.md`
- `docs/kiem-thu/tuan07.http`

## Nguồn tham khảo / AI hỗ trợ

Skeleton ban đầu được xây dựng với sự hỗ trợ của ChatGPT (OpenAI) và được tổ chức lại theo Quy định Code ITEC4401.

Các phần có AI hỗ trợ được ghi chú theo AI-05 trong source. Người nộp chịu trách nhiệm đọc, kiểm thử và giải thích được code khi bảo vệ.
