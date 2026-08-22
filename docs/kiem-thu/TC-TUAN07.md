# Test Case Tuần 07

## 1. Phạm vi

Tuần 07 tập trung thiết kế test case phủ các use case chính, Human-in-the-loop, vector duplicate detection, Module/Coverage, Export, Prompt Config và Version Restore. Manual case chưa chạy giữ trạng thái `Chưa chạy`; không ghi PASS nếu chưa có bằng chứng.

Bằng chứng tự động hiện có trước khi bổ sung frontend/docs:

- Backend Unit Test: `73 passed`.
- Tested commit: `06675fe`.
- Ruff check / format: PASS.
- Alembic: `0009_nc10_user_admin (head)`.

## 2. TC-07 - Kỹ thuật kiểm thử sử dụng

| Kỹ thuật | Áp dụng |
|---|---|
| State Transition | Vòng đời Test Case: DRAFT → IN_REVIEW → APPROVED → EXPORTED; có thể chuyển sang NEEDS_FIX hoặc REJECTED theo rule |
| Decision Table | Quyền theo role × trạng thái × hành động approve/export/module/prompt |
| Boundary Value Analysis | Requirement min 20 ký tự; similarity threshold 0.85; pagination/pageSize; tags tối đa 10 |
| Equivalence Partitioning | Input hợp lệ/không hợp lệ cho Requirement, Module, Prompt Config, User |



---

## 3A. Test case chi tiết theo TC-03

> Các bảng phía dưới là bản đặc tả chi tiết dùng để đáp ứng TC-03/TC-04/TC-05.
> Các bảng ở các mục tiếp theo vẫn được giữ làm catalog theo use case và kỹ thuật kiểm thử.
>
> Kết quả `PASS - Unit Test` dưới đây dựa trên lần chạy `73 passed` ngày 22/08/2026
> tại commit `06675fe`. Test manual chưa thực thi không được tự đổi thành PASS.

### TC-REQ-012 — Requirement dưới min boundary

| Trường | Nội dung |
|---|---|
| Mã TC | TC-REQ-012 |
| Chức năng / UC | UC05 - Nhập/Cập nhật Requirement |
| Mục tiêu | Chứng minh hệ thống từ chối Requirement có content nhỏ hơn 20 ký tự. |
| Tiền điều kiện | User QA đã đăng nhập; có quyền tạo/cập nhật Requirement. |
| Dữ liệu đầu vào | `content` có đúng 19 ký tự; các field còn lại hợp lệ. |
| Các bước | 1. Mở form Requirement. 2. Nhập content 19 ký tự. 3. Nhập các field bắt buộc còn lại. 4. Bấm lưu. |
| Kết quả mong đợi | Backend trả HTTP 422; Requirement không được lưu. |
| Kết quả thực tế | Chưa chạy manual. |
| Trạng thái | Chưa chạy manual; thiết kế 22/08/2026. |

### TC-REQ-013 — Requirement tại min boundary

| Trường | Nội dung |
|---|---|
| Mã TC | TC-REQ-013 |
| Chức năng / UC | UC05 - Nhập/Cập nhật Requirement |
| Mục tiêu | Chứng minh content đúng 20 ký tự được schema chấp nhận. |
| Tiền điều kiện | User QA đã đăng nhập; dữ liệu liên quan hợp lệ. |
| Dữ liệu đầu vào | `content` có đúng 20 ký tự. |
| Các bước | 1. Mở form Requirement. 2. Nhập content 20 ký tự. 3. Điền field bắt buộc. 4. Bấm lưu. |
| Kết quả mong đợi | Không bị từ chối bởi rule min-length; nếu dữ liệu còn lại hợp lệ thì request được xử lý. |
| Kết quả thực tế | Chưa chạy manual. |
| Trạng thái | Chưa chạy manual; thiết kế 22/08/2026. |

### TC-REQ-014 — Requirement trên min boundary

| Trường | Nội dung |
|---|---|
| Mã TC | TC-REQ-014 |
| Chức năng / UC | UC05 - Nhập/Cập nhật Requirement |
| Mục tiêu | Chứng minh content 21 ký tự thuộc phân vùng hợp lệ. |
| Tiền điều kiện | User QA đã đăng nhập. |
| Dữ liệu đầu vào | `content` có đúng 21 ký tự. |
| Các bước | 1. Mở form Requirement. 2. Nhập content 21 ký tự. 3. Điền dữ liệu bắt buộc. 4. Bấm lưu. |
| Kết quả mong đợi | Request không bị từ chối bởi rule min-length. |
| Kết quả thực tế | Chưa chạy manual. |
| Trạng thái | Chưa chạy manual; thiết kế 22/08/2026. |

### TC-REQ-015 — Không sửa Requirement của user khác

| Trường | Nội dung |
|---|---|
| Mã TC | TC-REQ-015 |
| Chức năng / UC | UC05 - Requirement / Authorization |
| Mục tiêu | Chứng minh BR-07 chặn QA sửa Requirement không thuộc quyền. |
| Tiền điều kiện | QA A đăng nhập; Requirement thuộc QA B tồn tại. |
| Dữ liệu đầu vào | ID Requirement của QA B; nội dung update hợp lệ. |
| Các bước | 1. Đăng nhập QA A. 2. Gửi request cập nhật Requirement của QA B. 3. Quan sát response và database. |
| Kết quả mong đợi | HTTP 403 `FORBIDDEN_RECORD`; dữ liệu Requirement không thay đổi. |
| Kết quả thực tế | Unit Test PASS. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-REQ-016 — Optimistic lock conflict

| Trường | Nội dung |
|---|---|
| Mã TC | TC-REQ-016 |
| Chức năng / UC | UC05 - Requirement |
| Mục tiêu | Chứng minh hệ thống chặn cập nhật bằng `lock_version` cũ. |
| Tiền điều kiện | Requirement hiện tại có `lock_version` mới hơn giá trị client đang giữ. |
| Dữ liệu đầu vào | `lock_version` cũ; content update hợp lệ. |
| Các bước | 1. Đọc Requirement. 2. Làm record thay đổi ở phiên khác. 3. Gửi update với lock_version cũ. |
| Kết quả mong đợi | HTTP 409 CONFLICT; không ghi đè dữ liệu mới. |
| Kết quả thực tế | Unit Test PASS. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-REQ-017 — BR-08 Requirement thay đổi

| Trường | Nội dung |
|---|---|
| Mã TC | TC-REQ-017 |
| Chức năng / UC | UC05 - Requirement / BR-08 |
| Mục tiêu | Chứng minh Test Case APPROVED phải review lại khi Requirement nguồn thay đổi. |
| Tiền điều kiện | Requirement có ít nhất một Test Case ở trạng thái APPROVED. |
| Dữ liệu đầu vào | Nội dung Requirement mới hợp lệ và `lock_version` hiện tại. |
| Các bước | 1. Mở Requirement. 2. Chỉnh nội dung. 3. Lưu. 4. Đọc lại Test Case liên quan và version/audit. |
| Kết quả mong đợi | Requirement tạo version mới; Test Case liên quan chuyển `NEEDS_FIX`; có audit/version tương ứng. |
| Kết quả thực tế | Unit Test PASS. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-GEN-004 — Submit AI generation job

| Trường | Nội dung |
|---|---|
| Mã TC | TC-GEN-004 |
| Chức năng / UC | UC06 - AI Generation |
| Mục tiêu | Chứng minh generation chạy background job, không chặn HTTP request. |
| Tiền điều kiện | QA đã đăng nhập; Requirement hợp lệ và thuộc quyền QA; Celery/RabbitMQ được cấu hình. |
| Dữ liệu đầu vào | ID Requirement hợp lệ. |
| Các bước | 1. Gửi yêu cầu generation. 2. Quan sát HTTP response. 3. Đọc generation job. |
| Kết quả mong đợi | HTTP 202; job được tạo trạng thái QUEUED; worker xử lý bất đồng bộ. |
| Kết quả thực tế | Unit Test PASS; provider thật chưa xác nhận do API key local HTTP 401. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`; manual provider chưa chạy thành công. |

### TC-GEN-005 — Generation record-level authorization

| Trường | Nội dung |
|---|---|
| Mã TC | TC-GEN-005 |
| Chức năng / UC | UC06 - AI Generation / Authorization |
| Mục tiêu | Chứng minh QA không được generate từ Requirement của QA khác. |
| Tiền điều kiện | QA A đăng nhập; Requirement thuộc QA B. |
| Dữ liệu đầu vào | ID Requirement của QA B. |
| Các bước | 1. Đăng nhập QA A. 2. Gửi yêu cầu generation cho Requirement của QA B. |
| Kết quả mong đợi | HTTP 403; không tạo/enqueue generation job. |
| Kết quả thực tế | Unit Test PASS. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-GEN-006 — Provider/AppError được bảo toàn

| Trường | Nội dung |
|---|---|
| Mã TC | TC-GEN-006 |
| Chức năng / UC | UC06 - AI Generation / Error Handling |
| Mục tiêu | Chứng minh worker giữ đúng mã lỗi nghiệp vụ khi provider lỗi. |
| Tiền điều kiện | Generation job tồn tại; AI provider được mock trả `AI_PROVIDER_ERROR`. |
| Dữ liệu đầu vào | Generation job hợp lệ; provider phát sinh AppError 502. |
| Các bước | 1. Khởi chạy generation task. 2. Mock provider lỗi. 3. Đọc trạng thái job sau xử lý. |
| Kết quả mong đợi | Job FAILED; error code giữ `AI_PROVIDER_ERROR`, không đổi thành lỗi không xác định. |
| Kết quả thực tế | Regression Unit Test PASS. |
| Trạng thái | PASS - Regression Test - 22/08/2026 - commit `06675fe`. |

### TC-REV-001 — Edit Test Case

| Trường | Nội dung |
|---|---|
| Mã TC | TC-REV-001 |
| Chức năng / UC | UC07 - Human-in-the-loop Review |
| Mục tiêu | Chứng minh Test Case mutable được chỉnh sửa và có version/audit. |
| Tiền điều kiện | QA có quyền; Test Case ở DRAFT hoặc NEEDS_FIX. |
| Dữ liệu đầu vào | Summary, Steps, Expected Result hợp lệ; lock_version hiện tại. |
| Các bước | 1. Mở Test Case. 2. Chỉnh nội dung. 3. Bấm Save. 4. Đọc version/audit. |
| Kết quả mong đợi | Nội dung mới được lưu; version tăng; có audit `EDIT_TEST_CASE`. |
| Kết quả thực tế | Unit Test PASS. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-REV-002 — DRAFT → IN_REVIEW

| Trường | Nội dung |
|---|---|
| Mã TC | TC-REV-002 |
| Chức năng / UC | UC07 - Human-in-the-loop Review |
| Mục tiêu | Chứng minh lifecycle cho phép DRAFT submit review. |
| Tiền điều kiện | Test Case DRAFT hợp lệ và thuộc quyền user. |
| Dữ liệu đầu vào | ID Test Case; lock_version hiện tại. |
| Các bước | 1. Mở Test Case DRAFT. 2. Bấm Submit Review. 3. Tải lại record. |
| Kết quả mong đợi | Status chuyển `IN_REVIEW`; có version/audit tương ứng. |
| Kết quả thực tế | Unit Test PASS; manual đã quan sát được trong Tuần 07. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-REV-005 — IN_REVIEW → NEEDS_FIX

| Trường | Nội dung |
|---|---|
| Mã TC | TC-REV-005 |
| Chức năng / UC | UC07 - Human-in-the-loop Review |
| Mục tiêu | Chứng minh reviewer có thể Request Fix khi có review note. |
| Tiền điều kiện | Test Case ở IN_REVIEW. |
| Dữ liệu đầu vào | Review note: `Bổ sung expected result cụ thể`. |
| Các bước | 1. Mở Test Case IN_REVIEW. 2. Nhập review note. 3. Bấm Request Fix. 4. Tải lại record. |
| Kết quả mong đợi | Status chuyển `NEEDS_FIX`; note/version/audit được lưu. |
| Kết quả thực tế | Unit Test PASS; manual đã xác nhận validation note rỗng bị chặn. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-APP-001 — Approve hợp lệ

| Trường | Nội dung |
|---|---|
| Mã TC | TC-APP-001 |
| Chức năng / UC | UC08 - Approve Test Case |
| Mục tiêu | Chứng minh reviewer có quyền approve Test Case đủ BR-02/BR-03. |
| Tiền điều kiện | QA/Manager có quyền; Test Case IN_REVIEW; đủ field bắt buộc và liên kết nguồn. |
| Dữ liệu đầu vào | Test Case IN_REVIEW có summary, steps, expected result, priority, module, requirement. |
| Các bước | 1. Mở Test Case IN_REVIEW. 2. Kiểm tra field bắt buộc. 3. Bấm Approve. 4. Tải lại record. |
| Kết quả mong đợi | Status chuyển `APPROVED`; có version/audit approve. |
| Kết quả thực tế | Unit Test PASS; manual đã approve demo Test Case Tuần 07. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-APP-002 — Không DRAFT → APPROVED trực tiếp

| Trường | Nội dung |
|---|---|
| Mã TC | TC-APP-002 |
| Chức năng / UC | UC08 - Approve Test Case |
| Mục tiêu | Chứng minh BR-01 bắt buộc human-review lifecycle trước approve. |
| Tiền điều kiện | Test Case đang DRAFT. |
| Dữ liệu đầu vào | ID Test Case DRAFT hợp lệ. |
| Các bước | 1. Đăng nhập reviewer. 2. Gửi hành động approve trên Test Case DRAFT. |
| Kết quả mong đợi | HTTP 409; Test Case vẫn DRAFT. |
| Kết quả thực tế | Unit Test PASS. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-APP-004 — Thiếu field bắt buộc

| Trường | Nội dung |
|---|---|
| Mã TC | TC-APP-004 |
| Chức năng / UC | UC08 - Approve Test Case |
| Mục tiêu | Chứng minh BR-02 chặn approve Test Case thiếu dữ liệu bắt buộc. |
| Tiền điều kiện | Test Case IN_REVIEW; user có quyền approve. |
| Dữ liệu đầu vào | Test Case thiếu Summary hoặc Steps hoặc Expected Result. |
| Các bước | 1. Chuẩn bị Test Case IN_REVIEW thiếu field. 2. Gửi approve. |
| Kết quả mong đợi | HTTP 422; Test Case không chuyển APPROVED. |
| Kết quả thực tế | Unit Test PASS. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-DUP-001 — Similarity dưới threshold

| Trường | Nội dung |
|---|---|
| Mã TC | TC-DUP-001 |
| Chức năng / UC | NC-05 - Duplicate Detection |
| Mục tiêu | Kiểm tra boundary ngay dưới threshold 0.85. |
| Tiền điều kiện | Target/candidate có embedding tương thích. |
| Dữ liệu đầu vào | Similarity = `0.8499`. |
| Các bước | 1. Chuẩn bị candidate similarity 0.8499. 2. Chạy duplicate search. |
| Kết quả mong đợi | Candidate không thuộc tập vượt ngưỡng. |
| Kết quả thực tế | Chưa có fixture/integration xác nhận boundary này. |
| Trạng thái | Chưa chạy integration; thiết kế 22/08/2026. |

### TC-DUP-002 — Similarity đúng threshold

| Trường | Nội dung |
|---|---|
| Mã TC | TC-DUP-002 |
| Chức năng / UC | NC-05 - Duplicate Detection |
| Mục tiêu | Kiểm tra boundary đúng threshold 0.85. |
| Tiền điều kiện | Duplicate service và repository được mock/fixture phù hợp. |
| Dữ liệu đầu vào | Similarity = `0.8500`. |
| Các bước | 1. Chuẩn bị candidate similarity 0.8500. 2. Chạy duplicate search. |
| Kết quả mong đợi | Candidate được tính là đạt ngưỡng theo rule hiện tại. |
| Kết quả thực tế | Logic Unit Test PASS. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-DUP-003 — Similarity trên threshold

| Trường | Nội dung |
|---|---|
| Mã TC | TC-DUP-003 |
| Chức năng / UC | NC-05 - Duplicate Detection |
| Mục tiêu | Kiểm tra boundary ngay trên threshold 0.85. |
| Tiền điều kiện | Duplicate service được chuẩn bị dữ liệu candidate. |
| Dữ liệu đầu vào | Similarity = `0.8501`. |
| Các bước | 1. Chuẩn bị candidate similarity 0.8501. 2. Chạy duplicate search. |
| Kết quả mong đợi | Candidate được trả trong danh sách duplicate candidate. |
| Kết quả thực tế | Logic Unit Test PASS. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-MOD-001 — Tạo Module

| Trường | Nội dung |
|---|---|
| Mã TC | TC-MOD-001 |
| Chức năng / UC | UC04 - Module |
| Mục tiêu | Chứng minh Manager tạo Module hợp lệ. |
| Tiền điều kiện | Manager đã đăng nhập. |
| Dữ liệu đầu vào | `name=Booking`, `parent_id=null`. |
| Các bước | 1. Mở Module Management. 2. Chọn Create. 3. Nhập Booking. 4. Submit. |
| Kết quả mong đợi | HTTP 201; module mới xuất hiện trong danh sách. |
| Kết quả thực tế | Unit Test PASS. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-COV-001 — Coverage khi total = 0

| Trường | Nội dung |
|---|---|
| Mã TC | TC-COV-001 |
| Chức năng / UC | UC04 - Coverage |
| Mục tiêu | Chứng minh coverage không chia cho 0. |
| Tiền điều kiện | Module tồn tại và chưa có Requirement. |
| Dữ liệu đầu vào | `total_requirements=0`, `covered_requirements=0`. |
| Các bước | 1. Tạo/chọn module không có Requirement. 2. Xem coverage. |
| Kết quả mong đợi | Coverage = `0%`; không phát sinh exception chia cho 0. |
| Kết quả thực tế | Unit Test PASS. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-EXP-001 — Export CSV

| Trường | Nội dung |
|---|---|
| Mã TC | TC-EXP-001 |
| Chức năng / UC | UC09 - Export |
| Mục tiêu | Chứng minh chỉ Test Case APPROVED được export CSV và có audit. |
| Tiền điều kiện | QA/Manager có quyền; tồn tại ít nhất một APPROVED và một DRAFT. |
| Dữ liệu đầu vào | Format `CSV`. |
| Các bước | 1. Mở danh sách Test Case. 2. Chọn Export CSV. 3. Mở file tải về. 4. Kiểm tra audit. |
| Kết quả mong đợi | File CSV chỉ chứa các Test Case đang APPROVED tại thời điểm export; sau export thành công các record đó chuyển EXPORTED; có audit export. |
| Kết quả thực tế | Unit Test PASS; manual đã tải được CSV. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-EXP-002 — Export XLSX

| Trường | Nội dung |
|---|---|
| Mã TC | TC-EXP-002 |
| Chức năng / UC | UC09 - Export |
| Mục tiêu | Chứng minh export XLSX tạo file hợp lệ. |
| Tiền điều kiện | QA/Manager có quyền; có Test Case APPROVED. |
| Dữ liệu đầu vào | Format `XLSX`. |
| Các bước | 1. Chọn Export XLSX. 2. Tải file. 3. Mở file bằng Excel. |
| Kết quả mong đợi | File XLSX mở được và chỉ chứa các Test Case đang APPROVED tại thời điểm export; sau export thành công các record đó chuyển EXPORTED. |
| Kết quả thực tế | Unit Test PASS; manual XLSX đã mở đúng. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-VER-002 — Compare version

| Trường | Nội dung |
|---|---|
| Mã TC | TC-VER-002 |
| Chức năng / UC | NC-08 - Version History |
| Mục tiêu | Chứng minh compare trả đúng field thay đổi giữa hai version. |
| Tiền điều kiện | Test Case có ít nhất version 1 và version 2. |
| Dữ liệu đầu vào | `from_version=1`, `to_version=2`. |
| Các bước | 1. Mở Version History. 2. Chọn v1 và v2. 3. Bấm Compare. |
| Kết quả mong đợi | Hiển thị các field thay đổi với giá trị from/to. |
| Kết quả thực tế | Unit Test PASS; manual compare đã xác nhận. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-VER-004 — Restore version

| Trường | Nội dung |
|---|---|
| Mã TC | TC-VER-004 |
| Chức năng / UC | NC-08 - Version Restore |
| Mục tiêu | Chứng minh restore không tự APPROVED mà chuyển lại NEEDS_FIX. |
| Tiền điều kiện | Test Case có version cũ và user có quyền restore. |
| Dữ liệu đầu vào | Restore version `4`. |
| Các bước | 1. Mở Version History. 2. Chọn version 4. 3. Bấm Restore. 4. Tải lại record. |
| Kết quả mong đợi | Nội dung trở về version 4; status `NEEDS_FIX`; lock_version tăng; có audit/version mới. |
| Kết quả thực tế | Unit Test PASS; manual restore version 4 đã xác nhận. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-PROMPT-001 — Tạo Prompt Config

| Trường | Nội dung |
|---|---|
| Mã TC | TC-PROMPT-001 |
| Chức năng / UC | UC03 - Prompt Configuration |
| Mục tiêu | Chứng minh Admin tạo version Prompt Config hợp lệ. |
| Tiền điều kiện | Admin đã đăng nhập. |
| Dữ liệu đầu vào | Template chứa `{requirement_text}` và `{acceptance_criteria}`; model_name không rỗng. |
| Các bước | 1. Mở Prompt Config. 2. Nhập template hợp lệ. 3. Submit. 4. Đọc history. |
| Kết quả mong đợi | Tạo config/version mới active; version cũ vẫn còn history. |
| Kết quả thực tế | Unit Test PASS. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-USER-013 — QA không được Create User

| Trường | Nội dung |
|---|---|
| Mã TC | TC-USER-013 |
| Chức năng / UC | UC02 - User Management |
| Mục tiêu | Chứng minh RBAC chặn QA tạo user. |
| Tiền điều kiện | QA đã đăng nhập. |
| Dữ liệu đầu vào | Email `qa2@example.com`, role `QA`, dữ liệu user hợp lệ. |
| Các bước | 1. Đăng nhập QA. 2. Gửi thao tác Create User. |
| Kết quả mong đợi | HTTP 403 `FORBIDDEN_ROLE`; user không được tạo. |
| Kết quả thực tế | Unit Test PASS. |
| Trạng thái | PASS - Unit Test - 22/08/2026 - commit `06675fe`. |

### TC-FE-001 — Loading state

| Trường | Nội dung |
|---|---|
| Mã TC | TC-FE-001 |
| Chức năng / UC | Frontend - Test Case List |
| Mục tiêu | Chứng minh màn hình có loading state theo FE-03. |
| Tiền điều kiện | Frontend chạy; API request chưa hoàn tất. |
| Dữ liệu đầu vào | API list Test Case bị giữ ở trạng thái pending. |
| Các bước | 1. Mở Test Case List. 2. Quan sát trong lúc request pending. |
| Kết quả mong đợi | Hiển thị loading state; không trắng màn hình. |
| Kết quả thực tế | Chưa chạy manual chính thức. |
| Trạng thái | Chưa chạy manual; thiết kế 22/08/2026. |

### TC-FE-002 — Empty state

| Trường | Nội dung |
|---|---|
| Mã TC | TC-FE-002 |
| Chức năng / UC | Frontend - Test Case List |
| Mục tiêu | Chứng minh màn hình có empty state theo FE-03. |
| Tiền điều kiện | Frontend chạy; API trả danh sách rỗng. |
| Dữ liệu đầu vào | `data=[]`, `total=0`. |
| Các bước | 1. Chuẩn bị account/module không có Test Case. 2. Mở Test Case List. |
| Kết quả mong đợi | Hiển thị thông báo empty state; không crash/không trắng màn hình. |
| Kết quả thực tế | Chưa chạy manual chính thức. |
| Trạng thái | Chưa chạy manual; thiết kế 22/08/2026. |

### TC-FE-003 — Error state

| Trường | Nội dung |
|---|---|
| Mã TC | TC-FE-003 |
| Chức năng / UC | Frontend - Requirement |
| Mục tiêu | Chứng minh màn hình xử lý API 4xx/5xx theo FE-03. |
| Tiền điều kiện | Frontend chạy; API trả lỗi. |
| Dữ liệu đầu vào | Response HTTP 500 hoặc lỗi request tương đương. |
| Các bước | 1. Mô phỏng API lỗi. 2. Mở màn hình Requirement. |
| Kết quả mong đợi | Hiển thị error state/thông báo phù hợp; ứng dụng không crash. |
| Kết quả thực tế | Chưa chạy manual chính thức. |
| Trạng thái | Chưa chạy manual; thiết kế 22/08/2026. |


## 3. UC01 - Đăng nhập

| ID | Kỹ thuật | Tình huống | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|
| TC-AUTH-011 | EP | Email/password demo hợp lệ | HTTP 200, có Bearer token và user role | Chưa chạy manual |
| TC-AUTH-012 | EP | Password sai | HTTP 401, không lưu token | Chưa chạy manual |
| TC-AUTH-013 | Negative | Email sai định dạng | HTTP 422 | Chưa chạy manual |

## 4. UC02 - Quản lý User

| ID | Kỹ thuật | Tình huống | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|
| TC-USER-012 | Decision Table | Admin tạo QA hợp lệ | HTTP 201, trả user mới | Unit Test/Manual cần xác nhận |
| TC-USER-013 | Decision Table | QA gọi Create User | HTTP 403 FORBIDDEN_ROLE | PASS - Unit Test |
| TC-USER-014 | EP | Admin tạo email trùng | HTTP 409 USER_ALREADY_EXISTS | PASS - Unit Test |
| TC-USER-015 | EP | Admin list user page 1 | HTTP 200, có data/total/page/pageSize | Cần chạy lại Unit Test gói cuối |
| TC-USER-016 | Decision Table | Admin đổi role hoặc is_active | User được cập nhật và ghi audit an toàn | Cần chạy lại Unit Test gói cuối |
| TC-USER-017 | Decision Table | QA gọi PATCH user | HTTP 403 FORBIDDEN_ROLE | Cần chạy lại Unit Test gói cuối |
| TC-AUTH-014 | State/Authorization | User is_active=false đăng nhập | HTTP 403 ACCOUNT_DISABLED | Cần chạy lại Unit Test gói cuối |

## 5. UC03 / NC-09 - Prompt / Model Configuration

| ID | Kỹ thuật | Tình huống | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|
| TC-PROMPT-001 | EP | Admin tạo config đủ placeholder | Tạo version mới, active=true, version cũ giữ history | PASS - Unit Test |
| TC-PROMPT-002 | Negative | Template thiếu `{requirement_text}` | HTTP 422 | PASS - Unit Test |
| TC-PROMPT-003 | Decision Table | QA/Manager truy cập prompt config | HTTP 403 | PASS - Unit Test |

## 6. UC04 / NC-06 / NC-12 - Module, Tag, Coverage

| ID | Kỹ thuật | Tình huống | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|
| TC-MOD-001 | EP | Manager tạo module hợp lệ | HTTP 201, module xuất hiện trong list | PASS - Unit Test |
| TC-MOD-002 | Negative | Parent không tồn tại | HTTP 404 MODULE_NOT_FOUND | PASS - Unit Test |
| TC-MOD-003 | State/Graph | Update parent tạo vòng lặp | HTTP 422, không cập nhật | PASS - Unit Test |
| TC-MOD-004 | Decision Table | QA tạo/sửa module | HTTP 403 | PASS - Unit Test |
| TC-MOD-005 | EP | Manager gắn tag trùng/case khác nhau | Tag được normalize, loại duplicate | PASS - Unit Test |
| TC-COV-001 | BVA | Module 0 requirement | Coverage = 0%, không chia cho 0 | PASS - Unit Test |
| TC-COV-002 | BVA | Covered = total | Coverage = 100% | Chưa chạy manual |
| TC-COV-003 | Decision Table | Admin xem coverage | HTTP 403 theo SRS hiện tại | PASS - Unit Test |

## 7. UC05 / NC-01 / BR-08 - Requirement

| ID | Kỹ thuật | Tình huống | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|
| TC-REQ-012 | BVA | Content 19 ký tự | HTTP 422 | Chưa chạy manual |
| TC-REQ-013 | BVA | Content 20 ký tự | Được schema chấp nhận nếu các điều kiện khác hợp lệ | Chưa chạy manual |
| TC-REQ-014 | BVA | Content 21 ký tự | Được schema chấp nhận | Chưa chạy manual |
| TC-REQ-015 | Authorization | QA sửa Requirement người khác | HTTP 403 FORBIDDEN_RECORD | PASS - Unit Test |
| TC-REQ-016 | Optimistic Lock | lock_version cũ | HTTP 409 CONFLICT | PASS - Unit Test |
| TC-REQ-017 | BR-08 | Sửa Requirement có Test Case APPROVED | Test Case liên quan chuyển NEEDS_FIX và tạo version/audit | PASS - Unit Test |

## 8. UC06 - AI Generation / Background Job

| ID | Kỹ thuật | Tình huống | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|
| TC-GEN-004 | Happy Path | QA submit Requirement hợp lệ | HTTP 202, job QUEUED; worker xử lý async | PASS - Unit Test; provider thật phụ thuộc key |
| TC-GEN-005 | Authorization | QA submit Requirement người khác | 403, không enqueue | PASS - Unit Test |
| TC-GEN-006 | Error Handling | Provider/AppError | Job FAILED và giữ error code nghiệp vụ | PASS - Regression Test |

## 9. UC07 - Human-in-the-loop Review

Kỹ thuật chính: **State Transition**.

| ID | Trạng thái đầu | Hành động | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|
| TC-REV-001 | DRAFT | Edit nội dung hợp lệ | Lưu version mới, audit EDIT_TEST_CASE | PASS - Unit Test |
| TC-REV-002 | DRAFT | Submit Review | IN_REVIEW | PASS - Unit Test |
| TC-REV-003 | NEEDS_FIX | Submit Review | IN_REVIEW | PASS - Unit Test |
| TC-REV-004 | APPROVED | Edit trực tiếp | Bị chặn theo rule hiện tại | PASS - Unit Test |
| TC-REV-005 | IN_REVIEW | Request Fix có note | NEEDS_FIX | PASS - Unit Test |
| TC-REV-006 | DRAFT/IN_REVIEW | Reject | REJECTED + audit/version | PASS - Unit Test |
| TC-REV-007 | Bất kỳ mutable state | lock_version cũ | HTTP 409 | PASS - Unit Test |

## 10. UC08 - Approve Test Case

Kỹ thuật chính: **Decision Table (role × status × dữ liệu bắt buộc)**.

| ID | Role | Status | Dữ liệu | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|---|
| TC-APP-001 | QA/Manager có quyền | IN_REVIEW | Đủ BR-02/BR-03 | APPROVED | PASS - Unit Test |
| TC-APP-002 | QA/Manager | DRAFT | Đủ | HTTP 409, không DRAFT → APPROVED trực tiếp | PASS - Unit Test |
| TC-APP-003 | Admin | IN_REVIEW | Đủ | HTTP 403 theo reviewer role hiện tại | PASS - Unit Test |
| TC-APP-004 | QA/Manager | IN_REVIEW | Thiếu field bắt buộc | HTTP 422 | PASS - Unit Test |

## 11. NC-05 - Duplicate Detection / pgvector

Kỹ thuật chính: **Boundary Value Analysis quanh threshold 0.85**.

| ID | Similarity | Kết quả mong đợi | Trạng thái |
|---|---:|---|---|
| TC-DUP-001 | 0.8499 | Không thuộc candidate vượt ngưỡng | Thiết kế - cần fixture/integration |
| TC-DUP-002 | 0.8500 | Thuộc candidate theo điều kiện ngưỡng hiện tại | PASS logic Unit Test |
| TC-DUP-003 | 0.8501 | Thuộc candidate | PASS logic Unit Test |
| TC-DUP-004 | N/A | Target chưa có embedding | Tạo embedding qua adapter rồi lưu | PASS - Unit Test |
| TC-DUP-005 | N/A | Candidate REJECTED | Không trả candidate rejected | PASS - Unit Test |

## 12. UC09 / NC-07 - Export CSV/XLSX

Kỹ thuật chính: **Decision Table (role × status × format)**.

| ID | Role | Dữ liệu | Format | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|---|
| TC-EXP-001 | QA/Manager | Có APPROVED | CSV | Tải CSV từ APPROVED; export thành công chuyển record sang EXPORTED; có audit | PASS - Unit Test |
| TC-EXP-002 | QA/Manager | Có APPROVED | XLSX | Tải XLSX bằng openpyxl; export thành công chuyển record sang EXPORTED | PASS - Unit Test |
| TC-EXP-003 | QA/Manager | Chỉ DRAFT/REJECTED | CSV | Không export record chưa approved | PASS - Unit Test |
| TC-EXP-004 | Admin | Có APPROVED | CSV | HTTP 403 theo SRS hiện tại | PASS - Unit Test |
| TC-EXP-005 | QA | Record chứa `=SUM(...)` | XLSX | Neutralize spreadsheet formula injection | PASS - Unit Test |

## 13. NC-08 - Version History / Compare / Restore

| ID | Kỹ thuật | Tình huống | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|
| TC-VER-001 | EP | List version của Test Case có quyền | Trả list version theo pagination | PASS - Unit Test |
| TC-VER-002 | EP | Compare v1 với v2 | Trả field thay đổi from/to | PASS - Unit Test |
| TC-VER-003 | Negative | Compare version không tồn tại | HTTP 404 | PASS - Unit Test |
| TC-VER-004 | State Transition | Restore version cũ | Nội dung được restore, status NEEDS_FIX, lock_version tăng | PASS - Unit Test |
| TC-VER-005 | Authorization | QA restore Test Case người khác | HTTP 403 | PASS - Unit Test |

## 14. FE-03 - Loading / Empty / Error

| ID | Màn hình | Tình huống | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|
| TC-FE-001 | Test Case List | API đang tải | Hiển thị loading state | Chưa chạy manual |
| TC-FE-002 | Test Case List | List rỗng | Hiển thị empty state, không trắng màn hình | Chưa chạy manual |
| TC-FE-003 | Requirement | API 4xx/5xx | Hiển thị error state, không crash | Chưa chạy manual |
| TC-FE-004 | Admin | User không phải Admin | Không hiển thị System Config tab | Chưa chạy manual |
| TC-FE-005 | Module | Role không đủ quyền | Button/action bị ẩn hoặc disable và backend vẫn chặn | Chưa chạy manual |

## 15. TC-12 - Authorization Matrix tối thiểu

| ID | Role | Endpoint không thuộc quyền | Record-level case | Kết quả mong đợi |
|---|---|---|---|---|
| TC-AUTHZ-001 | QA | POST `/api/v1/users` | Test Case/Requirement của QA khác | HTTP 403 |
| TC-AUTHZ-002 | Manager | POST `/api/v1/prompt-configs` | Action không đúng scope SRS | HTTP 403 |
| TC-AUTHZ-003 | Admin | GET `/api/v1/modules/{id}/coverage` | Review/Export không thuộc reviewer role | HTTP 403 |

## 16. Ghi chú

- Unit Test AI/embedding mock provider theo TE-18, không dùng network/chi phí thật.
- Test case manual chưa chạy không được đổi sang PASS trước khi có bằng chứng.
- Lượt chạy toàn bộ test case lần thứ nhất và integration test chính bắt đầu ở Tuần 08 theo lộ trình.

## 17. TC-11 - Negative Test cho form mới Tuần 07

### Module Form

| ID | Dữ liệu âm | Kết quả mong đợi |
|---|---|---|
| TC-MOD-101 | Bỏ trống name | Frontend báo lỗi cạnh input / backend 422 |
| TC-MOD-102 | Name 1 ký tự | Frontend báo tối thiểu 2 ký tự / backend 422 |
| TC-MOD-103 | Name > 150 ký tự | Backend 422 |
| TC-MOD-104 | parent_id = 0 | Backend 422 |
| TC-MOD-105 | parent_id không tồn tại | Backend 404 |
| TC-MOD-106 | Tên trùng cùng cấp | Backend 409 |

### Prompt Configuration Form

| ID | Dữ liệu âm | Kết quả mong đợi |
|---|---|---|
| TC-PROMPT-101 | Name < 2 ký tự | Frontend báo lỗi / backend 422 |
| TC-PROMPT-102 | System Prompt < 20 ký tự | Frontend báo lỗi / backend 422 |
| TC-PROMPT-103 | Thiếu `{requirement_text}` | Frontend báo lỗi / backend 422 |
| TC-PROMPT-104 | Thiếu `{acceptance_criteria}` | Frontend báo lỗi / backend 422 |
| TC-PROMPT-105 | model_name rỗng | Backend 422 |
| TC-PROMPT-106 | max_output_tokens < 256 hoặc > 16000 | Backend 422 |

### Test Case Edit Form

| ID | Dữ liệu âm | Kết quả mong đợi |
|---|---|---|
| TC-REV-101 | Summary < 3 ký tự | Frontend báo lỗi / backend 422 |
| TC-REV-102 | Steps rỗng | Frontend báo lỗi / backend 422 |
| TC-REV-103 | Expected Result < 3 ký tự | Frontend báo lỗi / backend 422 |
| TC-REV-104 | Priority ngoài enum | Backend 422 |
| TC-REV-105 | Review Note > 1000 ký tự | Backend 422 |
| TC-REV-106 | lock_version cũ | Backend 409, yêu cầu tải lại record |

### Tags Form

| ID | Dữ liệu âm | Kết quả mong đợi |
|---|---|---|
| TC-TAG-101 | > 10 tags | Backend 422 |
| TC-TAG-102 | Tag > 50 ký tự | Backend 422 |
| TC-TAG-103 | Tag rỗng xen kẽ | Normalize và loại tag rỗng |
| TC-TAG-104 | Tag trùng khác hoa/thường | Normalize và loại duplicate |
| TC-TAG-105 | Test Case không thuộc module | Backend 403 |
| TC-TAG-106 | QA/Admin gọi endpoint Manager-only | Backend 403 |
