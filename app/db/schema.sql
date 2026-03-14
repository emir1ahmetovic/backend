CREATE EXTENSION IF NOT EXISTS "uuid-ossp";     
CREATE EXTENSION IF NOT EXISTS "pgvector";     


CREATE TYPE project_status AS ENUM (
    'active',
    'archived',
    'deleted'
);


CREATE TYPE project_role AS ENUM (
    'owner',
    'admin',
    'editor',
    'viewer'
);

CREATE TYPE invitation_status AS ENUM (
    'pending',
    'accepted',
    'declined',
    'expired',
    'revoked'
);

CREATE TYPE file_type AS ENUM (
    'pdf',
    'docx',
    'pptx',
    'txt',
    'md'
);

CREATE TYPE processing_status AS ENUM (
    'pending',
    'processing',
    'completed',
    'failed'
);

CREATE TYPE embedding_status AS ENUM (
    'pending',
    'generating',
    'completed',
    'failed'
);

CREATE TYPE summary_type AS ENUM (
    'brief',
    'detailed',
    'comprehensive',
    'custom'
);

CREATE TYPE difficulty_level AS ENUM (
    'easy',
    'medium',
    'hard',
    'expert'
);

CREATE TYPE message_role AS ENUM (
    'user',
    'assistant',
    'system'
);


CREATE TABLE users (
    user_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email               VARCHAR(255) NOT NULL,
    password_hash       VARCHAR(255) NOT NULL,
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    avatar_url          VARCHAR(512),
    is_email_verified   BOOLEAN NOT NULL DEFAULT FALSE,
    verification_token  VARCHAR(255),
    reset_password_token VARCHAR(255),
    last_login_at       TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT chk_users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);


CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_verification_token ON users (verification_token) WHERE verification_token IS NOT NULL;
CREATE INDEX idx_users_reset_password_token ON users (reset_password_token) WHERE reset_password_token IS NOT NULL;

COMMENT ON TABLE users IS 'Core user accounts with authentication credentials and profile information';
COMMENT ON COLUMN users.password_hash IS 'BCrypt hashed password (cost factor 12)';
COMMENT ON COLUMN users.verification_token IS 'One-time token for email verification workflow';

CREATE TABLE projects (
    project_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id            UUID NOT NULL,
    project_name        VARCHAR(255) NOT NULL,
    project_description VARCHAR(2000),
    project_status      TEXT,
    status              project_status NOT NULL DEFAULT 'active',
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at          TIMESTAMP WITH TIME ZONE,

    CONSTRAINT fk_projects_owner FOREIGN KEY (owner_id)
        REFERENCES users (user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_projects_name_length CHECK (char_length(project_name) >= 1)
);

CREATE INDEX idx_projects_owner_id ON projects (owner_id);
CREATE INDEX idx_projects_status ON projects (status) WHERE status = 'active';
CREATE INDEX idx_projects_deleted_at ON projects (deleted_at) WHERE deleted_at IS NULL;

COMMENT ON TABLE projects IS 'Study projects that organize materials, summaries, and AI interactions';
COMMENT ON COLUMN projects.deleted_at IS 'Soft delete timestamp; NULL indicates active record';

CREATE TABLE project_members (
    project_member_id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id          UUID NOT NULL,
    user_id             UUID NOT NULL,
    invited_by          UUID,
    role                project_role NOT NULL DEFAULT 'viewer',
    joined_at           TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_project_members_project FOREIGN KEY (project_id)
        REFERENCES projects (project_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_project_members_user FOREIGN KEY (user_id)
        REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_project_members_invited_by FOREIGN KEY (invited_by)
        REFERENCES users (user_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT uq_project_members_user_project UNIQUE (project_id, user_id)
);

CREATE INDEX idx_project_members_project_id ON project_members (project_id);
CREATE INDEX idx_project_members_user_id ON project_members (user_id);
CREATE INDEX idx_project_members_role ON project_members (role);

COMMENT ON TABLE project_members IS 'Project membership with role-based access control (RBAC)';

CREATE TABLE project_invitations (
    project_invitation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id            UUID NOT NULL,
    invited_by            UUID NOT NULL,
    invited_email         VARCHAR(255) NOT NULL,
    token                 VARCHAR(255) NOT NULL,
    status                invitation_status NOT NULL DEFAULT 'pending',
    expires_at            TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    responded_at          TIMESTAMP WITH TIME ZONE,

    CONSTRAINT fk_project_invitations_project FOREIGN KEY (project_id)
        REFERENCES projects (project_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_project_invitations_invited_by FOREIGN KEY (invited_by)
        REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_project_invitations_token UNIQUE (token),
    CONSTRAINT chk_project_invitations_expiry CHECK (expires_at > created_at)
);

CREATE INDEX idx_project_invitations_token ON project_invitations (token);
CREATE INDEX idx_project_invitations_email ON project_invitations (invited_email);
CREATE INDEX idx_project_invitations_status ON project_invitations (status) WHERE status = 'pending';

COMMENT ON TABLE project_invitations IS 'Email-based invitation workflow for project collaboration';



CREATE TABLE materials (
    material_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id          UUID NOT NULL,
    uploaded_by         UUID NOT NULL,
    original_file_name  VARCHAR(512) NOT NULL,
    file_type           file_type NOT NULL,
    s3_bucket           VARCHAR(255) NOT NULL,
    s3_key              VARCHAR(1024) NOT NULL,
    processing_status   processing_status NOT NULL DEFAULT 'pending',
    processing_error    TEXT,
    total_chunks        INTEGER DEFAULT 0,
    total_tokens        INTEGER DEFAULT 0,
    page_count          INTEGER DEFAULT 0,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at          TIMESTAMP WITH TIME ZONE,

    CONSTRAINT fk_materials_project FOREIGN KEY (project_id)
        REFERENCES projects (project_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_materials_uploaded_by FOREIGN KEY (uploaded_by)
        REFERENCES users (user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_materials_total_chunks CHECK (total_chunks >= 0),
    CONSTRAINT chk_materials_total_tokens CHECK (total_tokens >= 0),
    CONSTRAINT chk_materials_page_count CHECK (page_count >= 0)
);

CREATE INDEX idx_materials_project_id ON materials (project_id);
CREATE INDEX idx_materials_uploaded_by ON materials (uploaded_by);
CREATE INDEX idx_materials_processing_status ON materials (processing_status);
CREATE INDEX idx_materials_deleted_at ON materials (deleted_at) WHERE deleted_at IS NULL;

COMMENT ON TABLE materials IS 'Uploaded study materials stored in S3 with processing metadata';
COMMENT ON COLUMN materials.s3_bucket IS 'AWS S3 bucket name for object storage';
COMMENT ON COLUMN materials.s3_key IS 'AWS S3 object key (path) within the bucket';

CREATE TABLE material_chunks (
    material_chunk_id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    material_id         UUID NOT NULL,
    chunk_index         INTEGER NOT NULL,
    content             TEXT NOT NULL,
    token_count         INTEGER NOT NULL,
    page_number         INTEGER,
    slide_number        INTEGER,
    section_heading     VARCHAR(512),
    chunk_hash          VARCHAR(64) NOT NULL,
    embedding_id        VARCHAR(255),
    embedding_model     VARCHAR(100),
    embedding_status    embedding_status NOT NULL DEFAULT 'pending',
    embedding           vector(1536),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_material_chunks_material FOREIGN KEY (material_id)
        REFERENCES materials (material_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_material_chunks_material_index UNIQUE (material_id, chunk_index),
    CONSTRAINT chk_material_chunks_token_count CHECK (token_count > 0),
    CONSTRAINT chk_material_chunks_chunk_index CHECK (chunk_index >= 0)
);

CREATE INDEX idx_material_chunks_material_id ON material_chunks (material_id);
CREATE INDEX idx_material_chunks_embedding_status ON material_chunks (embedding_status);
CREATE INDEX idx_material_chunks_chunk_hash ON material_chunks (chunk_hash);

CREATE INDEX idx_material_chunks_embedding ON material_chunks 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

COMMENT ON TABLE material_chunks IS 'Semantically chunked text segments with vector embeddings for RAG retrieval';
COMMENT ON COLUMN material_chunks.chunk_hash IS 'SHA-256 hash for deduplication and change detection';
COMMENT ON COLUMN material_chunks.embedding IS 'Amazon Titan Embeddings vector (1536 dimensions)';



CREATE TABLE summaries (
    summary_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id          UUID NOT NULL,
    created_by          UUID NOT NULL,
    summary_title       VARCHAR(255) NOT NULL,
    summary_content     TEXT NOT NULL,
    summary_type        summary_type NOT NULL DEFAULT 'detailed',
    ai_model            VARCHAR(100) NOT NULL,
    prompt_tokens       INTEGER NOT NULL DEFAULT 0,
    completion_tokens   INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_summaries_project FOREIGN KEY (project_id)
        REFERENCES projects (project_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_summaries_created_by FOREIGN KEY (created_by)
        REFERENCES users (user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_summaries_prompt_tokens CHECK (prompt_tokens >= 0),
    CONSTRAINT chk_summaries_completion_tokens CHECK (completion_tokens >= 0)
);

CREATE INDEX idx_summaries_project_id ON summaries (project_id);
CREATE INDEX idx_summaries_created_by ON summaries (created_by);
CREATE INDEX idx_summaries_summary_type ON summaries (summary_type);

COMMENT ON TABLE summaries IS 'AI-generated summaries of project materials with token usage tracking';
COMMENT ON COLUMN summaries.ai_model IS 'AWS Bedrock model identifier (e.g., anthropic.claude-3-sonnet)';

CREATE TABLE summary_chunks (
    summary_id          UUID NOT NULL,
    chunk_id            UUID NOT NULL,
    relevance_score     REAL NOT NULL,
    chunk_order         INTEGER NOT NULL,

    CONSTRAINT pk_summary_chunks PRIMARY KEY (summary_id, chunk_id),
    CONSTRAINT fk_summary_chunks_summary FOREIGN KEY (summary_id)
        REFERENCES summaries (summary_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_summary_chunks_chunk FOREIGN KEY (chunk_id)
        REFERENCES material_chunks (material_chunk_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_summary_chunks_relevance CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0),
    CONSTRAINT chk_summary_chunks_order CHECK (chunk_order >= 0)
);

CREATE INDEX idx_summary_chunks_chunk_id ON summary_chunks (chunk_id);

COMMENT ON TABLE summary_chunks IS 'Junction table linking summaries to source material chunks for citation provenance';

CREATE TABLE key_concepts (
    key_concept_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id          UUID NOT NULL,
    created_by          UUID NOT NULL,
    concept_name        VARCHAR(255) NOT NULL,
    concept_definition  TEXT NOT NULL,
    concept_category    VARCHAR(100),
    ai_model            VARCHAR(100) NOT NULL,
    prompt_tokens       INTEGER NOT NULL DEFAULT 0,
    completion_tokens   INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_key_concepts_project FOREIGN KEY (project_id)
        REFERENCES projects (project_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_key_concepts_created_by FOREIGN KEY (created_by)
        REFERENCES users (user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_key_concepts_prompt_tokens CHECK (prompt_tokens >= 0),
    CONSTRAINT chk_key_concepts_completion_tokens CHECK (completion_tokens >= 0)
);

CREATE INDEX idx_key_concepts_project_id ON key_concepts (project_id);
CREATE INDEX idx_key_concepts_category ON key_concepts (concept_category);
CREATE INDEX idx_key_concepts_name ON key_concepts USING gin (to_tsvector('english', concept_name));

COMMENT ON TABLE key_concepts IS 'AI-extracted key concepts and terminology from study materials';


CREATE TABLE key_concept_chunks (
    key_concept_id      UUID NOT NULL,
    chunk_id            UUID NOT NULL,
    relevance_score     INTEGER NOT NULL,

    CONSTRAINT pk_key_concept_chunks PRIMARY KEY (key_concept_id, chunk_id),
    CONSTRAINT fk_key_concept_chunks_concept FOREIGN KEY (key_concept_id)
        REFERENCES key_concepts (key_concept_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_key_concept_chunks_chunk FOREIGN KEY (chunk_id)
        REFERENCES material_chunks (material_chunk_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_key_concept_chunks_relevance CHECK (relevance_score >= 0 AND relevance_score <= 100)
);

CREATE INDEX idx_key_concept_chunks_chunk_id ON key_concept_chunks (chunk_id);

COMMENT ON TABLE key_concept_chunks IS 'Junction table linking key concepts to source material chunks';

CREATE TABLE generated_questions (
    question_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id          UUID NOT NULL,
    created_by          UUID NOT NULL,
    question_text       TEXT NOT NULL,
    difficulty_level    difficulty_level NOT NULL DEFAULT 'medium',
    ai_model            VARCHAR(100) NOT NULL,
    prompt_tokens       INTEGER NOT NULL DEFAULT 0,
    completion_tokens   INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_generated_questions_project FOREIGN KEY (project_id)
        REFERENCES projects (project_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_generated_questions_created_by FOREIGN KEY (created_by)
        REFERENCES users (user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_generated_questions_prompt_tokens CHECK (prompt_tokens >= 0),
    CONSTRAINT chk_generated_questions_completion_tokens CHECK (completion_tokens >= 0)
);

CREATE INDEX idx_generated_questions_project_id ON generated_questions (project_id);
CREATE INDEX idx_generated_questions_difficulty ON generated_questions (difficulty_level);

COMMENT ON TABLE generated_questions IS 'AI-generated practice questions for self-assessment';

CREATE TABLE question_chunks (
    question_id         UUID NOT NULL,
    chunk_id            UUID NOT NULL,
    relevance_score     REAL NOT NULL,

    CONSTRAINT pk_question_chunks PRIMARY KEY (question_id, chunk_id),
    CONSTRAINT fk_question_chunks_question FOREIGN KEY (question_id)
        REFERENCES generated_questions (question_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_question_chunks_chunk FOREIGN KEY (chunk_id)
        REFERENCES material_chunks (material_chunk_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_question_chunks_relevance CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0)
);

CREATE INDEX idx_question_chunks_chunk_id ON question_chunks (chunk_id);

COMMENT ON TABLE question_chunks IS 'Junction table linking generated questions to source material chunks';




CREATE TABLE chat_messages (
    chat_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id          UUID NOT NULL,
    created_by          UUID NOT NULL,
    role                message_role NOT NULL,
    content             TEXT NOT NULL,
    token_count         INTEGER NOT NULL DEFAULT 0,
    is_error            BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_chat_messages_project FOREIGN KEY (project_id)
        REFERENCES projects (project_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_chat_messages_created_by FOREIGN KEY (created_by)
        REFERENCES users (user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_chat_messages_token_count CHECK (token_count >= 0)
);

CREATE INDEX idx_chat_messages_project_id ON chat_messages (project_id, created_at DESC);
CREATE INDEX idx_chat_messages_created_by ON chat_messages (created_by);

COMMENT ON TABLE chat_messages IS 'Conversational AI messages with role-based attribution';
COMMENT ON COLUMN chat_messages.is_error IS 'Flag indicating if the AI response resulted in an error';

CREATE TABLE chat_message_chunks (
    chat_id             UUID NOT NULL,
    chunk_id            UUID NOT NULL,
    relevance_score     INTEGER NOT NULL,
    was_used_in_prompt  BOOLEAN NOT NULL DEFAULT TRUE,
    chunk_order         INTEGER NOT NULL,

    CONSTRAINT pk_chat_message_chunks PRIMARY KEY (chat_id, chunk_id),
    CONSTRAINT fk_chat_message_chunks_chat FOREIGN KEY (chat_id)
        REFERENCES chat_messages (chat_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_chat_message_chunks_chunk FOREIGN KEY (chunk_id)
        REFERENCES material_chunks (material_chunk_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_chat_message_chunks_relevance CHECK (relevance_score >= 0 AND relevance_score <= 100),
    CONSTRAINT chk_chat_message_chunks_order CHECK (chunk_order >= 0)
);

CREATE INDEX idx_chat_message_chunks_chunk_id ON chat_message_chunks (chunk_id);

COMMENT ON TABLE chat_message_chunks IS 'Junction table tracking which chunks were retrieved for RAG context';
COMMENT ON COLUMN chat_message_chunks.was_used_in_prompt IS 'Indicates if chunk was included in final prompt (vs. retrieved but filtered)';

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_materials_updated_at
    BEFORE UPDATE ON materials
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_summaries_updated_at
    BEFORE UPDATE ON summaries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();



CREATE VIEW vw_active_projects AS
SELECT 
    p.project_id,
    p.project_name,
    p.project_description,
    p.owner_id,
    u.email AS owner_email,
    CONCAT(u.first_name, ' ', u.last_name) AS owner_name,
    COUNT(DISTINCT pm.user_id) AS member_count,
    COUNT(DISTINCT m.material_id) AS material_count,
    p.created_at,
    p.updated_at
FROM projects p
INNER JOIN users u ON p.owner_id = u.user_id
LEFT JOIN project_members pm ON p.project_id = pm.project_id
LEFT JOIN materials m ON p.project_id = m.project_id AND m.deleted_at IS NULL
WHERE p.status = 'active' AND p.deleted_at IS NULL
GROUP BY p.project_id, u.user_id;

COMMENT ON VIEW vw_active_projects IS 'Aggregated view of active projects with member and material counts';

CREATE VIEW vw_material_processing AS
SELECT 
    m.material_id,
    m.original_file_name,
    m.file_type,
    m.processing_status,
    m.total_chunks,
    m.total_tokens,
    COUNT(mc.material_chunk_id) AS processed_chunks,
    COUNT(CASE WHEN mc.embedding_status = 'completed' THEN 1 END) AS embedded_chunks,
    p.project_name,
    CONCAT(u.first_name, ' ', u.last_name) AS uploaded_by_name,
    m.created_at
FROM materials m
INNER JOIN projects p ON m.project_id = p.project_id
INNER JOIN users u ON m.uploaded_by = u.user_id
LEFT JOIN material_chunks mc ON m.material_id = mc.material_id
WHERE m.deleted_at IS NULL
GROUP BY m.material_id, p.project_name, u.first_name, u.last_name;

COMMENT ON VIEW vw_material_processing IS 'Material processing pipeline status with chunk/embedding progress';