BÁO CÁO TIẾN ĐỘ TUẦN 05

Đề tài: Công cụ sinh test case tự động từ đặc tả yêu cầu bằng AI

Môn: ITEC4401 - Đồ án ngành

GVHD: ThS. Võ Việt Khoa

1. Công việc đã thực hiện

Trong Tuần 05, em tập trung xây dựng skeleton backend, cấu hình môi trường phát triển và triển khai vertical slice đầu tiên cho chức năng nhập đặc tả yêu cầu và sinh test case.

1.1. Cấu trúc và môi trường dự án

Tổ chức source code trong src/.

Backend sử dụng Python và FastAPI.

Tổ chức backend theo các lớp:

Router/Controller

Service

Repository

Tách adapter tích hợp AI tại app/common/ai/.

Sử dụng PostgreSQL làm hệ quản trị cơ sở dữ liệu.

Sử dụng SQLAlchemy để thao tác dữ liệu.

Sử dụng Alembic để quản lý database migration.

Cấu hình các file:

.gitignore

.env.example

.editorconfig

pyproject.toml

Cấu hình Ruff để kiểm tra và định dạng mã nguồn.

Secret và thông tin môi trường được đặt trong .env, không commit lên Git.

1.2. Cơ sở dữ liệu

Đã tạo database PostgreSQL phục vụ hệ thống và chạy Alembic migration thành công.

Các bảng baseline hiện có gồm:

users

modules

requirements

test_cases

audit_logs

alembic_version

Đã seed dữ liệu demo gồm các tài khoản có vai trò:

Admin

Manager

QA

Mật khẩu được lưu dưới dạng hash, không lưu plaintext.

1.3. Authentication và Authorization

Đã triển khai:

Đăng nhập bằng email và mật khẩu.

Xác thực bằng JWT Bearer Token.

Mã hóa mật khẩu bằng bcrypt.

Phân quyền theo vai trò người dùng.

Kiểm tra quyền truy cập bản ghi ở tầng backend.

Kết quả kiểm thử qua Swagger:

Đăng nhập sai thông tin: HTTP 401.

Đăng nhập tài khoản QA hợp lệ: HTTP 200.

Server trả về JWT Bearer Token hợp lệ.

1.4. Requirement Management

Đã triển khai chức năng nhập đặc tả yêu cầu.

Luồng xử lý:

Router -> Service -> Repository -> PostgreSQL

Đã kiểm thử tạo Requirement qua API:

API nhận module_id.

API nhận nội dung requirement.

API nhận Acceptance Criteria.

Requirement hợp lệ được lưu xuống PostgreSQL.

Kết quả tạo thành công: HTTP 201.

1.5. AI Test Case Generation

Đã xây dựng OpenAI Adapter để tách việc giao tiếp với dịch vụ AI khỏi business logic.

Luồng thiết kế:

Router -> TestCaseGenerationService -> OpenAIAdapter -> OpenAI API

Đầu ra AI được thiết kế theo Structured Output và được kiểm tra bằng Pydantic schema trước khi lưu.

Các quy tắc nghiệp vụ chính đã được đưa vào luồng xử lý:

Test case do AI sinh ra phải ở trạng thái DRAFT.

Test case phải có cấu trúc dữ liệu bắt buộc.

Test case phải truy vết được về Requirement.

Output không hợp lệ không được persist xuống database.

Người dùng không được thao tác Requirement không thuộc quyền truy cập của mình.

1.6. Human-in-the-loop

Đã chuẩn bị cấu trúc trạng thái phục vụ quy trình Human-in-the-loop.

Luồng mục tiêu:

DRAFT -> IN_REVIEW -> APPROVED

Các trạng thái mở rộng được thiết kế cho các bước tiếp theo:

NEEDS_FIX

REJECTED

EXPORTED

AI chỉ có nhiệm vụ tạo test case nháp. Quyền rà soát và duyệt cuối cùng thuộc về người dùng có thẩm quyền.

2. Kiểm thử, chất lượng mã nguồn và Issue

2.1. Unit Test

Framework sử dụng:

pytest

Lệnh chạy:

pytest -v

Kết quả:

Tổng số test: 10.

Passed: 10.

Failed: 0.

Các trường hợp đã kiểm thử gồm:

Tài khoản bị khóa không được đăng nhập.

Người dùng không có vai trò QA không được tạo Requirement.

Không cho tạo Requirement khi Module không tồn tại.

Structured Output thiếu trường bắt buộc bị từ chối.

AI output hợp lệ được lưu với trạng thái DRAFT.

QA không được sinh test case từ Requirement của người dùng khác.

AI output không hợp lệ không được persist.

Requirement không tồn tại thì không gọi AI.

Người không phải Admin không được tạo User.

Không cho tạo User với email đã tồn tại.

2.2. Coverage

Lệnh chạy:

pytest --cov=app --cov-report=term-missing

Kết quả:

Tổng coverage backend: 62%.

app/testcases/service.py: 100%.

app/requirements/service.py: 79%.

app/users/service.py: 80%.

Một số Router, Error Handler, Logging và phần tích hợp chưa được Unit Test bao phủ đầy đủ nên coverage toàn backend hiện ở mức 62%.

Ở Tuần 05, ưu tiên kiểm thử các Business Rule và Service cốt lõi thay vì tăng coverage bằng các test không mang nhiều giá trị nghiệp vụ.

2.3. Lint và Format

Công cụ sử dụng:

Ruff.

Các lệnh:

ruff format src/backend

ruff check src/backend

Trong quá trình kiểm tra đã xử lý:

Import chưa đúng thứ tự.

Import chưa đúng format.

Cảnh báo B008 do FastAPI Depends() được đặt trong default argument.

Chuẩn hóa Dependency Injection bằng Annotated.

Cảnh báo liên quan đến giá trị bearer.

Một số vấn đề formatting trong source code và test code.

Trước khi tạo Pull Request sẽ chạy lại:

ruff format src/backend

ruff check src/backend

pytest -v

để xác nhận source code vẫn đạt lint và toàn bộ Unit Test vẫn pass.

2.4. Kiểm thử API

Đã sử dụng Swagger UI để kiểm tra các API đã triển khai.

Kết quả:

Chức năng

Kết quả

Login sai email/mật khẩu

HTTP 401

Login QA hợp lệ

HTTP 200 + JWT

Authorize bằng Bearer Token

Thành công

Tạo Requirement hợp lệ

HTTP 201

Lưu Requirement xuống PostgreSQL

Thành công

Gọi luồng sinh Test Case

Request đi được tới OpenAI Provider

OpenAI API thật

HTTP 429 do không còn API credit

2.5. Issue / Defect phát hiện

DF-T05-01 - OpenAI API không còn credit

Khi kiểm thử OpenAI API thật, request đã đi theo luồng:

FastAPI -> TestCaseGenerationService -> OpenAIAdapter -> OpenAI API

Provider trả:

HTTP 429

insufficient_quota

credit_balance_exhausted

Nguyên nhân được xác định là tài khoản OpenAI API hiện không còn API credit.

Đây không phải lỗi kết nối của FastAPI, JWT, PostgreSQL hoặc Requirement API.

Unit Test cho business logic AI hiện sử dụng mock adapter để không phụ thuộc vào mạng và chi phí dịch vụ ngoài.

DF-T05-02 - PytestCollectionWarning

Pytest ban đầu hiểu nhầm các class có tên bắt đầu bằng Test, ví dụ:

TestCaseStatus

TestCaseGenerationService

là test class.

Cách xử lý:

Sử dụng alias trong file Unit Test.

Chạy lại pytest -v.

Kết quả:

10 test passed.

Không còn warning liên quan.

DF-T05-03 - Ruff B008 với FastAPI Depends

Ruff cảnh báo việc gọi Depends() trực tiếp trong default argument của FastAPI endpoint.

Cách xử lý:

Chuyển Dependency Injection sang Annotated.

Giữ nguyên cơ chế Dependency Injection của FastAPI.

Ví dụ:

Annotated[AsyncSession, Depends(get_session)]

DF-T05-04 - Import và formatting

Ruff phát hiện một số import chưa đúng thứ tự hoặc chưa đúng format.

Cách xử lý:

ruff check src/backend --fix

ruff format src/backend

2.6. Bảng tổng hợp Issue Tuần 05

ID

Vấn đề

Mức độ

Trạng thái

Cách xử lý

DF-T05-01

OpenAI API trả HTTP 429 do hết API credit

Medium

Open

Mock AI trong Unit Test; Integration Test thật thực hiện khi có API credit

DF-T05-02

Pytest hiểu nhầm class bắt đầu bằng Test

Low

Closed

Sử dụng alias trong Unit Test

DF-T05-03

Ruff B008 với FastAPI Depends()

Low

Closed

Chuyển sang Annotated

DF-T05-04

Import/format chưa đúng chuẩn Ruff

Low

Closed

Ruff auto-fix và format

3. Phần chưa hoàn thành, kế hoạch tiếp theo và câu hỏi GVHD

3.1. Phần chưa hoàn thành

Các nội dung chưa hoàn thành trong Tuần 05:

Chưa có một lần sinh test case end-to-end thành công bằng OpenAI API thật do tài khoản hiện không có API credit.

Chức năng Human-in-the-loop Review/Approve chưa hoàn thiện toàn bộ API.

Chức năng phát hiện và gộp test case trùng lặp chưa hoàn thiện.

Chức năng Export CSV/Excel chưa hoàn thiện.

Frontend Next.js chưa hoàn thiện luồng end-to-end.

Integration Test chưa được thực hiện đầy đủ.

Coverage cho Router và một số thành phần hạ tầng còn thấp.

Các nội dung trên sẽ tiếp tục được phát triển ở các tuần tiếp theo theo tiến độ đồ án.

3.2. Kế hoạch Tuần 06

Dự kiến Tuần 06 thực hiện:

Hoàn thiện API rà soát Test Case.

Hoàn thiện luồng trạng thái:

DRAFT

IN_REVIEW

NEEDS_FIX

APPROVED

REJECTED

Bổ sung Audit Log cho thao tác Edit và Approve.

Triển khai kiểm tra Test Case trùng lặp.

Bổ sung chức năng Merge khi cần thiết.

Hoàn thiện Alembic migration khi mô hình dữ liệu thay đổi.

Bổ sung Unit Test cho các Business Rule mới.

Cấu hình GitHub Actions CI.

Tiếp tục cập nhật Test Case.

Cập nhật Ma trận truy vết Requirement - Use Case - Business Rule - Test Case.

3.3. Câu hỏi gửi GVHD

Thưa thầy, ở mốc Tuần 05 em đã tích hợp OpenAI Adapter và kiểm thử các Business Rule của chức năng sinh test case bằng mock trong Unit Test; khi thử gọi OpenAI API thật thì provider trả HTTP 429 do tài khoản chưa có API credit. Ở Tuần 05 em có thể tiếp tục sử dụng mock để kiểm thử business logic và thực hiện Integration Test với LLM thật ở giai đoạn Integration Test sau, hay phải có ít nhất một lần gọi OpenAI API thật thành công ngay trong Tuần 05 luôn ạ?

4. Tổng kết Tuần 05

Trong Tuần 05 đã hoàn thành các nội dung chính sau:

Khởi tạo và cấu hình backend FastAPI.

Tổ chức backend theo Router -> Service -> Repository.

Kết nối PostgreSQL thành công.

Chạy Alembic migration thành công.

Seed dữ liệu demo thành công.

Triển khai JWT Authentication.

Triển khai kiểm tra Role và quyền truy cập dữ liệu.

Triển khai API nhập Requirement.

Requirement được lưu thành công xuống PostgreSQL.

Xây dựng OpenAI Adapter.

Xây dựng Structured Output Schema cho dữ liệu AI.

Cài đặt logic lưu Test Case AI ở trạng thái DRAFT.

Viết Unit Test cho các Business Rule chính.

Kết quả Unit Test: 10/10 passed.

Coverage backend hiện tại: 62%.

Đã kiểm thử luồng gọi OpenAI API thật và xác định dependency về API credit.

Đã sử dụng mock OpenAI Adapter để Unit Test không phụ thuộc vào dịch vụ bên ngoài.

Kết quả Tuần 05 tạo được nền tảng backend và kiểm thử ban đầu để tiếp tục phát triển các chức năng Human-in-the-loop, duplicate detection, approval, export và integration ở các tuần tiếp theo.
