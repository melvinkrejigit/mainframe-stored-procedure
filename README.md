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

After deployment, the `AutomatedTest` stage renders `versionCheck.testQuery` into `jcl/test-version.jcl`, submits it with Zowe, retrieves status and all spool content by job ID, parses `SYSPRINT`, and asserts that the result equals `versionCheck.expectedTestVersion` (`V2`).

## Independent rollback pipeline

Rollback is intentionally separate from the normal deployment pipeline. The file `rollback-pipeline.yml` has no push or pull-request trigger, so it can be run manually days later without making the deployment pipeline wait. In Azure DevOps, create a second pipeline from this YAML and choose **Run pipeline**. Set `Rollback needed?` to `Yes` to submit the reusable `jcl/rollback-date.jcl`; set it to `No` to skip the mainframe operation. The rollback query comes from `rollback.query` in `application.json` and currently selects `CURRENT DATE` from `SYSIBM.SYSDUMMY1`. The job ID, status response, full spool response, and pipe-delimited `SYSPRINT` value are printed in the run log.

The automated V2 test runs after the deployment stage completes successfully.

Create an Azure DevOps variable group named `mainframe-devops` or add pipeline variables with these names:

- `MAINFRAME_PASSWORD`: secret variable

Host, port, and user ID are configured in `application.json`. `MAINFRAME_PASSWORD` is intentionally the only Azure variable because passwords must not be committed to GitHub.

The pipeline creates a temporary Zowe config during the run. Do not commit `~/.zowe/zowe.config.json`, usernames, or passwords to GitHub. Rotate the password that was shared in chat because it is now exposed.

## Approval before mainframe work

The pipeline has three stages: `Validate`, `Approval`, and `Deploy`. After `Validate` succeeds, `ManualValidation@0` pauses the run before any Zowe command executes. Azure DevOps sends an email notification to `melvinkreji@gmail.com`; open the run and select `Resume` to allow the version check, USS upload, and SQL JCL submission. Select `Reject` to stop the deployment.

The email address must be able to receive Azure DevOps notifications in your organization. If the email is not delivered, add the user or an approved group under Azure DevOps notification settings and use that identity in `notifyUsers`.
