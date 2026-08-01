# Nhật ký Đồ án – Tuần 4 (Cập nhật ngày 01/08/2026)

## 1. Công việc đã hoàn thành
* **Hoàn thiện tài liệu Báo cáo (Chương 3 & Hình thức):**
  * Bổ sung Sơ đồ Thiết kế kiến trúc kỹ thuật tổng thể (Architecture Diagram) theo mô hình Application Layer 3 lớp kết hợp Claude API, PostgreSQL và Redis.
  * Lập Bảng Ma trận truy vết (Traceability Matrix) kết nối 100% Yêu cầu nghiệp vụ (FR) <-> Use Case <-> Bảng CSDL (ERD).
  * Viết đặc tả chi tiết đủ 9 Use Case chính (UC01 – UC09) khớp với sơ đồ Use Case UML và tài liệu BRD.
  * Khắc phục triệt để lỗi hình thức: Dùng Heading Styles cho mục lục/chú thích tự động, căn lề chuẩn 3-2-2-2 cm, đánh số Hình/Bảng/Từ viết tắt.
* **Cấu trúc lại thư mục mã nguồn & Kiểm thử API:**
  * Tối ưu cấu trúc thư mục dự án, chuyển toàn bộ mã nguồn Backend vào thư mục `src/backend/`.
  * Khởi tạo và tổ chức cấu trúc dự án Backend FastAPI: `app/`, `routes/`, `services/`, `database.py`, `config.py`.
  * Kiểm thử độc lập (Unit Test / API Testing) các endpoint khởi tạo của Backend bằng công cụ Postman để đảm bảo luồng nhận/trả dữ liệu hoạt động ổn định.

## 2. Kế hoạch tuần tiếp theo (Tuần 5)
* Rà soát toàn bộ tài liệu báo cáo để đối chiếu và bổ sung đầy đủ trích dẫn nguồn `[n]` tương ứng với danh mục tài liệu tham khảo ở cuối bài.
* Hiện thực luồng gọi Claude API sử dụng Structured Output (JSON Schema) ở Backend FastAPI.
* Xây dựng cơ chế kiểm tra Schema Validation và tự động gọi lại API khi dữ liệu trả về sai cấu trúc (Quy tắc BR-04).
* Kết nối CSDL PostgreSQL để lưu trữ test case nháp và quản lý lịch sử phiên bản (`TestCaseVersion`).

## 3. Khó khăn / Đề xuất
* **Khó khăn:** Việc tham khảo nhiều tài liệu nghiên cứu trong quá trình viết báo cáo dẫn đến việc cần nhiều thời gian để rà soát và đối chiếu chính xác từng trích dẫn `[n]` trong thân bài.
* **Đề xuất:** Tuần sau sẽ tập trung rà soát và hoàn thiện 100% phần trích dẫn này cùng với việc tích hợp API lõi.
