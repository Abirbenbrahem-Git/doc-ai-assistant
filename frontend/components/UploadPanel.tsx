"use client";
import { useState, useCallback } from "react";
import { Document, UploadResponse } from "@/types";

interface Props {
  documents: Document[];
  onUploadSuccess: (doc: Document) => void;
}

export default function UploadPanel({ documents, onUploadSuccess }: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpload, setLastUpload] = useState<UploadResponse | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      const allowed = ["application/pdf", "text/plain"];
      if (!allowed.includes(file.type)) {
        setError("Seuls les fichiers PDF et TXT sont acceptés.");
        return;
      }
      setIsUploading(true);
      setError(null);
      setLastUpload(null);

      const formData = new FormData();
      formData.append("file", file);

      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/upload`,
          { method: "POST", body: formData }
        );
        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.detail || "Erreur upload");
        }
        const data: UploadResponse = await res.json();
        setLastUpload(data);
        onUploadSuccess({ doc_id: data.doc_id, filename: file.name });
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Erreur inconnue");
      } finally {
        setIsUploading(false);
      }
    },
    [onUploadSuccess]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div className="p-4">
      <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 uppercase tracking-wide">
        Documents
      </h2>

      <label
        className={`flex flex-col items-center justify-center w-full h-28 border-2 border-dashed rounded-xl cursor-pointer transition-all ${
          isDragging
            ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20 scale-[0.98]"
            : "border-gray-300 dark:border-gray-600 hover:border-blue-400 hover:bg-gray-50 dark:hover:bg-gray-700/50"
        }`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
      >
        <input
          type="file"
          className="hidden"
          accept=".pdf,.txt"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          disabled={isUploading}
        />
        {isUploading ? (
          <div className="flex flex-col items-center gap-2">
            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-xs text-blue-600 dark:text-blue-400 font-medium">
              Indexation en cours...
            </span>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-1">
            <div className="text-2xl">📄</div>
            <p className="text-xs font-medium text-gray-600 dark:text-gray-300">
              Glisser ou cliquer pour uploader
            </p>
            <p className="text-xs text-gray-400">PDF ou TXT — max 10 MB</p>
          </div>
        )}
      </label>

      {error && (
        <div className="mt-2 p-2 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <p className="text-xs text-red-600 dark:text-red-400">⚠️ {error}</p>
        </div>
      )}

      {lastUpload && (
        <div className="mt-2 p-2 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
          <p className="text-xs text-green-700 dark:text-green-400">
            ✓ {lastUpload.chunks} chunks · {lastUpload.pages} page{lastUpload.pages > 1 ? "s" : ""}
          </p>
        </div>
      )}

      {documents.length > 0 && (
        <div className="mt-4">
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 font-medium">
            {documents.length} document{documents.length > 1 ? "s" : ""} indexé{documents.length > 1 ? "s" : ""}
          </p>
          <ul className="space-y-1">
            {documents.map((doc) => (
              <li
                key={doc.doc_id}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600"
              >
                <span className="text-base">📑</span>
                <span className="text-xs text-gray-700 dark:text-gray-300 truncate flex-1">
                  {doc.filename}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}