# Agent concept

## Why do we want agentic system

Agentic system is a system where agents work together, and interact without other parts of the existing system. Mostly through tools, mcp (mcp is just a tool interface). 

The actual knowledge to perform a particular task on a domain is still very limited.

Agentic works very well on SDLC because of the following reasons:
1. Software development lifecycle is heavily standardize, everything can be digitalize and documented into process, and there are valuation at every steps. 
2. Test, evaluation is cheap and well understood, a lot of available tool.
3. Limited scope, can be regularize more easily than other practice.

By building an agentic system, we can automate and release the working effort on thinking tasks that cannot be done before without human. 
Example:
  - DS engineer, when receiving requirement from customer, let the AI system reasoning on the data, then produce a verifiable result. We don't need to guide them through every step.
  - SW, when customer state the issue, they can receive the result, or view the proposal in very quick window. 
    - PM role can be replaced with Agent that can model, asking verification questions, produce plan, ticket for Dev
    - Dev role can be replaced with agent that looks at the ticket dashboard, produce running code, test, verify, publish and deploy them for reviewing
    - Reviewer can flag issues, suggest improvements, approve or reject with reasoning

---

## SDLC Automation Map

### Stage-by-Stage: What Agent Does

| SDLC Stage | Automated Action | Verifiable Output |
|---|---|---|
| **Requirements** | Interview stakeholder, extract acceptance criteria, write tickets | Ticket with Definition of Done, testable criteria |
| **Design** | Propose architecture, data model, API contract, ERD | Design doc, schema file, ADR |
| **Implementation** | Write code against ticket, run linter, fix errors | Green lint, compiling code |
| **Testing** | Generate test cases from acceptance criteria, run suite | Test report, coverage %, pass/fail |
| **Review** | Read diff, flag bugs, suggest refactor, check security | Review comment list, approval or block |
| **Deploy** | Open PR, merge on green CI, trigger pipeline/deploy | Deployment receipt, URL, version tag |
| **Monitor** | Watch metrics post-deploy, alert on anomaly, trigger re-investigation | Alert log, incident ticket, rollback trigger |

### Mapped to Data Analyst Workflow

| DA Step | SDLC Analog | Agent Action |
|---|---|---|
| Receive business question | Requirements | Clarify scope, define KPI (numerator/denominator), set success metric |
| Data discovery | Design | Scan schema/catalog, identify relevant tables, map joins |
| EDA | Implementation | Hypothesis → query → interpret → next hypothesis loop |
| Validation | Testing | Compare to prior period, source-of-truth, check nulls/row counts/fan-out |
| Peer review | Review | Check query assumptions, flag inflating joins, verify business logic |
| Publish dashboard/report | Deploy | Push notebook/dbt model, trigger Airflow DAG, version artifact |
| Monitor KPI | Monitor | Watch for metric drift, auto-trigger investigation on anomaly |

**Why DA fits agentic well:**
- Steps discrete and verifiable (query runs or not; numbers match or not)
- Feedback cheap (seconds per iteration)
- Scope bounded per request

---

## Fully Functional Agentic SDLC: Complete Specification

### Conceptual Architecture

```
Stakeholder / Human
       │
       ▼
[PM Agent] ──── requirements, tickets ────► [Ticket Store]
                                                   │
                                                   ▼
                                          [Dev Agent(s)]
                                                   │
                                          write code, tests
                                                   │
                                                   ▼
                                          [CI Agent] ──── run tests, lint, security scan
                                                   │
                                                   ▼
                                          [Review Agent]
                                                   │
                                           approve / block
                                                   │
                                                   ▼
                                          [Deploy Agent]
                                                   │
                                          deploy to staging → prod
                                                   │
                                                   ▼
                                          [Monitor Agent] ──── anomaly → feedback loop
```

---

### Step 1: Requirements & Ticketing Agent

**What it does:**
- Receives raw input (Slack message, email, voice transcript)
- Asks clarifying questions until Definition of Done is unambiguous
- Decomposes into atomic tickets with acceptance criteria
- Assigns priority, labels, estimates complexity

**Tools needed:**
- LLM with structured output (JSON schema for ticket format)
- Jira / Linear / GitHub Issues API
- Slack / email integration for input

**Production requirements:**
- Human approval gate before tickets are created (or created as "draft")
- Audit log: who/what triggered ticket creation, timestamp, raw input stored
- Dedup detection: don't create duplicate tickets for same issue
- Ticket schema versioned — agent output must conform

**What to know:**
- Requirements quality determines everything downstream — garbage in, garbage out
- Agent must be trained/prompted on your domain (what "done" means for your team)
- Need feedback loop: if dev finds ticket ambiguous, route back to PM agent

---

### Step 2: Design Agent

**What it does:**
- Reads ticket, existing codebase context, architecture docs
- Proposes implementation approach (ADR format)
- Generates data model / API schema / component diagram
- Flags risk, dependencies, breaking changes

**Tools needed:**
- Code search (grep, AST parser, embeddings over codebase)
- Diagram generation (Mermaid, PlantUML)
- ADR template store

**Production requirements:**
- Design must be approved by human architect before dev starts
- Store design artifact linked to ticket (traceability)
- Breaking change detection: flag if design touches public API / DB schema

**What to know:**
- Agent context window limits how much codebase it can see — need chunking/retrieval strategy
- Design agent should have read-only access to codebase, no write

---

### Step 3: Development Agent

**What it does:**
- Reads ticket + approved design
- Writes code, commits incrementally
- Runs lint/typecheck after each file change
- Self-corrects on error output (up to N retries)
- Writes unit tests alongside code

**Tools needed:**
- Code editor tools (Read, Edit, Write, Bash for running tests)
- Git (commit, branch, push)
- Language server / LSP for error feedback

**Production requirements:**
- Agent works in isolated branch, never touches main directly
- Resource limits: max N LLM calls per ticket, max wall-clock time, kill switch
- All LLM calls logged with prompt + response for audit
- Secrets never passed to agent — use env injection, agent sees only `$VAR_NAME` references
- No agent internet access unless explicitly scoped (supply chain risk)

**What to know:**
- Multi-file changes require careful ordering (define before use)
- Agent will get stuck in loops — need loop detection (same error 3x → escalate to human)
- Cost control: set token budget per ticket; complex tickets need human decomposition first

---

### Step 4: CI Agent

**What it does:**
- Triggered on push
- Runs: lint, typecheck, unit tests, integration tests, security scan (SAST)
- Parses failures, annotates PR with specific line-level feedback
- Blocks merge on failure

**Tools needed:**
- CI platform (GitHub Actions, GitLab CI, Buildkite)
- SAST tools (Semgrep, Bandit, Snyk)
- Dependency vulnerability scanner (Dependabot, Safety)
- Test framework runner

**Production requirements:**
- CI runs in ephemeral sandboxed environment
- No production credentials in CI — use short-lived tokens (OIDC)
- Build artifacts signed (supply chain integrity)
- Test results stored, queryable (flaky test detection over time)
- SLA on CI runtime — fail fast, parallelize

**Security requirements:**
- Dependency pinning + lock files committed
- No `pip install` from arbitrary URLs
- Container images scanned before use
- Secrets scanning on every commit (detect accidental credential commit)

---

### Step 5: Review Agent

**What it does:**
- Reads diff + ticket + design doc
- Checks: correctness, security, performance, style, test coverage
- Posts inline comments on PR
- Gives approve / request-changes verdict with reasoning

**Tools needed:**
- GitHub / GitLab PR API for inline comments
- Static analysis output integration
- Semantic diff understanding (not just line-level)

**Production requirements:**
- Human reviewer still required for: security-sensitive changes, DB migrations, auth, public API changes
- Review agent opinion is advisory — human has final approve authority
- Agent comment attributed clearly as AI-generated (transparency)
- Review stored linked to PR for audit

**What to know:**
- Agent review catches obvious bugs well; misses business logic errors
- Agent should explicitly list what it did NOT check (scope honesty)

---

### Step 6: Deploy Agent

**What it does:**
- Triggered post-approval
- Runs deploy pipeline: build image → push registry → deploy staging → smoke test → promote prod
- Manages rollback if smoke test fails
- Updates changelog, tags release, notifies stakeholders

**Tools needed:**
- Container registry (ECR, GCR, Docker Hub)
- Orchestration (Kubernetes, ECS, Cloud Run)
- Deploy tool (Helm, Terraform, CDK)
- Smoke test runner
- Notification (Slack, PagerDuty)

**Production requirements:**
- Deploy agent has write access to staging only; prod requires human approval step or automated gate
- Blue/green or canary deploy — no big-bang prod push
- Every deploy logged: who triggered, what version, what diff, timestamp
- Rollback automated and tested (not just documented)
- Deploy window enforcement: no prod deploy Friday 3pm–Monday 9am without incident ticket

**Infrastructure requirements:**
- Infra as code — no manual console changes
- State management for IaC (Terraform state in S3 + lock)
- Separate accounts/projects for staging vs prod (blast radius containment)
- Least-privilege IAM for deploy agent service account

---

### Step 7: Monitor Agent

**What it does:**
- Watches metrics, logs, error rates post-deploy
- Detects anomaly (spike in errors, latency regression, metric drift)
- Correlates anomaly with recent deploy
- Triggers: alert → auto-rollback (if configured) → incident ticket → investigation loop

**Tools needed:**
- Metrics platform (Datadog, Prometheus/Grafana, CloudWatch)
- Log aggregation (Loki, Splunk, CloudWatch Logs)
- Alerting (PagerDuty, OpsGenie)
- Incident management (PagerDuty, Linear incident)

**Production requirements:**
- SLO defined before deploy — agent monitors against SLO, not raw metrics
- Runbook linked to every alert — agent executes runbook steps autonomously up to a limit
- Human escalation path always exists — agent cannot be sole on-call
- False positive rate tracked — noisy agent alerts get ignored, defeating purpose

---

### Cross-Cutting: Production Requirements

#### Audit & Compliance
- Every agent action logged: input, output, model, timestamp, cost
- Logs immutable, tamper-evident (append-only store)
- Human decisions logged alongside agent actions (who approved, when)
- Retention policy matched to compliance requirement (SOC2, GDPR, HIPAA as applicable)
- Ability to reconstruct: "why was this code written this way" → trace back to ticket → to requirement → to stakeholder input

#### Security
- Agent identities separate from human identities (service accounts, not personal tokens)
- Principle of least privilege: each agent has only tools/permissions needed for its stage
- No agent can grant itself more permissions
- Prompt injection defense: agent inputs from external sources (tickets, code comments) treated as untrusted data, not instructions
- Agent outputs reviewed before acting on them for high-risk actions (deploy, DB migration)
- Sensitive data (PII, secrets) never in LLM prompts — use references, not values

#### Observability
- Agent call latency and cost tracked per stage, per ticket
- Token usage alerted if exceeding budget
- Agent "stuck" detection: same state for > N minutes → alert
- Human-readable audit trail, not just raw logs

#### Human-in-the-Loop Gates
Mandatory human approval before:
1. Ticket created from unstructured input (PM agent output)
2. Design approved and dev starts
3. Code merged to main
4. Any prod deploy
5. Incident runbook executes destructive action (scale-down, data delete)

---

### Minimal Version (MVP)

**Scope: one agent, one loop, one task type**

```
Human writes ticket (manually)
        │
        ▼
Dev Agent reads ticket
        │
  writes code in branch
        │
  runs tests locally
        │
  opens PR
        │
Human reviews + merges
        │
        ▼
Human deploys (manually)
```

**What to build first:**

1. **Dev agent** — reads a well-formed ticket, writes code to a branch, runs `make test`, opens PR
   - Stack: Claude API + tool use (Read/Edit/Write/Bash) + GitHub API for PR
   - Input: ticket markdown file
   - Output: open PR with code + test

2. **Acceptance criteria:** agent can close 3 types of tickets autonomously:
   - Add a function with unit test
   - Fix a bug described in the ticket
   - Add a new API endpoint (CRUD, no auth)

3. **Guardrails for MVP:**
   - Agent works only in `agent/` branch prefix
   - Max 20 LLM calls per run, then stops and comments on PR what it did
   - All runs logged to `agent_runs/` directory (prompt, response, tool calls, cost)
   - No prod access whatsoever

4. **What NOT to build yet:**
   - PM agent (write tickets manually)
   - Deploy agent (deploy manually)
   - Monitor agent (check manually)
   - Multi-agent coordination

---

## Evaluation

Agent says "done" — evaluation proves whether that's true.

### Layer 1: Deterministic Checks (cheapest, run always)

| Check | What It Catches |
|---|---|
| Tests pass | Functional regression |
| Lint / typecheck green | Syntax, type errors |
| Coverage threshold met | Agent wrote tests at all |
| Build succeeds | Import errors, missing deps |
| No secrets in diff | Accidental credential leak |
| Diff scope within expected files | Agent didn't touch unrelated code |

**Rule: deterministic check fails → stop. Don't escalate to LLM evaluation.**

---

### Layer 2: Specification Conformance

Did output match what was asked?

- **Ticket ↔ diff**: LLM-as-judge reads ticket + diff, scores: "does this implement the requirement?"
- **Acceptance criteria checklist**: extract AC from ticket, evaluate each as pass/fail
- **Schema validation**: if output is structured (JSON, SQL, API response), validate against schema

---

### Layer 3: Adversarial Evaluator (separate LLM call)

Different agent, same context, explicit goal: find problems.

```
Evaluator prompt:
"Here is a ticket. Here is the code diff.
Your job is to find bugs, missing cases, security issues.
Do NOT give benefit of the doubt. Be adversarial.
Output: list of concrete issues, or PASS."
```

Evaluator must be a **separate call** — same agent evaluating its own output is worthless. Different temperature, optionally different model.

---

### Layer 4: Runtime Evaluation

Run the code, observe behavior — not just "does it compile."

| Technique | How |
|---|---|
| Smoke test on staging | Deploy, hit endpoints, check responses |
| Property-based tests | Random inputs, verify invariants hold |
| Golden file comparison | Agent output vs known-good baseline |
| Differential testing | Old vs new code, same inputs, compare outputs |
| Shadow mode | Run new agent code in parallel with old silently, compare |

---

### Layer 5: Human Spot-Check (sampled, not 100%)

- Sample 10–20% of agent PRs for full human review
- Always review: auth, DB migrations, public API, security-adjacent code
- Track: what % of sampled PRs had issues → calibrate confidence in agent over time

---

### Evaluation by Risk Level

```
Low risk (add util function, fix typo):
  → tests pass + lint + LLM-judge score > threshold → auto-merge

Medium risk (new endpoint, schema change):
  → above + adversarial evaluator + staging smoke test → human approval gate

High risk (auth, payment, PII, DB migration):
  → all above + mandatory human review, no exceptions
```

---

### What Evaluation Proves (and Doesn't)

Evaluation proves **code does what the ticket said**. It does NOT prove:
- Ticket described the right thing (requirements bug)
- No cross-system interaction breaks (integration gap)
- Business outcome achieved (KPI moved)

Stack layers — no single check is sufficient.

---

### Evaluation for DA Workflow

| DA Output | Evaluation Method |
|---|---|
| SQL query result | Row count vs expected range, reconcile to source system total |
| KPI value | Compare prior period, flag >X% deviation for human review |
| Data pipeline | Null check, schema check, SLA on completion time |
| Insight narrative | LLM-as-judge: "does claim follow from the data shown?" |

---

---

## Infrastructure & DevOps

### Why Infra Is Different From Code

Code changes reversible (git revert). Infra often not:
- deleted storage = data gone
- misconfigured NSG = security hole
- manual + agent = worst combo (agent assumes state it reads; manual changes cause drift)

**Rule: don't automate a broken manual process. Automate a working one.**

---

### Current State: Azure, Manual-Heavy, Terraform Partial

Fix in this order before any agent touches infra:

**Step 0 — Audit**
- `az resource list` — full inventory
- `terraform plan` — measure drift today
- Tag all manual resources: `managed-by: manual`

**Step 1 — Stop new manual changes**
- Everything new goes through Terraform
- Existing manual resources: `terraform import` or accept as legacy

**Step 2 — Terraform as source of truth**
- State in Azure Blob Storage backend with state locking
- Separate state files per environment (dev / staging / prod)
- CI runs `terraform plan` on every PR, posts diff as comment
- `terraform apply` only via CI, never from local machine

**Step 3 — Only then consider infra agent**

---

### What Infra Agent Can Do (once IaC solid)

| Task | Automatable | Risk |
|---|---|---|
| Generate Terraform module for new resource | Yes | Low — human reviews plan |
| Run `terraform plan`, post diff to PR | Yes | Low — read-only |
| Flag drift (plan shows unexpected changes) | Yes | Low |
| `terraform apply` on staging | Yes (gated) | Medium |
| `terraform apply` on prod | Human only | High |
| Resize/scale resources based on metrics | Yes (within bounds) | Medium |
| Create/delete resource groups | Human only | High |
| Manage IAM / RBAC | Human only | Critical |

---

### Minimal Infra Automation for MVP

Don't build infra agent yet. Build guardrails and observability:

```
1. terraform fmt + validate on every PR (CI check)
2. terraform plan output posted as PR comment (no auto-apply)
3. Azure Cost alert → Slack when spend exceeds threshold
4. Drift detection: scheduled terraform plan, alert if non-empty
5. Human applies all changes
```

---

### Prerequisites Before Agent Touches Infra

- [ ] All resources in Terraform (or explicitly tagged legacy/unmanaged)
- [ ] State backend locked and versioned
- [ ] `terraform apply` never runs locally
- [ ] Staging and prod separate state + separate service principals
- [ ] Rollback procedure tested (not just documented)

Agent scope when ready: **generate and plan only, never apply to prod.**

---

### Practical Next Step

1. `az resource list -o table` — full inventory
2. `terraform plan` — measure drift today
3. Pick one resource group, get it 100% Terraform-managed
4. That's the pilot — agent generates modules for that RG only

---

**Milestone to graduate MVP → production:**
- Agent closes >70% of tickets without human code edits
- Agent cost per ticket < defined threshold
- Zero security incidents from agent-written code in 90-day window
- Audit log passes internal review
