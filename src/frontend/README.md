# Frontend - Next.js 16

## Cài đặt

```bash
cd src/frontend
npm install
copy .env.example .env.local
npm run dev
```

Mặc định frontend gọi backend qua:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Workspace Tuần 07

- Requirement & AI: QA nhập/cập nhật requirement và theo dõi generation job.
- Review Test Case: list/filter, edit, state transition, duplicate candidates, versions/compare/restore.
- Module & Coverage: module management, coverage/statistics và export.
- System Config: Admin tạo user và quản lý prompt/model versions.

Mỗi luồng chính có loading, empty và error state theo FE-03. Quyền cuối cùng luôn được backend kiểm tra lại; frontend chỉ ẩn/disable action để UX rõ hơn.

## Quality check

```bash
npm run format
npm run format:check
npm run lint
npm run build
```
