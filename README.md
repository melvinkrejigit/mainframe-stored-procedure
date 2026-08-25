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

The version-check stage reads `versionCheck.query` from `application.json`, renders it as plain in-stream SQL inside `jcl/version-check.jcl` (without a `//` prefix), and submits the temporary JCL with Zowe. It extracts the submitted `jobid`, then runs `zowe zos-jobs view job-status-by-jobid <jobid> --rfj` and `zowe zos-jobs view all-spool-content <jobid> --rfj`. `scripts/parse_sysprint.py` reads the `SYSPRINT` DD from the job log and extracts one pipe-delimited version such as `|V1|` from a line like `1_| V1 |`. The Azure log shows each Zowe command and response. Change the query in `application.json` without changing the pipeline or JCL template.

After the upload, the pipeline reads `sqlDeployment.ussDirectory` and `sqlDeployment.jclTemplate` from `application.json`, renders the USS path of every prepared SQL file into `jcl/execute-sql.jcl`, and submits one generic DSNTEP2 job per SQL file. The template uses `SYSIN DD PATH='...'` with `RECFM=FB,LRECL=80`.

Create an Azure DevOps variable group named `mainframe-devops` or add pipeline variables with these names:

- `MAINFRAME_PASSWORD`: secret variable

Host, port, and user ID are configured in `application.json`. `MAINFRAME_PASSWORD` is intentionally the only Azure variable because passwords must not be committed to GitHub.

The pipeline creates a temporary Zowe config during the run. Do not commit `~/.zowe/zowe.config.json`, usernames, or passwords to GitHub. Rotate the password that was shared in chat because it is now exposed.
