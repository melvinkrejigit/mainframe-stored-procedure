# Mainframe Stored Procedure Deployment

Initial repository setup for local development.

## Repository structure

- `src/stored_procedure/` — DB2 SQL source files.
- `config/application.json` — non-secret connection and deployment configuration.
- `pipelines/` — Azure DevOps pipeline definitions (`ci-pipeline.yml`, `cd-pipeline.yml`, `rollback-pipeline.yml`).
- `pipelines/scripts/` — Python/Bash automation used by the pipelines.
- `pipelines/templates/` — reusable JCL templates rendered at pipeline run time.

## Current test query

`src/stored_procedure/current-timestamp.sql` runs a DB2 query that returns the current timestamp:

```sql
SELECT CURRENT TIMESTAMP
FROM SYSIBM.SYSDUMMY1;
```

Stored procedure source, JCL, Zowe integration, and Azure DevOps pipeline configuration will be added in later steps.
Azure trigger test
Automatic trigger test

## CI and CD pipelines

Deployment is split into two separate Azure DevOps pipelines so mainframe changes are never pushed automatically:

- **`pipelines/ci-pipeline.yml`** (CI) triggers on every push/PR to `feature/*` and `develop`. Its `Validate` stage identifies changed stored procedure SQL via `git diff`, validates and prepares it as FB80 records, and publishes it as a versioned package (`prepared-sql`) to the Azure Artifacts feed `mf-devops-sql`.
- **`pipelines/cd-pipeline.yml`** (CD) has `trigger: none` — it never runs automatically. After CI succeeds, go to this pipeline in Azure DevOps and click **Run pipeline** to deploy. It downloads the latest `prepared-sql` package from the feed, runs the mainframe version check, uploads the SQL to USS, submits the DSNTEP2 JCL, and runs the automated `AutomatedTest` stage.

Both pipelines must be registered as separate pipeline definitions in Azure DevOps (**Pipelines → New pipeline**, pointing at each YAML file respectively).

## Pipeline validation

The CI `Validate` stage first runs `git diff --name-only HEAD~1 HEAD -- 'src/stored_procedure/*.sql'` to identify only the stored procedure SQL files that changed in the triggering commit (falling back to a full scan of `src/stored_procedure` if no diff is found, e.g. on the first run). That changed-file list is then passed to `pipelines/scripts/validate_sql.py`, which requires non-empty SQL, a terminating `;`, and a supported DB2 statement keyword, and is reused by the FB80 preparation step below so only changed files are validated, prepared, and packaged.

## USS upload configuration

After validation, the pipeline prepares every `.sql` file as 80-character fixed records. SQL must fit in columns 1-72; the remaining columns are padded with spaces. Zowe CLI then uploads the prepared directory with `dir-to-uss --encoding "IBM-1047"`, so Zowe performs the EBCDIC conversion. The original filename is preserved and uploaded to `/z/z82437/<filename>`.

The repository contains `config/application.json` as the non-secret connection configuration. The actual `zowe.config.json` is generated temporarily during the Azure run from `config/application.json` plus the secret password.

The version-check stage reads `versionCheck.query` from `config/application.json`, renders it as plain in-stream SQL inside `pipelines/templates/version-check.jcl` (without a `//` prefix), and submits the temporary JCL with Zowe. It extracts the submitted `jobid`, then runs `zowe zos-jobs view job-status-by-jobid <jobid> --rfj` and `zowe zos-jobs view all-spool-content <jobid> --rfj`. `pipelines/scripts/parse_sysprint.py` reads the `SYSPRINT` DD from the job log and extracts one pipe-delimited version such as `|V1|` from a line like `1_| V1 |`. The Azure log shows each Zowe command and response. Change the query in `config/application.json` without changing the pipeline or JCL template.

After the upload, the pipeline reads `sqlDeployment.ussDirectory` and `sqlDeployment.jclTemplate` from `config/application.json`, renders the USS path of every prepared SQL file into `pipelines/templates/execute-sql.jcl`, and submits one generic DSNTEP2 job per SQL file. The template uses `SYSIN DD PATH='...'` with `RECFM=FB,LRECL=80`.

After deployment, the `AutomatedTest` stage (in `cd-pipeline.yml`) renders `versionCheck.testQuery` into `pipelines/templates/test-version.jcl`, submits it with Zowe, retrieves status and all spool content by job ID, parses `SYSPRINT`, and asserts that the result equals `versionCheck.expectedTestVersion` (`V2`).

## Independent rollback pipeline

Rollback is intentionally separate from the normal deployment pipeline. The file `pipelines/rollback-pipeline.yml` has no push or pull-request trigger, so it can be run manually days later without making the deployment pipeline wait. In Azure DevOps, create a second pipeline from this YAML and choose **Run pipeline**. Set `Rollback needed?` to `Yes` to submit the reusable `pipelines/templates/rollback-date.jcl`; set it to `No` to skip the mainframe operation. The rollback query comes from `rollback.query` in `config/application.json` and currently selects `CURRENT DATE` from `SYSIBM.SYSDUMMY1`. The job ID, status response, full spool response, and pipe-delimited `SYSPRINT` value are printed in the run log.

The automated V2 test runs after the deployment stage completes successfully.

Create an Azure DevOps variable group named `mainframe-devops` or add pipeline variables with these names:

- `MAINFRAME_PASSWORD`: secret variable

Host, port, and user ID are configured in `config/application.json`. `MAINFRAME_PASSWORD` is intentionally the only Azure variable because passwords must not be committed to GitHub.

The pipeline creates a temporary Zowe config during the run. Do not commit `~/.zowe/zowe.config.json`, usernames, or passwords to GitHub. Rotate the password that was shared in chat because it is now exposed.

## Self-hosted agent

All jobs run on a self-hosted agent (pool `SelfHosted-Mainframe`) instead of the Microsoft-hosted `ubuntu-latest` image. To avoid Azure VM cost, the agent runs on your local WSL Ubuntu distro (`Ubuntu-24.04`) instead of a cloud VM.

1. Open a WSL terminal (`wsl -d Ubuntu-24.04`) and run `pipelines/scripts/setup-wsl-agent-host.sh`. It installs Python, Node.js 20, and `@zowe/cli` once instead of on every pipeline run.
2. In Azure DevOps, go to **Organization settings > Agent pools > Add pool** and create a self-hosted pool named `SelfHosted-Mainframe`.
3. Create a PAT with **Agent Pools (Read & manage)** scope under **User settings > Personal access tokens**.
4. In the same WSL terminal, run `pipelines/scripts/register-agent.sh`, entering the PAT when prompted. It downloads the Azure Pipelines agent and registers it under `SelfHosted-Mainframe`.

Because the agent runs in WSL, it only picks up jobs while WSL is running on your machine (no jobs run while your PC is off or WSL is shut down). Keep a WSL terminal open, or enable systemd in `/etc/wsl.conf` and use `sudo ./svc.sh start` inside the agent folder so it starts automatically whenever WSL starts.

