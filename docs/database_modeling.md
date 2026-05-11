# Database Modeling — Grounded Document Assistant

## 1. Database objective

The database must support a multi-workspace RAG application with users, documents, versions, chunks, embeddings, conversations, citations, and evaluation results.

The model must make three things easy:

1. restrict access by workspace and role;
2. retrieve document chunks efficiently;
3. trace every answer back to source chunks.

## 2. Main entities

### users

Stores application users.

Suggested fields:

| Field | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| name | text | Required |
| email | text | Unique, required |
| password_hash | text | Required for local auth |
| created_at | timestamp | Required |
| updated_at | timestamp | Required |

Indexes:

- unique index on `email`.

### workspaces

Stores tenant/business spaces.

| Field | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| name | text | Required |
| slug | text | Unique |
| created_by_user_id | uuid | FK to users |
| created_at | timestamp | Required |
| updated_at | timestamp | Required |

### workspace_memberships

Connects users to workspaces and roles.

| Field | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| workspace_id | uuid | FK to workspaces |
| user_id | uuid | FK to users |
| role | enum | owner, admin, member, viewer |
| created_at | timestamp | Required |

Constraints:

- unique `(workspace_id, user_id)`.

### documents

Represents a logical document inside a workspace.

| Field | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| workspace_id | uuid | FK to workspaces |
| title | text | Display title |
| description | text | Optional |
| status | enum | pending, processing, processed, failed, disabled |
| visibility | enum | workspace, restricted, private |
| uploaded_by_user_id | uuid | FK to users |
| created_at | timestamp | Required |
| updated_at | timestamp | Required |

Indexes:

- `(workspace_id, status)`;
- `(workspace_id, visibility)`.

### document_versions

Tracks file versions and ingestion attempts.

| Field | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| document_id | uuid | FK to documents |
| version_number | integer | Incremental |
| file_name | text | Original name |
| file_path | text | Private storage path |
| mime_type | text | PDF or text initially |
| file_size_bytes | integer | Required |
| checksum | text | For duplicate detection |
| extraction_status | enum | pending, processing, processed, failed |
| extracted_text_path | text | Optional |
| created_at | timestamp | Required |

Constraints:

- unique `(document_id, version_number)`.

### document_chunks

Stores processed text units used for retrieval.

| Field | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| workspace_id | uuid | Denormalized for filtering |
| document_id | uuid | FK to documents |
| document_version_id | uuid | FK to document_versions |
| chunk_index | integer | Position in document |
| page_number | integer | Nullable |
| section_title | text | Nullable |
| content | text | Required |
| token_count | integer | Approximate |
| metadata | jsonb | Flexible metadata |
| created_at | timestamp | Required |

Indexes:

- `(workspace_id, document_id)`;
- `(document_version_id, chunk_index)`;
- full-text index on `content`.

### chunk_embeddings

Stores vector representation for chunks.

| Field | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| chunk_id | uuid | FK to document_chunks |
| embedding_model | text | Required |
| embedding | vector | pgvector column |
| created_at | timestamp | Required |

Indexes:

- vector index on `embedding`;
- unique `(chunk_id, embedding_model)`.

### conversations

Stores chat sessions.

| Field | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| workspace_id | uuid | FK to workspaces |
| user_id | uuid | FK to users |
| title | text | Optional |
| created_at | timestamp | Required |
| updated_at | timestamp | Required |

### messages

Stores user and assistant messages.

| Field | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| conversation_id | uuid | FK to conversations |
| role | enum | user, assistant, system |
| content | text | Required |
| retrieval_metadata | jsonb | For assistant messages |
| model_name | text | Nullable |
| token_usage | jsonb | Nullable |
| created_at | timestamp | Required |

### message_citations

Links answers to source chunks.

| Field | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| message_id | uuid | FK to messages |
| chunk_id | uuid | FK to document_chunks |
| document_id | uuid | FK to documents |
| page_number | integer | Nullable |
| quote | text | Optional short excerpt |
| relevance_score | numeric | Optional |
| created_at | timestamp | Required |

Indexes:

- `(message_id)`;
- `(document_id)`.

### evaluation_sets

Stores named golden question sets.

| Field | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| workspace_id | uuid | FK to workspaces |
| name | text | Required |
| description | text | Optional |
| created_at | timestamp | Required |

### evaluation_questions

Stores expected test cases.

| Field | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| evaluation_set_id | uuid | FK to evaluation_sets |
| question | text | Required |
| expected_answer_notes | text | Required |
| expected_document_ids | uuid[] | Optional depending on ORM |
| created_at | timestamp | Required |

### evaluation_runs

Stores evaluation executions.

| Field | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| evaluation_set_id | uuid | FK to evaluation_sets |
| model_name | text | Required |
| embedding_model | text | Required |
| retrieval_config | jsonb | Required |
| score_summary | jsonb | Optional |
| created_at | timestamp | Required |

### evaluation_results

Stores result per question.

| Field | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| evaluation_run_id | uuid | FK to evaluation_runs |
| evaluation_question_id | uuid | FK to evaluation_questions |
| generated_answer | text | Required |
| retrieved_chunk_ids | uuid[] | Optional depending on ORM |
| score | numeric | Nullable |
| passed | boolean | Nullable |
| notes | text | Optional |
| created_at | timestamp | Required |

### ingestion_logs

Stores pipeline events.

| Field | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| document_version_id | uuid | FK to document_versions |
| step | text | Required |
| status | enum | started, success, failed |
| message | text | Optional |
| details | jsonb | Optional |
| created_at | timestamp | Required |

## 3. Enums

### workspace_role

- owner
- admin
- member
- viewer

### document_status

- pending
- processing
- processed
- failed
- disabled

### document_visibility

- workspace
- restricted
- private

### extraction_status

- pending
- processing
- processed
- failed

### message_role

- user
- assistant
- system

### log_status

- started
- success
- failed

## 4. Relationships

```text
User 1 -> N WorkspaceMembership
Workspace 1 -> N WorkspaceMembership
Workspace 1 -> N Document
Document 1 -> N DocumentVersion
DocumentVersion 1 -> N DocumentChunk
DocumentChunk 1 -> N ChunkEmbedding
Workspace 1 -> N Conversation
Conversation 1 -> N Message
Message 1 -> N MessageCitation
DocumentChunk 1 -> N MessageCitation
Workspace 1 -> N EvaluationSet
EvaluationSet 1 -> N EvaluationQuestion
EvaluationSet 1 -> N EvaluationRun
EvaluationRun 1 -> N EvaluationResult
```

## 5. Business rules

- A user can only query documents from workspaces where the user has membership.
- A disabled document must not be used in retrieval.
- Only the latest processed document version should be active by default.
- Citations must reference chunks actually retrieved for that answer.
- Failed ingestion must not delete the original file metadata.
- Evaluation runs must be immutable after creation.

## 6. Recommended indexes

- `users.email` unique.
- `workspaces.slug` unique.
- `workspace_memberships(workspace_id, user_id)` unique.
- `documents(workspace_id, status)`.
- `document_chunks(workspace_id, document_id)`.
- Full-text index on `document_chunks.content`.
- Vector index on `chunk_embeddings.embedding`.
- `messages(conversation_id, created_at)`.
- `message_citations(message_id)`.

## 7. Suggested initial seed

Seed data should include:

- one demo workspace;
- one owner user;
- one viewer user;
- three sample documents:
  - public FAQ;
  - internal policy;
  - restricted procedure;
- 10 golden evaluation questions;
- one demo conversation.

## 8. Conceptual schema example

```text
workspace
  documents
    document_versions
      document_chunks
        chunk_embeddings
  conversations
    messages
      message_citations
  evaluation_sets
    evaluation_questions
    evaluation_runs
      evaluation_results
```
