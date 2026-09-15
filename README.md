# Công cụ sinh Test Case tự động từ đặc tả yêu cầu bằng AI

**Đồ án ngành ITEC4401 - Đề tài #13**

Hệ thống hỗ trợ quản lý Requirement/SRS, sinh Test Case bằng AI, tạo Test Case thủ công, Human-in-the-loop review, quản lý phiên bản, phát hiện trùng lặp, theo dõi coverage và export Test Case ra CSV/XLSX.

---

## 1. Chức năng chính

- Quản lý người dùng theo vai trò Admin / Manager / QA.
- Quản lý Module và Requirement.
- Sinh Test Case từ Requirement bằng OpenAI.
- Xử lý tác vụ sinh Test Case bất đồng bộ bằng Celery + RabbitMQ.
- Tạo Test Case thủ công mà không cần OpenAI API.
- Human-in-the-loop review:
  - Draft
  - In Review
  - Approved
  - Needs Fix
  - Rejected
- Chỉnh sửa Test Case với:
  - Summary
  - Priority
  - Preconditions
  - Steps
  - Expected Result
  - Test Techniques
  - Review Note
- Quản lý version của Test Case.
- Duplicate Detection bằng embedding + pgvector.
- Theo dõi Requirement Coverage theo Module.
- Export Test Case đã Approved sang:
  - CSV
  - XLSX
- Health Check cho:
  - Application
  - PostgreSQL
  - RabbitMQ
- Audit log cho các thao tác quan trọng.

---

## 2. Công nghệ sử dụng

### Backend

- Python 3.11+
- FastAPI
- SQLAlchemy Async
- Alembic
- PostgreSQL
- pgvector
- Celery
- RabbitMQ
- OpenAI API
- Pytest
- Ruff

### Frontend

- Next.js 16
- React
- TypeScript
- ESLint
- Prettier

### DevOps / Quality

- Git / GitHub
- GitHub Actions
- Automated Unit Test
- Automated Integration Test

> Project không yêu cầu Docker hoặc PyCharm.  
> Trên Windows, các script được chạy bằng Git Bash.

---

## 3. Kiến trúc tổng quan

```text
User
  |
  v
Next.js Frontend
  |
  | REST API
  v
FastAPI Backend
  |
  +--------------------+
  |                    |
  v                    v
PostgreSQL          RabbitMQ
+ pgvector              |
                        v
                     Celery
                        |
                        v
                    OpenAI API
```

Luồng sinh Test Case bằng AI:

```text
Requirement
    |
    v
FastAPI
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
OpenAI API
    |
    v
Generated Test Cases
    |
    v
Human Review
    |
    v
Approved / Needs Fix / Rejected
```

Luồng tạo Test Case thủ công:

```text
Requirement
    |
    v
Manual Test Case Form
    |
    v
FastAPI
    |
    v
DRAFT Test Case
    |
    v
Version 1
    |
    v
Human Review
```

---

## 4. Cấu trúc thư mục

```text
ai-assisted-test-case-generation/
├── database/
├── docs/
│   └── assets/
│       └── final/
├── scripts/
│   ├── dev-up.sh
│   ├── dev-down.sh
│   ├── install.sh
│   ├── init-demo.sh
│   └── python.sh
├── src/
│   ├── backend/
│   │   ├── app/
│   │   ├── scripts/
│   │   ├── tests/
│   │   ├── alembic/
│   │   └── requirements.txt
│   └── frontend/
├── .env.example
├── LICENSE
├── pyproject.toml
└── README.md
```

---

# 5. Yêu cầu môi trường

Cài đặt trước:

- Git
- Git Bash nếu sử dụng Windows
- Python 3.11+
- Node.js 20.9+
- npm
- PostgreSQL 15+
- extension `pgvector`
- RabbitMQ 4+

PostgreSQL và RabbitMQ phải được cài đặt và có thể chạy trên máy.

Kiểm tra nhanh:

```bash
git --version
python --version
node --version
npm --version
```

Nếu Windows không nhận `python` nhưng có Python Launcher:

```bash
py --version
```

Script `install.sh` sẽ tự tìm Python hợp lệ từ:

```text
python3
python
py -3
```

và chỉ chấp nhận Python từ version 3.11 trở lên.

---

# 6. Chạy nhanh

Quy trình dưới đây đã được kiểm thử lại trên một fresh clone độc lập.

## Bước 1 - Clone repository

```bash
git clone -b overall https://github.com/NguyenPhuongQuyen/ai-assisted-test-case-generation.git
cd ai-assisted-test-case-generation
```

## Bước 2 - Cài dependency và tạo môi trường local

```bash
./scripts/install.sh
```

Script tự động:

- tạo `.env` từ `.env.example` nếu chưa có;
- tạo `src/frontend/.env.local`;
- tạo Python virtual environment `.venv`;
- cài Backend dependencies;
- cài Frontend dependencies.

## Bước 3 - Kiểm tra cấu hình database

Mở file:

```text
.env
```

Cấu hình mặc định:

```text
DATABASE_URL=postgresql+asyncpg://app_user:change_me@localhost:5432/testcase_ai
```

Nếu PostgreSQL local sử dụng username/password khác thì sửa `DATABASE_URL` cho phù hợp.

Database cần có extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Bước 4 - Migration và seed demo

```bash
./scripts/init-demo.sh
```

Script sẽ:

- chạy Alembic migration;
- tạo demo data.

Demo seed hiện gồm:

```text
Users        : 3
Modules      : 2
Requirements : 3
Test cases   : 12
```

## Bước 5 - Khởi động hệ thống

```bash
./scripts/dev-up.sh
```

Sau khi hệ thống khởi động:

| Thành phần | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend | http://127.0.0.1:8001 |
| Swagger | http://127.0.0.1:8001/docs |
| Health | http://127.0.0.1:8001/health |

Dừng các service của ứng dụng:

```bash
./scripts/dev-down.sh
```

PostgreSQL và RabbitMQ được giữ lại vì đây là service môi trường dùng chung.

---

# 7. Cấu hình môi trường

File `.env.example`:

```env
DATABASE_URL=postgresql+asyncpg://app_user:change_me@localhost:5432/testcase_ai

JWT_SECRET=change_me_to_a_long_random_secret_at_least_32_chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

OPENAI_API_KEY=sk-example-not-a-real-key
OPENAI_MODEL=gpt-5
OPENAI_MAX_OUTPUT_TOKENS=4000

OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSIONS=1536

DUPLICATE_SIMILARITY_THRESHOLD=0.85

AI_RATE_LIMIT_MAX_REQUESTS=10
AI_RATE_LIMIT_WINDOW_SECONDS=300

FRONTEND_ORIGIN=http://localhost:3000

LOG_LEVEL=INFO

DEMO_USER_PASSWORD=Demo_Change_Me_123!

CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
```

## OpenAI API Key

Muốn sử dụng chức năng sinh Test Case bằng AI hoặc embedding, cập nhật:

```env
OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
```

Không commit API key thật lên GitHub.

Nếu không có OpenAI API key, người dùng vẫn có thể:

- đăng nhập;
- quản lý Module;
- quản lý Requirement;
- tạo Test Case thủ công;
- review Test Case;
- quản lý version;
- export các Test Case hợp lệ.

---

# 8. Tài khoản demo

Sau khi chạy:

```bash
./scripts/init-demo.sh
```

có các tài khoản:

```text
admin@example.com
manager@example.com
qa@example.com
```

Password mặc định:

```text
Demo_Change_Me_123!
```

Password được cấu hình qua:

```env
DEMO_USER_PASSWORD
```

---

# 9. Health Check

Endpoint:

```text
GET /health
```

Ví dụ:

```json
{
  "status": "ok",
  "components": {
    "application": "ok",
    "database": "ok",
    "queue": "ok"
  }
}
```

Health check kiểm tra thực tế:

- FastAPI application;
- kết nối PostgreSQL;
- kết nối RabbitMQ.

Nếu dependency quan trọng không hoạt động, endpoint trả HTTP `503`.

![Health Check](docs/assets/final/08_health.jpg)

---

# 10. Requirement và AI Generation

QA có thể chọn Requirement và tạo Generation Job.

Generation Job được đưa qua:

```text
FastAPI
→ RabbitMQ
→ Celery Worker
→ OpenAI
→ Test Case
```

Việc sinh AI chạy bất đồng bộ, frontend có thể theo dõi trạng thái job.

Các trạng thái job gồm:

```text
pending
running
completed
failed
```

Ví dụ Generation Job hoàn tất:

![Requirement AI Completed](docs/assets/final/04_requirement_ai_completed.jpg)

---

# 11. Tạo Test Case thủ công

Ngoài AI Generation, hệ thống hỗ trợ tạo Test Case trực tiếp từ Requirement.

Route:

```text
POST /requirements/{requirement_id}/test-cases/manual
```

Các trường hỗ trợ:

```text
Summary
Preconditions
Steps
Expected Result
Priority
Test Techniques
```

Test Case tạo thủ công:

- không gọi OpenAI;
- không tạo Generation Job;
- được tạo ở trạng thái `DRAFT`;
- tự động có Version 1;
- có thể tiếp tục review như Test Case do AI tạo.

![Manual Test Case Created](docs/assets/final/03_manual_testcase_created.jpg)

---

# 12. Human-in-the-loop Review

QA/Manager có thể review Test Case trước khi sử dụng.

Workflow:

```text
DRAFT
  |
  v
IN REVIEW
  |
  +-----------> APPROVED
  |
  +-----------> NEEDS FIX
  |
  +-----------> REJECTED
```

Editor hỗ trợ:

- Summary
- Priority
- Preconditions
- Steps
- Expected Result
- Test Techniques
- Review Note

![Review Test Case](docs/assets/final/05_review_testcase_editor.jpg)

---

# 13. Versioning

Khi Test Case được chỉnh sửa, hệ thống lưu lại lịch sử version.

Mỗi version lưu snapshot của nội dung Test Case.

Chức năng hỗ trợ:

- xem lịch sử version;
- so sánh version;
- restore version cũ.

Test Case thủ công mới được tạo có:

```text
Version 1
```

---

# 14. Duplicate Detection

Hệ thống hỗ trợ tìm Test Case có nội dung tương đồng bằng:

```text
OpenAI Embedding
+
PostgreSQL pgvector
```

Cấu hình:

```env
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSIONS=1536
DUPLICATE_SIMILARITY_THRESHOLD=0.85
```

Duplicate Detection hỗ trợ reviewer nhận biết và xử lý các Test Case có độ tương đồng cao.

---

# 15. Module Coverage và Export

Module workspace hiển thị:

- tổng số Requirement;
- Requirement đã được cover;
- Coverage percentage;
- số Test Case theo trạng thái.

![Module Coverage](docs/assets/final/06_module_coverage.jpg)

Hệ thống hỗ trợ export các Test Case hợp lệ sang:

```text
CSV
XLSX
```

Export sử dụng database locking để tránh hai request đồng thời export cùng một tập Test Case.

---

# 16. Swagger / OpenAPI

FastAPI tự động cung cấp Swagger UI tại:

```text
http://127.0.0.1:8001/docs
```

Swagger bao gồm API cho:

- authentication;
- users;
- modules;
- requirements;
- AI generation;
- manual Test Case creation;
- review;
- versioning;
- duplicate detection;
- export.

![Swagger API](docs/assets/final/07_swagger.jpg)

---

# 17. Automated Tests

## Unit Tests

```bash
PYTHONPATH=src/backend ./scripts/python.sh -m pytest src/backend/tests/unit -q
```

Kết quả kiểm thử cuối:

```text
92 passed
```

## Integration Tests

Integration tests sử dụng database riêng:

```text
testcase_ai_test
```

Ví dụ cấu hình:

```bash
export TEST_DATABASE_URL="postgresql+asyncpg://app_user:change_me@localhost:5432/testcase_ai_test"
```

Chạy integration tests:

```bash
DATABASE_URL="$TEST_DATABASE_URL" PYTHONPATH=src/backend ./scripts/python.sh -m pytest src/backend/tests/integration -q
```

Kết quả:

```text
18 passed
```

## Toàn bộ Backend Tests

```bash
DATABASE_URL="$TEST_DATABASE_URL" PYTHONPATH=src/backend ./scripts/python.sh -m pytest src/backend/tests -q
```

Kết quả cuối:

```text
110 passed
```

Tổng:

| Nhóm | Kết quả |
|---|---:|
| Unit Test | 92 passed |
| Integration Test | 18 passed |
| Backend Automated Test | 110 passed |

Một số integration flow được kiểm thử gồm:

- authentication;
- requirement;
- testcase lifecycle;
- AI generation boundary bằng mock;
- export;
- concurrent export;
- manual Test Case creation;
- versioning;
- duplicate flow.

---

# 18. Backend Quality Check

Format:

```bash
./scripts/python.sh -m ruff format --check src/backend
```

Lint:

```bash
./scripts/python.sh -m ruff check src/backend
```

Kết quả cuối:

```text
122 files already formatted
All checks passed!
```

---

# 19. Frontend Quality Check

```bash
cd src/frontend
npm run format:check
npm run lint
npm run build
```

Kết quả cuối:

```text
Prettier: PASS
ESLint: PASS
Next.js production build: PASS
```

---

# 20. Fresh Clone Verification

Project đã được kiểm thử trên một thư mục clone mới hoàn toàn.

Quy trình được xác nhận:

```text
git clone
    ↓
./scripts/install.sh
    ↓
tạo .env
    ↓
tạo .env.local
    ↓
tạo .venv
    ↓
cài Backend dependencies
    ↓
cài Frontend dependencies
    ↓
./scripts/init-demo.sh
    ↓
Alembic migration
    ↓
Demo seed
    ↓
./scripts/dev-up.sh
    ↓
Frontend + Backend + Celery hoạt động
    ↓
Đăng nhập thành công
```

Fresh clone được kiểm thử trên Windows bằng Git Bash mà không phụ thuộc đường dẫn ổ đĩa cụ thể.

---

# 21. Development Scripts

## Python Wrapper

```bash
./scripts/python.sh
```

Script tự tìm Python trong virtual environment:

```text
.venv/bin/python
```

hoặc:

```text
.venv/Scripts/python.exe
```

Nhờ đó command trong project không phụ thuộc trực tiếp vào hệ điều hành.

## Install

```bash
./scripts/install.sh
```

## Initialize Database

```bash
./scripts/init-demo.sh
```

## Start Development

```bash
./scripts/dev-up.sh
```

## Stop Development

```bash
./scripts/dev-down.sh
```

---

# 22. CI

Repository sử dụng GitHub Actions để kiểm tra source code tự động.

Quality gate bao gồm các bước như:

```text
Backend lint
Backend tests
Frontend lint
Frontend build
```

Mục tiêu là phát hiện lỗi trước khi merge hoặc release source.

---

# 23. Bảo mật

Các nguyên tắc được áp dụng:

- API key không commit vào Git.
- `.env` và `.env.local` nằm trong `.gitignore`.
- JWT secret lấy từ biến môi trường.
- Password được hash trước khi lưu.
- Role-based access control cho Admin / Manager / QA.
- Rate limiting cho AI Generation.
- Audit log cho các hành động quan trọng.
- Test database tách biệt với development database.
- Export chỉ xử lý Test Case phù hợp với workflow.
- Database transaction/locking được sử dụng cho các thao tác đồng thời quan trọng.

---

# 24. AI Assistance

Trong quá trình phát triển, AI được sử dụng để hỗ trợ:

- phân tích requirement;
- đề xuất implementation;
- review source code;
- viết và cải thiện automated tests;
- hỗ trợ tài liệu kỹ thuật;
- debug trong quá trình phát triển.

Các phần source có sử dụng AI assistance được ghi chú theo quy định của môn học khi cần thiết.

AI không thay thế quá trình kiểm thử, review và xác nhận kết quả của người phát triển.

---

# 25. Ảnh minh họa hệ thống

## Tạo Test Case thủ công

![Manual Test Case](docs/assets/final/03_manual_testcase_created.jpg)

## Requirement và AI Generation hoàn tất

![AI Generation](docs/assets/final/04_requirement_ai_completed.jpg)

## Human-in-the-loop Review

![Human Review](docs/assets/final/05_review_testcase_editor.jpg)

## Module Coverage

![Module Coverage](docs/assets/final/06_module_coverage.jpg)

## Swagger / OpenAPI

![Swagger](docs/assets/final/07_swagger.jpg)

## Health Check

![Health](docs/assets/final/08_health.jpg)

---

# 26. License

Project sử dụng MIT License.

Xem chi tiết tại:

```text
LICENSE
```

---

# 27. Tác giả

**Nguyễn Phương Quyên**

Đồ án ngành ITEC4401  
Đề tài #13 - Công cụ sinh Test Case tự động từ đặc tả yêu cầu bằng AI