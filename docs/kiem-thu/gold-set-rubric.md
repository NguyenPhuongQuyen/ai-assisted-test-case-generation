# Gold Set - Rubric đánh giá chất lượng AI

Gold Set gồm 20 requirement chuẩn dùng để đánh giá chất lượng test case do AI sinh.

## Tiêu chí đánh giá mỗi mẫu

Mỗi requirement được chấm theo 4 tiêu chí:

1. **Schema Valid**
   - PASS nếu AI trả về test case đúng schema hệ thống và lưu được thành công.
   - FAIL nếu output sai cấu trúc hoặc generation thất bại do schema.

2. **Coverage**
   - PASS nếu tập test case AI bao phủ đầy đủ các trường hợp bắt buộc trong cột `must_cover`.
   - PARTIAL nếu chỉ bao phủ một phần.
   - FAIL nếu bỏ sót phần lớn yêu cầu quan trọng.

3. **Technique Match**
   - PASS nếu AI sử dụng ít nhất một kỹ thuật kiểm thử phù hợp với `expected_techniques`.
   - FAIL nếu kỹ thuật không phù hợp hoặc không có.

4. **Hallucination**
   - PASS nếu AI không tự thêm business rule trái hoặc vượt quá requirement.
   - FAIL nếu AI tự suy diễn rule được liệt kê trong `hallucination_guard` hoặc rule tương tự.

## KPI tổng hợp

- Schema Valid Rate = số mẫu Schema PASS / 20 × 100%
- Full Coverage Rate = số mẫu Coverage PASS / 20 × 100%
- Technique Match Rate = số mẫu Technique PASS / 20 × 100%
- No Hallucination Rate = số mẫu Hallucination PASS / 20 × 100%
- Generation Success Rate = số generation COMPLETED / 20 × 100%

Kết quả phải được ghi từ lần chạy AI thực tế, không tự điền PASS khi chưa kiểm chứng.
