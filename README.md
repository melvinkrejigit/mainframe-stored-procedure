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

After validation, CI prepares every changed `.sql` file as 80-character fixed records. SQL must fit in columns 1-72; the remaining columns are padded with spaces. In `cd-pipeline.yml`, the `Deploy` stage then creates a build-specific USS subdirectory named after the current run (`zowe zos-files create uss-directory <ussDirectory>/$(Build.BuildId)`) and uploads the prepared files there with `dir-to-uss --encoding "IBM-1047"`, so Zowe performs the EBCDIC conversion. Each CD run's SQL therefore lands in its own path, e.g. `/z/z80145/<buildId>/<filename>`, instead of overwriting a shared directory - this keeps every deployment's files traceable back to the run that produced them and matches the `buildId` you look up when running the rollback pipeline. The generic DSNTEP2 JCL is then submitted against files in that same build-specific path.

The repository contains `config/application.json` as the non-secret connection configuration. The actual `zowe.config.json` is generated temporarily during the Azure run from `config/application.json` plus the secret password.

The version-check stage reads `versionCheck.query` from `config/application.json`, renders it as plain in-stream SQL inside `pipelines/templates/version-check.jcl` (without a `//` prefix), and submits the temporary JCL with Zowe. It extracts the submitted `jobid`, then runs `zowe zos-jobs view job-status-by-jobid <jobid> --rfj` and `zowe zos-jobs view all-spool-content <jobid> --rfj`. `pipelines/scripts/parse_sysprint.py` reads the `SYSPRINT` DD from the job log and extracts one pipe-delimited version such as `|V1|` from a line like `1_| V1 |`. The Azure log shows each Zowe command and response. Change the query in `config/application.json` without changing the pipeline or JCL template.

After the upload, the pipeline reads `sqlDeployment.jclTemplate` from `config/application.json`, renders the build-specific USS path (`<ussDirectory>/<buildId>/<filename>`) of every prepared SQL file into `pipelines/templates/execute-sql.jcl`, and submits one generic DSNTEP2 job per SQL file. The template uses `SYSIN DD PATH='...'` with `RECFM=FB,LRECL=80`.

After deployment, the `AutomatedTest` stage (in `cd-pipeline.yml`) renders `versionCheck.testQuery` into `pipelines/templates/test-version.jcl`, submits it with Zowe, retrieves status and all spool content by job ID, parses `SYSPRINT`, and asserts that the result equals `versionCheck.expectedTestVersion` (`V2`).

## Independent rollback pipeline

Rollback is intentionally separate from the CI/CD pipelines. The file `pipelines/rollback-pipeline.yml` has no push or pull-request trigger, so it can be run manually days later without making CI/CD wait. In Azure DevOps, create a pipeline from this YAML and choose **Run pipeline**. It prompts for three parameters:

- `Rollback needed?` (`Yes`/`No`) — set to `Yes` to actually submit the mainframe rollback; `No` skips it.
- `Build ID of the previously deployed CD run to roll back` — the numeric run ID of the `MF DevOps - CD` run being rolled back. The pipeline calls the Azure DevOps REST API (using the `ADO_PAT` secret from the `ado-automation` variable group) to confirm that build exists and prints its pipeline name/status/result before continuing; it fails fast if the build ID is missing or not found.
- `Stored procedure component to roll back` — a dropdown of known components (currently just `current-timestamp`; add new entries here as new stored procedures are added under `src/stored_procedure/`).

After verifying the build ID and logging the selected component, the pipeline reads `sqlDeployment.ussDirectory` from `config/application.json`, builds the same build-specific path CD uploaded to (`<ussDirectory>/<buildId>/<component>.sql`), and runs `zowe zos-files view uss-file` to print that exact deployed file's contents in the run log - so you can confirm what's currently on USS for that build/component before rolling back. It then submits the reusable `pipelines/templates/rollback-date.jcl` exactly as before. The rollback query comes from `rollback.query` in `config/application.json` and currently selects `CURRENT DATE` from `SYSIBM.SYSDUMMY1`. The job ID, status response, full spool response, and pipe-delimited `SYSPRINT` value are printed in the run log.

Create Azure DevOps variable groups with these names:

- `mainframe-devops` — `MAINFRAME_PASSWORD` (secret variable).
- `ado-automation` — `ADO_PAT` (secret variable; a PAT scoped to **Build: Read & execute**, also used by `ci-pipeline.yml` to queue the CD pipeline).

Host, port, and user ID are configured in `config/application.json`. `MAINFRAME_PASSWORD` is intentionally the only mainframe-related Azure variable because passwords must not be committed to GitHub.

The pipeline creates a temporary Zowe config during the run. Do not commit `~/.zowe/zowe.config.json`, usernames, or passwords to GitHub. Rotate the password that was shared in chat because it is now exposed.

## Self-hosted agent

All jobs run on a self-hosted agent (pool `SelfHosted-Mainframe`) instead of the Microsoft-hosted `ubuntu-latest` image. To avoid Azure VM cost, the agent runs on your local WSL Ubuntu distro (`Ubuntu-24.04`) instead of a cloud VM.

1. Open a WSL terminal (`wsl -d Ubuntu-24.04`) and run `pipelines/scripts/setup-wsl-agent-host.sh`. It installs Python, Node.js 20, and `@zowe/cli` once instead of on every pipeline run.
2. In Azure DevOps, go to **Organization settings > Agent pools > Add pool** and create a self-hosted pool named `SelfHosted-Mainframe`.
3. Create a PAT with **Agent Pools (Read & manage)** scope under **User settings > Personal access tokens**.
4. In the same WSL terminal, run `pipelines/scripts/register-agent.sh`, entering the PAT when prompted. It downloads the Azure Pipelines agent and registers it under `SelfHosted-Mainframe`.

Because the agent runs in WSL, it only picks up jobs while WSL is running on your machine (no jobs run while your PC is off or WSL is shut down). Keep a WSL terminal open, or enable systemd in `/etc/wsl.conf` and use `sudo ./svc.sh start` inside the agent folder so it starts automatically whenever WSL starts.

