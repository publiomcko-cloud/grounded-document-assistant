# Screen Flows and Navigation — Grounded Document Assistant

## 1. UX objective

The interface must make the product understandable quickly. A reviewer should understand the value of the project in less than one minute:

1. upload documents;
2. process documents;
3. ask questions;
4. receive cited answers;
5. verify sources;
6. measure quality.

## 2. User roles

### Owner

Can manage workspace, documents, users, chat, and evaluations.

### Admin

Can manage documents, run evaluations, and view dashboard.

### Member

Can upload documents and ask questions.

### Viewer

Can ask questions and view allowed documents, but cannot upload or manage settings.

## 3. Planned screens

## 3.1 Landing page

Purpose:

- explain the product;
- show the business problem;
- link to demo login;
- present portfolio value.

Main actions:

- open demo;
- view GitHub repository;
- view documentation;
- contact developer.

Sections:

- hero;
- problem;
- how it works;
- feature list;
- architecture summary;
- demo call-to-action.

## 3.2 Login page

Purpose:

- authenticate users;
- provide demo credentials.

Main actions:

- login;
- access demo account;
- navigate to register if implemented.

States:

- default;
- loading;
- invalid credentials;
- server error.

## 3.3 Workspace dashboard

Purpose:

- show the state of the workspace.

Content:

- total documents;
- processed documents;
- failed documents;
- recent questions;
- last evaluation score;
- ingestion warnings.

Main actions:

- upload document;
- ask a question;
- open documents;
- run evaluation.

## 3.4 Documents page

Purpose:

- manage documents and processing status.

Content:

- document table;
- title;
- status;
- visibility;
- uploaded date;
- version;
- actions.

Main actions:

- upload document;
- open document detail;
- disable document;
- retry ingestion;
- delete document.

States:

- empty list;
- processing;
- processed;
- failed;
- no permission.

## 3.5 Document detail page

Purpose:

- inspect one document and its ingestion state.

Content:

- metadata;
- processing status;
- version history;
- extracted chunks preview;
- ingestion logs;
- visibility settings.

Main actions:

- retry processing;
- disable document;
- update visibility;
- ask question about this document.

## 3.6 Chat page

Purpose:

- ask questions and receive grounded answers.

Content:

- conversation list;
- active conversation;
- question input;
- answer block;
- citation cards;
- source snippet drawer.

Main actions:

- ask question;
- start new conversation;
- open citation;
- copy answer;
- provide feedback if implemented.

Answer states:

- answering;
- answer with citations;
- insufficient context;
- retrieval failed;
- permission denied.

## 3.7 Evaluation page

Purpose:

- test the quality of the RAG pipeline.

Content:

- golden question sets;
- question list;
- run evaluation button;
- evaluation results;
- score summary;
- retrieved source preview.

Main actions:

- create question;
- run evaluation;
- inspect result;
- compare runs if implemented.

## 3.8 Settings page

Purpose:

- manage workspace configuration.

MVP content:

- workspace name;
- role list;
- model configuration display;
- retrieval configuration display.

Future content:

- invitations;
- billing;
- integrations;
- audit logs.

## 4. Main navigation

```text
Landing
  -> Login
    -> Workspace Dashboard
      -> Documents
        -> Document Detail
      -> Chat
        -> Citation Drawer
      -> Evaluation
      -> Settings
```

## 5. Main user flows

### Flow A — Upload and ask

1. User logs in.
2. User opens Documents.
3. User uploads PDF.
4. System shows status as processing.
5. Worker processes file.
6. Status becomes processed.
7. User opens Chat.
8. User asks a question.
9. System returns answer with citations.

### Flow B — Verify source

1. User receives answer.
2. User clicks citation.
3. Source drawer opens.
4. Drawer shows document title, page, and quoted chunk.
5. User confirms answer grounding.

### Flow C — Run evaluation

1. Admin opens Evaluation page.
2. Admin selects golden set.
3. Admin runs evaluation.
4. System executes all questions.
5. Results show score, generated answers, and retrieved chunks.
6. Admin identifies weak retrieval or answer issues.

### Flow D — Permission check demo

1. Admin marks one document as restricted.
2. Viewer asks a question whose answer exists only in the restricted document.
3. System must not retrieve restricted content.
4. System responds with insufficient context or only cites allowed documents.

## 6. Reusable components

- AppShell
- SidebarNavigation
- WorkspaceSwitcher
- StatusBadge
- DocumentUploadDropzone
- DocumentTable
- IngestionLogTable
- ChatMessage
- CitationCard
- SourceSnippetDrawer
- EvaluationRunTable
- EmptyState
- LoadingState
- ErrorAlert
- ConfirmDialog

## 7. Basic UX rules

- Always show document processing status.
- Never hide ingestion errors.
- Citations must be visually linked to answers.
- Insufficient context should be treated as a valid answer state, not as a failure.
- Demo credentials must be easy to find in portfolio mode.
- Use plain language for business users.
- Keep technical details available but not intrusive.
