import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Doc AI Assistant",
  description: "Chat with your documents using Groq AI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className="h-full">
      <body className="antialiased h-full">{children}</body>
    </html>
  );
}