#!/usr/bin/env bash
# Creates or updates the "Jobs <date>" issue. Comments when (new) AI scores arrive, so GitHub emails the owner.
set -euo pipefail

DATE="$1"
TITLE="Jobs $DATE"
SCORED_MARK="scored against your profile"

gh label create jobs --color 0E8A16 --description "Daily job digest" >/dev/null 2>&1 || true

BODY_FILE=$(mktemp)
python -m jobagent render "$DATE" > "$BODY_FILE"

# List (not search) so a just-created issue is found immediately
NUMBER=$(gh issue list --label jobs --state all --limit 50 --json number,title \
  --jq ".[] | select(.title == \"$TITLE\") | .number" | head -n1)

if [ -z "$NUMBER" ]; then
  # Assigning the owner makes GitHub notify them; it fails for org-owned repos, so fall back
  gh issue create --title "$TITLE" --label jobs --body-file "$BODY_FILE" --assignee "$GITHUB_REPOSITORY_OWNER" \
    || gh issue create --title "$TITLE" --label jobs --body-file "$BODY_FILE"
  exit 0
fi

OLD_BODY=$(gh issue view "$NUMBER" --json body --jq .body)
gh issue edit "$NUMBER" --body-file "$BODY_FILE"

# Line 2 is the summary ("N worth a look out of M…"); a change there means new or more scores
NEW_SUMMARY=$(sed -n '2p' "$BODY_FILE")
OLD_SUMMARY=$(sed -n '2p' <<<"$OLD_BODY" | tr -d '\r')
if grep -q "$SCORED_MARK" "$BODY_FILE" && [ "$NEW_SUMMARY" != "$OLD_SUMMARY" ]; then
  gh issue comment "$NUMBER" --body "Scores are in: $NEW_SUMMARY"
fi
