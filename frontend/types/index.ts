export interface Document {
  doc_id: string;
  filename: string;
}

export interface Source {
  filename: string;
  page: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  timestamp: Date;
}

export interface UploadResponse {
  message: string;
  doc_id: string;
  chunks: number;
  pages: number;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
}