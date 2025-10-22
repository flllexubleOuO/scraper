-- Initialize database for job scraper
-- This script runs when the PostgreSQL container starts for the first time

-- Create database (already exists via POSTGRES_DB env var)
-- CREATE DATABASE job_scraper_db;

-- Create user (already exists via POSTGRES_USER env var)
-- CREATE USER scraper_user WITH PASSWORD 'scraper_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE job_scraper_db TO scraper_user;

-- Connect to the database
\c job_scraper_db;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO scraper_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO scraper_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO scraper_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO scraper_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO scraper_user;
