-- Migration: Add file_hash and updated_at to KNOWLEDGE_DOCS
-- Purpose: enable idempotent re-ingestion (skip VLM/embedding when file unchanged)
-- WHY: Existing dev/prod DBs were created before file_hash existed.
-- NOTE: Oracle persistent volume means oracle-init/*.sql does NOT auto-run on existing DBs.
--       Apply this manually: docker exec fieldops-ai-oracle-1 sqlplus PDBADMIN/<pw>@<svc> @/path/to/04_add_file_hash.sql

ALTER TABLE KNOWLEDGE_DOCS
    ADD (
        file_hash  VARCHAR2(64),
        updated_at TIMESTAMP DEFAULT SYSTIMESTAMP
    );

COMMIT;
