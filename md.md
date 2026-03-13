## NotebookLM-Style Backend – Project Overview

### 1. Purpose

This backend provides a **FastAPI-based API** for a notebook/project-oriented app that:

- Manages **projects** and **documents**
- Handles **user authentication** via AWS Cognito
- Stores raw files in **S3** and extracts text via **Textract**
- Uses **Bedrock** for summarization, Q&A, and question generation
- Uses **OpenSearch** for **semantic search** over document embeddings
- Persists relational data in **PostgreSQL (via SQLAlchemy)**

The architecture follows a clear separation of concerns:

- **Routers** = HTTP front doors (no business logic)
- **Services** = Workers / AWS-specific integrations
- **Domain services (e.g. QA)** = Orchestrate multiple services
- **Tasks** = Background pipelines (long-running jobs)
- **Models** = Database entities
- **Schemas** = Pydantic contracts for request/response bodies

---

### 2. High-Level Architecture

- **Framework**: FastAPI
- **Main entrypoint**: `app/main.py`
  - Creates the `FastAPI` app.
  - Configures CORS.
  - Includes routers:
    - `auth`
    - `projects`
    - `documents`
    - `ai`
    - `collaboration` (stub)
- **Configuration**: `app/config.py`
  - `Settings` via `pydantic-settings`:
    - `aws_region`
    - `cognito_user_pool_id`
    - `cognito_client_id`
    - `database_url`
    - `opensearch_endpoint`
    - `s3_bucket_name`
    - `bedrock_model_id`
    - `bedrock_embedding_model_id`

---

### 3. Authentication & Dependencies

- **Cognito service**: `app/services/cognito.py`
  - `login(email, password)`:
    - Calls Cognito’s `initiate_auth` to obtain an access token.
    - Returns `TokenResponse` (with fallback dummy token in dev).
  - `signup(email, password)`:
    - Calls Cognito’s `sign_up` API.
  - `verify_token(token)`:
    - Currently a **stub**: accepts `dummy-token` and any non-empty token otherwise.
    - Intended to be replaced by full JWT verification (JWKS, issuer, audience, etc.).

- **Dependency**: `app/dependencies.py`
  - `get_current_user`:
    - Uses `HTTPBearer` to get the Bearer token.
    - Calls `cognito.verify_token`.
    - Raises `401` if missing/invalid.
    - Returns a normalized user dict.

---

### 4. Database & Models

- **Database setup**: `app/database.py`
  - `Base = declarative_base()`.
  - `get_engine()` uses `Settings.database_url`.
  - `get_db()` yields a `Session` for dependency injection.

- **Key models** (under `app/models/`):
  - `Project` (`project.py`):
    - Fields: `id`, `name`, `owner_id`, `created_at`.
  - `Document` (`document.py`):
    - Fields: `id`, `project_id`, `s3_key`, `filename`, `status`, `created_at`.
    - `status` represents processing state (e.g. `queued`, `processed`, `failed`).
  - `AIOutput` (`ai_output.py`):
    - Fields: `id`, `project_id`, `document_id`, `type`, `content`, `created_at`.
    - Stores AI-generated outputs (e.g. summaries).

---

### 5. Routers (HTTP Front Doors)

#### 5.1 Projects Router – `app/routers/projects.py`

- **Prefix**: `/api/projects`
- **Endpoints**:
  - `GET /` → `list_projects`:
    - Auth via `get_current_user`, DB via `get_db`.
    - Currently returns an empty list (stub).
  - `POST /` → `create_project`:
    - Accepts `ProjectCreate` (name).
    - Returns `ProjectRead` (currently stubbed with `id=1`).
  - `DELETE /{project_id}` → `delete_project`:
    - Deletes a project (stub currently returns a simple JSON payload).

#### 5.2 Documents Router – `app/routers/documents.py`

- **Prefix**: `/api/projects/{project_id}/documents`
- **Endpoints**:
  - `GET /` → `list_documents`:
    - Fetches all `Document` rows for the project.
    - Returns list of `DocumentRead` (id, project_id, filename, s3_key, status).
  - `POST /` → `create_document`:
    - Accepts `DocumentCreate` (filename, s3_key).
    - Creates a `Document` with status `"queued"`.
    - Schedules background task `process_uploaded_document(document.id, db)`.
    - Returns the created document as `DocumentRead`.
  - `DELETE /{document_id}` → `delete_document`:
    - Loads `Document` by `id` and `project_id`.
    - Deletes the S3 object via `services.s3.delete_file`.
    - Deletes the DB record and returns `{ ok: True, ... }` on success.

#### 5.3 AI Router – `app/routers/ai.py`

- **Prefix**: `/api/projects/{project_id}`, tag `["ai"]`
- **Schemas**: defined in `app/schemas/ai.py`:
  - `SummarizeRequest`, `SummarizeResponse`
  - `AskRequest`, `AskResponse`
  - `QuestionsRequest`, `QuestionsResponse`

- **Endpoints**:
  - `POST /summarize`:
    - Validates `SummarizeRequest`.
    - Auth via `get_current_user`.
    - Delegates to `bedrock.summarize_text`.
    - Returns `SummarizeResponse`.
  - `POST /ask`:
    - Validates `AskRequest` (question + optional context).
    - Delegates to `qa.answer_project_question(project_id, question, fallback_context)`.
    - Returns `AskResponse` with the AI-generated answer.
  - `POST /questions`:
    - Validates `QuestionsRequest`.
    - Delegates to `bedrock.generate_questions`.
    - Returns `QuestionsResponse` with a list of questions.

> Note: Routers remain thin; orchestration lives in services.

---

### 6. Services (AWS Integration Layer)

All live under `app/services/` and are imported via `app/services/__init__.py`.

#### 6.1 Cognito Service – `cognito.py`

- Handles login, signup, and token verification against AWS Cognito.
- Uses `Settings.cognito_client_id` and `Settings.aws_region`.

#### 6.2 S3 Service – `s3.py`

- `generate_upload_url(bucket, key, content_type, expires_in)`:
  - Uses `boto3` S3 client to generate presigned `put_object` URLs.
  - Falls back to a dummy URL if boto3 is unavailable.
- `delete_file(bucket, key)`:
  - Deletes an object from S3, swallowing errors for robustness.

#### 6.3 Textract Service – `textract.py`

- `extract_text_from_s3(s3_bucket, s3_key)`:
  - Uses Textract `detect_document_text` to read text from S3-stored documents.
  - Extracts line-level text into a newline-joined string.
  - Returns empty string on failure.

#### 6.4 Bedrock Service – `bedrock.py`

- Creates a `bedrock-runtime` client using `Settings.aws_region` and `Settings.bedrock_model_id`.
- **Functions**:
  - **`summarize_text(text)`**:
    - Sends a summarization prompt to Claude and returns the summary.
  - **`answer_question(question, context)`**:
    - Answers a question, optionally constrained to a provided context (for grounded Q&A).
  - **`generate_questions(text, count)`**:
    - Generates a list of follow-up questions about a text.
  - **`embed_text(text)`**:
    - Uses `Settings.bedrock_embedding_model_id` to produce embedding vectors.
    - Returns an empty list if embedding is not available (e.g. local dev).

#### 6.5 OpenSearch Service – `opensearch.py`

- Lazily constructs an `OpenSearch` client from `Settings.opensearch_endpoint`.
- **Functions**:
  - **`index_document_embedding(project_id, document_id, embedding, text)`**:
    - Indexes a document’s embedding and raw text into a `documents` index.
  - **`search_similar_documents(project_id, query_embedding, k=5)`**:
    - Performs a k-NN search filtered by `project_id`.
    - Returns a list of `_source` dicts (with `text` and metadata).

#### 6.6 QA Domain Service – `qa.py`

- **`answer_project_question(project_id, question, fallback_context=None)`**:
  - Orchestrates Q&A for a project:
    - Embeds the question using `bedrock.embed_text`.
    - Retrieves similar documents via `opensearch.search_similar_documents`.
    - Builds a combined context string from retrieved `text` fields.
    - Falls back to `fallback_context` if retrieval yields nothing.
    - Calls `bedrock.answer_question` with the combined context.
  - This service is the **“brain”** for question answering and keeps routers and low-level services clean.

---

### 7. Background Tasks / Pipelines

#### 7.1 Document Processing Task – `app/tasks/document_tasks.py`

- **Function**: `process_uploaded_document(document_id, db)`
  - Loads the `Document` row by ID.
  - Uses `Settings.s3_bucket_name` + document’s `s3_key` with Textract to extract text.
  - On success:
    - Summarizes text via `bedrock.summarize_text`.
    - Embeds text via `bedrock.embed_text`.
    - Indexes embedding + text into OpenSearch via `opensearch.index_document_embedding`.
    - Creates an `AIOutput` entry of type `"summary"` for the document.
    - Marks the `Document.status` as `"processed"`.
  - On failure:
    - Marks the `Document.status` as `"failed"` and commits.

- Triggered by `BackgroundTasks` from the `documents` router on document creation.

---

### 8. Schemas (Pydantic Models)

- **AI schemas** – `app/schemas/ai.py`:
  - `SummarizeRequest`, `SummarizeResponse`
  - `AskRequest`, `AskResponse`
  - `QuestionsRequest`, `QuestionsResponse`
- **Document schemas** – `app/schemas/document.py`:
  - `DocumentCreate` (filename, s3_key)
  - `DocumentRead` (id, project_id, filename, s3_key, status)
- **Project schemas** – `app/schemas/project.py`:
  - `ProjectCreate`
  - `ProjectRead`
  - `ProjectList` (wrapper around list of `ProjectRead`)

---

### 9. Current Status / TODOs (High-Level)

- **Implemented**:
  - Core architecture (routers, services, tasks, models, schemas).
  - Basic AWS integration patterns for Cognito, S3, Textract, Bedrock, OpenSearch.
  - Document ingestion + summarization + embedding pipeline.
  - Project/document CRUD stubs with auth dependency.

- **To harden for production** (future work):
  - Real JWT verification against Cognito JWKS.
  - Secure OpenSearch auth and index mapping definition.
  - CORS restrictions and rate limiting.
  - More robust error handling, logging, and monitoring.
  - Better text chunking and citation metadata in embeddings.
  - Completed implementations for project CRUD and collaboration features.

---