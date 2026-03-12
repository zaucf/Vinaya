import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Vinaya",
  description: "An AI judgment purification engine that evaluates before execution.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
