#!/usr/bin/env bash
# Hook: At end of turn (Stop), check if any source files were modified
# and remind Claude to update documentation if needed.

set -euo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
if [ -z "$REPO_ROOT" ]; then
  exit 0
fi

cd "$REPO_ROOT"

# Get all modified/added files (staged + unstaged) excluding doc files
SOURCE_FILES=$(git diff --name-only HEAD 2>/dev/null; git diff --name-only 2>/dev/null; git ls-files --others --exclude-standard 2>/dev/null) || true

# Filter to only source files (exclude docs, config, etc.)
HAS_SOURCE_CHANGES=false
while IFS= read -r file; do
  [ -z "$file" ] && continue

  # Skip root-level .md files (README.md, CLAUDE.md, etc.)
  if [[ "$file" != */* && "$file" == *.md ]]; then
    continue
  fi
  # Skip .claude/ config files
  if [[ "$file" == .claude/* ]]; then
    continue
  fi
  # Skip SKILL.md and reference docs
  if [[ "$file" == */SKILL.md || ("$file" == */references/*.md) ]]; then
    continue
  fi

  HAS_SOURCE_CHANGES=true
  break
done <<< "$SOURCE_FILES"

if [ "$HAS_SOURCE_CHANGES" = false ]; then
  exit 0
fi

# Emit reminder via Stop hook output
jq -n '{
  "hookSpecificOutput": {
    "hookEventName": "Stop",
    "additionalContext": "DOCUMENTATION REMINDER: Source files were modified this turn. Before finishing, check if any of these docs need updating:\n- README.md (user-facing docs, skill descriptions, usage examples)\n- CLAUDE.md (developer guidance, file listings, skill descriptions)\n- skills/*/SKILL.md (skill-specific instructions if the skill was modified)\n- skills/*/references/*.md (reference docs if APIs or behavior changed)\nOnly update docs that are actually affected by the changes made."
  }
}'
