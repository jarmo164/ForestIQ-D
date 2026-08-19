#!/bin/bash

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  CREATE EXTENSION IF NOT EXISTS hstore;
  CREATE EXTENSION IF NOT EXISTS pgcrypto;

  REVOKE ALL ON DATABASE $POSTGRES_DB FROM PUBLIC;

  -- Common role for read/write actions
  CREATE ROLE readwrite;
  GRANT CONNECT ON DATABASE $POSTGRES_DB TO readwrite;
  GRANT USAGE ON SCHEMA public TO readwrite;

  -- Alter privileges for existing objects
  GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO readwrite;
  GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO readwrite;

  -- App user can read/write
  CREATE USER app WITH PASSWORD 'app' CREATEROLE;
  GRANT readwrite TO app;

  CREATE USER liquibase WITH PASSWORD 'liquibase' SUPERUSER;

  SET ROLE = 'liquibase';

  -- Alter privileges for future objects
  ALTER DEFAULT PRIVILEGES FOR ROLE liquibase IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO readwrite;
  ALTER DEFAULT PRIVILEGES FOR ROLE liquibase IN SCHEMA public GRANT USAGE ON SEQUENCES TO readwrite;
  ALTER DEFAULT PRIVILEGES FOR ROLE liquibase IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO liquibase;

  RESET ROLE;

EOSQL

