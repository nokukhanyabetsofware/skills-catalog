#!/usr/bin/env bash
set -euo pipefail

# args:
# 1: TARGET_REPO (org/repo)
# 2: SKILLS_COMMA_LIST (e.g. "code-review,api-design")
# 3: SKILLS_REPO_URL (URL to skills-catalog)
# 4: SKILLS_SOURCE_REF (branch or commit / usually github.sha)
# 5: BRANCH_NAME (branch to push in target)
# 6: TARGET_PATH (prefix in target repo, e.g. ".codex/skills")
# 7: GIT_AUTHOR_NAME
# 8: GIT_AUTHOR_EMAIL
# env: SYNC_TOKEN should be set

usage() {
  echo "Usage: $0 TARGET_REPO SKILLS_CSV SKILLS_REPO_URL SKILLS_SOURCE_REF BRANCH_NAME TARGET_PATH [GIT_AUTHOR_NAME] [GIT_AUTHOR_EMAIL]" >&2
}

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

if [ "$#" -lt 6 ]; then
  usage
  exit 64
fi

if [ -z "${SYNC_TOKEN:-}" ]; then
  echo "SYNC_TOKEN is required" >&2
  exit 65
fi

TARGET_REPO="$1"
SKILLS_CSV="$2"
SKILLS_REPO_URL="$3"
SKILLS_SOURCE_REF="$4"
BRANCH_NAME="$5"
TARGET_PATH="$6"
GIT_AUTHOR_NAME="${7:-codex-sync-bot}"
GIT_AUTHOR_EMAIL="${8:-codex-sync-bot@local}"

IFS=',' read -r -a RAW_SKILLS <<< "$SKILLS_CSV"
SYNCED_SKILLS=()
for raw_skill in "${RAW_SKILLS[@]}"; do
  skill="$(trim "$raw_skill")"
  if [ -n "$skill" ]; then
    SYNCED_SKILLS+=("$skill")
  fi
done

if [ "${#SYNCED_SKILLS[@]}" -eq 0 ]; then
  echo "No skills were requested for sync" >&2
  exit 66
fi

TARGET_PARENT="$(dirname "$TARGET_PATH")"
TARGET_NAME="$(basename "$TARGET_PATH")"
if [ "$TARGET_PARENT" = "." ]; then
  METADATA_PATH="${TARGET_NAME}_sync.yaml"
else
  METADATA_PATH="${TARGET_PARENT}/${TARGET_NAME}_sync.yaml"
fi

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT
echo "Working in $TMPDIR"
cd "$TMPDIR"

if [[ "$SKILLS_REPO_URL" == https://github.com/* ]]; then
  SKILLS_REPO_WITH_TOKEN="${SKILLS_REPO_URL/https:\/\/github.com/https://${SYNC_TOKEN}@github.com}"
else
  SKILLS_REPO_WITH_TOKEN="$SKILLS_REPO_URL"
fi

echo "Cloning target repo $TARGET_REPO"
git clone "https://x-access-token:${SYNC_TOKEN}@github.com/${TARGET_REPO}.git" target >/dev/null 2>&1 || {
  echo "Failed to clone target repo" >&2
  exit 67
}
cd target

git config user.name "$GIT_AUTHOR_NAME"
git config user.email "$GIT_AUTHOR_EMAIL"

REMOTE_BRANCH_EXISTS=false
if git ls-remote --exit-code --heads origin "$BRANCH_NAME" >/dev/null 2>&1; then
  REMOTE_BRANCH_EXISTS=true
  git fetch origin "$BRANCH_NAME" >/dev/null 2>&1
  git checkout -B "$BRANCH_NAME" "origin/$BRANCH_NAME" >/dev/null 2>&1
else
  git checkout -b "$BRANCH_NAME" >/dev/null 2>&1
fi

git remote add skills-catalog "$SKILLS_REPO_WITH_TOKEN"
git fetch --depth=1 skills-catalog "$SKILLS_SOURCE_REF" >/dev/null 2>&1
SOURCE_SHA="$(git rev-parse FETCH_HEAD)"
echo "Source SHA: $SOURCE_SHA"

MISSING_SKILLS=()
for skill in "${SYNCED_SKILLS[@]}"; do
  if ! git cat-file -e "${SOURCE_SHA}:skills/${skill}/SKILL.md" 2>/dev/null; then
    MISSING_SKILLS+=("$skill")
  fi
done

if [ "${#MISSING_SKILLS[@]}" -gt 0 ]; then
  echo "Unknown skills requested: ${MISSING_SKILLS[*]}" >&2
  exit 68
fi

git rm -rf --ignore-unmatch "$TARGET_PATH" >/dev/null 2>&1 || true
rm -rf "$TARGET_PATH"
mkdir -p "$TARGET_PATH"

for skill in "${SYNCED_SKILLS[@]}"; do
  git archive --format=tar "$SOURCE_SHA" "skills/${skill}" \
    | tar -xf - --strip-components=1 -C "$TARGET_PATH"
done

mkdir -p "$(dirname "$METADATA_PATH")"
{
  printf 'source_repo: %s\n' "$SKILLS_REPO_URL"
  printf 'source_ref: %s\n' "$SKILLS_SOURCE_REF"
  printf 'source_commit: %s\n' "$SOURCE_SHA"
  printf 'synced_at: %s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  printf 'target_path: %s\n' "$TARGET_PATH"
  printf 'skills:\n'
  for skill in "${SYNCED_SKILLS[@]}"; do
    printf '  - %s\n' "$skill"
  done
} > "$METADATA_PATH"

git add -A "$TARGET_PATH" "$METADATA_PATH"

if git diff --quiet --cached; then
  echo "No changes to push for $TARGET_REPO"
  if [ "$REMOTE_BRANCH_EXISTS" = true ]; then
    echo "SYNC_STATUS=branch_unchanged"
  else
    echo "SYNC_STATUS=no_changes"
  fi
  echo "SYNC_BRANCH_NAME=$BRANCH_NAME"
  echo "SYNC_SOURCE_SHA=$SOURCE_SHA"
  echo "SYNC_METADATA_PATH=$METADATA_PATH"
  echo "SYNC_SKILLS=$(IFS=,; printf '%s' "${SYNCED_SKILLS[*]}")"
  exit 0
fi

COMMIT_MSG="Sync skills from skills-catalog@${SOURCE_SHA:0:10} -> ${TARGET_PATH}"
git commit -m "$COMMIT_MSG" >/dev/null 2>&1
git push "https://x-access-token:${SYNC_TOKEN}@github.com/${TARGET_REPO}.git" HEAD:"$BRANCH_NAME" >/dev/null 2>&1

echo "Pushed sync branch $BRANCH_NAME to $TARGET_REPO"
echo "SYNC_STATUS=pushed"
echo "SYNC_BRANCH_NAME=$BRANCH_NAME"
echo "SYNC_SOURCE_SHA=$SOURCE_SHA"
echo "SYNC_METADATA_PATH=$METADATA_PATH"
echo "SYNC_SKILLS=$(IFS=,; printf '%s' "${SYNCED_SKILLS[*]}")"
