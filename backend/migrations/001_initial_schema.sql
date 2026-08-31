-- =============================================================================
-- SAGAR- Complete Database Schema Migration
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enable pgvector for semantic knowledge retrieval if available
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS vector;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'pgvector extension not installed or not supported in this environment.';
END $$;

-- -----------------------------------------------------------------------------
-- 1. Users Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supabase_uid VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    name VARCHAR(255),
    preferred_language VARCHAR(10) DEFAULT 'en',
    home_port VARCHAR(255),
    vessel_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_supabase_uid ON users(supabase_uid);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- -----------------------------------------------------------------------------
-- 2. Assessments Table (Top-level workflow runs)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS assessments (
    assessment_id TEXT PRIMARY KEY,
    trip_id TEXT NOT NULL,
    origin TEXT,
    departure_time TEXT,
    language VARCHAR(10) DEFAULT 'en',
    overall_risk_level VARCHAR(50),
    workflow_status VARCHAR(50),
    task_plan JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_assessments_trip_id ON assessments(trip_id);
CREATE INDEX IF NOT EXISTS idx_assessments_risk_level ON assessments(overall_risk_level);
CREATE INDEX IF NOT EXISTS idx_assessments_created_at ON assessments(created_at DESC);

-- -----------------------------------------------------------------------------
-- 3. Risk Evidence Table (Deterministic risk evaluations)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS risk_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id TEXT REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    trip_id TEXT NOT NULL,
    advisory_category TEXT,
    risk_level VARCHAR(50),
    summary TEXT,
    evidence_json JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_risk_evidence_assessment_id ON risk_evidence(assessment_id);
CREATE INDEX IF NOT EXISTS idx_risk_evidence_trip_id ON risk_evidence(trip_id);

-- -----------------------------------------------------------------------------
-- 4. Weather Evidence Table (Waypoint atmospheric observations)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS weather_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id TEXT REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    trip_id TEXT NOT NULL,
    waypoint_index INTEGER,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    time_iso TEXT,
    weather_json JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_weather_evidence_assessment ON weather_evidence(assessment_id);

-- -----------------------------------------------------------------------------
-- 5. Marine Evidence Table (SST, Chlorophyll, HAB, Currents)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marine_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id TEXT REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    trip_id TEXT NOT NULL,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    marine_json JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_marine_evidence_assessment ON marine_evidence(assessment_id);

-- -----------------------------------------------------------------------------
-- 6. Advisories Table (Synthesized advisories with translation)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS advisories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id TEXT REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    trip_id TEXT NOT NULL,
    advisory_category TEXT,
    recommendation_text TEXT,
    reason TEXT,
    language VARCHAR(10) DEFAULT 'en',
    translation_provider VARCHAR(50),
    evidence_summary TEXT,
    disclaimer TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_advisories_assessment ON advisories(assessment_id);

-- -----------------------------------------------------------------------------
-- 7. Agent Executions Table (Traceability & provenance)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id TEXT REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    trip_id TEXT NOT NULL,
    agent_name VARCHAR(100),
    status VARCHAR(50),
    started_at TEXT,
    completed_at TEXT,
    data_sources JSONB,
    output_summary TEXT,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_executions_assessment ON agent_executions(assessment_id);

-- -----------------------------------------------------------------------------
-- 8. Reports Table (Structured reports for fishermen)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id TEXT REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    trip_id TEXT NOT NULL,
    summary TEXT,
    recommendation TEXT,
    report_json JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reports_assessment ON reports(assessment_id);

-- -----------------------------------------------------------------------------
-- 9. Evidence Registry Table (Item-level evidence provenance)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS evidence_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id TEXT REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    evidence_id TEXT,
    category VARCHAR(50),
    value TEXT,
    unit VARCHAR(50),
    source VARCHAR(100),
    agent VARCHAR(100),
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    confidence DOUBLE PRECISION,
    timestamp TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evidence_registry_assessment ON evidence_registry(assessment_id);

-- -----------------------------------------------------------------------------
-- 10. Knowledge Chunks Table & RPC Search (pgvector RAG for Copilot)
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        CREATE TABLE IF NOT EXISTS knowledge_chunks (
            id BIGSERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            metadata JSONB,
            embedding vector(768)
        );

        CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding
            ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);

        -- Function for LangChain SupabaseVectorStore similarity search
        CREATE OR REPLACE FUNCTION match_knowledge_chunks (
            query_embedding vector(768),
            match_count int DEFAULT 5,
            filter jsonb DEFAULT '{}'::jsonb
        )
        RETURNS TABLE (
            id bigint,
            content text,
            metadata jsonb,
            similarity float
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT
                kc.id,
                kc.content,
                kc.metadata,
                1 - (kc.embedding <=> query_embedding) AS similarity
            FROM knowledge_chunks kc
            WHERE (filter = '{}'::jsonb OR kc.metadata @> filter)
            ORDER BY kc.embedding <=> query_embedding
            LIMIT match_count;
        END;
        $$;
    ELSE
        -- Fallback table if vector extension is not available
        CREATE TABLE IF NOT EXISTS knowledge_chunks (
            id BIGSERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            metadata JSONB
        );
    END IF;
END $$;

