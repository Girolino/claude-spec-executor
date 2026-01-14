#!/usr/bin/env python3
"""
Count tasks in SPEC.json or SPEC.md files.

Usage:
    python3 count_tasks.py <spec-file>

Output:
    Total tasks: N
    [List of all task IDs for verification]
"""

import json
import re
import sys
from pathlib import Path


def extract_tasks_from_list(task_list: list) -> list[str]:
    """Extract tasks from a list of task objects."""
    tasks = []
    for task in task_list:
        task_id = task.get('id', '')
        task_desc = task.get('task', '')[:50]  # Truncate for display
        if task_id and task_desc:
            tasks.append(f"{task_id}: {task_desc}")
    return tasks


def count_json_tasks(spec_path: Path) -> tuple[int, list[str]]:
    """Count tasks in a SPEC.json file."""
    with open(spec_path, 'r') as f:
        spec = json.load(f)

    tasks = []
    phases = spec.get('phases', [])

    for phase in phases:
        # Regular tasks array
        phase_tasks = phase.get('tasks', [])
        tasks.extend(extract_tasks_from_list(phase_tasks))

        # Loop tasks (nested structure)
        loop = phase.get('loop', {})
        if loop:
            loop_tasks = loop.get('tasks', [])
            tasks.extend(extract_tasks_from_list(loop_tasks))

    return len(tasks), tasks


def count_md_tasks(spec_path: Path) -> tuple[int, list[str]]:
    """Count tasks in a SPEC.md file."""
    with open(spec_path, 'r') as f:
        content = f.read()

    tasks = []

    # Pattern 1: "- [ ] Task description" (checkbox style)
    checkbox_pattern = r'- \[ \] (.+)'
    for match in re.finditer(checkbox_pattern, content):
        tasks.append(match.group(1)[:50])

    # Pattern 2: "#### X.Y Task description" or "### X.Y Task"
    header_pattern = r'#{3,4}\s+(\d+\.\d+)\s+(.+)'
    for match in re.finditer(header_pattern, content):
        task_id = match.group(1)
        task_desc = match.group(2)[:50]
        tasks.append(f"{task_id}: {task_desc}")

    # Pattern 3: "| X.Y | task | description |" (table format)
    table_pattern = r'\|\s*(\d+\.\d+)\s*\|\s*([^|]+)\s*\|'
    for match in re.finditer(table_pattern, content):
        task_id = match.group(1)
        task_desc = match.group(2).strip()[:50]
        tasks.append(f"{task_id}: {task_desc}")

    # Deduplicate while preserving order
    seen = set()
    unique_tasks = []
    for task in tasks:
        if task not in seen:
            seen.add(task)
            unique_tasks.append(task)

    return len(unique_tasks), unique_tasks


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 count_tasks.py <spec-file>")
        sys.exit(1)

    spec_path = Path(sys.argv[1])

    if not spec_path.exists():
        print(f"Error: File not found: {spec_path}")
        sys.exit(1)

    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    if spec_path.suffix == '.json':
        count, tasks = count_json_tasks(spec_path)
    elif spec_path.suffix == '.md':
        count, tasks = count_md_tasks(spec_path)
    else:
        print(f"Error: Unsupported file type: {spec_path.suffix}")
        print("Supported: .json, .md")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"SPEC FILE: {spec_path.name}")
    print(f"{'='*50}")
    print(f"\nTotal tasks: {count}")
    print(f"\nYour TODO must have EXACTLY {count} items.")
    print(f"{'='*50}")

    # Warning for large task counts
    if count > 400:
        print(f"\n{'!'*50}")
        print("WARNING: SPEC has more than 400 tasks!")
        print(f"{'!'*50}")
        print(f"""
This SPEC has {count} tasks which may cause issues:
- Context window overflow during TODO creation
- Very long execution time (potentially days)
- Risk of Claude summarizing or skipping tasks

RECOMMENDATION: Split into multiple smaller SPECs:
- feature-part1.json (Phase 0-N, ~150-200 tasks)
- feature-part2.json (Phase N-M, ~150-200 tasks)
- etc.

Each SPEC runs as a separate session with handoff via
the SPEC.md Execution Log.

STOP and ask the user to split before proceeding.
""")

    if verbose:
        print("\nAll tasks:")
        for i, task in enumerate(tasks, 1):
            print(f"  {i:3d}. {task}")
    else:
        print("\n(Run with -v or --verbose to see all task IDs)")


if __name__ == "__main__":
    main()
