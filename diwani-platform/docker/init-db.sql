-- ===================================
-- منصة ديواني - Database Initialization
-- Diwani Platform - PostgreSQL + PostGIS
-- ===================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create Arabic text search configuration
CREATE TEXT SEARCH CONFIGURATION IF NOT EXISTS arabic (COPY = simple);

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE diwani_db TO diwani_user;

-- Performance optimizations for development
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '128MB';
ALTER SYSTEM SET effective_cache_size = '512MB';
ALTER SYSTEM SET random_page_cost = 1.1;

-- Enable query logging for debugging (development only)
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_duration = on;

-- Reload configuration
SELECT pg_reload_conf();

-- Verify PostGIS installation
SELECT PostGIS_Full_Version();

-- Create helpful functions
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Diwani Database initialized successfully!';
    RAISE NOTICE '📍 PostGIS extension enabled';
    RAISE NOTICE '🔤 Arabic text search configured';
END $$;
