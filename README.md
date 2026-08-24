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

## USS upload configuration

After validation, the pipeline prepares every `.sql` file as 80-character fixed records. SQL must fit in columns 1-72; the remaining columns are padded with spaces. Zowe CLI then uploads the prepared directory with `dir-to-uss --encoding "IBM-1047"`, so Zowe performs the EBCDIC conversion. The original filename is preserved and uploaded to `/z/z80145/<filename>`.

The repository contains `application.json` as the non-secret connection configuration. The actual `zowe.config.json` is generated temporarily during the Azure run from `application.json` plus the secret password.

Create an Azure DevOps variable group named `mainframe-devops` or add pipeline variables with these names:

- `MAINFRAME_PASSWORD`: secret variable

Host, port, and user ID are configured in `application.json`. `MAINFRAME_PASSWORD` is intentionally the only Azure variable because passwords must not be committed to GitHub.

The pipeline creates a temporary Zowe config during the run. Do not commit `~/.zowe/zowe.config.json`, usernames, or passwords to GitHub. Rotate the password that was shared in chat because it is now exposed.
