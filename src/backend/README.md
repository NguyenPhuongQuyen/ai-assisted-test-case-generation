# Backend - FastAPI

## Yêu cầu

- Python 3.11+
- PostgreSQL 15+ với extension pgvector
- RabbitMQ 4+ cho Celery background worker

## Cài đặt

Từ thư mục gốc repo:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r src/backend/requirements.txt
copy .env.example .env
```

Tạo database PostgreSQL `testcase_ai`, sau đó cập nhật `DATABASE_URL` và các biến local trong `.env`.

Chạy migration và seed:

```bash
alembic -c src/backend/alembic.ini upgrade head
python src/backend/scripts/seed_demo.py
```

Migration hiện tại đi từ baseline `0001` đến `0009_nc10_user_admin`.

## Chạy dev

Backend API:

```bash
uvicorn app.main:app --reload --app-dir src/backend
```

Celery worker:

```bash
celery -A app.worker.celery_app worker --loglevel=INFO --pool=solo --workdir=src/backend
```

Swagger: `http://localhost:8000/docs`.

## Kiểm tra

```bash
ruff format --check src/backend
ruff check src/backend
pytest
pytest --cov=app --cov-report=term-missing
```

## pgvector cho NC-05

Duplicate detection dùng PostgreSQL pgvector, cosine similarity và HNSW index. Cấu hình mặc định:

```env
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSIONS=1536
DUPLICATE_SIMILARITY_THRESHOLD=0.85
```

Migration `0004_week07_pgvector_duplicates` bật extension `vector`, thêm cột `embedding vector(1536)` và tạo HNSW index `ix_test_cases_embedding_hnsw`.

Nếu nội dung test case được chỉnh sửa, embedding cũ bị vô hiệu hóa và được tạo lại khi kiểm tra duplicate. Build lại toàn bộ embedding:

```bash
PYTHONPATH=src/backend python src/backend/scripts/rebuild_embeddings.py --batch-size 50
```

## Export NC-07

CSV không cần dependency bổ sung. XLSX dùng `openpyxl`. API export chỉ lấy test case `APPROVED`, kiểm quyền theo role và ghi audit event.

## Prompt/Model Configuration NC-09

Prompt, model name, schema version và max output tokens được lưu theo version trong database. Generation service lấy active prompt config thay vì hardcode prompt trong nghiệp vụ.

## User Administration NC-10

Admin có thể list/create/update/vô hiệu hóa tài khoản. `is_active=false` chặn đăng nhập, và thao tác quản trị user được ghi audit mà không lưu password/password hash vào before/after state.

## Kiến trúc

Feature-based theo AR-08; trong mỗi feature tách Router -> Service -> Repository theo AR-02/AR-03.
OpenAI chỉ được gọi qua `app/common/ai/` theo AR-11.
