# Nhật ký Tuần 07

## 1. Đã làm

### Backend nghiệp vụ

- Hoàn thiện truy vấn danh sách/chi tiết Test Case phục vụ frontend review.
- Hoàn thiện Human-in-the-loop: edit, submit review, approve, request-fix và reject theo vòng đời trạng thái.
- Bổ sung optimistic locking bằng `lock_version`, version snapshot và audit cho thao tác review.
- Bổ sung NC-05 duplicate detection bằng PostgreSQL pgvector, cosine similarity, HNSW index và embedding rebuild script.
- Bổ sung NC-07 export CSV/XLSX, chỉ lấy Test Case `APPROVED`, có kiểm quyền và audit.
- Bổ sung NC-06 quản lý Module, tags và NC-12 coverage/statistics theo module.
- Bổ sung NC-09 versioned Prompt/Model Configuration; generation lấy active config thay vì prompt nghiệp vụ hardcode.
- Bổ sung NC-08 list/compare/restore Test Case version.
- Bổ sung BR-08: Requirement thay đổi làm Test Case liên quan cần review lại.
- RabbitMQ/Celery đã chạy local; pgvector đã cài cho PostgreSQL. Trước gói hoàn thiện cuối, migration đã xác nhận ở `0008_nc08_version_restore`. Gói cuối thêm `0009_nc10_user_admin`.

### Frontend Tuần 07

- Bổ sung giao diện login và lưu Bearer token local.
- Bổ sung workspace Requirement & AI: chọn module, nhập Requirement/AC, cập nhật Requirement, submit generation job và polling trạng thái.
- Bổ sung workspace Review Test Case: list/filter, edit, review/approve/request-fix/reject.
- Bổ sung duplicate candidate, version history, compare và restore.
- Bổ sung Module & Coverage: tạo/sửa module cho Manager, coverage/statistics, export CSV/XLSX.
- Bổ sung System Config cho Admin: list/create/update/disable User và Prompt/Model Configuration.
- Các màn hình chính có loading, empty và error state theo FE-03.

### Tài liệu / CI

- Bổ sung `TC-TUAN07.md` với TC-07: State Transition, Decision Table, Boundary Value và Equivalence Partitioning.
- Cập nhật `matran-truyvet.md` để phủ NC-01..NC-12, BR-01..BR-09 và các YC chính.
- Bổ sung `tuan07.http` cho manual API test.
- Cập nhật README cho RabbitMQ/Celery, pgvector, HNSW, embeddings, XLSX, frontend và migration Tuần 07.
- Mở rộng GitHub Actions để kiểm cả backend và frontend trên nhánh `tuan-07`.

## 2. Kết quả kiểm thử đã có bằng chứng

- Backend Ruff check: PASS.
- Backend Ruff format check: PASS.
- Backend Unit Test: **69 passed** trên local tại commit `d3e7f71`. Gói hoàn thiện cuối bổ sung 4 test NC-10; cần chạy lại full suite trước PR.
- Alembic đã xác nhận `0008_nc08_version_restore (head)`; sau khi áp dụng gói cuối cần nâng lên `0009_nc10_user_admin`.
- Swagger đã hiển thị các endpoint Module, Prompt Config, Requirement Update, Test Case Version/Restore và các endpoint HITL.
- RabbitMQ/Celery worker đã kết nối local ở các bước kiểm thử trước trong Tuần 07.
- pgvector đã được build/install vào PostgreSQL 18 local và migration `0004` chạy thành công.

## 3. Cần chạy lại trước khi mở PR

- `ruff check`, `ruff format --check`, `pytest` sau khi copy gói hoàn thiện Tuần 07.
- Frontend: `npm run format:check`, `npm run lint`, `npm run build`.
- Kiểm nhanh UI thật với ba role QA / Manager / Admin.
- GitHub Actions phải xanh ở commit cuối.
- Không ghi PASS cho manual test chưa chạy; kết quả lần chạy đầu toàn bộ test case bắt buộc theo lộ trình bắt đầu ở Tuần 08.

## 4. Đối chiếu yêu cầu Tuần 07

- [x] Có frontend cho các luồng nghiệp vụ chính.
- [x] Có loading / empty / error state ở frontend.
- [x] API call tập trung qua `src/services/api.ts`, backend URL lấy từ `NEXT_PUBLIC_API_URL`.
- [x] Form chính có client validation và thông báo lỗi cạnh input; submit bị disable khi đang gửi.
- [x] Test case phủ các use case chính theo TC-06.
- [x] Chức năng lõi có kỹ thuật kiểm thử theo TC-07.
- [x] Có `docs/kiem-thu/matran-truyvet.md` theo TC-08.
- [x] Có API test specification và `tuan07.http` theo TC-09.
- [x] Có authorization test cho các role theo TC-12.
- [x] README được cập nhật khi cách chạy thay đổi.
- [ ] Xác nhận frontend lint/build PASS trên máy local sau khi copy code.
- [ ] Xác nhận CI xanh trên GitHub trước khi nộp PR.

## 5. Còn thiếu / giới hạn đã biết

- OpenAI happy path phụ thuộc API key/credit hợp lệ; Unit Test tiếp tục mock provider theo TE-18.
- Full integration test gọi API thật trên database test và lượt chạy test case thứ nhất thuộc mốc Tuần 08.
- OpenAI happy path và semantic embedding happy path vẫn cần API key/credit hợp lệ; Unit Test mock provider theo TE-18.

## 6. Câu hỏi cho GVHD

Tuần 07 em đã hoàn thiện frontend cho các luồng chính, bổ sung HITL review, pgvector duplicate detection, module/coverage, export, prompt configuration và version restore. Test case đã được cập nhật theo TC-07 và ma trận truy vết TC-08; backend local hiện có 69 Unit Test PASS trước bước hoàn thiện frontend/docs.

Cho em hỏi với phần duplicate detection, việc dùng PostgreSQL pgvector + HNSW + cosine similarity và embedding rebuild script như hiện tại đã phù hợp yêu cầu vector database của đề tài chưa, hay thầy muốn em bổ sung thêm tiêu chí đánh giá duplicate vào gold set ở giai đoạn Tuần 08–09?
