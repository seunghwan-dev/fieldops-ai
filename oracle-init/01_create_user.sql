-- WHY: Auto-executed on Oracle 26ai startup. Creates fieldops user + grants.
-- RISK: Password mismatch between ORACLE_PWD and this script causes connection failure.
-- INTERVIEW: "Automated DB initialization via Oracle startup scripts."

ALTER SESSION SET CONTAINER = FREEPDB1;

-- WARNING: Replace 'changeme' below with a strong password BEFORE first startup.
--   This password is only used during the first 'docker compose up' with an empty oracle-data volume.
--   For existing environments, change the password via: ALTER USER fieldops IDENTIFIED BY "<your-password>";
CREATE USER fieldops IDENTIFIED BY "changeme"
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
