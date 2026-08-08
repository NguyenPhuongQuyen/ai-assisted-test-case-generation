import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Test Case Generator",
  description: "Công cụ sinh test case tự động từ đặc tả yêu cầu bằng AI",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
