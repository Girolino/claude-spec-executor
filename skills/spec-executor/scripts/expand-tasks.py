#!/usr/bin/env python3
"""
Expand tasks in SPEC.json based on their type field.

Usage:
    python3 expand-tasks.py SPEC-compact.json [--output SPEC.json]
    python3 expand-tasks.py SPEC-compact.json --preview

Task Types and Expansions:
    ui:      pre (skills) + main + post (visual QA) = 3 tasks
    backend: main + post (test) = 2 tasks
    func:    main + post (test) = 2 tasks
    docs:    main + post (verify) = 2 tasks
    default: main only = 1 task

Also warns about alternating UI tasks per phase.
"""

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path


def get_task_name(task: dict) -> str:
    """Extract a short name from task description for use in expanded tasks."""
    task_desc = task.get("task", "")
    # Try to extract component/function name from task
    # e.g., "Create ProfileCard component" -> "ProfileCard"
    # e.g., "Implement getUserById query" -> "getUserById"
    words = task_desc.split()
    for i, word in enumerate(words):
        if word in ("Create", "Implement", "Build", "Add", "Update", "Write"):
            if i + 1 < len(words):
                return words[i + 1].rstrip(",.:;")
    # Fallback: first meaningful word
    return words[1] if len(words) > 1 else task_desc[:20]


def expand_ui_task(task: dict) -> list[dict]:
    """Expand UI task to: pre (skills) + main + post (visual QA)."""
    task_id = task.get("id", "")
    task_name = get_task_name(task)

    expanded = []

    # Pre-task: Run design skills
    pre_task = {
        "id": f"{task_id}a",
        "task": f"Run /frontend-design and /vercel-design-guidelines for {task_name}",
        "type": "_expanded_pre",
        "parent_id": task_id
    }
    expanded.append(pre_task)

    # Main task (copy original, remove type to avoid re-expansion)
    main_task = deepcopy(task)
    main_task.pop("type", None)
    expanded.append(main_task)

    # Post-task: Visual QA (Claude decides if needed)
    post_task = {
        "id": f"{task_id}b",
        "task": f"Visual QA for {task_name} - run /visual-qa for new components, skip for minor edits",
        "type": "_expanded_post",
        "parent_id": task_id
    }
    expanded.append(post_task)

    return expanded


def expand_backend_task(task: dict) -> list[dict]:
    """Expand backend task to: main + post (test)."""
    task_id = task.get("id", "")
    task_name = get_task_name(task)

    expanded = []

    # Main task
    main_task = deepcopy(task)
    main_task.pop("type", None)
    expanded.append(main_task)

    # Post-task: Test
    post_task = {
        "id": f"{task_id}a",
        "task": f"Test {task_name} - verify returns correct data and handles errors",
        "type": "_expanded_post",
        "parent_id": task_id
    }
    expanded.append(post_task)

    return expanded


def expand_func_task(task: dict) -> list[dict]:
    """Expand func task to: main + post (test)."""
    task_id = task.get("id", "")
    task_name = get_task_name(task)

    expanded = []

    # Main task
    main_task = deepcopy(task)
    main_task.pop("type", None)
    expanded.append(main_task)

    # Post-task: Test
    post_task = {
        "id": f"{task_id}a",
        "task": f"Test {task_name} - run tests and verify passes",
        "type": "_expanded_post",
        "parent_id": task_id
    }
    expanded.append(post_task)

    return expanded


def expand_docs_task(task: dict) -> list[dict]:
    """Expand docs task to: main + post (verify exists)."""
    task_id = task.get("id", "")
    files = task.get("files", [])
    file_name = files[0].split("/")[-1] if files else "file"

    expanded = []

    # Main task
    main_task = deepcopy(task)
    main_task.pop("type", None)
    expanded.append(main_task)

    # Post-task: Verify exists
    post_task = {
        "id": f"{task_id}a",
        "task": f"Verify {file_name} exists and is properly updated",
        "type": "_expanded_post",
        "parent_id": task_id,
        "files": files
    }
    expanded.append(post_task)

    return expanded


def expand_task(task: dict) -> list[dict]:
    """Expand a single task based on its type."""
    task_type = task.get("type", "")

    if task_type == "ui":
        return expand_ui_task(task)
    elif task_type == "backend":
        return expand_backend_task(task)
    elif task_type == "func":
        return expand_func_task(task)
    elif task_type == "docs":
        return expand_docs_task(task)
    else:
        # No expansion, return as-is
        return [task]


def check_alternating_ui(tasks: list[dict], phase_id: str) -> str | None:
    """Check for alternating UI tasks pattern and return warning if found."""
    if len(tasks) < 4:
        return None

    # Get sequence of types
    types = []
    for task in tasks:
        task_type = task.get("type", "default")
        task_id = task.get("id", "?")
        types.append((task_id, task_type))

    # Check for alternating pattern (UI -> non-UI -> UI)
    alternations = 0
    last_was_ui = None
    pattern_parts = []

    for task_id, task_type in types:
        is_ui = task_type == "ui"
        if last_was_ui is not None and is_ui != last_was_ui:
            alternations += 1
        if task_type in ("ui", "backend", "func"):
            pattern_parts.append(f"{task_id}({task_type})")
        last_was_ui = is_ui

    # Warn if 3+ alternations (UI -> X -> UI -> X pattern)
    if alternations >= 3:
        pattern_str = " → ".join(pattern_parts[:6])
        if len(pattern_parts) > 6:
            pattern_str += " → ..."
        return (
            f"⚠️  Phase {phase_id} has alternating UI tasks: {pattern_str}\n"
            f"   Consider grouping UI tasks together to reduce repeated visual validations.\n"
            f"   This is a suggestion, not a blocker."
        )

    return None


def expand_phase_tasks(phase: dict) -> tuple[dict, list[str]]:
    """Expand all tasks in a phase and return warnings."""
    warnings = []
    phase_id = phase.get("id", "unknown")

    # Check for alternating UI before expansion
    tasks = phase.get("tasks", [])
    alt_warning = check_alternating_ui(tasks, phase_id)
    if alt_warning:
        warnings.append(alt_warning)

    # Expand tasks
    expanded_tasks = []
    for task in tasks:
        expanded_tasks.extend(expand_task(task))

    # Handle loop phase
    loop = phase.get("loop", {})
    if loop:
        loop_tasks = loop.get("tasks", [])
        loop_warning = check_alternating_ui(loop_tasks, f"{phase_id} (loop)")
        if loop_warning:
            warnings.append(loop_warning)

        expanded_loop_tasks = []
        for task in loop_tasks:
            expanded_loop_tasks.extend(expand_task(task))

        phase = deepcopy(phase)
        phase["loop"]["tasks"] = expanded_loop_tasks
    else:
        phase = deepcopy(phase)

    phase["tasks"] = expanded_tasks
    return phase, warnings


def expand_spec(spec: dict) -> tuple[dict, list[str]]:
    """Expand all tasks in a SPEC and return warnings."""
    all_warnings = []
    expanded_spec = deepcopy(spec)

    expanded_phases = []
    for phase in spec.get("phases", []):
        expanded_phase, warnings = expand_phase_tasks(phase)
        expanded_phases.append(expanded_phase)
        all_warnings.extend(warnings)

    expanded_spec["phases"] = expanded_phases

    # Add metadata about expansion
    expanded_spec["_expansion"] = {
        "expanded": True,
        "warnings": all_warnings
    }

    return expanded_spec, all_warnings


def count_tasks(spec: dict) -> int:
    """Count total tasks in a SPEC."""
    count = 0
    for phase in spec.get("phases", []):
        count += len(phase.get("tasks", []))
        loop = phase.get("loop", {})
        if loop:
            count += len(loop.get("tasks", []))
    return count


def main():
    parser = argparse.ArgumentParser(
        description="Expand tasks in SPEC.json based on type field"
    )
    parser.add_argument("spec_file", help="Input SPEC.json file (compact)")
    parser.add_argument(
        "--output", "-o",
        help="Output file (default: overwrite input or stdout with --preview)"
    )
    parser.add_argument(
        "--preview", "-p",
        action="store_true",
        help="Preview expansion without writing (prints to stdout)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress warnings and info messages"
    )

    args = parser.parse_args()

    # Read input
    spec_path = Path(args.spec_file)
    if not spec_path.exists():
        print(f"Error: File not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    with open(spec_path) as f:
        spec = json.load(f)

    # Check if already expanded
    if spec.get("_expansion", {}).get("expanded"):
        if not args.quiet:
            print("SPEC is already expanded. Skipping.", file=sys.stderr)
        if args.preview:
            print(json.dumps(spec, indent=2))
        sys.exit(0)

    # Count before
    count_before = count_tasks(spec)

    # Expand
    expanded_spec, warnings = expand_spec(spec)

    # Count after
    count_after = count_tasks(expanded_spec)

    # Print warnings
    if warnings and not args.quiet:
        print("\n" + "="*60, file=sys.stderr)
        print("EXPANSION WARNINGS", file=sys.stderr)
        print("="*60, file=sys.stderr)
        for warning in warnings:
            print(warning, file=sys.stderr)
        print("="*60 + "\n", file=sys.stderr)

    # Print summary
    if not args.quiet:
        print(f"\nExpansion complete:", file=sys.stderr)
        print(f"  Tasks before: {count_before}", file=sys.stderr)
        print(f"  Tasks after:  {count_after}", file=sys.stderr)
        print(f"  Added:        {count_after - count_before}", file=sys.stderr)

    # Output
    if args.preview:
        print(json.dumps(expanded_spec, indent=2))
    else:
        output_path = Path(args.output) if args.output else spec_path
        with open(output_path, "w") as f:
            json.dump(expanded_spec, f, indent=2)
        if not args.quiet:
            print(f"\nWritten to: {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
