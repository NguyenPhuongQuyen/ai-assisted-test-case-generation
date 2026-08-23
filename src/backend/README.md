# Backend - FastAPI

## Yêu cầu
- Python 3.11+
- PostgreSQL 15+

## Cài đặt
Từ thư mục gốc repo:
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r src/backend/requirements.txt
copy .env.example .env
```

Tạo database PostgreSQL `testcase_ai`, sau đó cập nhật `DATABASE_URL` trong `.env`.

Chạy migration và seed:
```bash
alembic -c src/backend/alembic.ini upgrade head
PYTHONPATH=src/backend python src/backend/scripts/seed_demo.py
```

## Chạy dev
```bash
uvicorn app.main:app --reload --app-dir src/backend
```

Swagger: `http://localhost:8000/docs`.

## Kiểm tra
```bash
ruff format --check src/backend
ruff check src/backend
pytest
pytest --cov=app --cov-report=term-missing
```

## Kiến trúc
Feature-based theo AR-08; trong mỗi feature tách Router -> Service -> Repository theo AR-02/AR-03.
OpenAI chỉ được gọi qua `app/common/ai/openai_adapter.py` theo AR-11.
