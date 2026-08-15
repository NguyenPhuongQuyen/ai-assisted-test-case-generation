# Công cụ sinh test case tự động từ đặc tả yêu cầu bằng AI

Đồ án ngành ITEC4401 - Đề tài #13. Stack: Next.js 16 + TypeScript, FastAPI + Python, PostgreSQL, OpenAI API.

## Kiến trúc
- Source nằm trong `src/`, tách `frontend/` và `backend/` (AR-01).
- Backend feature-based; Router -> Service -> Repository (AR-02, AR-03, AR-08).
- OpenAI adapter chỉ nằm tại `src/backend/app/common/ai/` (AR-11).
- Business Rule được gắn mã BR trong Service (DC-03).

## Yêu cầu môi trường
- Python 3.11+
- Node.js 20.9+ (khuyến nghị Node 22 LTS)
- PostgreSQL 15+
- npm 10+

## Chạy nhanh
1. Copy `.env.example` thành `.env` và thay `DATABASE_URL`, `JWT_SECRET`, `OPENAI_API_KEY` bằng giá trị local.
2. Backend: `pip install -r src/backend/requirements.txt`
3. Database: `alembic -c src/backend/alembic.ini upgrade head && python src/backend/scripts/seed_demo.py`
4. Backend: `uvicorn app.main:app --reload --app-dir src/backend`
5. Frontend: `cd src/frontend && npm install && copy .env.example .env.local && npm run dev`
6. Mở `http://localhost:3000`; Swagger ở `http://localhost:8000/docs`.

> Alembic baseline + seed đã được chuẩn bị sớm để repo chạy lại được. Tuần 06 tiếp tục chấm đầy đủ nhóm DB/AP và thêm GitHub Actions CI theo Mục 21.1.

## Kiểm thử và chất lượng
Backend, từ root repo:
```bash
ruff format --check src/backend
ruff check src/backend
pytest
pytest --cov=app --cov-report=term-missing
```

Frontend:
```bash
cd src/frontend
npm run format:check
npm run lint
npm run build
```

## Biến môi trường
Không commit `.env`. `.env.example` chỉ chứa giá trị mẫu vô hại (SE-01, CF-01, CF-02).

## Tài liệu tiến độ
- `docs/weekly/Tuan05.md`
- `docs/kiem-thu/TC-TUAN05.md`
- `docs/kiem-thu/matran-truyvet.md`
- `docs/assets/NGUON.md`

## Nguồn tham khảo / AI hỗ trợ
Skeleton ban đầu được xây dựng với sự hỗ trợ của ChatGPT (OpenAI) và được tổ chức lại theo Quy định Code ITEC4401.
Người nộp phải tự đọc, chạy thử, chỉnh sửa và giải thích được mọi dòng code theo AI-01..AI-04.

OpenAI API chỉ được dùng qua adapter riêng; model được cấu hình bằng `OPENAI_MODEL` để không hardcode nhà cung cấp/model trong nghiệp vụ.

## Tài khoản demo local
Sau khi chạy seed:
- Admin: `admin@example.com`
- Manager: `manager@example.com`
- QA: `qa@example.com`
- Password: giá trị `DEMO_USER_PASSWORD` trong `.env` (file `.env.example` chỉ chứa mật khẩu mẫu vô hại).

## Hướng dẫn chạy chi tiết và Postman
- `docs/kiem-thu/Tuan05_OpenAI.postman_collection.json`
- `docs/kiem-thu/Tuan05_OpenAI.postman_environment.json`
- `docs/kiem-thu/database_checks.sql`

---

## Background Job cho AI Generation - Tuần 06

Tác vụ sinh Test Case bằng AI được đưa sang background job bằng Celery để HTTP request không phải chờ OpenAI xử lý hoàn tất.

### Thành phần

- FastAPI
- PostgreSQL
- SQLAlchemy Async
- Alembic
- OpenAI Adapter
- Celery 5.6
- RabbitMQ broker

### Cấu hình

Tạo file `.env` từ `.env.example` và điền các giá trị local cần thiết.

```env
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//

```
