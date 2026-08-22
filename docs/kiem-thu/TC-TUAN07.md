# Test Case Tuần 07

## 1. Phạm vi

Tuần 07 tập trung thiết kế test case phủ các use case chính, Human-in-the-loop, vector duplicate detection, Module/Coverage, Export, Prompt Config và Version Restore. Manual case chưa chạy giữ trạng thái `Chưa chạy`; không ghi PASS nếu chưa có bằng chứng.

Bằng chứng tự động hiện có trước khi bổ sung frontend/docs:

- Backend Unit Test: `69 passed`.
- Tested commit: `d3e7f71`.
- Ruff check / format: PASS.
- Alembic: `0008_nc08_version_restore (head)`.

## 2. TC-07 - Kỹ thuật kiểm thử sử dụng

| Kỹ thuật | Áp dụng |
|---|---|
| State Transition | Vòng đời Test Case: DRAFT → IN_REVIEW → APPROVED / NEEDS_FIX / REJECTED |
| Decision Table | Quyền theo role × trạng thái × hành động approve/export/module/prompt |
| Boundary Value Analysis | Requirement min 20 ký tự; similarity threshold 0.85; pagination/pageSize; tags tối đa 10 |
| Equivalence Partitioning | Input hợp lệ/không hợp lệ cho Requirement, Module, Prompt Config, User |

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
| TC-EXP-001 | QA/Manager | Có APPROVED | CSV | Tải CSV, chỉ gồm APPROVED, audit export | PASS - Unit Test |
| TC-EXP-002 | QA/Manager | Có APPROVED | XLSX | Tải XLSX bằng openpyxl | PASS - Unit Test |
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

| Role | Endpoint không thuộc quyền | Record-level case | Kết quả mong đợi |
|---|---|---|---|
| QA | POST `/api/v1/users` | Test Case/Requirement của QA khác | 403 |
| Manager | POST `/api/v1/prompt-configs` | Action không đúng scope SRS | 403 |
| Admin | GET `/api/v1/modules/{id}/coverage` | Review/Export không thuộc reviewer role | 403 |

## 16. Ghi chú

- Unit Test AI/embedding mock provider theo TE-18, không dùng network/chi phí thật.
- Test case manual chưa chạy không được đổi sang PASS trước khi có bằng chứng.
- Lượt chạy toàn bộ test case lần thứ nhất và integration test chính bắt đầu ở Tuần 08 theo lộ trình.

## 17. TC-11 - Negative Test cho form mới Tuần 07

### Module Form

| ID | Dữ liệu âm | Kết quả mong đợi |
|---|---|---|
| TC-MOD-N01 | Bỏ trống name | Frontend báo lỗi cạnh input / backend 422 |
| TC-MOD-N02 | Name 1 ký tự | Frontend báo tối thiểu 2 ký tự / backend 422 |
| TC-MOD-N03 | Name > 150 ký tự | Backend 422 |
| TC-MOD-N04 | parent_id = 0 | Backend 422 |
| TC-MOD-N05 | parent_id không tồn tại | Backend 404 |
| TC-MOD-N06 | Tên trùng cùng cấp | Backend 409 |

### Prompt Configuration Form

| ID | Dữ liệu âm | Kết quả mong đợi |
|---|---|---|
| TC-PROMPT-N01 | Name < 2 ký tự | Frontend báo lỗi / backend 422 |
| TC-PROMPT-N02 | System Prompt < 20 ký tự | Frontend báo lỗi / backend 422 |
| TC-PROMPT-N03 | Thiếu `{requirement_text}` | Frontend báo lỗi / backend 422 |
| TC-PROMPT-N04 | Thiếu `{acceptance_criteria}` | Frontend báo lỗi / backend 422 |
| TC-PROMPT-N05 | model_name rỗng | Backend 422 |
| TC-PROMPT-N06 | max_output_tokens < 256 hoặc > 16000 | Backend 422 |

### Test Case Edit Form

| ID | Dữ liệu âm | Kết quả mong đợi |
|---|---|---|
| TC-REV-N01 | Summary < 3 ký tự | Frontend báo lỗi / backend 422 |
| TC-REV-N02 | Steps rỗng | Frontend báo lỗi / backend 422 |
| TC-REV-N03 | Expected Result < 3 ký tự | Frontend báo lỗi / backend 422 |
| TC-REV-N04 | Priority ngoài enum | Backend 422 |
| TC-REV-N05 | Review Note > 1000 ký tự | Backend 422 |
| TC-REV-N06 | lock_version cũ | Backend 409, yêu cầu tải lại record |

### Tags Form

| ID | Dữ liệu âm | Kết quả mong đợi |
|---|---|---|
| TC-TAG-N01 | > 10 tags | Backend 422 |
| TC-TAG-N02 | Tag > 50 ký tự | Backend 422 |
| TC-TAG-N03 | Tag rỗng xen kẽ | Normalize và loại tag rỗng |
| TC-TAG-N04 | Tag trùng khác hoa/thường | Normalize và loại duplicate |
| TC-TAG-N05 | Test Case không thuộc module | Backend 403 |
| TC-TAG-N06 | QA/Admin gọi endpoint Manager-only | Backend 403 |
