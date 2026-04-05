-- WHY: Auto-executed on Oracle 26ai startup. Creates fieldops user + grants.
-- RISK: Password mismatch between ORACLE_PWD and this script causes connection failure.
-- INTERVIEW: "Automated DB initialization via Oracle startup scripts."

ALTER SESSION SET CONTAINER = FREEPDB1;

CREATE USER fieldops IDENTIFIED BY "***REMOVED***"
  DEFAULT TABLESPACE USERS
  TEMPORARY TABLESPACE TEMP
  QUOTA UNLIMITED ON USERS;

GRANT CONNECT, RESOURCE TO fieldops;
GRANT CREATE SESSION TO fieldops;
GRANT CREATE TABLE TO fieldops;
GRANT CREATE SEQUENCE TO fieldops;
GRANT CREATE VIEW TO fieldops;

-- Required for Vector Search operations
GRANT DB_DEVELOPER_ROLE TO fieldops;

COMMIT;
