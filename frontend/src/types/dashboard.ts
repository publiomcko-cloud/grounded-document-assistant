export type DashboardDocumentMetrics = {
  total_documents: number;
  pending_documents: number;
  processing_documents: number;
  processed_documents: number;
  failed_documents: number;
  disabled_documents: number;
};

export type DashboardUsageMetrics = {
  total_conversations: number;
  total_questions: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
};

export type DashboardRecentQuestion = {
  id: string;
  conversation_id: string;
  content: string;
  created_at: string;
};

export type DashboardIngestionLogEntry = {
  id: string;
  document_id: string;
  document_version_id: string;
  document_title: string;
  step: string;
  status: string;
  message: string | null;
  created_at: string;
};

export type DashboardLatestEvaluationRun = {
  id: string;
  evaluation_set_id: string;
  evaluation_set_name: string;
  created_at: string;
  pass_rate: number | null;
  average_score: number | null;
  passed_questions: number | null;
  total_questions: number | null;
};

export type DashboardSummaryResponse = {
  document_metrics: DashboardDocumentMetrics;
  usage_metrics: DashboardUsageMetrics;
  recent_questions: DashboardRecentQuestion[];
  recent_ingestion_logs: DashboardIngestionLogEntry[];
  latest_evaluation_run: DashboardLatestEvaluationRun | null;
};
