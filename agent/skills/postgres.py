"""PostgreSQL skill — query, inspect, and manage Postgres databases via psql."""

from ._base import Skill

POSTGRES = Skill(
    name="postgres",
    tools=("Bash",),
    prompt_section="""\
## PostgreSQL (psql — connection via DATABASE_URL or explicit flags)

### Query
- `psql "$DATABASE_URL" -c "<SQL>"` — run single statement
- `psql "$DATABASE_URL" -f <file.sql>` — run SQL file
- `psql "$DATABASE_URL" -c "\\copy (<query>) TO STDOUT CSV HEADER" > out.csv` — export CSV

### Inspect schema
- `psql "$DATABASE_URL" -c "\\dt <schema>.*"` — list tables
- `psql "$DATABASE_URL" -c "\\d <table>"` — describe table (columns, indexes, constraints)
- `psql "$DATABASE_URL" -c "\\di <table>*"` — list indexes on table
- `psql "$DATABASE_URL" -c "SELECT * FROM information_schema.columns WHERE table_name='<t>'"` — column metadata

### Explain / analyze
- Prefix heavy queries with `EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)` before running in prod.
- Never run `EXPLAIN ANALYZE` on write statements in prod — use `EXPLAIN` only.

### Backup / restore
- `pg_dump "$DATABASE_URL" -Fc -f dump.pgc` — custom-format dump
- `pg_restore -d "$DATABASE_URL" dump.pgc` — restore

### Safety rules
- Never run DDL (DROP, TRUNCATE, ALTER) without explicit user confirmation.
- Always use parameterized queries or quoted literals — never interpolate raw user input into SQL.
- If DATABASE_URL is unset, stop and report; do not prompt for credentials.
- If psql exits non-zero: stop, report exact error, do not retry silently.
""",
)
