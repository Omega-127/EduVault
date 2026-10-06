import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EduVault — University Knowledge Assistant",
  description:
    "AI-powered university knowledge assistant. Ask natural-language questions and receive concise, source-grounded answers from institutional documents.",
  keywords: [
    "university",
    "knowledge base",
    "AI assistant",
    "document search",
    "RAG",
    "EduVault",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
      </head>
      <body className="min-h-screen bg-surface-primary text-text-primary font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
