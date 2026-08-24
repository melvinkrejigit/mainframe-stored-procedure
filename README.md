# Mainframe Stored Procedure Deployment

Initial repository setup for local development.

## Current test query

`current-timestamp.sql` runs a DB2 query that returns the current timestamp:

```sql
SELECT CURRENT TIMESTAMP
FROM SYSIBM.SYSDUMMY1;
```

Stored procedure source, JCL, Zowe integration, and Azure DevOps pipeline configuration will be added in later steps.
Azure trigger test
Automatic trigger test

## Pipeline validation

The first Azure DevOps step uses `scripts/validate_sql.py` to automatically discover and validate every `*.sql` file in the repository before any later deployment work. It requires non-empty SQL, a terminating `;`, and a supported DB2 statement keyword. Add or remove SQL files without changing the pipeline YAML.
