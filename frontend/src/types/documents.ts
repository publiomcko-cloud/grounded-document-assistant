export type DocumentStatus =
  | "pending"
  | "processing"
  | "processed"
  | "failed"
  | "disabled";

export type DocumentVisibility = "workspace" | "restricted" | "private";

export type DocumentVersionSummary = {
  id: string;
  version_number: number;
  file_name: string;
  mime_type: string;
  file_size_bytes: number;
  extraction_status: "pending" | "processing" | "processed" | "failed";
  created_at: string;
};

export type IngestionLogEntry = {
  id: string;
  step: string;
  status: "started" | "success" | "failed";
  message: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
};

export type DocumentChunkPreview = {
  id: string;
  chunk_index: number;
  page_number: number | null;
  section_title: string | null;
  content: string;
  token_count: number | null;
  created_at: string;
};

export type DocumentSummary = {
  id: string;
  workspace_id: string;
  title: string;
  description: string | null;
  status: DocumentStatus;
  visibility: DocumentVisibility;
  uploaded_by_user_id: string;
  created_at: string;
  updated_at: string;
  latest_version: DocumentVersionSummary | null;
};

export type DocumentDetail = DocumentSummary & {
  versions: DocumentVersionSummary[];
  latest_version_logs: IngestionLogEntry[];
  latest_version_chunk_preview: DocumentChunkPreview[];
  latest_version_chunk_count: number;
  latest_version_embedding_count: number;
  latest_version_extracted_text: string | null;
};
