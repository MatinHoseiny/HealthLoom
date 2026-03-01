-- HealthLoom Database Schema
-- Version: 1.0.0
-- PostgreSQL 15+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- USERS TABLE
-- Stores user profiles and health preferences
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Basic Info
    name VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    
    -- Demographics
    age INTEGER CHECK (age > 0 AND age < 120),
    gender VARCHAR(20),
    
    -- Health Profile
    limitations_json JSONB DEFAULT '[]',
    conditions_json JSONB DEFAULT '[]',
    profile_data JSONB DEFAULT '{}',
    
    -- Preferences
    language_preference VARCHAR(10) DEFAULT 'en',
    
    -- Metadata (for future vector store integration)
    embedding_updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- =====================================================
-- TEST RESULTS TABLE
-- Stores all medical test data with AI analysis
-- =====================================================
CREATE TABLE IF NOT EXISTS test_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Test Identification
    test_name VARCHAR(255) NOT NULL,
    test_type_normalized VARCHAR(255),
    category VARCHAR(100),
    
    -- Test Values
    value VARCHAR(100),
    unit VARCHAR(50),
    reference_range VARCHAR(100),
    is_abnormal BOOLEAN DEFAULT false,
    
    -- Dates
    test_date DATE,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Source Information
    source_file_path TEXT,
    source_file_type VARCHAR(50),
    
    -- AI Analysis (stored as JSONB for flexibility)
    ai_analysis JSONB DEFAULT '{}',
    extracted_data JSONB DEFAULT '{}',
    
    -- Additional Data
    extra_data JSONB DEFAULT '{}'
);

CREATE INDEX idx_test_results_user_date ON test_results(user_id, test_date DESC);
CREATE INDEX idx_test_results_category ON test_results(category);
CREATE INDEX idx_test_results_normalized ON test_results(test_type_normalized);
CREATE INDEX idx_test_results_abnormal ON test_results(user_id, is_abnormal) WHERE is_abnormal = true;

-- =====================================================
-- MEDICATIONS TABLE
-- Tracks user medications with conflict detection
-- =====================================================
CREATE TABLE IF NOT EXISTS medications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Medication Details
    brand_name VARCHAR(255) NOT NULL,
    active_molecule VARCHAR(255),
    dosage VARCHAR(100),
    frequency VARCHAR(100),
    
    -- Timeline
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,
    
    -- Conflict Detection (AI-generated)
    conflict_data JSONB DEFAULT '{}',
    interactions JSONB DEFAULT '[]',
    
    -- Notes
    notes TEXT,
    
    -- Additional Data
    extra_data JSONB DEFAULT '{}'
);

CREATE INDEX idx_medications_user ON medications(user_id, is_active);
CREATE INDEX idx_medications_molecule ON medications(active_molecule);
CREATE INDEX idx_medications_dates ON medications(user_id, start_date, end_date);

-- =====================================================
-- SESSION STATES TABLE
-- Stores conversation session state for continuity
-- =====================================================
CREATE TABLE IF NOT EXISTS session_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Session Data
    session_json JSONB NOT NULL DEFAULT '{}',
    
    -- Session Metadata
    is_active BOOLEAN DEFAULT true,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_session_states_user ON session_states(user_id, is_active);
CREATE INDEX idx_session_states_activity ON session_states(last_activity DESC);

-- =====================================================
-- CONVERSATIONS TABLE
-- Stores all chat messages for memory and context
-- =====================================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES session_states(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Message Content
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    
    -- Context Used (what health data was referenced)
    context_used JSONB DEFAULT '{}',
    
    -- Additional Data
    token_count INTEGER,
    extra_data JSONB DEFAULT '{}'
);

CREATE INDEX idx_conversations_user ON conversations(user_id, created_at DESC);
CREATE INDEX idx_conversations_session ON conversations(session_id, created_at DESC);

-- =====================================================
-- TEST CATEGORIES TABLE
-- Predefined categories for test organization
-- =====================================================
CREATE TABLE IF NOT EXISTS test_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    icon_name VARCHAR(50),
    color_code VARCHAR(7),
    sort_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default categories
INSERT INTO test_categories (name, description, icon_name, color_code, sort_order) VALUES
    ('Blood Chemistry', 'Basic metabolic panel, glucose, electrolytes', 'blood_drop', '#e74c3c', 1),
    ('Lipid Profile', 'Cholesterol, triglycerides, HDL, LDL', 'heart', '#3498db', 2),
    ('Liver Function', 'ALT, AST, bilirubin, alkaline phosphatase', 'liver', '#f39c12', 3),
    ('Kidney Function', 'Creatinine, BUN, eGFR', 'kidney', '#9b59b6', 4),
    ('Thyroid', 'TSH, T3, T4', 'thyroid', '#1abc9c', 5),
    ('Vitamins', 'Vitamin D, B12, folate', 'vitamins', '#2ecc71', 6),
    ('Hormones', 'Testosterone, estrogen, cortisol', 'hormones', '#e91e63', 7),
    ('Complete Blood Count', 'RBC, WBC, platelets, hemoglobin', 'cells', '#c7254e', 8),
    ('Inflammation', 'CRP, ESR', 'inflammation', '#ff6b6b', 9),
    ('Other', 'Uncategorized tests', 'other', '#95a5a6', 99)
ON CONFLICT (name) DO NOTHING;

-- =====================================================
-- TRIGGERS
-- Auto-update timestamps
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_medications_updated_at
    BEFORE UPDATE ON medications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_session_states_updated_at
    BEFORE UPDATE ON session_states
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- COMMENTS
-- Documentation for future reference
-- =====================================================
COMMENT ON TABLE users IS 'User profiles with health information and preferences';
COMMENT ON TABLE test_results IS 'Medical test results with AI analysis and categorization';
COMMENT ON TABLE medications IS 'User medications with conflict detection data';
COMMENT ON TABLE session_states IS 'Conversation session state for continuity';
COMMENT ON TABLE conversations IS 'Chat message history with context tracking';
COMMENT ON TABLE test_categories IS 'Predefined categories for organizing test results';

COMMENT ON COLUMN users.embedding_updated_at IS 'Timestamp for vector store synchronization (future use)';
COMMENT ON COLUMN test_results.ai_analysis IS 'Full AI-generated analysis and insights';
COMMENT ON COLUMN medications.conflict_data IS 'AI-detected drug interactions and conflicts';
