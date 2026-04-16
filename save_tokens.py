"""
OAuth1 アクセストークンを取得して .env に保存するスクリプト。
初回のみ実行すること。
"""

import os
import re
import pathlib
from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session

ENV_PATH = pathlib.Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)

CONSUMER_KEY    = os.environ["X_OAUTH_CONSUMER_KEY"]
CONSUMER_SECRET = os.environ["X_OAUTH_CONSUMER_SECRET"]

REQUEST_TOKEN_URL = "https://api.x.com/oauth/request_token"
AUTHORIZE_URL     = "https://api.x.com/oauth/authorize"
ACCESS_TOKEN_URL  = "https://api.x.com/oauth/access_token"
CALLBACK_URL      = "oob"  # PIN-based flow（ブラウザが開く）


def update_env(key: str, value: str) -> None:
    text = ENV_PATH.read_text(encoding="utf-8")
    pattern = rf"^({re.escape(key)}=).*$"
    replacement = rf"\g<1>{value}"
    new_text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
    if new_text == text:
        new_text += f"\n{key}={value}\n"
    ENV_PATH.write_text(new_text, encoding="utf-8")


def main():
    oauth = OAuth1Session(CONSUMER_KEY, client_secret=CONSUMER_SECRET, callback_uri=CALLBACK_URL)
    request_token = oauth.fetch_request_token(REQUEST_TOKEN_URL)

    auth_url = oauth.authorization_url(AUTHORIZE_URL)
    print(f"\n以下のURLをブラウザで開いて認証してください:\n{auth_url}\n")

    pin = input("表示された PIN を入力してください: ").strip()

    oauth = OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=request_token["oauth_token"],
        resource_owner_secret=request_token["oauth_token_secret"],
        verifier=pin,
    )
    access_token = oauth.fetch_access_token(ACCESS_TOKEN_URL)

    access_key    = access_token["oauth_token"]
    access_secret = access_token["oauth_token_secret"]

    update_env("X_OAUTH_ACCESS_TOKEN", access_key)
    update_env("X_OAUTH_ACCESS_TOKEN_SECRET", access_secret)

    print(f"\nトークンを .env に保存しました。")
    print(f"X_OAUTH_ACCESS_TOKEN        = {access_key[:10]}...")
    print(f"X_OAUTH_ACCESS_TOKEN_SECRET = {access_secret[:10]}...")


if __name__ == "__main__":
    main()
