import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Synapse Code Auditor — AI Code Review & Bug Detection",
  description:
    "Synapse detects bugs, security vulnerabilities, and performance issues in AI-generated code — instantly. Powered by LLaMA 3.3 70B via Groq.",
  keywords: "code auditor, AI code review, security, bug detection, SQL injection, race condition, Groq, LLaMA",
  authors: [{ name: "Synapse" }],
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
  openGraph: {
    title: "Synapse Code Auditor",
    description: "AI code review that catches what humans miss.",
    type: "website",
    url: "https://huggingface.co/spaces/coderMayank69/Synapse_Code_Auditor",
  },
  twitter: {
    card: "summary_large_image",
    title: "Synapse Code Auditor",
    description: "AI code review that catches what humans miss.",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
