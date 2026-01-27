#!/bin/bash
# PostgreSQL initialization script
# This script runs on first container startup to create required databases

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create the main application database (if not exists)
    SELECT 'CREATE DATABASE lender_matching'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'lender_matching')\gexec

    -- Create Hatchet database for workflow orchestration
    SELECT 'CREATE DATABASE hatchet'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'hatchet')\gexec

    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE lender_matching TO postgres;
    GRANT ALL PRIVILEGES ON DATABASE hatchet TO postgres;
EOSQL

echo "Database initialization complete!"
