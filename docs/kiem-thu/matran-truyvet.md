# Ma trận truy vết yêu cầu -> test case

> Cập nhật Tuần 07.
>
> Ma trận chính bên dưới truy vết từng yêu cầu/rule trong SRS tới các mã test case.
> Không ghi PASS cho manual test chưa chạy. Lượt integration/manual đầy đủ bắt đầu ở Tuần 08.

## 1. Ma trận TC-08 - Yêu cầu / Business Rule -> Test Case

| Mã yêu cầu / rule | Nội dung | Test case phủ | Kết quả lượt gần nhất |
|---|---|---|---|
| YC-01 | Nhập và cập nhật Requirement | TC-REQ-012, TC-REQ-013, TC-REQ-014, TC-REQ-015, TC-REQ-016, TC-REQ-017 | Unit Test phần service PASS; BVA manual 19/20/21 chưa chạy |
| YC-02 | Sinh Test Case tự động và structured output | TC-GEN-004, TC-GEN-005, TC-GEN-006, TC-GEN-007 | PASS - Unit/Regression Test; provider thật chưa xác nhận do API key local HTTP 401 |
| YC-03 | Human-in-the-loop review/edit và duplicate detection | TC-REV-001, TC-REV-002, TC-REV-003, TC-REV-004, TC-REV-005, TC-REV-006, TC-REV-007, TC-DUP-001, TC-DUP-002, TC-DUP-003, TC-DUP-004, TC-DUP-005 | Review Unit Test PASS; duplicate logic Unit Test PASS; một số boundary/integration chưa chạy |
| YC-04 | Module, tag, coverage và export | TC-MOD-001, TC-MOD-002, TC-MOD-003, TC-MOD-004, TC-MOD-005, TC-COV-001, TC-COV-002, TC-COV-003, TC-EXP-001, TC-EXP-002, TC-EXP-003, TC-EXP-004, TC-EXP-005 | Unit Test PASS; một số manual frontend/coverage chưa chạy |
| YC-05 | Version, prompt config, authentication/RBAC, user management và audit | TC-VER-001, TC-VER-002, TC-VER-003, TC-VER-004, TC-VER-005, TC-PROMPT-001, TC-PROMPT-002, TC-PROMPT-003, TC-AUTH-011, TC-AUTH-012, TC-AUTH-013, TC-AUTH-014, TC-USER-012, TC-USER-013, TC-USER-014, TC-USER-015, TC-USER-016, TC-USER-017, TC-AUTHZ-001, TC-AUTHZ-002, TC-AUTHZ-003 | Unit Test suite PASS; manual Admin/User flow chưa chạy đầy đủ |
| BR-01 | AI output phải human review trước sử dụng | TC-REV-002, TC-APP-002, TC-EXP-003 | PASS - Unit Test |
| BR-02 | Test Case có summary, steps, expected result, priority | TC-APP-001, TC-APP-004, TC-GEN-006 | PASS - Unit Test |
| BR-03 | Test Case gắn module và requirement nguồn | TC-APP-001, TC-GEN-004 | PASS - Unit Test |
| BR-04 | Structured output phải validate schema | TC-GEN-007 | PASS - Unit Test |
| BR-05 | Chỉ user có quyền được approve/export | TC-APP-003, TC-EXP-004, TC-AUTHZ-001, TC-AUTHZ-002, TC-AUTHZ-003 | PASS - Unit Test cho các rule đã tự động kiểm; authorization matrix đã thiết kế |
| BR-06 | Generate/edit/approve được lưu version và audit | TC-GEN-004, TC-REV-001, TC-APP-001 | PASS - Unit Test |
| BR-07 | Requirement/Test Case được phân quyền | TC-REQ-015, TC-VER-005, TC-GEN-005, TC-AUTHZ-001 | PASS - Unit Test |
| BR-08 | Requirement thay đổi -> Test Case cần review lại | TC-REQ-017 | PASS - Unit Test |
| BR-09 | Chính sách chất lượng/boundary/high priority | TC-DUP-001, TC-DUP-002, TC-DUP-003, TC-REQ-012, TC-REQ-013, TC-REQ-014, TC-APP-001 | TC-07 đã thiết kế; một số boundary manual/integration chưa chạy |

## 2. Mapping phạm vi chức năng NC / Use Case

> Bảng này bổ sung để liên kết phạm vi đề tài với các test case; bảng TC-08 chính là bảng YC/BR phía trên.

| Mã phạm vi | Use Case / chức năng | Test case chính |
|---|---|---|
| NC-01 | UC05 - Requirement | TC-REQ-012 đến TC-REQ-017 |
| NC-02 | UC06 - AI background generation | TC-GEN-004 đến TC-GEN-006 |
| NC-03 | Structured Test Case generation | TC-GEN-004, TC-GEN-006, TC-GEN-007 |
| NC-04 | UC07 - Human-in-the-loop | TC-REV-001 đến TC-REV-007, TC-APP-001 đến TC-APP-004 |
| NC-05 | Duplicate detection / pgvector | TC-DUP-001 đến TC-DUP-005 |
| NC-06 | UC04 - Module và Tag | TC-MOD-001 đến TC-MOD-005 |
| NC-07 | UC09 - Export CSV/XLSX | TC-EXP-001 đến TC-EXP-005 |
| NC-08 | Version History / Compare / Restore | TC-VER-001 đến TC-VER-005 |
| NC-09 | UC03 - Prompt / Model Configuration | TC-PROMPT-001 đến TC-PROMPT-003 |
| NC-10 | UC01/UC02 - Authentication, RBAC, User Management | TC-AUTH-011 đến TC-AUTH-014, TC-USER-012 đến TC-USER-017, TC-AUTHZ-001 đến TC-AUTHZ-003 |
| NC-11 | Audit | TC-GEN-004, TC-REV-001, TC-APP-001, TC-EXP-001, TC-PROMPT-001, TC-MOD-001, TC-REQ-017, TC-VER-004 |
| NC-12 | Coverage / statistics | TC-COV-001 đến TC-COV-003 |

## 3. Frontend evidence

| Rule | Nội dung | Test case | Kết quả gần nhất |
|---|---|---|---|
| FE-03 | Loading / empty / error cho luồng chính | TC-FE-001, TC-FE-002, TC-FE-003, TC-FE-004, TC-FE-005 | Chưa chạy manual frontend |

## 4. Ghi chú Tuần 07

- Backend Unit Test: 74/74 PASS trên source commit `aafea6e` ngày 23/08/2026.
- Ruff check / format: PASS.
- Alembic: `0010_module_name_unique (head)`.
- GitHub Actions backend-quality: chưa xác nhận trên commit cuối `aafea6e`.
- GitHub Actions frontend-quality: chưa xác nhận trên commit cuối `aafea6e`.
- AI/embedding unit test mock provider theo TE-18, không gọi network/chi phí thật.
- Manual OpenAI happy-path chưa xác nhận do API key local trả HTTP 401.
- Lượt integration test và lượt chạy toàn bộ test case đầu tiên thực hiện ở Tuần 08.
