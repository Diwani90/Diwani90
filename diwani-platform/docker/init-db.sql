-- ===================================
-- منصة ديواني - Database Initialization
-- PostgreSQL + PostGIS Setup
-- ===================================

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable full-text search for Arabic
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Create custom text search configuration for Arabic
-- This helps with Arabic text search

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE diwani_db TO diwani_user;
GRANT ALL ON SCHEMA public TO diwani_user;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Diwani Database initialized successfully with PostGIS support!';
END $$;
