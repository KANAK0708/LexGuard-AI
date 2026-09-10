-- PostgreSQL DDL Schema for Supabase (LexGuard AI)

CREATE TABLE IF NOT EXISTS contracts (
    doc_id VARCHAR(255) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    full_text TEXT NOT NULL,
    entity_map JSONB DEFAULT '{}'::jsonb,
    parser_mode VARCHAR(50) DEFAULT 'layout',
    role VARCHAR(50) DEFAULT 'Client',
    content_hash VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clauses (
    id SERIAL PRIMARY KEY,
    doc_id VARCHAR(255) REFERENCES contracts(doc_id) ON DELETE CASCADE,
    clause_id VARCHAR(100) NOT NULL,
    text TEXT NOT NULL,
    masked_text TEXT,
    category VARCHAR(100),
    confidence VARCHAR(20) DEFAULT 'high',
    risk_score NUMERIC(5, 3),
    role_weights_applied JSONB DEFAULT '{}'::jsonb,
    char_span JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS llm_claims (
    id SERIAL PRIMARY KEY,
    clause_db_id INTEGER REFERENCES clauses(id) ON DELETE CASCADE,
    doc_id VARCHAR(255) REFERENCES contracts(doc_id) ON DELETE CASCADE,
    quoted_text TEXT NOT NULL,
    explanation TEXT,
    claim_type VARCHAR(50) DEFAULT 'risk',
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS drift_comparisons (
    id SERIAL PRIMARY KEY,
    left_doc_id VARCHAR(255) REFERENCES contracts(doc_id) ON DELETE CASCADE,
    right_doc_id VARCHAR(255) REFERENCES contracts(doc_id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'Client',
    drift_results JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
