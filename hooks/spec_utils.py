#!/usr/bin/env python3
"""
Shared utilities for SPEC file operations.

Provides functions for:
- Finding SPEC files in a project
- Counting tasks in SPEC.json/SPEC.md
- Extracting task IDs for validation

Used by both count_tasks.py and validate-todo.py
"""

import json
import re
from pathlib import Path


def find_spec_file(project_dir: Path) -> Path | None:
    """
    Find SPEC.json in the project directory.

    Search order:
    1. SPEC.json in project root
    2. spec.json in project root
    3. .claude/SPEC.json
    4. Any *SPEC*.json file

    Returns: Path to SPEC file or None if not found
    """
    candidates = [
        project_dir / "SPEC.json",
        project_dir / "spec.json",
        project_dir / ".claude" / "SPEC.json",
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate

    # Fallback: search for any SPEC*.json
    for json_file in project_dir.glob("**/SPEC*.json"):
        if json_file.is_file():
            # Skip files in node_modules, .git, etc.
            parts = json_file.parts
            if not any(p.startswith('.') or p == 'node_modules' for p in parts):
                return json_file

    return None


def extract_task_ids_from_list(task_list: list) -> list[str]:
    """Extract task IDs from a list of task objects."""
    ids = []
    for task in task_list:
        task_id = task.get('id', '')
        if task_id:
            ids.append(task_id)
    return ids


def count_json_tasks(spec_path: Path) -> tuple[int, list[str]]:
    """
    Count tasks in a SPEC.json file.

    Returns: (count, list_of_task_ids)
    """
    with open(spec_path, 'r') as f:
        spec = json.load(f)

    task_ids = []
    phases = spec.get('phases', [])

    for phase in phases:
        # Regular tasks array
        phase_tasks = phase.get('tasks', [])
        task_ids.extend(extract_task_ids_from_list(phase_tasks))

        # Loop tasks (nested structure)
        loop = phase.get('loop', {})
        if loop:
            loop_tasks = loop.get('tasks', [])
            task_ids.extend(extract_task_ids_from_list(loop_tasks))

    return len(task_ids), task_ids


def count_md_tasks(spec_path: Path) -> tuple[int, list[str]]:
    """
    Count tasks in a SPEC.md file.

    Returns: (count, list_of_task_ids)
    """
    with open(spec_path, 'r') as f:
        content = f.read()

    task_ids = []

    # Pattern: "#### X.Y Task description" or "### X.Y Task"
    header_pattern = r'#{3,4}\s+(\d+\.\d+)\s+'
    for match in re.finditer(header_pattern, content):
        task_ids.append(match.group(1))

    # Pattern: "| X.Y | task | description |" (table format)
    table_pattern = r'\|\s*(\d+\.\d+)\s*\|'
    for match in re.finditer(table_pattern, content):
        task_id = match.group(1)
        if task_id not in task_ids:
            task_ids.append(task_id)

    return len(task_ids), task_ids


def count_spec_tasks(spec_path: Path) -> tuple[int, list[str]] | None:
    """
    Count tasks in a SPEC file (JSON or MD).

    Returns: (count, list_of_task_ids) or None if file type unsupported
    """
    if not spec_path.exists():
        return None

    try:
        if spec_path.suffix == '.json':
            return count_json_tasks(spec_path)
        elif spec_path.suffix == '.md':
            return count_md_tasks(spec_path)
        else:
            return None
    except (json.JSONDecodeError, IOError):
        return None


def is_spec_execution_context(project_dir: Path) -> bool:
    """
    Check if we're in a SPEC execution context.

    True if any of:
    - /tmp/claude-expected-todo-count exists
    - .claude/checkpoints/ has checkpoint files
    - SPEC.json exists in project
    """
    expected_count_file = Path("/tmp/claude-expected-todo-count")
    if expected_count_file.exists():
        return True

    checkpoints_dir = project_dir / ".claude" / "checkpoints"
    if checkpoints_dir.exists() and any(checkpoints_dir.glob("*.json")):
        return True

    if find_spec_file(project_dir):
        return True

    return False
