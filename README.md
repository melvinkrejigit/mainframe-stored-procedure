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

After validation, the pipeline converts every `.sql` file to EBCDIC IBM-037 fixed records with LRECL 80. Each source line must be at most 72 characters and is padded with EBCDIC blanks to 80 bytes. The original filename is preserved and uploaded to `/z/z80145/<filename>` using Zowe CLI with `--binary`.

Create an Azure DevOps variable group named `mainframe-devops` or add pipeline variables with these names:

- `MAINFRAME_HOST`: `204.90.115.200`
- `MAINFRAME_USER`: your mainframe user ID
- `MAINFRAME_PASSWORD`: secret variable
- `ZOSMF_PORT`: `10443`
- `ZOSMF_REJECT_UNAUTHORIZED`: `false` only for a controlled test system with a certificate exception

The pipeline creates a temporary Zowe config during the run. Do not commit `~/.zowe/zowe.config.json`, usernames, or passwords to GitHub. Rotate the password that was shared in chat because it is now exposed.
