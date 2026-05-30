"""Testing skill — test writing, coverage, and QA guidance."""

from ._base import Skill

TESTING = Skill(
    name="testing",
    tools=("Read", "Bash", "Glob", "Grep"),
    prompt_section="""\
## Testing
- Read existing tests before writing new ones — follow same patterns, fixtures, assertion style
- Cover: happy path, edge cases, error paths
- Test commands: `pytest -x -q` (Python), `npm test` (JS/TS), `go test ./...` (Go)
- Never mock the database in integration tests — use real fixtures
- Flag missing test coverage in your findings
- For QA reviews: check for missing edge cases, flaky async tests, hardcoded values,
  missing teardown
""",
)
