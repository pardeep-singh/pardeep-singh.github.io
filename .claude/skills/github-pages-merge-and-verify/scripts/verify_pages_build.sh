#!/bin/bash
# Usage: verify_pages_build.sh <owner/repo> <base-url> [page ...]
# Run on main after pull. Waits for the Pages build of HEAD, then prints HTTP status per page.
set -u
repo="$1"; base="$2"; shift 2
head_sha=$(git rev-parse HEAD)
status=""
for _ in $(seq 1 30); do
  line=$(gh api "repos/$repo/pages/builds/latest" --jq '[.status,.commit]|@tsv')
  case "$line" in
    *"$head_sha"*)
      case "$line" in
        built*|errored*) status="$line"; break;;
      esac;;
  esac
  sleep 10
done
echo "build: ${status:-timeout}"
for p in "$@"; do
  printf '%s /%s\n' "$(curl -s -o /dev/null -w '%{http_code}' "$base/$p")" "$p"
done
