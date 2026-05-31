"""Langfuse skill — query traces and observations at runtime."""

from ._base import Skill

LANGFUSE_SKILL = Skill(
    name="langfuse",
    tools=("Bash",),
    prompt_section="""\
## Langfuse tracing (Python SDK)
Query traces and observations for debugging agent runs.

```python
from langfuse import Langfuse
lf = Langfuse()

# List recent traces
traces = lf.fetch_traces(limit=20)
for t in traces.data:
    print(t.id, t.name, t.timestamp)

# Fetch a specific trace
trace = lf.fetch_trace("<trace_id>")

# List observations (spans/tool calls) for a trace
obs = lf.fetch_observations(trace_id="<trace_id>")
for o in obs.data:
    print(o.name, o.type, o.input, o.output)
```

Use `Bash` to run inline Python snippets. LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY must be set.
If keys absent, skip Langfuse lookups and note it in output.
""",
)
