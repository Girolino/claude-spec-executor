#!/usr/bin/env python3
"""
PostToolUse hook for TodoWrite validation.

Ensures TODO integrity during long SPEC executions by:
1. Saving a "canonical" TODO on first write
2. Validating all subsequent writes against the canonical
3. Allowing status changes but blocking task removal

Usage: Automatically triggered by Claude Code after TodoWrite calls
Input: JSON from stdin with tool_input.todos
Output: JSON with decision (allow/block) and reason

Canonical file: .claude/todo-canonical.json
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_project_dir() -> Path:
    """Get project directory from environment or current working directory."""
    # Try environment variable first
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        return Path(project_dir)

    # Fall back to cwd from hook input (set later) or current directory
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
        "phase-2: Loop (5/40)" -> "phase-2"
    """
    content = content.strip()

    # Remove leading whitespace/indentation markers
    content = content.lstrip(" \t")

    # Pattern: "X.Y: description" or "X.x: description" or "phase-N: description"
    if ":" in content:
        prefix = content.split(":")[0].strip()
        # Valid task IDs: "0.1", "2.10", "1.x", "phase-2"
        if prefix and (
            "." in prefix or
            prefix.startswith("phase-") or
            prefix[0].isdigit()
        ):
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
    """
    Check if a TODO item is a collapsed phase summary.

    Examples:
        "0.x: Pre-Flight completed" -> True
        "1.x: Discovery (5/5) ✓" -> True
        "2.loop: Process items (5/40)" -> True
        "0.1: Verify environment" -> False
    """
    content = content.strip()

    # Patterns for collapsed phases
    if ".x:" in content.lower():
        return True
    if ".loop:" in content.lower():
        return True
    if "completed" in content.lower() and "✓" in content:
        return True

    return False


def normalize_task_id(task_id: str) -> str:
    """
    Normalize task ID for comparison.

    Handles collapsed phases like "0.x" which represent "0.1", "0.2", etc.
    """
    return task_id.lower().strip()


def get_phase_number(task_id: str) -> str | None:
    """Extract phase number from task ID."""
    if "." in task_id:
        return task_id.split(".")[0]
    if task_id.startswith("phase-"):
        return task_id.replace("phase-", "")
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


def find_spec_file(project_dir: Path) -> str | None:
    """Try to find SPEC.json in common locations."""
    candidates = [
        project_dir / "SPEC.json",
        project_dir / "spec.json",
        project_dir / ".claude" / "SPEC.json",
    ]

    # Also check for any .json file with "spec" in the name
    for json_file in project_dir.glob("**/SPEC*.json"):
        if json_file.is_file():
            return str(json_file.relative_to(project_dir))

    for candidate in candidates:
        if candidate.exists():
            return str(candidate.relative_to(project_dir))

    return None


def save_canonical(project_dir: Path, todos: list[dict], spec_file: str | None = None) -> bool:
    """Save TODO as canonical reference."""
    canonical_path = get_canonical_path(project_dir)

    # Try to find spec file if not provided
    if spec_file is None:
        spec_file = find_spec_file(project_dir)

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


def clear_canonical(project_dir: Path) -> None:
    """Clear canonical file (called when spec execution completes)."""
    canonical_path = get_canonical_path(project_dir)
    if canonical_path.exists():
        canonical_path.unlink()


def validate_todos(
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

    Returns: (is_valid, error_message)
    """
    original_ids = set(canonical.get("task_ids", []))
    new_ids = extract_task_ids(new_todos)

    # Check for removed tasks
    # But allow collapsed phases (e.g., "0.x" can replace "0.1", "0.2", "0.3")
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
            continue  # Present, OK

        # Check if this task's phase is collapsed
        phase_num = get_phase_number(orig_id)
        if phase_num and phase_num in collapsed_phases:
            continue  # Collapsed into phase summary, OK

        # Check if there's a matching .x collapse
        if phase_num and f"{phase_num}.x" in new_ids:
            continue  # Collapsed, OK

        missing_ids.add(orig_id)

    if missing_ids:
        sorted_missing = sorted(missing_ids, key=lambda x: (
            int(x.split(".")[0]) if x.split(".")[0].isdigit() else 999,
            x
        ))
        return False, f"Task removal not allowed. Missing: {sorted_missing}"

    # Validate count hasn't decreased unexpectedly
    # (allow decrease only if phases are properly collapsed)
    original_count = canonical.get("task_count", 0)
    new_count = len(new_todos)

    if new_count < original_count and not collapsed_phases:
        return False, (
            f"TODO count decreased from {original_count} to {new_count} "
            f"without proper phase collapse"
        )

    return True, ""


def check_expected_count(new_todos: list[dict]) -> tuple[bool, str]:
    """
    Check against expected count file (for initial validation).
    This is the original behavior from validate-todo.sh.
    """
    expected_file = Path("/tmp/claude-expected-todo-count")

    if not expected_file.exists():
        return True, ""

    try:
        expected_count = int(expected_file.read_text().strip())
        actual_count = len(new_todos)

        if actual_count != expected_count:
            return False, (
                f"=== TODO COUNT VALIDATION FAILED ===\n"
                f"Expected: {expected_count} items\n"
                f"Actual: {actual_count} items\n\n"
                f"You MUST recreate the TODO with EXACTLY {expected_count} items.\n"
                f"Do NOT proceed until counts match.\n"
                f"====================================="
            )

        # Count matched - remove expectation file and save as canonical
        expected_file.unlink()
        return True, "count_validated"

    except (ValueError, IOError):
        return True, ""


def main():
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({
            "decision": "block",
            "reason": f"Invalid hook input JSON: {e}"
        }))
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

    # PART 1: Check expected count (initial validation)
    is_valid, message = check_expected_count(todos)

    if not is_valid:
        print(json.dumps({
            "decision": "block",
            "reason": message
        }))
        return

    # If count was just validated, save as canonical
    if message == "count_validated":
        save_canonical(project_dir, todos)
        print(json.dumps({
            "status": "canonical_created",
            "task_count": len(todos)
        }), file=sys.stderr)
        return

    # PART 2: Validate against canonical (continuous validation)
    canonical = load_canonical(project_dir)

    if canonical is None:
        # No canonical exists and no expected count - save this as canonical
        # This handles cases where spec-executor wasn't used
        save_canonical(project_dir, todos)
        print(json.dumps({
            "status": "canonical_created_implicit",
            "task_count": len(todos)
        }), file=sys.stderr)
        return

    if "_error" in canonical:
        print(json.dumps({
            "decision": "block",
            "reason": canonical["_error"]
        }))
        return

    # Validate against canonical
    is_valid, error_message = validate_todos(todos, canonical)

    if not is_valid:
        # Find SPEC file from canonical if available
        spec_file = canonical.get("spec_file", "SPEC.json")

        print(json.dumps({
            "decision": "block",
            "reason": (
                f"=== TODO VALIDATION FAILED ===\n\n"
                f"{error_message}\n\n"
                f"Original task count: {canonical.get('task_count', '?')}\n"
                f"Current task count: {len(todos)}\n\n"
                f"TO RECOVER, regenerate the TODO from SPEC:\n\n"
                f"  # Option 1: Use generate-todo.py\n"
                f"  python3 $SCRIPTS/generate-todo.py --spec {spec_file} --base --format json\n\n"
                f"  # Option 2: Read canonical directly\n"
                f"  cat {get_canonical_path(project_dir)}\n\n"
                f"Then recreate TodoWrite with ALL original task IDs.\n"
                f"==============================="
            )
        }))
        return

    # Validation passed
    print(json.dumps({
        "status": "validated",
        "task_count": len(todos),
        "canonical_count": canonical.get("task_count", 0)
    }), file=sys.stderr)


if __name__ == "__main__":
    main()
