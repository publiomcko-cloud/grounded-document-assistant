export type EvaluationSetSummary = {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  question_count: number;
};

export type EvaluationQuestionResponse = {
  id: string;
  question: string;
  expected_answer_notes: string;
  expected_document_ids: string[] | null;
  created_at: string;
};

export type EvaluationRunSummary = {
  id: string;
  model_name: string;
  embedding_model: string;
  retrieval_config: Record<string, unknown>;
  score_summary: Record<string, unknown> | null;
  created_at: string;
};

export type EvaluationSetDetail = {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  questions: EvaluationQuestionResponse[];
  recent_runs: EvaluationRunSummary[];
};

export type EvaluationQuestionCreate = {
  question: string;
  expected_answer_notes: string;
  expected_document_ids?: string[] | null;
};

export type EvaluationSetCreateRequest = {
  name: string;
  description: string | null;
  questions: EvaluationQuestionCreate[];
};

export type EvaluationResultResponse = {
  id: string;
  evaluation_question_id: string;
  generated_answer: string;
  retrieved_chunk_ids: string[] | null;
  score: number | null;
  passed: boolean | null;
  notes: string | null;
  created_at: string;
  question: string;
  expected_answer_notes: string;
  expected_document_ids: string[] | null;
};

export type EvaluationRunDetail = {
  id: string;
  evaluation_set_id: string;
  evaluation_set_name: string;
  model_name: string;
  embedding_model: string;
  retrieval_config: Record<string, unknown>;
  score_summary: Record<string, unknown> | null;
  created_at: string;
  results: EvaluationResultResponse[];
};
