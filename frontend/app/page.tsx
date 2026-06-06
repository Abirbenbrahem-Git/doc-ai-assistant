"use client";
import { useState, useEffect } from "react";
import UploadPanel from "@/components/UploadPanel";
import ChatInterface from "@/components/ChatInterface";
import { Document } from "@/types";

export default function Home() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [apiStatus, setApiStatus] = useState<"checking" | "ok" | "error">("checking");

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/health`)
      .then((r) => r.json())
      .then(() => setApiStatus("ok"))
      .catch(() => setApiStatus("error"));

    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/documents`)
      .then((r) => r.json())
      .then((data) => setDocuments(data.documents || []))
      .catch(console.error);
  }, []);

  const handleUploadSuccess = (doc: Document) => {
    setDocuments((prev) =>
      prev.find((d) => d.doc_id === doc.doc_id) ? prev : [...prev, doc]
    );
  };

  return (
    <main className="flex h-screen bg-gray-100 dark:bg-gray-900">
      {/* Sidebar */}
      <aside className="w-72 flex-shrink-0 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col shadow-sm">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">📚</span>
            <h1 className="text-base font-bold text-gray-900 dark:text-white">
              Doc AI Assistant
            </h1>
          </div>

        </div>
        <div className="flex-1 overflow-y-auto">
          <UploadPanel
            documents={documents}
            onUploadSuccess={handleUploadSuccess}
          />
        </div>
      </aside>

      {/* Zone chat */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-3 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
              {documents.length > 0
                ? `💬 Chat — ${documents.length} document${documents.length > 1 ? "s" : ""} disponible${documents.length > 1 ? "s" : ""}`
                : "💬 Chat — Aucun document chargé"}
            </h2>
            
          </div>
        </header>
        <div className="flex-1 overflow-hidden">
          <ChatInterface hasDocuments={documents.length > 0} />
        </div>
      </div>
    </main>
  );
}