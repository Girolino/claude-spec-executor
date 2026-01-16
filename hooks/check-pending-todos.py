#!/usr/bin/env python3
"""
Stop hook that prevents premature execution stops.

Blocks stopping if there are pending TODO items in the canonical file.
Claude must either continue with pending tasks or use AskUserQuestion if stuck.

This is the escape valve pattern:
- If pending tasks exist → Block and instruct to continue
- If genuinely stuck → Claude uses AskUserQuestion (user helps)
- If all done → Allow stop

No infinite loop because Claude always has an exit:
1. Continue working, OR
2. Ask user for help via AskUserQuestion
"""

import json
import os
import sys
from pathlib import Path


def get_project_dir() -> Path:
    """Get project directory from environment or current working directory."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        return Path(project_dir)
    return Path.cwd()


def get_pending_todos(project_dir: Path) -> tuple[list[str], bool]:
    """
    Read canonical TODO state and return pending items.

    Returns:
        (pending_tasks, is_spec_mode) - only block if in SPEC mode
    """
    canonical_path = project_dir / ".claude" / "todo-canonical.json"

    if not canonical_path.exists():
        return [], False

    try:
        with open(canonical_path) as f:
            canonical = json.load(f)

        # Only block during SPEC execution (has expected_count)
        is_spec_mode = canonical.get("expected_count") is not None

        todos = canonical.get("todos", [])
        pending = [
            t.get("content", "Unknown task")
            for t in todos
            if t.get("status") != "completed"
        ]
        return pending, is_spec_mode
    except (json.JSONDecodeError, IOError):
        return [], False


def main():
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Can't parse input, allow stop to avoid blocking on errors
        return

    # Get project directory from hook input or environment
    cwd = hook_input.get("cwd", "")
    project_dir = Path(cwd) if cwd else get_project_dir()

    pending, is_spec_mode = get_pending_todos(project_dir)

    # Only block during SPEC execution mode
    # Normal TODO usage shouldn't prevent stopping
    if pending and is_spec_mode:
        # Format a few examples of pending tasks
        examples = pending[:3]
        example_str = ", ".join(f'"{t[:40]}..."' if len(t) > 40 else f'"{t}"' for t in examples)
        if len(pending) > 3:
            example_str += f" and {len(pending) - 3} more"

        print(json.dumps({
            "decision": "block",
            "reason": (
                f"{len(pending)} tasks still pending: {example_str}. "
                "Continue execution with the next pending task. "
                "If you are blocked or need clarification, use AskUserQuestion."
            )
        }))
    else:
        # No pending tasks, allow stop
        print(json.dumps({
            "decision": "approve"
        }))


if __name__ == "__main__":
    main()
