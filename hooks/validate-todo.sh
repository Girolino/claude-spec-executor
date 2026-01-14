#!/bin/bash
#
# PostToolUse hook for TodoWrite validation
#
# This hook does TWO things:
# 1. COUNT VALIDATION: If /tmp/claude-expected-todo-count exists, validates exact count
# 2. STRUCTURE FEEDBACK: If a checkpoint is active, suggests proper TODO expansion
#
# Usage: Automatically triggered by Claude Code after TodoWrite calls
#

set -euo pipefail

# Read hook input from stdin
input=$(cat)

# Extract tool name
tool_name=$(echo "$input" | jq -r '.tool_name // empty')

# Only validate TodoWrite calls
if [[ "$tool_name" != "TodoWrite" ]]; then
  exit 0
fi

# Get actual TODO count
actual_count=$(echo "$input" | jq '.tool_input.todos | length // 0')

# ============================================
# PART 1: COUNT VALIDATION (blocking)
# ============================================

expected_file="/tmp/claude-expected-todo-count"
if [[ -f "$expected_file" ]]; then
  expected_count=$(cat "$expected_file")

  # Validate expected_count is a number
  if [[ "$expected_count" =~ ^[0-9]+$ ]]; then
    if [[ "$actual_count" -ne "$expected_count" ]]; then
      # Return blocking feedback as JSON
      jq -n \
        --arg expected "$expected_count" \
        --arg actual "$actual_count" \
        '{
          "decision": "block",
          "reason": "=== TODO COUNT VALIDATION FAILED ===\nExpected: \($expected) items\nActual: \($actual) items\n\nYou MUST recreate the TODO with EXACTLY \($expected) items.\nDo NOT proceed until counts match.\n====================================="
        }'
      exit 0
    fi

    # Count matched - clean up expectation file
    rm -f "$expected_file"
    echo '{"status": "count_validated", "count": '$actual_count'}' >&2
  fi
fi

# ============================================
# PART 2: STRUCTURE FEEDBACK (informational)
# ============================================

# Look for active checkpoints
CHECKPOINT_DIR=".claude/checkpoints"
if [[ -d "$CHECKPOINT_DIR" ]]; then
  for checkpoint_file in "$CHECKPOINT_DIR"/*.json; do
    if [[ -f "$checkpoint_file" ]]; then
      checkpoint_status=$(jq -r '.status // "unknown"' "$checkpoint_file" 2>/dev/null || echo "unknown")

      if [[ "$checkpoint_status" == "in_progress" ]]; then
        # We have an active checkpoint - extract info
        checkpoint_name=$(basename "$checkpoint_file" .json)
        current_index=$(jq -r '.current_index // 0' "$checkpoint_file")
        current_item=$(jq -r '.current_item_name // "Unknown"' "$checkpoint_file")
        current_item_id=$(jq -r '.current_item_id // ""' "$checkpoint_file")
        total=$(jq -r '.total_items // 0' "$checkpoint_file")
        completed=$(jq -r '.completed_items | length' "$checkpoint_file")
        current_task=$(jq -r '.current_task // "2.0"' "$checkpoint_file")

        # Check if TODO contains the current item name (indicating proper expansion)
        # Use grep -F for literal string matching (no regex metacharacter issues)
        todo_content=$(echo "$input" | jq -r '.tool_input.todos[].content' 2>/dev/null | tr '\n' ' ')
        item_index_pattern="[$(( current_index + 1 ))/"

        has_item_name=$(echo "$todo_content" | grep -F "$current_item" || true)
        has_index_pattern=$(echo "$todo_content" | grep -F "$item_index_pattern" || true)

        if [[ -z "$has_item_name" ]] && [[ -z "$has_index_pattern" ]]; then
          # TODO doesn't have current profile expanded - give feedback

          # Get SPEC file from checkpoint if stored, otherwise guess
          spec_file=$(jq -r '.spec_file // ""' "$checkpoint_file" 2>/dev/null)
          if [[ -z "$spec_file" ]] || [[ ! -f "$spec_file" ]]; then
            # Fallback: try to find a SPEC file
            spec_file=""
            for possible_spec in .claude/skills/*/SPEC/*.json SPEC.json; do
              if [[ -f "$possible_spec" ]]; then
                spec_file="$possible_spec"
                break
              fi
            done
          fi

          profile_num=$((current_index + 1))

          jq -n \
            --arg profile_num "$profile_num" \
            --arg profile_name "$current_item" \
            --arg total "$total" \
            --arg completed "$completed" \
            --arg current_task "$current_task" \
            --arg checkpoint "$checkpoint_name" \
            --arg spec "$spec_file" \
            --arg actual "$actual_count" \
            '{
              "decision": "block",
              "reason": "=== TODO STRUCTURE FEEDBACK ===\n\nActive checkpoint detected: \($checkpoint)\n- Current profile: #\($profile_num)/\($total) - \($profile_name)\n- Completed profiles: \($completed)/\($total)\n- Current task: \($current_task)\n\nYour TODO has \($actual) items but does NOT show the current profile expanded.\n\nTo generate the correct TODO structure, run:\n\n  python3 .claude/skills/spec-executor/scripts/generate-todo.py \\\n    --spec \($spec) \\\n    --checkpoint \($checkpoint) \\\n    --format preview\n\nThen recreate the TODO with the expanded structure.\nOr use --format json to get the exact JSON for TodoWrite.\n================================="
            }'
          exit 0
        fi

        # TODO has proper expansion - give positive feedback
        echo "{\"status\": \"structure_ok\", \"checkpoint\": \"$checkpoint_name\", \"profile\": \"$current_item\", \"progress\": \"$completed/$total\"}" >&2
        break
      fi
    fi
  done
fi

exit 0
