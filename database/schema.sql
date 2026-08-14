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

COMMIT;
