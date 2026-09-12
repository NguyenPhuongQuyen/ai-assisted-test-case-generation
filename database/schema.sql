BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001_week05_baseline

CREATE TYPE user_role AS ENUM ('qa', 'manager', 'admin');

CREATE TABLE users (
    id SERIAL NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL,
    failed_login_attempts INTEGER DEFAULT '0' NOT NULL,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_users_email UNIQUE (email)
);

CREATE INDEX ix_users_email ON users (email);

CREATE INDEX ix_users_role ON users (role);

CREATE TABLE modules (
    id SERIAL NOT NULL,
    name VARCHAR(150) NOT NULL,
    parent_id INTEGER,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(parent_id) REFERENCES modules (id) ON DELETE SET NULL,
    FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_modules_created_by ON modules (created_by);

CREATE TABLE requirements (
    id SERIAL NOT NULL,
    module_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    acceptance_criteria TEXT,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(module_id) REFERENCES modules (id) ON DELETE RESTRICT,
    FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_requirements_module_id ON requirements (module_id);

CREATE INDEX ix_requirements_created_by ON requirements (created_by);

CREATE TYPE test_case_priority AS ENUM ('high', 'medium', 'low');

CREATE TYPE test_case_status AS ENUM ('draft', 'in_review', 'needs_fix', 'approved', 'exported', 'rejected');

CREATE TABLE test_cases (
    id SERIAL NOT NULL,
    requirement_id INTEGER NOT NULL,
    module_id INTEGER NOT NULL,
    summary VARCHAR(300) NOT NULL,
    preconditions JSON NOT NULL,
    steps JSON NOT NULL,
    expected_result TEXT NOT NULL,
    priority test_case_priority NOT NULL,
    test_techniques JSON NOT NULL,
    review_note TEXT,
    status test_case_status NOT NULL,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(requirement_id) REFERENCES requirements (id) ON DELETE RESTRICT,
    FOREIGN KEY(module_id) REFERENCES modules (id) ON DELETE RESTRICT,
    FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_test_cases_requirement_id ON test_cases (requirement_id);

CREATE INDEX ix_test_cases_module_id ON test_cases (module_id);

CREATE INDEX ix_test_cases_status ON test_cases (status);

CREATE INDEX ix_test_cases_created_by ON test_cases (created_by);

CREATE TYPE audit_action AS ENUM ('generate_test_cases');

CREATE TABLE audit_logs (
    id SERIAL NOT NULL,
    user_id INTEGER NOT NULL,
    action audit_action NOT NULL,
    entity_type VARCHAR(80) NOT NULL,
    entity_id INTEGER NOT NULL,
    before_state JSON,
    after_state JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id);

CREATE INDEX ix_audit_logs_action ON audit_logs (action);

CREATE INDEX ix_audit_logs_entity_id ON audit_logs (entity_id);

CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at);

INSERT INTO alembic_version (version_num) VALUES ('0001_week05_baseline') RETURNING alembic_version.version_num;

-- Running upgrade 0001_week05_baseline -> 0002_week06_generation_jobs

CREATE TYPE generation_job_status AS ENUM ('queued', 'running', 'completed', 'failed');

CREATE TABLE generation_jobs (
    id SERIAL NOT NULL,
    requirement_id INTEGER NOT NULL,
    created_by INTEGER NOT NULL,
    status generation_job_status NOT NULL,
    error_code VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE RESTRICT,
    FOREIGN KEY(requirement_id) REFERENCES requirements (id) ON DELETE RESTRICT
);

CREATE INDEX ix_generation_jobs_requirement_id ON generation_jobs (requirement_id);

CREATE INDEX ix_generation_jobs_created_by ON generation_jobs (created_by);

CREATE INDEX ix_generation_jobs_status ON generation_jobs (status);

UPDATE alembic_version SET version_num='0002_week06_generation_jobs' WHERE alembic_version.version_num = '0001_week05_baseline';

-- Running upgrade 0002_week06_generation_jobs -> 0003_week07_hitl_review

ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'edit_test_case';

ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'submit_test_case_review';

ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'request_test_case_fix';

ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'approve_test_case';

ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'reject_test_case';

ALTER TABLE test_cases ADD COLUMN lock_version INTEGER DEFAULT '1' NOT NULL;

CREATE TABLE test_case_versions (
    id SERIAL NOT NULL,
    test_case_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    snapshot JSON NOT NULL,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_test_case_versions_case_number UNIQUE (test_case_id, version_number),
    FOREIGN KEY(test_case_id) REFERENCES test_cases (id) ON DELETE RESTRICT,
    FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_test_case_versions_test_case_id ON test_case_versions (test_case_id);

CREATE INDEX ix_test_case_versions_created_by ON test_case_versions (created_by);

CREATE INDEX ix_test_case_versions_created_at ON test_case_versions (created_at);

INSERT INTO test_case_versions (test_case_id, version_number, snapshot, created_by)
            SELECT id, 1,
                json_build_object(
                    'summary', summary, 'preconditions', preconditions, 'steps', steps,
                    'expected_result', expected_result, 'priority', priority::text,
                    'test_techniques', test_techniques, 'review_note', review_note,
                    'status', status::text, 'lock_version', lock_version,
                    'requirement_id', requirement_id, 'module_id', module_id
                ),
                created_by
            FROM test_cases;

UPDATE alembic_version SET version_num='0003_week07_hitl_review' WHERE alembic_version.version_num = '0002_week06_generation_jobs';

-- Running upgrade 0003_week07_hitl_review -> 0004_week07_pgvector_duplicates

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE test_cases ADD COLUMN embedding vector(1536);

CREATE INDEX ix_test_cases_embedding_hnsw ON test_cases USING hnsw (embedding vector_cosine_ops) WHERE embedding IS NOT NULL;

UPDATE alembic_version SET version_num='0004_week07_pgvector_duplicates' WHERE alembic_version.version_num = '0003_week07_hitl_review';

-- Running upgrade 0004_week07_pgvector_duplicates -> 0005_week07_test_case_export

ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'export_test_cases';

UPDATE alembic_version SET version_num='0005_week07_test_case_export' WHERE alembic_version.version_num = '0004_week07_pgvector_duplicates';

-- Running upgrade 0005_week07_test_case_export -> 0006_week07_module_coverage

ALTER TABLE test_cases ADD COLUMN tags JSON DEFAULT '[]'::json NOT NULL;

ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'create_module';

ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'update_module';

ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'tag_test_case';

UPDATE alembic_version SET version_num='0006_week07_module_coverage' WHERE alembic_version.version_num = '0005_week07_test_case_export';

-- Running upgrade 0006_week07_module_coverage -> 0007_week07_prompt_configuration

ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'create_prompt_config';

CREATE TABLE prompt_configs (
    id SERIAL NOT NULL,
    version_number INTEGER NOT NULL,
    name VARCHAR(120) NOT NULL,
    system_prompt TEXT NOT NULL,
    user_prompt_template TEXT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    schema_version VARCHAR(50) NOT NULL,
    max_output_tokens INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_by INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (version_number),
    FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX uq_prompt_configs_active ON prompt_configs (is_active) WHERE is_active;

INSERT INTO prompt_configs (version_number, name, system_prompt, user_prompt_template, model_name, schema_version, max_output_tokens, is_active, created_by) VALUES (1, 'Default', 'Bạn là Senior QA Engineer. Tạo test case có cấu trúc để con người rà soát. Đầu ra AI luôn là bản nháp và không tự phê duyệt.', 'Sinh test case từ requirement sau. Bao phủ happy path, negative scenarios, BVA/EP khi phù hợp. Không bịa quy tắc không có trong requirement; mọi giả định phải ghi vào review_note.

Requirement:
{requirement_text}

Acceptance Criteria:
{acceptance_criteria}', 'gpt-5', 'test-case-v1', 4000, true, NULL);

UPDATE alembic_version SET version_num='0007_week07_prompt_configuration' WHERE alembic_version.version_num = '0006_week07_module_coverage';

-- Running upgrade 0007_week07_prompt_configuration -> 0008_nc08_version_restore

ALTER TABLE requirements ADD COLUMN lock_version INTEGER DEFAULT '1' NOT NULL;

ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'create_requirement';

ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'update_requirement';

ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'restore_test_case';

UPDATE alembic_version SET version_num='0008_nc08_version_restore' WHERE alembic_version.version_num = '0007_week07_prompt_configuration';

-- Running upgrade 0008_nc08_version_restore -> 0009_nc10_user_admin

ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT true NOT NULL;

ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'create_user';

ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'update_user';

UPDATE alembic_version SET version_num='0009_nc10_user_admin' WHERE alembic_version.version_num = '0008_nc08_version_restore';

-- Running upgrade 0009_nc10_user_admin -> 0010_module_name_unique

CREATE UNIQUE INDEX uq_modules_root_name_ci
ON modules (lower(name))
WHERE parent_id IS NULL;

CREATE UNIQUE INDEX uq_modules_parent_name_ci
ON modules (parent_id, lower(name))
WHERE parent_id IS NOT NULL;

UPDATE alembic_version SET version_num='0010_module_name_unique'
WHERE alembic_version.version_num = '0009_nc10_user_admin';

COMMIT;
