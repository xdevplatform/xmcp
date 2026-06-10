# XMCP Docker Compose Deployment

## Endpoints

- Public MCP endpoint: `http://<server-ip>:8010/mcp`
- Host-only MCP endpoint: `http://127.0.0.1:8010/mcp`
- Dify Docker-network endpoint: `http://xmcp:8000/mcp`

The MCP port requires a Bearer token because this server has full X write/DM
permissions.

## X Developer Portal

In the X app, enable user authentication and set:

- App permissions: `Read and write and Direct message`
- OAuth 1.0a: enabled
- Callback URL: `http://127.0.0.1:8976/oauth/callback`
- Website URL: any valid URL accepted by the X console

Copy these values into `/opt/xmcp/.env`:

- `X_OAUTH_CONSUMER_KEY`
- `X_OAUTH_CONSUMER_SECRET`
- `X_BEARER_TOKEN`

Or run the interactive helper on the server:

```bash
/opt/xmcp/bin/set-x-secrets.sh
```

Leave `X_API_TOOL_ALLOWLIST` empty to load every supported XMCP tool.

`/2/news...` endpoints use `X_BEARER_TOKEN` because X rejects OAuth1 user
signing for these endpoints. Other user-write endpoints continue to use OAuth1.
`X_API_VALIDATE_OUTPUT=0` is intentional: X's live News responses can differ
from the published OpenAPI response schema.

## MCP Access Token

If `MCP_AUTH_TOKEN` is set in `/opt/xmcp/.env`, MCP clients must send:

```text
Authorization: Bearer <MCP_AUTH_TOKEN>
```

- URL: `http://<server-ip>:8010/mcp`
- Header: `Authorization: Bearer <MCP_AUTH_TOKEN>`

Read the token on the server:

```bash
grep '^MCP_AUTH_TOKEN=' /opt/xmcp/.env
```

## First Authorization

1. On your local machine, keep this tunnel open:

   ```bash
   ssh -L 8976:127.0.0.1:8976 root@<server-ip>
   ```

2. On the server, start XMCP and follow the logs:

   ```bash
   cd /opt/xmcp
   docker compose up -d --build
   docker compose logs -f xmcp
   ```

3. Open the printed `OAuth1 authorization URL` in your local browser.

4. After approval, the container writes `X_OAUTH_ACCESS_TOKEN` and
   `X_OAUTH_ACCESS_TOKEN_SECRET` back to `/opt/xmcp/.env`. Verify it:

   ```bash
   grep '^X_OAUTH_ACCESS_TOKEN' /opt/xmcp/.env
   ```

After that, container restarts use the persisted OAuth1 token and do not require
browser approval again unless the token is revoked or the X app keys change.
