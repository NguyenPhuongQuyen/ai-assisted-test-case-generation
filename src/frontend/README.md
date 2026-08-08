# Frontend - Next.js

## Yêu cầu
- Node.js 20.9+ (khuyến nghị Node 22 LTS)
- npm 10+

## Chạy
```bash
cp .env.example .env.local
npm install
npm run dev
```

Mở `http://localhost:3000`.

## Kiểm tra
```bash
npm run format:check
npm run lint
npm run build
```

FE-01: mọi lời gọi backend phải đi qua `src/services/api.ts`.
