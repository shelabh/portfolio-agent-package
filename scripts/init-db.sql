-- Database initialization script for Portfolio Agent
-- This script sets up the necessary tables and extensions

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create documents table for vector storage
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1536), -- OpenAI embedding dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for efficient vector search
CREATE INDEX IF NOT EXISTS documents_embedding_idx 
ON documents USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Create index for metadata queries
CREATE INDEX IF NOT EXISTS documents_metadata_idx 
ON documents USING GIN (metadata);

-- Create users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create sessions table for user sessions
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_data JSONB DEFAULT '{}',
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create audit_logs table for security auditing
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type TEXT NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    resource TEXT,
    action TEXT,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for audit log queries
CREATE INDEX IF NOT EXISTS audit_logs_user_id_idx ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS audit_logs_event_type_idx ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS audit_logs_created_at_idx ON audit_logs(created_at);

-- Create consent_records table for GDPR/CCPA compliance
CREATE TABLE IF NOT EXISTS consent_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id TEXT NOT NULL,
    consent_type TEXT NOT NULL,
    data_categories TEXT[] NOT NULL,
    processing_purposes TEXT[] NOT NULL,
    granted BOOLEAN NOT NULL,
    granted_at TIMESTAMP WITH TIME ZONE,
    withdrawn_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    legal_basis TEXT,
    consent_method TEXT,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for consent queries
CREATE INDEX IF NOT EXISTS consent_records_subject_id_idx ON consent_records(subject_id);
CREATE INDEX IF NOT EXISTS consent_records_granted_idx ON consent_records(granted);
CREATE INDEX IF NOT EXISTS consent_records_expires_at_idx ON consent_records(expires_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON documents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_consent_records_updated_at 
    BEFORE UPDATE ON consent_records 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function for vector similarity search
CREATE OR REPLACE FUNCTION search_documents(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id TEXT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        documents.id,
        documents.content,
        documents.metadata,
        1 - (documents.embedding <=> query_embedding) AS similarity
    FROM documents
    WHERE 1 - (documents.embedding <=> query_embedding) > match_threshold
    ORDER BY documents.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Create function for hybrid search (vector + text)
CREATE OR REPLACE FUNCTION hybrid_search_documents(
    query_embedding VECTOR(1536),
    query_text TEXT,
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id TEXT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT,
    text_rank FLOAT
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        documents.id,
        documents.content,
        documents.metadata,
        1 - (documents.embedding <=> query_embedding) AS similarity,
        ts_rank(to_tsvector('english', documents.content), plainto_tsquery('english', query_text)) AS text_rank
    FROM documents
    WHERE 1 - (documents.embedding <=> query_embedding) > match_threshold
       OR to_tsvector('english', documents.content) @@ plainto_tsquery('english', query_text)
    ORDER BY 
        (1 - (documents.embedding <=> query_embedding)) * 0.7 + 
        ts_rank(to_tsvector('english', documents.content), plainto_tsquery('english', query_text)) * 0.3 DESC
    LIMIT match_count;
$$;

-- Create view for document statistics
CREATE OR REPLACE VIEW document_stats AS
SELECT
    COUNT(*) as total_documents,
    COUNT(DISTINCT (metadata->>'source')) as unique_sources,
    AVG(LENGTH(content)) as avg_content_length,
    MIN(created_at) as oldest_document,
    MAX(created_at) as newest_document
FROM documents;

-- Create view for user activity
CREATE OR REPLACE VIEW user_activity AS
SELECT
    u.id,
    u.email,
    u.name,
    COUNT(al.id) as total_events,
    MAX(al.created_at) as last_activity,
    COUNT(DISTINCT DATE(al.created_at)) as active_days
FROM users u
LEFT JOIN audit_logs al ON u.id = al.user_id
GROUP BY u.id, u.email, u.name;

-- Insert sample data for testing (optional)
-- INSERT INTO users (email, name) VALUES 
--     ('test@example.com', 'Test User'),
--     ('admin@example.com', 'Admin User');

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO portfolio;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO portfolio;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO portfolio;
