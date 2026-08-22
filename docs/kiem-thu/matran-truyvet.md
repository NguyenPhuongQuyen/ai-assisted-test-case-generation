# Ma trận truy vết yêu cầu -> test case

> Cập nhật Tuần 07. Cột kết quả phản ánh bằng chứng hiện có; manual case chưa chạy giữ nguyên `Chưa chạy manual`.

| Mã yêu cầu / rule | Nội dung | Test case phủ | Kết quả lượt gần nhất |
|---|---|---|---|
| NC-01 / YC-01 / UC05 | Nhập và cập nhật Requirement | TC-REQ-012..017 | Unit Test phần service PASS; manual BVA chưa chạy |
| NC-02 / YC-02 / UC06 | Sinh Test Case tự động qua background job | TC-GEN-004..006 | PASS - Unit/Regression Test |
| NC-03 / YC-02 | Sinh cấu trúc Test Case và gợi ý kỹ thuật/biên | TC-GEN-004, TC-GEN-006 | PASS - schema/unit; provider thật phụ thuộc key |
| NC-04 / YC-03 / UC07 | Review/edit Human-in-the-loop | TC-REV-001..007 | PASS - Unit Test |
| NC-05 / YC-03 | Duplicate detection/semantic similarity | TC-DUP-001..005 | Unit logic PASS; boundary integration một phần chưa chạy |
| NC-06 / YC-04 / UC04 | Module, tags, tổ chức Test Case | TC-MOD-001..005 | PASS - Unit Test |
| NC-07 / YC-04 / UC09 | Export CSV/XLSX | TC-EXP-001..005 | PASS - Unit Test |
| NC-08 / YC-05 | Version history, compare, restore | TC-VER-001..005 | PASS - Unit Test |
| NC-09 / YC-05 / UC03 | Prompt/model/schema version config | TC-PROMPT-001..003 | PASS - Unit Test |
| NC-10 / YC-05 / UC02 | Authentication/RBAC/User management | TC-AUTH-011..014, TC-USER-012..017, TC-12 matrix | Unit permission đã có bằng chứng trước gói cuối; NC-10 final cần chạy lại full suite |
| NC-11 / YC-05 | Audit generate/edit/review/approve/export/config/module/requirement/restore | TC-GEN-004, TC-REV-001, TC-APP-001, TC-EXP-001, TC-PROMPT-001, TC-MOD-001, TC-REQ-017, TC-VER-004 | PASS qua Unit Test liên quan |
| NC-12 / YC-04 | Coverage/statistics theo module | TC-COV-001..003 | Unit Test PASS; 100% manual case chưa chạy |
| BR-01 | AI output phải human review trước sử dụng | TC-REV-002, TC-APP-002, TC-EXP-003 | PASS - Unit Test |
| BR-02 | Test Case có summary, steps, expected result, priority | TC-APP-001, TC-APP-004, TC-GEN-006 | PASS - Unit Test |
| BR-03 | Test Case gắn module và requirement nguồn | TC-APP-001, TC-GEN-004 | PASS - Unit Test |
| BR-04 | Structured output phải validate schema | TC-GEN-006 | PASS - Unit Test |
| BR-05 | Chỉ user có quyền được approve/export | TC-APP-003, TC-EXP-004, TC-12 matrix | PASS - Unit Test |
| BR-06 | Generate/edit/approve/export có version/audit | TC-GEN-004, TC-REV-001, TC-APP-001, TC-EXP-001 | PASS - Unit Test |
| BR-07 | Requirement/Test Case được phân quyền | TC-REQ-015, TC-VER-005, TC-GEN-005 | PASS - Unit Test |
| BR-08 | Requirement thay đổi → Test Case cần review lại | TC-REQ-017 | PASS - Unit Test |
| BR-09 | Chính sách chất lượng/boundary/high priority | TC-DUP-001..003, TC-REQ-012..014, TC-APP-001 | Thiết kế TC-07 hoàn tất; một số manual chưa chạy |
| FE-03 | Loading/empty/error cho luồng chính | TC-FE-001..005 | Chưa chạy manual frontend |
