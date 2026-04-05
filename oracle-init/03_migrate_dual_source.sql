-- Migration: KNOWLEDGE_CHUNKS -> LITERATURE_CHUNKS + QUANTITATIVE_CHUNKS
-- WHY: MDSK-RAG dual-source pattern requires physical table separation.
-- RISK: Run AFTER 02_create_tables.sql creates the new tables.
--       Existing KNOWLEDGE_CHUNKS data is redistributed by chunk_type.

ALTER SESSION SET CONTAINER = FREEPDB1;

-- Migrate text + figure chunks to LITERATURE_CHUNKS
INSERT INTO LITERATURE_CHUNKS (chunk_id, doc_id, chunk_type, chunk_text, page_number, section_title, embedding, created_at)
SELECT chunk_id, doc_id, chunk_type, chunk_text, page_number, section_title, embedding, created_at
FROM KNOWLEDGE_CHUNKS WHERE chunk_type IN ('text', 'figure');

-- Migrate table_row chunks to QUANTITATIVE_CHUNKS
INSERT INTO QUANTITATIVE_CHUNKS (chunk_id, doc_id, chunk_type, chunk_text, page_number, table_id, embedding, created_at)
SELECT chunk_id, doc_id, chunk_type, chunk_text, page_number, table_id, embedding, created_at
FROM KNOWLEDGE_CHUNKS WHERE chunk_type = 'table_row';

-- Drop old table and indexes
DROP INDEX idx_knowledge_text;
DROP INDEX idx_knowledge_embedding FORCE;
DROP TABLE KNOWLEDGE_CHUNKS;

COMMIT;
