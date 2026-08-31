-- ==============================================================================
-- SAGAR / ORCA Marine AI — Complete Supabase Database Schema
-- Run this script in the Supabase SQL Editor: Dashboard > SQL Editor > New query
-- ==============================================================================

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ------------------------------------------------------------------------------
-- 1. Users Table (Profile & Preferences)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supabase_uid TEXT UNIQUE,
    email TEXT,
    name TEXT,
    preferred_language TEXT DEFAULT 'en',
    home_port TEXT,
    vessel_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 2. Vessels Table (Physical Specs & Safety Constants)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.vessels (
    id TEXT PRIMARY KEY,
    vessel_id TEXT,
    user_id UUID REFERENCES public.users(user_id) ON DELETE SET NULL,
    vessel_type TEXT DEFAULT 'mechanized_trawler',
    name TEXT,
    beam_width_m FLOAT NOT NULL DEFAULT 3.5,
    length_m FLOAT DEFAULT 10.0,
    cruising_speed_kmh FLOAT DEFAULT 15.0,
    has_ais BOOLEAN DEFAULT FALSE,
    engine_power_hp FLOAT,
    draft_m FLOAT DEFAULT 1.5,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 3. Trips Table (Fishing Trip Records)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.trips (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES public.users(user_id) ON DELETE SET NULL,
    vessel_id TEXT,
    origin TEXT,
    origin_lat FLOAT,
    origin_lon FLOAT,
    destination_type TEXT DEFAULT 'NEAREST_PFZ',
    destination_lat FLOAT,
    destination_lon FLOAT,
    departure_time TIMESTAMPTZ,
    expected_return_time TIMESTAMPTZ,
    fishing_duration_hours FLOAT DEFAULT 6.0,
    status TEXT DEFAULT 'PLANNED',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 4. Assessments Table (Top-level LangGraph Assessment Runs)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.assessments (
    assessment_id TEXT PRIMARY KEY,
    trip_id TEXT,
    origin TEXT,
    departure_time TEXT,
    language TEXT DEFAULT 'en',
    overall_risk_level TEXT,
    workflow_status TEXT,
    task_plan JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 5. Risk Evidence Table (Deterministic SVAS & Safety Rule Outputs)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.risk_evidence (
    id BIGSERIAL PRIMARY KEY,
    assessment_id TEXT REFERENCES public.assessments(assessment_id) ON DELETE CASCADE,
    trip_id TEXT,
    advisory_category TEXT,
    risk_level TEXT,
    summary TEXT,
    evidence_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 6. Weather Evidence Table (Spatio-Temporal Weather Observations)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.weather_evidence (
    id BIGSERIAL PRIMARY KEY,
    assessment_id TEXT REFERENCES public.assessments(assessment_id) ON DELETE CASCADE,
    trip_id TEXT,
    waypoint_index INT,
    lat FLOAT,
    lon FLOAT,
    time_iso TEXT,
    weather_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 7. Marine Evidence Table (SST, Chlorophyll, HABs, Currents)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.marine_evidence (
    id BIGSERIAL PRIMARY KEY,
    assessment_id TEXT REFERENCES public.assessments(assessment_id) ON DELETE CASCADE,
    trip_id TEXT,
    lat FLOAT,
    lon FLOAT,
    marine_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 8. Advisories Table (Synthesized Multilingual Advisories)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.advisories (
    id BIGSERIAL PRIMARY KEY,
    assessment_id TEXT REFERENCES public.assessments(assessment_id) ON DELETE CASCADE,
    trip_id TEXT,
    advisory_category TEXT,
    recommendation_text TEXT,
    reason TEXT,
    language TEXT DEFAULT 'en',
    translation_provider TEXT,
    evidence_summary TEXT,
    disclaimer TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 9. Agent Executions Table (Audit & Provenance Trail)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.agent_executions (
    id BIGSERIAL PRIMARY KEY,
    assessment_id TEXT REFERENCES public.assessments(assessment_id) ON DELETE CASCADE,
    trip_id TEXT,
    agent_name TEXT,
    status TEXT,
    started_at TEXT,
    completed_at TEXT,
    data_sources JSONB,
    output_summary TEXT,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 10. Reports Table (Structured Assessment Reports)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.reports (
    id BIGSERIAL PRIMARY KEY,
    assessment_id TEXT REFERENCES public.assessments(assessment_id) ON DELETE CASCADE,
    trip_id TEXT,
    summary TEXT,
    recommendation TEXT,
    report_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 11. Evidence Registry Table (Granular Evidence Tracking)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.evidence_registry (
    id BIGSERIAL PRIMARY KEY,
    assessment_id TEXT REFERENCES public.assessments(assessment_id) ON DELETE CASCADE,
    evidence_id TEXT,
    category TEXT,
    value TEXT,
    unit TEXT,
    source TEXT,
    agent TEXT,
    lat FLOAT,
    lon FLOAT,
    confidence FLOAT,
    timestamp TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 12. Knowledge Chunks Table & Search Function (pgvector for RAG Copilot)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vector similarity search RPC function for LangChain/pgvector
CREATE OR REPLACE FUNCTION match_knowledge_chunks(
    query_embedding vector(768),
    match_count int DEFAULT 5,
    filter jsonb DEFAULT '{}'::jsonb
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        knowledge_chunks.id,
        knowledge_chunks.content,
        knowledge_chunks.metadata,
        1 - (knowledge_chunks.embedding <=> query_embedding) AS similarity
    FROM knowledge_chunks
    WHERE (filter = '{}'::jsonb OR knowledge_chunks.metadata @> filter)
    ORDER BY knowledge_chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ------------------------------------------------------------------------------
-- 13. Enable Row Level Security (RLS) & Development Policies
-- ------------------------------------------------------------------------------
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vessels ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trips ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.risk_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.weather_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.marine_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.advisories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evidence_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_chunks ENABLE ROW LEVEL SECURITY;

-- Allow read/write for authenticated users and service_role
CREATE POLICY "Allow all access to service_role" ON public.users FOR ALL TO service_role USING (true);
CREATE POLICY "Allow all access to service_role" ON public.vessels FOR ALL TO service_role USING (true);
CREATE POLICY "Allow all access to service_role" ON public.trips FOR ALL TO service_role USING (true);
CREATE POLICY "Allow all access to service_role" ON public.assessments FOR ALL TO service_role USING (true);
CREATE POLICY "Allow all access to service_role" ON public.risk_evidence FOR ALL TO service_role USING (true);
CREATE POLICY "Allow all access to service_role" ON public.weather_evidence FOR ALL TO service_role USING (true);
CREATE POLICY "Allow all access to service_role" ON public.marine_evidence FOR ALL TO service_role USING (true);
CREATE POLICY "Allow all access to service_role" ON public.advisories FOR ALL TO service_role USING (true);
CREATE POLICY "Allow all access to service_role" ON public.agent_executions FOR ALL TO service_role USING (true);
CREATE POLICY "Allow all access to service_role" ON public.reports FOR ALL TO service_role USING (true);
CREATE POLICY "Allow all access to service_role" ON public.evidence_registry FOR ALL TO service_role USING (true);
CREATE POLICY "Allow all access to service_role" ON public.knowledge_chunks FOR ALL TO service_role USING (true);

-- Allow public/anon read access for development and demo
CREATE POLICY "Allow anon read" ON public.assessments FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon read" ON public.advisories FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon read" ON public.risk_evidence FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon read" ON public.weather_evidence FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon read" ON public.marine_evidence FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon read" ON public.knowledge_chunks FOR SELECT TO anon USING (true);

