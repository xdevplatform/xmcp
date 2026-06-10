#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-/opt/xmcp/.env}"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

set_env() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}=" "$ENV_FILE"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
  else
    printf "%s=%s\n" "$key" "$value" >> "$ENV_FILE"
  fi
}

read -r -p "X_OAUTH_CONSUMER_KEY: " consumer_key
read -r -s -p "X_OAUTH_CONSUMER_SECRET: " consumer_secret
printf "\n"
read -r -s -p "X_BEARER_TOKEN: " bearer_token
printf "\n"

set_env X_OAUTH_CONSUMER_KEY "$consumer_key"
set_env X_OAUTH_CONSUMER_SECRET "$consumer_secret"
set_env X_BEARER_TOKEN "$bearer_token"

chmod 600 "$ENV_FILE"
echo "Updated $ENV_FILE"
