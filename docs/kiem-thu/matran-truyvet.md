# Ma trận truy vết yêu cầu -> test case

| Mã yêu cầu / rule | Nội dung | Test case phủ | Kết quả lượt gần nhất |
|---|---|---|---|
| NC-01 / YC-01 | Nhập đặc tả yêu cầu | TC-REQ-001 | Chưa chạy manual |
| NC-02 / YC-02 / AP-08 | Sinh test case tự động qua background job | TC-JOB-001, TC-JOB-002, TC-JOB-003, TC-JOB-004, TC-GEN-003 | PASS - Unit Test (15/08/2026, commit `5e9d478`, CI xanh) |
| BR-01 | AI output không được dùng trực tiếp; phần Tuần 05 bảo đảm sinh ở Draft | TC-GEN-001 | PASS - Unit Test (15/08/2026, commit `5e9d478`) |
| BR-02 | Đủ mô tả, bước, kết quả mong đợi, mức ưu tiên | TC-GEN-001, TC-GEN-003 | PASS - Unit Test (15/08/2026, commit `5e9d478`) |
| BR-03 | Test case gắn module và requirement nguồn | TC-GEN-001 | PASS - Unit Test (15/08/2026, commit `5e9d478`) |
| BR-04 | Đầu ra phải đúng schema | TC-GEN-003 | PASS - Unit Test (15/08/2026, commit `5e9d478`) |
| BR-06 / NC-11 | Ghi audit cho lần generate | TC-GEN-001 | PASS - Unit Test (15/08/2026, commit `5e9d478`) |
| BR-07 | Bảo mật và phân quyền dữ liệu | TC-GEN-002 | PASS - Unit Test (15/08/2026, commit `5e9d478`) |
| SE-05 / UC02 | Chỉ Admin quản lý tài khoản | TC-AUTH-002 | PASS - Unit Test (15/08/2026, commit `5e9d478`) |
| SE-11 | Login phải có rate limit/khóa tạm | TC-AUTH-001 | PASS - Unit Test (15/08/2026, commit `5e9d478`) |
