Chủ đề: Công cụ sinh Test Case tự động từ Đặc tả yêu cầu bằng AI (AI-assisted Test Case Generation from Requirements)

1. Giới thiệu (About the Project):
- Dự án này là một hệ thống hỗ trợ quá trình Đảm bảo chất lượng (QA) bằng cách tự động hóa bước sinh test case từ đặc tả yêu cầu. Việc phân tích requirement và viết kịch bản kiểm thử thủ công thường tốn thời gian và dễ bỏ sót các điều kiện biên. Công cụ này khắc phục vấn đề đó bằng việc gọi API mô hình ngôn ngữ lớn (Claude API) kết hợp với kỹ thuật Structured Output, đảm bảo test case sinh ra luôn đạt chuẩn cấu trúc bắt buộc (Bước thực hiện, Kết quả mong đợi, Mức ưu tiên).

- Điểm nhấn của hệ thống là phương pháp tiếp cận Human-in-the-loop: AI đóng vai trò phân tích và đề xuất tình huống, kỹ sư kiểm thử (Tester/QA) sẽ trực tiếp rà soát, tinh chỉnh và kiểm soát chất lượng cuối cùng trước khi đưa vào luồng kiểm thử thực tế.

2. Các tính năng chính (Key Features):
- Nhập yêu cầu (Requirement Input): Hỗ trợ nhập/dán mô tả tính năng và tiêu chí chấp nhận (Acceptance Criteria).
- Tự động sinh Test Case: Khai thác AI để sinh hàng loạt kịch bản kiểm thử có cấu trúc chuẩn.
- Gợi ý điều kiện biên (Edge Cases): Nhận diện và đề xuất các tình huống giới hạn/ngoại lệ dễ bị bỏ qua.
- Rà soát & Duyệt (Review & Approve): Giao diện tương tác cho phép đánh dấu hợp lệ, chỉnh sửa và khử trùng lặp các kịch bản kiểm thử.
- Quản lý theo Module: Tổ chức test case theo từng tính năng/module và theo dõi độ bao phủ.
- Xuất dữ liệu (Export): Kết xuất bộ test case đã duyệt ra định dạng CSV/Excel, dễ dàng tích hợp với các công cụ quản lý test bên ngoài.

3. Công nghệ sử dụng (Tech Stack):
- Frontend: Next.js (React + TypeScript), Vercel AI SDK.
- Backend: FastAPI (Python).
- Cơ sở dữ liệu: PostgreSQL.
- Trí tuệ nhân tạo (AI): Claude API.
- Triển khai & CI/CD: Docker, GitHub Actions.
