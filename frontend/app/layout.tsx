import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BugHunterLab",
  description: "Local AI-assisted bug bounty research platform"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}