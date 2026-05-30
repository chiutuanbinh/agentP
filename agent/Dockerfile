FROM python:3.14-slim

# System deps: git, gh CLI, curl, build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    build-essential \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
       | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
       > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y gh \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Git config (agent commits need an identity)
RUN git config --global user.email "agent@noreply.local" \
    && git config --global user.name "Dev Agent" \
    && git config --global safe.directory '*'

WORKDIR /agent

# Install Python deps via uv (no project code yet — just tooling layer)
RUN uv pip install --system \
    anthropic \
    claude-agent-sdk \
    langfuse \
    PyGithub \
    jira \
    requests \
    beautifulsoup4 \
    ruff \
    pytest \
    pytest-asyncio \
    python-dotenv

# Workspace mount point for repo checkouts
RUN mkdir /workspace

# Copy agent scripts
COPY run.py swe_agent.py jira_client.py wiki_client.py ./

# Credentials come from env at runtime (Key Vault / ACI env injection)
# ANTHROPIC_API_KEY, GITHUB_TOKEN, JIRA_URL, JIRA_USER, JIRA_API_TOKEN — never baked into image

ENV PYTHONUNBUFFERED=1
# Optional: CONFLUENCE_URL, CONFLUENCE_USER, CONFLUENCE_API_TOKEN (fall back to Jira creds)

CMD ["python", "-u", "run.py"]
