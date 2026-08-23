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

Các lệnh dưới đây dùng **Git Bash** và được chạy từ thư mục gốc repository.

Yêu cầu trước khi chạy: Python, Node.js và PostgreSQL đã được cài đặt. Database được cấu hình trong `.env.example`.

### Lệnh 1 - Chuẩn bị backend

```bash
test -f .env || cp .env.example .env && python -m venv .venv && source .venv/Scripts/activate && python -m pip install -r src/backend/requirements.txt
```

### Lệnh 2 - Migration và seed dữ liệu demo

```bash
source .venv/Scripts/activate && alembic -c src/backend/alembic.ini upgrade head && PYTHONPATH=src/backend python src/backend/scripts/seed_demo.py
```

### Lệnh 3 - Chạy backend

Mở một Git Bash và chạy:

```bash
source .venv/Scripts/activate && uvicorn app.main:app --reload --app-dir src/backend
```

### Lệnh 4 - Chạy frontend

Mở Git Bash khác và chạy:

```bash
cd src/frontend && npm install && { test -f .env.local || cp .env.example .env.local; } && npm run dev
```

Sau khi hai service đã chạy:

- Trang chủ: `http://localhost:3000`
- Swagger: `http://localhost:8000/docs`

Nếu cần sử dụng OpenAI thật, điền `OPENAI_API_KEY` hợp lệ trong `.env`.
Không commit file `.env`.

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

OpenAI API chỉ được dùng qua adapter riêng; model được cấu hình bằng `OPENAI_MODEL` để không hardcode nhà cung cấp/model trong nghiệp vụ.

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

## Hướng dẫn chạy chi tiết và Postman
- `docs/huong-dan/TUAN05-SETUP-POSTMAN.md`
- `docs/kiem-thu/Tuan05_OpenAI.postman_collection.json`
- `docs/kiem-thu/Tuan05_OpenAI.postman_environment.json`
- `docs/kiem-thu/database_checks.sql`
