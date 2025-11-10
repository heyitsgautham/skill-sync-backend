-- PostgreSQL Database Setup Script for SkillSync
-- Run this script to create the database and user

-- Create user (if not exists)
DO
$$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_user WHERE usename = 'gauthamkrishna'
   ) THEN
      CREATE USER gauthamkrishna WITH PASSWORD 'skillsync2024';
   END IF;
END
$$;

-- Create database
DROP DATABASE IF EXISTS skillsync;
CREATE DATABASE skillsync OWNER gauthamkrishna;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE skillsync TO gauthamkrishna;

-- Connect to the database and grant schema privileges
\c skillsync

-- Grant all privileges on public schema
GRANT ALL ON SCHEMA public TO gauthamkrishna;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO gauthamkrishna;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO gauthamkrishna;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO gauthamkrishna;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO gauthamkrishna;

-- Display success message
SELECT 'Database setup completed successfully!' AS status;
