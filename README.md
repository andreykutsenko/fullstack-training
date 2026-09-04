# Fullstack Training

Homework assignments from a fullstack development course.

Each task lives in its own folder with a short README on what it does and how to run it.
Deployable projects live in their own repositories and are linked from the table below.

**Stack:** HTML · CSS · Tailwind · JavaScript · TypeScript · React · Python · FastAPI · PostgreSQL · Git

## Assignments

| # | Task | Where | Description |
| --- | --- | --- | --- |
| 1 | [mdlinkcheck](mdlinkcheck/) | this repo | CLI tool that checks links in Markdown files. Generated from a single specification prompt — see the [report](mdlinkcheck/REPORT.md) for metrics, token spend and findings. |
| 2 | [tg-llm-agent](https://github.com/andreykutsenko/tg-llm-agent) | separate repo | Telegram bot in front of a language model. Stateless by design; pluggable backend — local Ollama or Anthropic, switched by env vars only. |
| 3 | [mcp-shop-server](https://github.com/andreykutsenko/mcp-shop-server) | separate repo | MCP server giving an AI agent read-only access to a shop database over stdio. Three independent write-protection layers; proof-of-run artifacts committed under `.agent/tasks/`. |
| 4 | [tg-llm-agent](https://github.com/andreykutsenko/tg-llm-agent) | same repo as #2 | Minimal AI agent: agentic loop, `exec` tool, skill files. Built on top of task 2 — see [PR #1](https://github.com/andreykutsenko/tg-llm-agent/pull/1) for exactly what this task added, and tags `v1-bot` / `v2-agent` for the two states. |
| 6 | [tg-llm-agent](https://github.com/andreykutsenko/tg-llm-agent) | same repo as #2 | Token audit of the agent from task 4: observability layer, a frozen 12-task benchmark with automated checks, and three measured optimisations. Cost per benchmark run cut by **72.3%** ($1.2667 → $0.3513) with success rate unchanged at 100% — see [PR #2](https://github.com/andreykutsenko/tg-llm-agent/pull/2) and the [audit report](https://github.com/andreykutsenko/tg-llm-agent/blob/main/REPORT-audit.md). |

Task 5 (RAG with hybrid search) is in progress and will be added once submitted —
hence the gap in the numbering.

Tasks 2, 4 and 6 share one repository: each extends the previous one, so the stages
are separated by tags and pull requests rather than by new repositories.

Task 6 is worth reading for one finding rather than for the percentage: two
optimisations that each help on their own cancel each other out. Loading skills on
demand shortens the system prompt and saves 46%; prompt caching saves 71%; together
they save only 55%, because the shorter prefix falls below the model's minimum
cacheable length and caching silently stops working. Each optimisation was measured
against the same baseline on its own branch — `feat/opt-cache`, `feat/opt-exec`,
`feat/opt-skills`, `feat/opt-all` — and those branches are kept as evidence.
