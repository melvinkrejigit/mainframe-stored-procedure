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

The repository contains `zowe.config.json.example` as a connection template. The actual `zowe.config.json` is generated temporarily during the Azure run from secret variables.

Create an Azure DevOps variable group named `mainframe-devops` or add pipeline variables with these names:

- `MAINFRAME_HOST`: `204.90.115.200`
- `MAINFRAME_USER`: your mainframe user ID
- `MAINFRAME_PASSWORD`: secret variable
- `ZOSMF_PORT`: `10443`
- `ZOSMF_REJECT_UNAUTHORIZED`: `false` only for a controlled test system with a certificate exception

The pipeline creates a temporary Zowe config during the run. Do not commit `~/.zowe/zowe.config.json`, usernames, or passwords to GitHub. Rotate the password that was shared in chat because it is now exposed.
