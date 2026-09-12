# Báo cáo đánh giá AI bằng Gold Set

## 1. Phương pháp

- Gold Set gồm 20 requirement.
- Mỗi requirement được gửi qua API backend thật.
- Backend xử lý bất đồng bộ qua RabbitMQ/Celery và gọi OpenAI API.
- Output được validate schema trước khi lưu vào PostgreSQL.
- Coverage được đánh giá nghiêm theo danh sách `must_cover` của từng mẫu.

## 2. Kết quả tổng hợp

| KPI | Kết quả |
|---|---:|
| Generation Success Rate | 20/20 (100.0%) |
| Schema Valid Rate | 20/20 (100.0%) |
| Full Coverage Rate | 15/20 (75.0%) |
| Requirements đạt Partial Coverage | 5/20 (25.0%) |
| Coverage Failure | 0/20 (0.0%) |
| At-least-partial Coverage | 20/20 (100.0%) |
| Technique Match Rate | 20/20 (100.0%) |
| No Hallucination Rate | 20/20 (100.0%) |
| Tổng test case AI sinh | 110 |
| Trung bình test case / requirement | 5.5 |

## 3. Các mẫu coverage chưa đầy đủ

- **GS03 – PARTIAL:** Bao phủ lớp 1-8 nhưng chưa có test riêng cho giá trị 7 ghế.
- **GS07 – PARTIAL:** Chưa có test riêng cho từ khóa chứa ký tự đặc biệt.
- **GS08 – PARTIAL:** Đã kiểm thử lớp non-PDF nhưng chưa tách riêng DOCX và PNG.
- **GS13 – PARTIAL:** Chưa sinh trường hợp concurrency hai khách cùng mua phần tồn kho cuối.
- **GS17 – PARTIAL:** Các trạng thái không APPROVED được gom thành một lớp, chưa tách riêng DRAFT/IN_REVIEW/NEEDS_FIX/REJECTED.

## 4. Nhận xét

AI đạt tỷ lệ thành công và schema validation cao trong tập Gold Set. Kết quả cho thấy mô hình nhận diện tốt các kỹ thuật như BVA, equivalence partitioning, negative testing, state transition và concurrency. Tuy nhiên, một số requirement có nhiều giá trị hoặc trạng thái cụ thể được AI gom thành cùng một lớp tương đương, nên 5/20 mẫu chỉ đạt PARTIAL thay vì FULL. Tuy nhiên, không có mẫu nào Coverage FAIL và toàn bộ 20/20 requirement đều được AI bao phủ ít nhất một phần. Đây là điểm cần Human-in-the-loop QA tiếp tục rà soát trước khi approve test case.
