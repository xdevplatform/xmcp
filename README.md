# X API FastMCP Server

Run a local MCP server that exposes the X API OpenAPI spec as tools using
FastMCP. Streaming and webhook endpoints are excluded.

Speaks the [`2026-07-28`](https://modelcontextprotocol.io/specification/2026-07-28/)
MCP specification (the "MCP 2.0" revision) and still serves handshake-era
clients on `2025-11-25` and earlier from the same endpoint. See
[MCP protocol version](#mcp-protocol-version).

## Prerequisites

- Python 3.10+ (required by FastMCP 4)
- An X Developer Platform app (to get tokens)
- Optional: an xAI API key if you want to run the Grok test client

## Setup (local)

1. Create a virtual environment and install dependencies:
   - `python -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`
2. Create your local `.env`:
   - `cp env.example .env`
   - Required values (do not skip):
     - `X_OAUTH_CONSUMER_KEY`
     - `X_OAUTH_CONSUMER_SECRET`
     - `X_BEARER_TOKEN` (required for this setup; keep it set even if using OAuth1)
   - OAuth1 callback (defaults are fine):
     - `X_OAUTH_CALLBACK_HOST` (default `127.0.0.1`)
     - `X_OAUTH_CALLBACK_PORT` (default `8976`)
     - `X_OAUTH_CALLBACK_PATH` (default `/oauth/callback`)
     - `X_OAUTH_CALLBACK_TIMEOUT` (default `300`)
   - Server settings (optional):
     - `X_API_BASE_URL` (default `https://api.x.com`)
     - `X_API_TIMEOUT` (default `30`)
     - `MCP_HOST` (default `127.0.0.1`)
     - `MCP_PORT` (default `8000`)
     - `MCP_CACHE_TTL` (default `300`; seconds, `0` disables)
     - `X_API_DEBUG` (default `1`)
  - Tool filtering (optional, comma-separated):
    - `X_API_TOOL_ALLOWLIST`
   - Optional Grok test client:
     - `XAI_API_KEY`
     - `XAI_MODEL` (default `grok-4-1-fast`)
     - `MCP_SERVER_URL` (default `http://127.0.0.1:8000/mcp`)
   - Optional OAuth2 token generation:
     - `CLIENT_ID`
     - `CLIENT_SECRET`
     - `X_OAUTH_ACCESS_TOKEN`
    - `X_OAUTH_ACCESS_TOKEN_SECRET` (optional)
   - Optional OAuth1 debug output:
     - `X_OAUTH_PRINT_TOKENS`
     - `X_OAUTH_PRINT_AUTH_HEADER`
3. Register the callback URL in your X Developer App:

```
http://<X_OAUTH_CALLBACK_HOST>:<X_OAUTH_CALLBACK_PORT><X_OAUTH_CALLBACK_PATH>
```

Example (defaults):

```
http://127.0.0.1:8976/oauth/callback
```

4. Start the server:

```
python server.py
```

The MCP endpoint is `http://127.0.0.1:8000/mcp` by default.

5. Connect an MCP client:
- Local client: point it to `http://127.0.0.1:8000/mcp`.
- Remote client: tunnel your local server (e.g., ngrok) and use the public URL.

## MCP protocol version

The server implements the `2026-07-28` MCP specification, the revision the SDKs
ship as their 2.0 major release. What that means here:

- **Stateless.** There is no `initialize`/`initialized` handshake and no
  `Mcp-Session-Id`. Every request carries its own protocol version, client
  identity, and capabilities in `_meta`, so requests can be load balanced
  round-robin across processes.
- **Discovery.** `server/discover` returns the supported versions, capabilities,
  and server identity in one request, with no prior handshake.
- **Cacheable listings.** The tool set is derived from the OpenAPI spec once at
  startup and is immutable for the life of the process, so `tools/list` and
  `server/discover` carry a `ttlMs`/`cacheScope` hint. Tune it with
  `MCP_CACHE_TTL` (seconds); `MCP_CACHE_TTL=0` leaves the protocol default of
  `ttlMs: 0`, which tells clients the result is immediately stale. The hint is
  only honored by `2026-07-28` clients that opt into caching.
- **Backward compatible.** The same `/mcp` endpoint still serves clients that
  use the older `initialize` handshake, including xAI's hosted MCP client used
  by `test_grok_mcp.py`. No separate deployment is needed.

Deprecated MCP features are not used by this server: it has no roots or
sampling, and it logs to stderr through Python's `logging` rather than the
deprecated MCP logging capability.

Authorization to the MCP endpoint itself is unchanged — the server is meant to
run locally and holds the X credentials itself, so the spec's authorization
hardening (issuer validation, Client ID Metadata Documents) does not apply.
If you expose this server publicly, put an authorizing proxy in front of it.

FastMCP 4 is currently a beta (`4.0.0b1`); it is the first release that
implements `2026-07-28`. `pip install -r requirements.txt` picks it up without
`--pre` because the pin names the prerelease explicitly.

## Whitelisting tools

Use `X_API_TOOL_ALLOWLIST` to load a small, explicit set of tools:

```
X_API_TOOL_ALLOWLIST=getUsersByUsername,createPosts,searchPostsRecent
```

Whitelisting is applied at startup when the OpenAPI spec is loaded, so restart
the server after changes. See the full tool list below before building your
allowlist.

## OAuth1 flow (startup behavior)

On startup, the server opens a browser for OAuth1 consent and waits for the
callback. Tokens are kept in memory only for the lifetime of the server
process. Set `X_OAUTH_PRINT_TOKENS=1` to print tokens, or
`X_OAUTH_PRINT_AUTH_HEADER=1` to print request headers.

## Available tool calls (allowlist-ready)

Below is the full list of tool calls you can whitelist via
`X_API_TOOL_ALLOWLIST`. Copy any of these into your `.env` allowlist.

- `addListsMember`
- `addUserPublicKey`
- `appendMediaUpload`
- `blockUsersDms`
- `createCommunityNotes`
- `createComplianceJobs`
- `createDirectMessagesByConversationId`
- `createDirectMessagesByParticipantId`
- `createDirectMessagesConversation`
- `createLists`
- `createMediaMetadata`
- `createMediaSubtitles`
- `createPosts`
- `createUsersBookmark`
- `deleteAllConnections`
- `deleteCommunityNotes`
- `deleteConnectionsByEndpoint`
- `deleteConnectionsByUuids`
- `deleteDirectMessagesEvents`
- `deleteLists`
- `deleteMediaSubtitles`
- `deletePosts`
- `deleteUsersBookmark`
- `evaluateCommunityNotes`
- `finalizeMediaUpload`
- `followList`
- `followUser`
- `getChatConversation`
- `getChatConversations`
- `getCommunitiesById`
- `getComplianceJobs`
- `getComplianceJobsById`
- `getConnectionHistory`
- `getDirectMessagesEvents`
- `getDirectMessagesEventsByConversationId`
- `getDirectMessagesEventsById`
- `getDirectMessagesEventsByParticipantId`
- `getInsights28Hr`
- `getInsightsHistorical`
- `getListsById`
- `getListsFollowers`
- `getListsMembers`
- `getListsPosts`
- `getMarketplaceHandleAvailability`
- `getMediaAnalytics`
- `getMediaByMediaKey`
- `getMediaByMediaKeys`
- `getMediaUploadStatus`
- `getNews`
- `getOpenApiSpec`
- `getPostsAnalytics`
- `getPostsById`
- `getPostsByIds`
- `getPostsCountsAll`
- `getPostsCountsRecent`
- `getPostsLikingUsers`
- `getPostsQuotedPosts`
- `getPostsRepostedBy`
- `getPostsReposts`
- `getSpacesBuyers`
- `getSpacesByCreatorIds`
- `getSpacesById`
- `getSpacesByIds`
- `getSpacesPosts`
- `getTrendsByWoeid`
- `getTrendsPersonalizedTrends`
- `getUsage`
- `getUserPublicKeys`
- `getUsersAffiliates`
- `getUsersBlocking`
- `getUsersBookmarkFolders`
- `getUsersBookmarks`
- `getUsersBookmarksByFolderId`
- `getUsersById`
- `getUsersByIds`
- `getUsersByUsername`
- `getUsersByUsernames`
- `getUsersFollowedLists`
- `getUsersFollowers`
- `getUsersFollowing`
- `getUsersLikedPosts`
- `getUsersListMemberships`
- `getUsersMe`
- `getUsersMentions`
- `getUsersMuting`
- `getUsersOwnedLists`
- `getUsersPinnedLists`
- `getUsersPosts`
- `getUsersRepostsOfMe`
- `getUsersTimeline`
- `hidePostsReply`
- `initializeMediaUpload`
- `likePost`
- `mediaUpload`
- `muteUser`
- `pinList`
- `removeListsMemberByUserId`
- `repostPost`
- `searchCommunities`
- `searchCommunityNotesWritten`
- `searchEligiblePosts`
- `searchNews`
- `searchPostsAll`
- `searchPostsRecent`
- `searchSpaces`
- `searchUsers`
- `sendChatMessage`
- `unblockUsersDms`
- `unfollowList`
- `unfollowUser`
- `unlikePost`
- `unmuteUser`
- `unpinList`
- `unrepostPost`
- `updateLists`

## Generate an OAuth2 user token (optional)

1. Add `CLIENT_ID` and `CLIENT_SECRET` to your `.env`.
2. Update `redirect_uri` in `generate_authtoken.py` to match your app settings.
3. Run `python generate_authtoken.py` and follow the prompts.
4. Copy the printed access token into `.env` as `X_OAUTH_ACCESS_TOKEN`.
   If your flow returns a secret, store it as `X_OAUTH_ACCESS_TOKEN_SECRET`.

## Run the Grok MCP test client (optional)

1. Set `XAI_API_KEY` in `.env`.
2. Make sure your MCP server is running locally (or set `MCP_SERVER_URL`).
3. If Grok is not running on your machine, use ngrok to expose your local MCP
   server and set `MCP_SERVER_URL` to the public HTTPS URL that ends with `/mcp`.
   Example flow: `ngrok http 8000` then `MCP_SERVER_URL=https://<id>.ngrok-free.dev/mcp`.
4. Run `python test_grok_mcp.py`.

## Notes

- Endpoints with `/stream`, `/webhooks`, `/account_activity`, or
  `/activity/subscriptions` in the path are excluded.
- Operations tagged `Stream`, `Webhooks`, `Activity`, or `Account Activity`, or
  marked with `x-twitter-streaming: true`, are excluded. The activity
  subscription endpoints configure webhook delivery, and most of them sit
  outside the `/webhooks` path prefix.
- The OpenAPI spec is fetched from `https://api.x.com/2/openapi.json` at
  startup.
