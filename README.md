# X API FastMCP Server

Run a local MCP server that exposes the X API OpenAPI spec as tools using
FastMCP. Streaming and webhook endpoints are excluded.

## Prerequisites

- Python 3.9+
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
     - `X_API_DEBUG` (default `1`)
  - Tool filtering (optional, comma-separated):
    - `X_API_TOOL_ALLOWLIST`
   - Optional Grok test client:
     - `XAI_API_KEY`
     - `XAI_MODEL` (default `grok-4-1-fast`)
     - `MCP_SERVER_URL` (default `http://127.0.0.1:8000/mcp`)
   - Optional OAuth 1.0a pre-provisioned user tokens (skip the browser flow at startup):
     - `X_OAUTH_ACCESS_TOKEN`
     - `X_OAUTH_ACCESS_TOKEN_SECRET`
   - Optional OAuth 2.0 user-context auth (see "Generate an OAuth 2.0 user token" below):
     - `CLIENT_ID`
     - `CLIENT_SECRET` (empty for public/PKCE-only clients)
     - `X_OAUTH2_ACCESS_TOKEN`
     - `X_OAUTH2_REFRESH_TOKEN`
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
- `deleteActivitySubscription`
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
- `getAccountActivitySubscriptionCount`
- `getActivitySubscriptions`
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
- `updateActivitySubscription`
- `updateLists`

## Generate an OAuth 2.0 user token (optional)

Several X API endpoints — bookmarks (`getUsersBookmarks`, `createUsersBookmark`),
`searchNews`, and others — reject OAuth 1.0a with a 403 `Unsupported
Authentication` error. They require **OAuth 2.0 User Context**. Follow
these steps to generate a user-context access token and have the server
use OAuth 2.0 Bearer auth for all outbound requests.

### 1. Configure your X Developer app for OAuth 2.0

In the X Developer Portal → your app → **User authentication settings**:

- App permissions: **Read and write and Direct message** (needed for
  `bookmark.write`, `follows.write`, etc.).
- Type of App: **Web App, Automated App or Bot** (confidential client).
- Callback URI: `http://127.0.0.1:8976/oauth/callback` (the default;
  matches `X_OAUTH_CALLBACK_*` in `.env`). Use a tailnet/LAN hostname
  with HTTPS if you want to complete the browser flow from a different
  device (see the TLS notes in the script docstring).
- Website URL: any valid URL.
- Enable OAuth 2.0.

After saving, copy the **Client ID** and **Client Secret** from the
Keys and Tokens tab.

### 2. Populate `.env`

```
CLIENT_ID=<your client id>
CLIENT_SECRET=<your client secret>
```

### 3. Run the token generator

```
python generate_oauth2_token.py
```

The script opens your browser for consent, listens on
`X_OAUTH_CALLBACK_*` for the redirect, exchanges the authorization code
for tokens, and writes `X_OAUTH2_ACCESS_TOKEN` + `X_OAUTH2_REFRESH_TOKEN`
into `.env`. Requested scopes: `tweet.read tweet.write users.read
follows.read follows.write offline.access bookmark.read bookmark.write
like.read like.write list.read list.write`.

### 4. Restart the server

Whenever `X_OAUTH2_ACCESS_TOKEN` is set, `sign_oauth1_request` writes
`Authorization: Bearer <token>` and skips OAuth 1.0a signing entirely.
Unset it to fall back to OAuth 1.0a.

Access tokens expire in 2 hours. The refresh token (granted via
`offline.access`) can renew the access token without another browser
round-trip; a helper for that is not yet included — re-run
`generate_oauth2_token.py` when the token expires, or add your own
refresh-flow script.

## Run the Grok MCP test client (optional)

1. Set `XAI_API_KEY` in `.env`.
2. Make sure your MCP server is running locally (or set `MCP_SERVER_URL`).
3. If Grok is not running on your machine, use ngrok to expose your local MCP
   server and set `MCP_SERVER_URL` to the public HTTPS URL that ends with `/mcp`.
   Example flow: `ngrok http 8000` then `MCP_SERVER_URL=https://<id>.ngrok-free.dev/mcp`.
4. Run `python test_grok_mcp.py`.

## Notes

- Endpoints with `/stream` or `/webhooks` in the path are excluded.
- Operations tagged `Stream` or `Webhooks`, or marked with
  `x-twitter-streaming: true`, are excluded.
- The OpenAPI spec is fetched from `https://api.twitter.com/2/openapi.json` at
  startup.
