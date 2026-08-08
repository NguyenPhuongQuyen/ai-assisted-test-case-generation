# Test case Tuần 05

Kỹ thuật áp dụng: Equivalence Partitioning, Boundary Value Analysis, State Transition và Authorization Testing.

## TC-GEN-001
| Trường | Nội dung |
|---|---|
| Mã TC | TC-GEN-001 |
| Chức năng / UC | UC06 - Sinh test case tự động |
| Mục tiêu | Chứng minh đầu ra AI hợp lệ được lưu ở `DRAFT` và có đủ trường bắt buộc theo BR-01/BR-02/BR-03 |
| Tiền điều kiện | QA đã đăng nhập; requirement id=10 thuộc QA; module id=3 tồn tại |
| Dữ liệu đầu vào | Requirement: “Một giao dịch đặt từ 1 đến 8 vé”; AC: “9 vé phải bị từ chối” |
| Các bước | 1. POST `/api/v1/requirements/10/test-cases`; 2. Gửi Bearer token hợp lệ; 3. Chờ response |
| Kết quả mong đợi | HTTP 201; item có `summary`, `steps`, `expected_result`, `priority`; `status=draft`; `requirement_id=10`; DB tạo TestCase + AuditLog |
| Kết quả thực tế | Chưa chạy |
| Trạng thái | Blocked - cập nhật ngày chạy và commit khi thực thi |

## TC-GEN-002
| Trường | Nội dung |
|---|---|
| Mã TC | TC-GEN-002 |
| Chức năng / UC | UC06 - Sinh test case tự động |
| Mục tiêu | Chứng minh hệ thống chặn IDOR khi QA truy cập requirement của người khác (SE-06/BR-07) |
| Tiền điều kiện | QA user_id=7; requirement id=10 thuộc user_id=99 |
| Dữ liệu đầu vào | POST `/api/v1/requirements/10/test-cases` bằng token user_id=7 |
| Các bước | 1. Đăng nhập QA A; 2. Gọi endpoint generate cho requirement của QA B |
| Kết quả mong đợi | HTTP 403; `error.code=FORBIDDEN_RECORD`; không gọi OpenAI; không tạo TestCase/AuditLog |
| Kết quả thực tế | Chưa chạy |
| Trạng thái | Blocked - cập nhật ngày chạy và commit khi thực thi |

## TC-GEN-003
| Trường | Nội dung |
|---|---|
| Mã TC | TC-GEN-003 |
| Chức năng / UC | UC06 - Sinh test case tự động |
| Mục tiêu | Chứng minh output AI sai schema bị chặn theo BR-04 |
| Tiền điều kiện | QA có quyền trên requirement id=10 |
| Dữ liệu đầu vào | Mock AI output thiếu `expected_result` |
| Các bước | 1. Gọi service generate; 2. Adapter/Pydantic validate output |
| Kết quả mong đợi | Nhận lỗi `AI_OUTPUT_INVALID`/ValidationError; không tạo TestCase; không commit transaction |
| Kết quả thực tế | Chưa chạy |
| Trạng thái | Blocked - cập nhật ngày chạy và commit khi thực thi |

## TC-REQ-001
| Trường | Nội dung |
|---|---|
| Mã TC | TC-REQ-001 |
| Chức năng / UC | UC05 - Nhập đặc tả yêu cầu |
| Mục tiêu | Chứng minh server từ chối requirement quá ngắn (SE-04/AP-05) |
| Tiền điều kiện | Đăng nhập role QA |
| Dữ liệu đầu vào | `content="abc"`, `module_id=3` |
| Các bước | 1. POST `/api/v1/requirements`; 2. Gửi body trên |
| Kết quả mong đợi | HTTP 422; body theo ER-05 với `error.code=VALIDATION_ERROR`; không tạo Requirement |
| Kết quả thực tế | Chưa chạy |
| Trạng thái | Blocked - cập nhật ngày chạy và commit khi thực thi |

## TC-AUTH-001
| Trường | Nội dung |
|---|---|
| Mã TC | TC-AUTH-001 |
| Chức năng / UC | UC01 - Đăng nhập |
| Mục tiêu | Chứng minh tài khoản bị khóa tạm sau nhiều lần đăng nhập sai theo SE-11 |
| Tiền điều kiện | Tài khoản QA tồn tại, `failed_login_attempts=4` |
| Dữ liệu đầu vào | Mật khẩu sai |
| Các bước | 1. POST `/api/v1/auth/login` với mật khẩu sai; 2. Gọi login lại trong thời gian khóa |
| Kết quả mong đợi | Lần sai thứ 5 trả 401 và đặt `locked_until`; lần tiếp theo trả HTTP 429 `ACCOUNT_LOCKED` |
| Kết quả thực tế | Chưa chạy |
| Trạng thái | Blocked - cập nhật ngày chạy và commit khi thực thi |


## TC-AUTH-002
| Trường | Nội dung |
|---|---|
| Mã TC | TC-AUTH-002 |
| Chức năng / UC | UC02 - Quản lý người dùng |
| Mục tiêu | Chứng minh QA không thể tạo tài khoản mới thay Admin (SE-05) |
| Tiền điều kiện | Đăng nhập role QA |
| Dữ liệu đầu vào | POST `/api/v1/users` với role=`qa` |
| Các bước | 1. Lấy token QA; 2. Gọi POST `/api/v1/users` |
| Kết quả mong đợi | HTTP 403; `error.code=FORBIDDEN_ROLE`; không tạo user mới |
| Kết quả thực tế | Chưa chạy |
| Trạng thái | Blocked - cập nhật ngày chạy và commit khi thực thi |
