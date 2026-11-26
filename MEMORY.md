# xmcp — Project Memory

> Agent-facing durable memory for this repo. Auto-loaded via `@MEMORY.md` in CLAUDE.md.
> Human narrative / status: none (no matching Obsidian project note).
> Related global memory: [[reference_bird_cli]] (X MCP + Bird CLI reference), [[reference_x_api_xurl]] (X API access rules — xurl for interactive/CLI use; this repo is the MCP-server path instead).
> Update this after significant work.

## What this is
A local MCP (Model Context Protocol) server that exposes the X (Twitter) API v2 as a set of callable tools via FastMCP, generated from X's OpenAPI spec. Forked from `xdevplatform/xmcp` to `PixelCove/xmcp`, patched to skip the interactive browser OAuth1 flow when tokens are pre-set. Deployed and running as a background LaunchD service (`co.pixelcove.xmcp`), registered in OpenClaw as the `x-api` MCP server.

## Stack & key commands
- Python 3.9+, FastMCP 3.2.0, `httpx`, `python-dotenv`, `requests-oauthlib`, `xai-sdk`, `xdk` (see `requirements.txt`)
- Setup: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`; copy `env.example` → `.env` and fill required X API creds
- Run server: `python server.py` — serves MCP endpoint at `http://127.0.0.1:8000/mcp` (streamable-http transport)
- In production this runs via LaunchD (`co.pixelcove.xmcp`, KeepAlive + RunAtLoad), not a manual foreground process — check `launchctl list | grep xmcp` before starting a second instance
- Tool filtering: `X_API_TOOL_ALLOWLIST` env var (comma-separated tool names) restricts which OpenAPI-derived tools load at startup; restart required after changes
- Optional test client: `python test_grok_mcp.py` (uses `xai-sdk`/Grok to exercise the MCP server)
- Not a dev-up/dev-down project (no Node/Vite/Hydrogen dev server involved) — it's a standalone Python process managed by LaunchD

## Architecture / where things live
- `server.py` — the FastMCP server: loads the X API OpenAPI spec, builds the OAuth1 client, filters tools by allowlist, serves MCP
- `env.example` — template for `.env` (required: `X_OAUTH_CONSUMER_KEY`, `X_OAUTH_CONSUMER_SECRET`, `X_BEARER_TOKEN`; optional OAuth1 callback settings, server settings, `X_API_TOOL_ALLOWLIST`, Grok test-client vars, OAuth2 token-gen vars)
- `test_grok_mcp.py` — sample client that connects a Grok model to the running MCP server for smoke-testing
- `.env` — live local credentials (git-ignored), resolved from 1Password, not fetched via `op run` at runtime
- 17 tools allowlisted in the live deployment: `getUsersByUsername`, `getUsersMe`, `getUsersPosts`, `getUsersMentions`, `getUsersTimeline`, `searchPostsRecent`, `createPosts`, `deletePosts`, `likePost`, `unlikePost`, `repostPost`, `unrepostPost`, `getUsersBookmarks`, `createUsersBookmark`, `deleteUsersBookmark`, `getUsersFollowers`, `getUsersFollowing`

## Durable decisions & gotchas
- Core patch vs. upstream: `build_oauth1_client()` checks for `X_OAUTH_ACCESS_TOKEN` + `X_OAUTH_ACCESS_TOKEN_SECRET` env vars — if set, it skips the interactive browser OAuth1 consent flow entirely (needed since this runs headless under LaunchD). Without them it falls back to upstream's browser-based OAuth1 flow.
- Two remotes: `origin` = `PixelCove/xmcp` (the fork, source of truth for our patches), `upstream` = `xdevplatform/xmcp` (original project, for pulling updates).
- Auth model: OAuth1 (Pixelcove X Developer app) for write/user-context calls; `X_BEARER_TOKEN` alone is sufficient for simple unauthenticated reads (e.g. `GET /2/tweets/{id}`) without needing the OAuth1 tokens at all — useful one-off fallback: `set -a; source ~/Projects/xmcp/.env; set +a` then `curl` with `Authorization: Bearer $X_BEARER_TOKEN`.
- Logs land in `/tmp/xmcp.out.log` and `/tmp/xmcp.err.log` (LaunchD stdout/stderr redirects), not in the repo.
- For interactive/one-off X API calls from a Claude Code session (not through this MCP server), the house rule is `xurl` instead — see [[reference_x_api_xurl]] for identity routing (`jon_a_thang` personal vs `jonpixelcove` business) and per-call metering costs. This repo is the always-on MCP-server path, complementary to `xurl`, not a replacement for it.
- Bird CLI (`@steipete/bird`, cookie-based) is a deprecated, unreliable fallback predating this MCP server — avoid unless both `x-api` MCP and `xurl` are unreachable.
- Secrets: `.env` is git-ignored and populated from 1Password; do not commit it or print its contents.

## Current focus / open threads
_unknown_ — no recent commits beyond a README/env-var naming cleanup (`028a62f`); no open Obsidian note or active-work signal found.

## Links
- Obsidian: none
- Repo remote: https://github.com/PixelCove/xmcp.git (origin, fork) / https://github.com/xdevplatform/xmcp.git (upstream)
- Related memory: [[reference_bird_cli]], [[reference_x_api_xurl]]
