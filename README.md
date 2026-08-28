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

Tasks 2 and 4 share one repository: task 4 extends the bot from task 2, so the two
stages are separated by a tag and a pull request rather than by a second repository.
