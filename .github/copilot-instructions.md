# GitHub Copilot Instructions

## PR Review Checklist

Apply these checks to every pull request review.

### General Code Review

- Verify logic correctness and edge cases
- Flag security issues (injection, auth bypass, secret exposure)
- Check error handling at system boundaries (user input, external APIs)
- Ensure no dead code, unused imports, or debug artifacts
- Confirm tests cover the changed behavior, not just structure

---

## Prompt Review (Required When PR Contains Prompts)

**Trigger:** Any file change containing a system prompt, user prompt template, few-shot examples, or prompt string (`.txt`, `.md`, `.py`, `.ts`, `.json` — look for strings sent to LLM APIs).

### Evaluate Against These Techniques

#### Clarity & Structure
- [ ] **Role/persona defined** — system prompt assigns a clear role before instructions
- [ ] **XML/structural tags used** — `<context>`, `<instructions>`, `<examples>`, `<output_format>` separate sections ([Anthropic best practice](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags))
- [ ] **Output format specified explicitly** — JSON schema, markdown shape, or example output shown

#### Reasoning Quality
- [ ] **Chain-of-Thought elicited** — complex tasks ask model to reason step-by-step before answering ([CoT guide](https://www.promptingguide.ai/techniques/cot))
- [ ] **No premature conclusion forcing** — prompt doesn't say "answer directly" for tasks requiring reasoning

#### Examples
- [ ] **Few-shot examples present** where output format is non-trivial (2–5 examples) ([few-shot guide](https://www.promptingguide.ai/techniques/fewshot))
- [ ] **Examples are representative** — cover edge cases, not just happy path

#### Prompt Chaining & Decomposition
- [ ] **Complex tasks decomposed** — long multi-step workflows split into sequential prompts, not one giant prompt ([prompt chaining](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/chain-prompts))
- [ ] **Each prompt has single responsibility**

#### Context & Grounding
- [ ] **Relevant context injected before query** — avoids hallucination by supplying data (RAG pattern)
- [ ] **Context window not bloated** — irrelevant or redundant context removed

#### Robustness
- [ ] **Ambiguous instructions eliminated** — test: would two different people interpret the instruction the same way?
- [ ] **Failure modes handled** — prompt instructs model what to do when it can't answer (e.g. "If unknown, say so")
- [ ] **No prompt injection surface** — user-supplied text wrapped or sanitized before insertion

#### 2024–2025 Techniques (Flag If Applicable)
- [ ] **Extended thinking / plan mode** used for complex reasoning tasks where model supports it
- [ ] **Meta-prompting considered** — for pipelines generating sub-prompts dynamically ([meta-prompting](https://www.promptingguide.ai/techniques/meta-prompting))
- [ ] **Self-consistency** applied for high-stakes classification (multiple samples + majority vote)

### Prompt Review Comment Format

One line per finding. Location, problem, fix. No throat-clearing.

**Format:** `<file>:L<line>: <severity> <problem>. <fix>. [<ref>]`

**Severity:**
- `🔴 bug:` — broken behavior (hallucination surface, injection vector, wrong output type)
- `🟡 risk:` — works but fragile (no failure fallback, ambiguous instruction, bloated context)
- `🔵 nit:` — best-practice gap, low impact. Author can ignore
- `❓ q:` — genuine question about intent, not a suggestion

**Drop:**
- "You might want to consider..." → use `nit:`
- "It seems like..." → use `q:`
- Restating what the prompt does — reviewer can read it
- Hedging ("perhaps", "maybe") — if unsure use `q:`

**Keep:**
- Exact line numbers
- Exact variable/template/tag names in backticks
- Concrete fix, not "improve this section"
- Reference URL when technique is non-obvious

**Examples:**

✅ `prompts/summarize.py:L12: 🔴 bug: no role defined. Add system prompt: "You are a ..."`

✅ `agent/prompts.py:L34-89: 🟡 risk: monolithic prompt does 5 tasks. Split into chained prompts. [chain-prompts](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/chain-prompts)`

✅ `templates/qa.txt:L5: 🔵 nit: no XML tags separating context from instructions. Wrap with <context></context>. [xml-tags](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags)`

✅ `src/agent.py:L22: 🔴 bug: user input interpolated directly into prompt. Prompt injection risk. Sanitize or wrap in <user_input></user_input>.`

**Security findings** (CVE-class prompt injection, data exfiltration via prompt): write full paragraph with reference, then resume terse.

### Reference Links

| Topic | URL |
|-------|-----|
| Anthropic Prompt Engineering Overview | https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview |
| Anthropic Claude 4 Best Practices | https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices |
| OpenAI Prompt Engineering Guide | https://platform.openai.com/docs/guides/prompt-engineering |
| DAIR.AI Prompt Engineering Guide | https://www.promptingguide.ai/ |
| Chain-of-Thought Prompting | https://www.promptingguide.ai/techniques/cot |
| Few-Shot Prompting | https://www.promptingguide.ai/techniques/fewshot |
| Meta-Prompting | https://www.promptingguide.ai/techniques/meta-prompting |
| Prompt Chaining (Anthropic) | https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/chain-prompts |
| XML Tags (Anthropic) | https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags |
| Systematic Survey (arXiv 2406.06608) | https://arxiv.org/abs/2406.06608 |
