-- MDSK-RAG Dual-Source Collection Pattern (ACS JCIM, 2025)
-- WHY: Separates literature knowledge from quantitative data per MDSK-RAG.
--      Literature: text passages, figure semantics from papers/reports.
--      Quantitative: structured table rows with numerical experiment data.
-- RISK: HNSW index creation may take 30s+ with large datasets.
-- INTERVIEW: "Applied MDSK-RAG dual-source pattern from ACS JCIM paper."

ALTER SESSION SET CONTAINER = FREEPDB1;

-- Document metadata
CREATE TABLE KNOWLEDGE_DOCS (
    doc_id        VARCHAR2(50)   PRIMARY KEY,
    doc_title     VARCHAR2(500)  NOT NULL,
    doc_type      VARCHAR2(20)   NOT NULL,  -- 'paper', 'report', 'safety'
    file_path     VARCHAR2(500),
    page_count    NUMBER,
    vlm_processed NUMBER(1)      DEFAULT 0,
    created_at    TIMESTAMP      DEFAULT SYSTIMESTAMP
);

-- Source 1: Literature Knowledge (text + figure semantics)
CREATE TABLE LITERATURE_CHUNKS (
    chunk_id      VARCHAR2(100)  PRIMARY KEY,
    doc_id        VARCHAR2(50)   REFERENCES KNOWLEDGE_DOCS,
    chunk_type    VARCHAR2(20)   NOT NULL,  -- 'text', 'figure'
    chunk_text    CLOB           NOT NULL,
    page_number   NUMBER,
    section_title VARCHAR2(500),
    embedding     VECTOR(1024),
    created_at    TIMESTAMP      DEFAULT SYSTIMESTAMP
);

-- Source 2: Quantitative Records (table rows with structured data)
CREATE TABLE QUANTITATIVE_CHUNKS (
    chunk_id      VARCHAR2(100)  PRIMARY KEY,
    doc_id        VARCHAR2(50)   REFERENCES KNOWLEDGE_DOCS,
    chunk_type    VARCHAR2(20)   NOT NULL,  -- 'table_row'
    chunk_text    CLOB           NOT NULL,  -- natural language representation
    page_number   NUMBER,
    table_id      VARCHAR2(50),
    embedding     VECTOR(1024),
    created_at    TIMESTAMP      DEFAULT SYSTIMESTAMP
);

-- WHY: CTXAPP role required for CTX_DDL.SYNC_INDEX after bulk ingestion.
GRANT CTXAPP TO fieldops;

-- Vector indexes for both sources
CREATE VECTOR INDEX idx_literature_embedding
    ON LITERATURE_CHUNKS(embedding)
    ORGANIZATION NEIGHBOR PARTITIONS
    DISTANCE COSINE
    WITH TARGET ACCURACY 95;

CREATE VECTOR INDEX idx_quantitative_embedding
    ON QUANTITATIVE_CHUNKS(embedding)
    ORGANIZATION NEIGHBOR PARTITIONS
    DISTANCE COSINE
    WITH TARGET ACCURACY 95;

-- BM25 full-text indexes for both sources
CREATE INDEX idx_literature_text
    ON LITERATURE_CHUNKS(chunk_text)
    INDEXTYPE IS CTXSYS.CONTEXT;

CREATE INDEX idx_quantitative_text
    ON QUANTITATIVE_CHUNKS(chunk_text)
    INDEXTYPE IS CTXSYS.CONTEXT;

COMMIT;
