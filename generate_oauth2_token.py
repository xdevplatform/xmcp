"""
X OAuth 2.0 Authorization Code + PKCE flow — generate a user-context access token.

Prerequisites (X Developer Portal → your app → User authentication settings):
  - App type: Confidential or Public client (PKCE required for public)
  - OAuth 2.0 enabled
  - Type of App: Web App / Automated App
  - Callback URI: http://127.0.0.1:8976/oauth/callback  (matches X_OAUTH_CALLBACK_* in .env)
  - Website URL: http://127.0.0.1 (or any valid URL)
  - Scopes selected: tweet.read, tweet.write, users.read, follows.read, follows.write,
                     offline.access, bookmark.read, bookmark.write, like.read, like.write

Required .env vars:
  - CLIENT_ID                   (from X Developer Portal → OAuth 2.0 settings)
  - CLIENT_SECRET               (confidential client only — leave empty for public/PKCE-only)
  - X_OAUTH_CALLBACK_HOST       (default 127.0.0.1; use a tailnet/hostname for cross-device auth)
  - X_OAUTH_CALLBACK_PORT       (default 8976)
  - X_OAUTH_CALLBACK_PATH       (default /oauth/callback)

Optional TLS (required when using a non-localhost callback host):
  - X_OAUTH_CALLBACK_SCHEME     (default: https if TLS_CERT_FILE set, else http)
  - TLS_CERT_FILE               (path to PEM cert; e.g. certs/<host>.crt)
  - TLS_KEY_FILE                (path to PEM key)

Tailscale example (run the flow from another tailnet device's browser):
  - Issue cert: `tailscale cert mac-mini.tailbd5748.ts.net` (cert + key land in CWD)
  - Move to certs/ with chmod 600 on the .key
  - Set in .env:
      X_OAUTH_CALLBACK_HOST=mac-mini.tailbd5748.ts.net
      X_OAUTH_CALLBACK_SCHEME=https
      TLS_CERT_FILE=certs/mac-mini.tailbd5748.ts.net.crt
      TLS_KEY_FILE=certs/mac-mini.tailbd5748.ts.net.key
  - Register callback URL in X Dev Portal:
      https://mac-mini.tailbd5748.ts.net:8976/oauth/callback

Usage:
  source .venv/bin/activate
  python generate_oauth2_token.py

The script opens your browser, handles the redirect, exchanges the code for an
access + refresh token, then writes both to .env as X_OAUTH2_ACCESS_TOKEN /
X_OAUTH2_REFRESH_TOKEN. The xmcp server picks up X_OAUTH2_ACCESS_TOKEN and uses
OAuth 2.0 Bearer auth for ALL subsequent API calls (supersedes OAuth 1.0a).
"""

from __future__ import annotations

import base64
import hashlib
import http.server
import os
import re
import secrets
import socketserver
import ssl
import sys
import threading
import urllib.parse
import webbrowser
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
except ImportError:
    print("python-dotenv is required. Run: pip install python-dotenv", file=sys.stderr)
    sys.exit(1)

AUTHORIZE_URL = "https://x.com/i/oauth2/authorize"
TOKEN_URL = "https://api.x.com/2/oauth2/token"

SCOPES = [
    "tweet.read",
    "tweet.write",
    "users.read",
    "follows.read",
    "follows.write",
    "offline.access",       # required for refresh tokens
    "bookmark.read",
    "bookmark.write",
    "like.read",
    "like.write",
    "list.read",
    "list.write",
]


def make_pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).decode("ascii").rstrip("=")
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def wait_for_callback(
    bind_host: str,
    port: int,
    path: str,
    timeout: int = 300,
    ssl_context: ssl.SSLContext | None = None,
) -> dict[str, str]:
    """Listen for the OAuth2 redirect and capture ?code= + ?state= query params.

    Binds on bind_host:port. If ssl_context is provided, serves HTTPS.
    """
    result: dict[str, str] = {}
    done = threading.Event()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != path:
                self.send_error(404)
                return
            params = dict(urllib.parse.parse_qsl(parsed.query))
            result.update(params)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            if "error" in params:
                body = f"<h1>OAuth2 error</h1><pre>{params}</pre><p>Close this tab.</p>"
            else:
                body = "<h1>Authorization complete.</h1><p>You can close this tab.</p>"
            self.wfile.write(body.encode("utf-8"))
            done.set()

        def log_message(self, *_args, **_kwargs):  # silence
            pass

    with socketserver.TCPServer((bind_host, port), Handler) as httpd:
        if ssl_context is not None:
            httpd.socket = ssl_context.wrap_socket(httpd.socket, server_side=True)
        httpd.timeout = 1
        start = threading.Event()
        def serve():
            start.set()
            while not done.is_set():
                httpd.handle_request()
        t = threading.Thread(target=serve, daemon=True)
        t.start()
        start.wait()
        done.wait(timeout=timeout)
        if not done.is_set():
            raise RuntimeError(f"Timed out waiting for OAuth2 callback after {timeout}s")
    return result


def update_env_file(path: Path, updates: dict[str, str]) -> None:
    """Set or replace env vars in a .env file. Preserves other content."""
    text = path.read_text() if path.exists() else ""
    for key, value in updates.items():
        pattern = rf"^{re.escape(key)}=.*$"
        if re.search(pattern, text, flags=re.M):
            text = re.sub(pattern, f"{key}={value}", text, flags=re.M)
        else:
            if text and not text.endswith("\n"):
                text += "\n"
            text += f"{key}={value}\n"
    path.write_text(text)


def main() -> int:
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path, override=True)

    client_id = os.getenv("CLIENT_ID", "").strip()
    client_secret = os.getenv("CLIENT_SECRET", "").strip()
    if not client_id:
        print("ERROR: Set CLIENT_ID in .env (from X Developer Portal OAuth 2.0 settings).", file=sys.stderr)
        return 1

    callback_host = os.getenv("X_OAUTH_CALLBACK_HOST", "127.0.0.1")
    callback_port = int(os.getenv("X_OAUTH_CALLBACK_PORT", "8976"))
    callback_path = os.getenv("X_OAUTH_CALLBACK_PATH", "/oauth/callback")
    cert_file = os.getenv("TLS_CERT_FILE", "").strip()
    key_file = os.getenv("TLS_KEY_FILE", "").strip()
    scheme_override = os.getenv("X_OAUTH_CALLBACK_SCHEME", "").strip().lower()

    ssl_context: ssl.SSLContext | None = None
    if cert_file and key_file:
        cert_path = Path(cert_file)
        key_path = Path(key_file)
        if not cert_path.is_absolute():
            cert_path = Path(__file__).resolve().parent / cert_path
        if not key_path.is_absolute():
            key_path = Path(__file__).resolve().parent / key_path
        if not cert_path.exists() or not key_path.exists():
            print(f"ERROR: TLS cert/key not found: {cert_path} / {key_path}", file=sys.stderr)
            return 1
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))

    scheme = scheme_override or ("https" if ssl_context else "http")
    if callback_host not in ("127.0.0.1", "localhost") and scheme != "https":
        print(
            "ERROR: non-localhost callback hosts must use HTTPS. "
            "Set TLS_CERT_FILE + TLS_KEY_FILE, or set X_OAUTH_CALLBACK_HOST=127.0.0.1.",
            file=sys.stderr,
        )
        return 1

    # Bind on 0.0.0.0 when serving a public hostname so remote browsers can reach us.
    bind_host = "0.0.0.0" if callback_host not in ("127.0.0.1", "localhost") else callback_host
    redirect_uri = f"{scheme}://{callback_host}:{callback_port}{callback_path}"

    print(f"Callback URL: {redirect_uri}")
    print(f"Binding local server on: {bind_host}:{callback_port} ({'HTTPS' if ssl_context else 'HTTP'})")
    print(f"Client type: {'confidential (with secret)' if client_secret else 'public (PKCE only)'}")
    print()

    verifier, challenge = make_pkce_pair()
    state = secrets.token_urlsafe(32)

    auth_params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": " ".join(SCOPES),
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    auth_url = f"{AUTHORIZE_URL}?{urllib.parse.urlencode(auth_params)}"

    print("Opening browser for X OAuth2 consent...")
    print(f"If it doesn't open, visit:\n  {auth_url}\n")
    webbrowser.open(auth_url)

    params = wait_for_callback(bind_host, callback_port, callback_path, ssl_context=ssl_context)
    if "error" in params:
        print(f"OAuth2 authorization failed: {params}", file=sys.stderr)
        return 1
    if params.get("state") != state:
        print("ERROR: state mismatch — possible CSRF. Aborting.", file=sys.stderr)
        return 1
    code = params.get("code")
    if not code:
        print(f"ERROR: no code returned: {params}", file=sys.stderr)
        return 1

    print("Got authorization code. Exchanging for access token...")
    token_payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "code_verifier": verifier,
    }
    auth = (client_id, client_secret) if client_secret else None
    resp = requests.post(
        TOKEN_URL,
        data=token_payload,
        auth=auth,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"ERROR: token exchange failed ({resp.status_code}): {resp.text}", file=sys.stderr)
        return 1

    token_data = resp.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token", "")
    expires_in = token_data.get("expires_in", "?")
    scopes_granted = token_data.get("scope", "")

    if not access_token:
        print(f"ERROR: no access_token in response: {token_data}", file=sys.stderr)
        return 1

    updates = {"X_OAUTH2_ACCESS_TOKEN": access_token}
    if refresh_token:
        updates["X_OAUTH2_REFRESH_TOKEN"] = refresh_token
    update_env_file(env_path, updates)

    print()
    print(f"✓ Access token saved to {env_path}")
    print(f"  Expires in: {expires_in}s")
    print(f"  Scopes granted: {scopes_granted}")
    if refresh_token:
        print(f"  Refresh token saved (X_OAUTH2_REFRESH_TOKEN) — use to renew without re-prompting.")
    else:
        print("  No refresh token (offline.access not granted). Re-run this script when the token expires.")
    print()
    print("Next step: restart Claude Code. xmcp will pick up the OAuth2 token and use it for all requests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
