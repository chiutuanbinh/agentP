"""Databricks skill — jobs, clusters, DBFS, and Delta Lake via Databricks CLI."""

from ._base import Skill

DATABRICKS = Skill(
    name="databricks",
    tools=("Bash",),
    prompt_section="""\
## Databricks (databricks CLI — configured via DATABRICKS_HOST + DATABRICKS_TOKEN)

### Auth check
- `databricks auth describe` — verify token and host before any operation.
- If not configured: stop, report "DATABRICKS_HOST / DATABRICKS_TOKEN not set", do not proceed.

### Jobs
- `databricks jobs list` — list jobs
- `databricks jobs get <job-id>` — job definition
- `databricks jobs run-now <job-id>` — trigger job run
- `databricks runs get <run-id>` — poll run status (repeat until state is TERMINATED or ERROR)
- `databricks runs get-output <run-id>` — fetch run logs / output

### Clusters
- `databricks clusters list` — list clusters with state
- `databricks clusters get <cluster-id>` — cluster details
- `databricks clusters start <cluster-id>` — start stopped cluster
- Never terminate clusters without explicit user confirmation.

### DBFS (Databricks File System)
- `databricks fs ls dbfs:<path>` — list
- `databricks fs cp <local> dbfs:<path>` — upload
- `databricks fs cp dbfs:<path> <local>` — download
- `databricks fs rm dbfs:<path>` — delete file (confirm before running)

### Notebooks
- `databricks workspace export <path> --format SOURCE -o <local.py>` — export notebook as Python
- `databricks workspace import <local.py> <path> --language PYTHON --overwrite` — deploy notebook

### Delta Lake (via PySpark / SQL in notebooks or jobs)
- Inspect: `DESCRIBE DETAIL <table>` — Delta metadata (partitions, files, version)
- History: `DESCRIBE HISTORY <table>` — audit log of changes
- Vacuum: `VACUUM <table> RETAIN <n> HOURS` — remove old files (never set < 168h on prod without confirming)
- Optimize: `OPTIMIZE <table> ZORDER BY (<col>)` — file compaction + ZOrder

### Safety rules
- Never drop Delta tables or DBFS paths without explicit user confirmation.
- Before schema changes (ALTER TABLE), check `DESCRIBE HISTORY` for active streams or jobs using the table.
- If databricks CLI exits non-zero: stop, report exact error, do not retry silently.
""",
)
