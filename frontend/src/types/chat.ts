export type CitationResponse = {
  id: string;
  chunk_id: string;
  document_id: string;
  page_number: number | null;
  quote: string | null;
  relevance_score: number | null;
  document_title: string;
};

export type MessageResponse = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  retrieval_metadata: Record<string, unknown> | null;
  model_name: string | null;
  token_usage: Record<string, unknown> | null;
  created_at: string;
  citations: CitationResponse[];
};

export type ConversationSummary = {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_preview: string | null;
};

export type ConversationDetail = {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  messages: MessageResponse[];
};

export type ChatAskResponse = {
  conversation: ConversationDetail;
  answer_message: MessageResponse;
};
