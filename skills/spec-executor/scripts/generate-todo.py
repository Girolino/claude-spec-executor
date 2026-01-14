#!/usr/bin/env python3
"""
Generate the correct TODO structure based on SPEC and checkpoint state.

This script creates a dynamic TODO that:
1. Collapses completed phases into summary items
2. Expands loop tasks for the CURRENT profile only
3. Shows pending phases as single items

Usage:
    python3 generate-todo.py --spec <spec.json> --checkpoint <name>
    python3 generate-todo.py --spec <spec.json>  # No checkpoint, base structure

Output:
    JSON array ready for TodoWrite, or --format count for item count

Examples:
    # Generate TODO for re-enrichment spec with active checkpoint
    python3 generate-todo.py --spec .claude/skills/industry-map-expert/SPEC/re-enrichment.json --checkpoint re-enrichment

    # Just count items
    python3 generate-todo.py --spec SPEC.json --checkpoint my-spec --format count
"""

import argparse
import json
import sys
from pathlib import Path


def load_spec(spec_path: Path) -> dict:
    """Load SPEC.json file."""
    if not spec_path.exists():
        print(f"Error: SPEC file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)
    with open(spec_path) as f:
        return json.load(f)


def load_checkpoint(name: str) -> dict | None:
    """Load checkpoint if it exists."""
    checkpoint_path = Path(f".claude/checkpoints/{name}.json")
    if not checkpoint_path.exists():
        return None
    with open(checkpoint_path) as f:
        return json.load(f)


def get_phase_tasks(phase: dict) -> list[dict]:
    """Extract tasks from a phase, handling both regular and loop phases."""
    loop = phase.get('loop')
    if loop:
        return loop.get('tasks', [])
    return phase.get('tasks', [])


def is_loop_phase(phase: dict) -> bool:
    """Check if phase is a loop phase."""
    return 'loop' in phase


def parse_task_id(task_id: str) -> tuple:
    """
    Convert task ID to tuple for natural sorting.

    '1.2' -> (1, 2)
    '1.10' -> (1, 10)
    '10.1' -> (10, 1)

    This ensures 1.10 > 1.2 (natural order) instead of 1.10 < 1.2 (lexicographic).
    """
    parts = task_id.split('.')
    return tuple(int(p) for p in parts if p.isdigit())


def generate_todos(spec: dict, checkpoint: dict | None) -> list[dict]:
    """
    Generate TODO list based on SPEC and checkpoint state.

    Structure:
    - Completed phases: collapsed to "X.x: Phase Name ✓"
    - Current loop phase: meta-task + expanded tasks for current item
    - Pending phases: collapsed to "X.x: Phase Name (N tasks)"
    """
    todos = []
    phases = spec.get('phases', [])

    # Determine current state from checkpoint
    in_loop = False
    current_profile_index = 0
    current_profile_name = "Unknown"
    current_task = None
    total_profiles = 0
    completed_profiles = 0
    completed_phase_ids = set()

    if checkpoint and checkpoint.get('status') == 'in_progress':
        in_loop = True
        current_profile_index = checkpoint.get('current_index', 0)
        current_profile_name = checkpoint.get('current_item_name', 'Unknown')
        current_task = checkpoint.get('current_task')
        total_profiles = checkpoint.get('total_items', 0)
        completed_profiles = len(checkpoint.get('completed_items', []))

        # Phases before the loop phase are considered complete
        for phase in phases:
            if is_loop_phase(phase):
                break
            completed_phase_ids.add(phase.get('id', ''))

    for phase in phases:
        phase_id = phase.get('id', '')
        phase_name = phase.get('name', 'Unnamed Phase')
        phase_tasks = get_phase_tasks(phase)

        if is_loop_phase(phase):
            if in_loop:
                # Active loop - expand current profile
                profile_num = current_profile_index + 1

                # Meta-task showing overall progress
                todos.append({
                    "content": f"{phase_id}: {phase_name} ({completed_profiles}/{total_profiles})",
                    "status": "in_progress",
                    "activeForm": f"Processing item {profile_num}/{total_profiles}"
                })

                # Expanded tasks for current profile
                for task in phase_tasks:
                    task_id = task.get('id', '')
                    task_desc = task.get('task', '')[:50]  # Truncate long descriptions

                    # Determine task status using natural ordering
                    status = "pending"
                    if current_task:
                        # Tasks before current_task are complete (natural sort)
                        if parse_task_id(task_id) < parse_task_id(current_task):
                            status = "completed"
                        elif task_id == current_task:
                            status = "in_progress"

                    todos.append({
                        "content": f"  {task_id}: [{profile_num}/{total_profiles}] {task_desc}",
                        "status": status,
                        "activeForm": f"{task_desc} for {current_profile_name}"
                    })
            else:
                # Not in loop yet - show as pending collapsed
                task_count = len(phase_tasks)
                todos.append({
                    "content": f"{phase_id}: {phase_name} ({task_count} tasks/item)",
                    "status": "pending",
                    "activeForm": f"Processing {phase_name}"
                })

        elif phase_id in completed_phase_ids:
            # Completed phase - collapse to summary
            task_count = len(phase_tasks)
            first_task_id = phase_tasks[0].get('id', '?') if phase_tasks else '?'
            # Extract phase number (e.g., "10.1" -> "10", not just "1")
            phase_num = first_task_id.split('.')[0] if '.' in first_task_id else first_task_id
            todos.append({
                "content": f"{phase_num}.x: {phase_name} ({task_count}/{task_count}) ✓",
                "status": "completed",
                "activeForm": f"Completed {phase_name}"
            })

        else:
            # Pending or current non-loop phase - show individual tasks
            for task in phase_tasks:
                task_id = task.get('id', '')
                task_desc = task.get('task', '')[:60]
                todos.append({
                    "content": f"{task_id}: {task_desc}",
                    "status": "pending",
                    "activeForm": f"Working on {task_desc}"
                })

    return todos


def generate_base_todos(spec: dict) -> list[dict]:
    """
    Generate base TODO without checkpoint (all tasks visible).
    Used for initial TODO creation before loop starts.
    """
    todos = []
    phases = spec.get('phases', [])

    for phase in phases:
        phase_tasks = get_phase_tasks(phase)

        for task in phase_tasks:
            task_id = task.get('id', '')
            task_desc = task.get('task', '')[:60]
            todos.append({
                "content": f"{task_id}: {task_desc}",
                "status": "pending",
                "activeForm": f"Working on {task_desc}"
            })

    return todos


def main():
    parser = argparse.ArgumentParser(
        description="Generate TODO structure based on SPEC and checkpoint state"
    )
    parser.add_argument('--spec', required=True, help='Path to SPEC.json')
    parser.add_argument('--checkpoint', help='Checkpoint name (without .json)')
    parser.add_argument(
        '--format',
        choices=['json', 'count', 'preview'],
        default='json',
        help='Output format: json (default), count, or preview'
    )
    parser.add_argument(
        '--base',
        action='store_true',
        help='Generate base TODO (all tasks, no expansion)'
    )
    args = parser.parse_args()

    spec = load_spec(Path(args.spec))

    if args.base:
        todos = generate_base_todos(spec)
    else:
        checkpoint = load_checkpoint(args.checkpoint) if args.checkpoint else None
        todos = generate_todos(spec, checkpoint)

    if args.format == 'count':
        print(len(todos))
    elif args.format == 'preview':
        print(f"\n{'='*60}")
        print(f"TODO Preview ({len(todos)} items)")
        print(f"{'='*60}\n")
        for todo in todos:
            status_icon = {
                'completed': '☒',
                'in_progress': '◐',
                'pending': '☐'
            }.get(todo['status'], '?')
            print(f"{status_icon} {todo['content']}")
        print()
    else:
        print(json.dumps(todos, indent=2))


if __name__ == "__main__":
    main()
