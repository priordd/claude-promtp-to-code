-- Datadog Database Monitoring Setup for PostgreSQL
-- This script sets up the necessary users and permissions for Datadog DBM

-- Create extension for query statistics (if not exists)
-- Note: This MUST be created as superuser before creating the datadog user
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Create Datadog monitoring user
CREATE USER datadog WITH PASSWORD 'datadog_password';

-- Grant necessary permissions for database monitoring
GRANT pg_monitor TO datadog;
GRANT SELECT ON pg_stat_database TO datadog;

-- For PostgreSQL 10+, grant permissions to read query statistics
GRANT SELECT ON pg_stat_statements TO datadog;

-- Grant permissions to read database and table statistics
GRANT SELECT ON pg_stat_user_tables TO datadog;
GRANT SELECT ON pg_stat_user_indexes TO datadog;

-- Grant permissions to read slow query logs and other performance data
GRANT SELECT ON pg_statio_user_tables TO datadog;
GRANT SELECT ON pg_statio_user_indexes TO datadog;

-- Grant permissions for connection and activity monitoring
GRANT SELECT ON pg_stat_activity TO datadog;
GRANT SELECT ON pg_stat_replication TO datadog;

-- Grant permissions for lock monitoring
GRANT SELECT ON pg_locks TO datadog;

-- Grant permissions for background writer and checkpointer stats
GRANT SELECT ON pg_stat_bgwriter TO datadog;
GRANT SELECT ON pg_stat_wal_receiver TO datadog;

-- For table size monitoring
GRANT SELECT ON pg_class TO datadog;
GRANT SELECT ON pg_namespace TO datadog;

-- Extension already created above as superuser

-- Create datadog schema for execution plan collection
CREATE SCHEMA IF NOT EXISTS datadog;
GRANT USAGE ON SCHEMA datadog TO datadog;
GRANT CREATE ON SCHEMA datadog TO datadog;

-- Grant access to application tables for custom queries
-- Use conditional grants since tables might not exist yet
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'transactions') THEN
        GRANT SELECT ON transactions TO datadog;
    END IF;
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'refunds') THEN
        GRANT SELECT ON refunds TO datadog;
    END IF;
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'payment_methods') THEN
        GRANT SELECT ON payment_methods TO datadog;
    END IF;
END $$;

-- Grant access to audit logs if they exist
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'audit_logs') THEN
        GRANT SELECT ON audit_logs TO datadog;
    END IF;
END $$;

-- Verify the user has the correct permissions
\echo 'Datadog user permissions granted successfully'
\echo 'User: datadog'
\echo 'Password: datadog_password'
\echo 'Extensions created: pg_stat_statements'
\echo 'Schema created: datadog'
\echo 'Application table access granted'