"""Azure data stack skill — ADF, ADLS, Azure SQL, Synapse via az CLI."""

from ._base import Skill

AZURE_DATA = Skill(
    name="azure_data",
    tools=("Bash",),
    prompt_section="""\
## Azure Data Stack (az CLI — authenticated via `az login` or service principal env vars)

### Auth check
- `az account show` — verify active subscription before any operation.
- If not logged in: stop, report "az CLI not authenticated", do not proceed.

### Azure Data Factory (ADF)
- `az datafactory pipeline run --factory-name <f> --resource-group <rg> --name <pipeline>` — trigger run
- `az datafactory pipeline-run show --factory-name <f> --resource-group <rg> --run-id <id>` — poll status
- `az datafactory trigger list --factory-name <f> --resource-group <rg>` — list triggers
- `az datafactory dataset list --factory-name <f> --resource-group <rg>` — list datasets

### Azure Data Lake Storage (ADLS Gen2 / Blob)
- `az storage blob list --account-name <acct> --container-name <c> --prefix <path>` — list files
- `az storage blob download --account-name <acct> --container-name <c> --name <blob> -f <local>` — download
- `az storage blob upload --account-name <acct> --container-name <c> --name <blob> -f <local>` — upload
- `az storage fs file list --account-name <acct> --file-system <fs> --path <dir>` — ADLS Gen2 list

### Azure SQL
- `az sql db show --server <srv> --resource-group <rg> --name <db>` — DB info
- `az sql db list --server <srv> --resource-group <rg>` — list databases
- Connect via psql/sqlcmd: `sqlcmd -S <srv>.database.windows.net -d <db> -U <user> -P "$AZURE_SQL_PASSWORD" -Q "<SQL>"`

### Azure Synapse Analytics
- `az synapse pipeline run create --workspace-name <ws> --name <pipeline>` — trigger pipeline
- `az synapse spark job submit --workspace-name <ws> --spark-pool-name <pool> --main-definition-file <file>` — submit Spark job
- `az synapse sql pool list --workspace-name <ws> --resource-group <rg>` — list SQL pools

### Safety rules
- Never delete storage containers or SQL databases without explicit user confirmation.
- Always specify `--resource-group` — never rely on default to avoid wrong-subscription ops.
- If az CLI exits non-zero: stop, report exact error message, do not retry silently.
""",
)
