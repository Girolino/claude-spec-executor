#!/usr/bin/env python3
"""
PostToolUse hook for TodoWrite validation.

VALIDATION LAYERS (in order):
1. Expected count file (/tmp/claude-expected-todo-count) - set by /spec-executor skill
2. Canonical file validation - ensures structure consistency during execution
3. Implicit canonical - for normal TodoWrite usage

The hook TRUSTS the /spec-executor skill to set up the expected count.
No auto-discovery - this prevents conflicts with old SPEC.json files
or interference with normal plan mode usage.

Usage: Automatically triggered by Claude Code after TodoWrite calls
Input: JSON from stdin with tool_input.todos
Output: JSON with decision (allow/block) and reason
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_project_dir() -> Path:
    """Get project directory from environment or current working directory."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        return Path(project_dir)
    return Path.cwd()


def get_canonical_path(project_dir: Path) -> Path:
    """Get path to canonical TODO file."""
    return project_dir / ".claude" / "todo-canonical.json"


def extract_task_id(content: str) -> str | None:
    """
    Extract task ID from TODO content.

    Examples:
        "0.1: Verify environment" -> "0.1"
        "  2.3: [5/40] Process item" -> "2.3"
        "1.x: Phase completed" -> "1.x"
    """
    content = content.strip().lstrip(" \t")

    if ":" in content:
        prefix = content.split(":")[0].strip()
        if prefix and ("." in prefix or prefix[0].isdigit()):
            return prefix
    return None


def extract_task_ids(todos: list[dict]) -> set[str]:
    """Extract all task IDs from a TODO list."""
    task_ids = set()
    for todo in todos:
        content = todo.get("content", "")
        task_id = extract_task_id(content)
        if task_id:
            task_ids.add(task_id)
    return task_ids


def is_collapsed_phase(content: str) -> bool:
    """Check if a TODO item is a collapsed phase summary."""
    content = content.strip().lower()
    return ".x:" in content or ".loop:" in content or ("completed" in content and "✓" in content)


def get_phase_number(task_id: str) -> str | None:
    """Extract phase number from task ID."""
    if "." in task_id:
        return task_id.split(".")[0]
    return None


def load_canonical(project_dir: Path) -> dict | None:
    """Load canonical TODO if it exists."""
    canonical_path = get_canonical_path(project_dir)
    if not canonical_path.exists():
        return None

    try:
        with open(canonical_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        return {"_error": f"Failed to read canonical: {e}"}


def save_canonical(
    project_dir: Path,
    todos: list[dict],
    spec_file: str | None = None,
    expected_count: int | None = None
) -> bool:
    """Save TODO as canonical reference."""
    canonical_path = get_canonical_path(project_dir)

    try:
        canonical_path.parent.mkdir(parents=True, exist_ok=True)

        task_ids = list(extract_task_ids(todos))
        task_ids.sort(key=lambda x: (
            int(x.split(".")[0]) if x.split(".")[0].isdigit() else 999,
            x
        ))

        canonical = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "spec_file": spec_file,
            "expected_count": expected_count or len(todos),
            "task_count": len(todos),
            "task_ids": task_ids,
            "todos": todos
        }

        with open(canonical_path, "w") as f:
            json.dump(canonical, f, indent=2)

        return True
    except IOError as e:
        print(f"Warning: Failed to save canonical: {e}", file=sys.stderr)
        return False


def validate_against_canonical(
    new_todos: list[dict],
    canonical: dict
) -> tuple[bool, str]:
    """
    Validate new TODO against canonical.

    Rules:
    1. All original task IDs must be present (or collapsed into phase summaries)
    2. Status changes are allowed
    3. New tasks can be added (for loop expansion)
    4. Task removal is blocked
    """
    original_ids = set(canonical.get("task_ids", []))
    new_ids = extract_task_ids(new_todos)

    missing_ids = set()
    collapsed_phases = set()

    # Find collapsed phases in new todos
    for todo in new_todos:
        content = todo.get("content", "")
        if is_collapsed_phase(content):
            task_id = extract_task_id(content)
            if task_id:
                phase_num = get_phase_number(task_id)
                if phase_num:
                    collapsed_phases.add(phase_num)

    # Check each original ID
    for orig_id in original_ids:
        if orig_id in new_ids:
            continue

        phase_num = get_phase_number(orig_id)
        if phase_num and (phase_num in collapsed_phases or f"{phase_num}.x" in new_ids):
            continue

        missing_ids.add(orig_id)

    if missing_ids:
        sorted_missing = sorted(missing_ids, key=lambda x: (
            int(x.split(".")[0]) if x.split(".")[0].isdigit() else 999,
            x
        ))
        return False, f"Task removal not allowed. Missing: {sorted_missing}"

    # Validate count hasn't decreased unexpectedly
    original_count = canonical.get("task_count", 0)
    new_count = len(new_todos)

    if new_count < original_count and not collapsed_phases:
        return False, (
            f"TODO count decreased from {original_count} to {new_count} "
            f"without proper phase collapse"
        )

    return True, ""


def check_expected_count_file(new_todos: list[dict]) -> tuple[bool, str, int | None]:
    """
    Check against expected count file (explicit expectation).

    Returns: (is_valid, message, expected_count_if_matched)
    """
    expected_file = Path("/tmp/claude-expected-todo-count")

    if not expected_file.exists():
        return True, "", None

    try:
        expected_count = int(expected_file.read_text().strip())
        actual_count = len(new_todos)

        if actual_count != expected_count:
            return False, (
                f"=== TODO COUNT VALIDATION FAILED ===\n"
                f"Expected: {expected_count} items (from explicit expectation)\n"
                f"Actual: {actual_count} items\n\n"
                f"You MUST recreate the TODO with EXACTLY {expected_count} items.\n"
                f"Each task ID (0.1, 0.2, 1.1, etc.) must be a SEPARATE TODO item.\n"
                f"Do NOT group tasks by phase or combine multiple tasks.\n"
                f"====================================="
            ), None

        # Count matched - remove expectation file
        expected_file.unlink()
        return True, "count_validated", expected_count

    except (ValueError, IOError):
        return True, "", None


def output_block(reason: str) -> None:
    """Output a blocking decision."""
    print(json.dumps({
        "decision": "block",
        "reason": reason
    }))


def output_allow(status: str, **kwargs) -> None:
    """Output an allow decision (to stderr for debugging)."""
    print(json.dumps({
        "status": status,
        **kwargs
    }), file=sys.stderr)


def main():
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        output_block(f"Invalid hook input JSON: {e}")
        return

    # Verify this is a TodoWrite call
    tool_name = hook_input.get("tool_name", "")
    if tool_name != "TodoWrite":
        return  # Not our concern

    # Get project directory
    cwd = hook_input.get("cwd", "")
    project_dir = Path(cwd) if cwd else get_project_dir()

    # Extract todos from input
    todos = hook_input.get("tool_input", {}).get("todos", [])

    if not todos:
        return  # Empty TODO, allow

    # =========================================
    # LAYER 1: Check explicit expected count
    # =========================================
    is_valid, message, expected_count = check_expected_count_file(todos)

    if not is_valid:
        output_block(message)
        return

    if message == "count_validated":
        # Explicit count matched - save as canonical for structure validation
        save_canonical(project_dir, todos, None, expected_count)
        output_allow("canonical_created_explicit", task_count=len(todos))
        return

    # =========================================
    # LAYER 2: Validate against existing canonical
    # =========================================
    canonical = load_canonical(project_dir)

    if canonical is not None:
        if "_error" in canonical:
            output_block(canonical["_error"])
            return

        # Check if this is completely new work (no overlap in task IDs)
        # If so, allow overwriting the canonical instead of blocking
        original_ids = set(canonical.get("task_ids", []))
        new_ids = extract_task_ids(todos)
        overlap = original_ids & new_ids

        if len(overlap) == 0 and len(original_ids) > 0 and len(new_ids) > 0:
            # Zero overlap = fresh start, different work context
            # Overwrite canonical instead of blocking
            save_canonical(project_dir, todos)
            output_allow(
                "canonical_replaced_fresh_start",
                task_count=len(todos),
                previous_count=canonical.get("task_count", 0)
            )
            return

        is_valid, error_message = validate_against_canonical(todos, canonical)

        if not is_valid:
            spec_file = canonical.get("spec_file", "SPEC.json")
            output_block(
                f"=== TODO STRUCTURE VALIDATION FAILED ===\n\n"
                f"{error_message}\n\n"
                f"Original task count: {canonical.get('task_count', '?')}\n"
                f"Current task count: {len(todos)}\n\n"
                f"TO RECOVER:\n"
                f"  python3 $SCRIPTS/generate-todo.py --spec {spec_file} --base --format json\n\n"
                f"Then recreate TodoWrite with ALL original task IDs.\n"
                f"========================================"
            )
            return

        # Update canonical with new todos (preserves status changes)
        save_canonical(
            project_dir,
            todos,
            canonical.get("spec_file"),
            canonical.get("expected_count")
        )
        output_allow("validated", task_count=len(todos), canonical_count=canonical.get("task_count", 0))
        return

    # =========================================
    # LAYER 3: No canonical - implicit save
    # =========================================
    # This is normal TodoWrite usage outside of SPEC execution
    save_canonical(project_dir, todos)
    output_allow("canonical_created_implicit", task_count=len(todos))


if __name__ == "__main__":
    main()
