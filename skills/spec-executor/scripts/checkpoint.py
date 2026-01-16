#!/usr/bin/env python3
"""
Checkpoint management for long-running SPEC executions.

Usage:
    # Initialize checkpoint for a SPEC
    python3 checkpoint.py init <spec-name> --total <N> [--spec-file <path>]

    # Update progress
    python3 checkpoint.py update <spec-name> --index <N> --task <task-id> [--item-id <id>] [--item-name <name>]

    # Mark item complete
    python3 checkpoint.py complete <spec-name> --index <N> [--item-id <id>]

    # Read current state
    python3 checkpoint.py read <spec-name>

    # Clear checkpoint (when done)
    python3 checkpoint.py clear <spec-name>

Checkpoint files are stored in: .claude/checkpoints/<spec-name>.json
Decisions files are stored in: .claude/checkpoints/<spec-name>-decisions.md

The --spec-file option stores the SPEC.json path in the checkpoint,
allowing the validation hook to find it without guessing.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Checkpoint directory relative to project root
CHECKPOINT_DIR = Path(".claude/checkpoints")


def get_checkpoint_path(spec_name: str) -> Path:
    """Get the checkpoint file path for a spec."""
    return CHECKPOINT_DIR / f"{spec_name}.json"


def ensure_checkpoint_dir():
    """Ensure checkpoint directory exists."""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def init_checkpoint(spec_name: str, total: int, loop_phase: str = "phase-2", spec_file: str | None = None) -> dict:
    """Initialize a new checkpoint."""
    ensure_checkpoint_dir()

    checkpoint = {
        "spec_name": spec_name,
        "spec_file": spec_file,  # Path to SPEC.json for hook reference
        "started_at": now_iso(),
        "last_updated": now_iso(),
        "loop_phase": loop_phase,
        "total_items": total,
        "current_index": 0,
        "current_item_id": None,
        "current_item_name": None,
        "current_task": None,
        "completed_items": [],
        "failed_items": [],
        "status": "in_progress"
    }

    path = get_checkpoint_path(spec_name)
    with open(path, 'w') as f:
        json.dump(checkpoint, f, indent=2)

    print(f"Checkpoint initialized: {path}")
    print(f"Total items to process: {total}")
    return checkpoint


def read_checkpoint(spec_name: str) -> dict | None:
    """Read existing checkpoint."""
    path = get_checkpoint_path(spec_name)

    if not path.exists():
        print(f"No checkpoint found for: {spec_name}")
        return None

    with open(path, 'r') as f:
        checkpoint = json.load(f)

    # Print summary
    completed = len(checkpoint.get('completed_items', []))
    total = checkpoint.get('total_items', 0)
    current = checkpoint.get('current_index', 0)
    task = checkpoint.get('current_task', 'N/A')
    item_name = checkpoint.get('current_item_name', 'N/A')

    print(f"\n{'='*50}")
    print(f"CHECKPOINT: {spec_name}")
    print(f"{'='*50}")
    print(f"Status: {checkpoint.get('status', 'unknown')}")
    print(f"Progress: {completed}/{total} completed")
    print(f"Current index: {current}")
    print(f"Current item: {item_name}")
    print(f"Current task: {task}")
    print(f"Last updated: {checkpoint.get('last_updated', 'N/A')}")
    print(f"{'='*50}")

    if checkpoint.get('failed_items'):
        print(f"\nFailed items ({len(checkpoint['failed_items'])}):")
        for item in checkpoint['failed_items']:
            print(f"  - {item}")

    return checkpoint


def update_checkpoint(
    spec_name: str,
    index: int,
    task: str,
    item_id: str | None = None,
    item_name: str | None = None
) -> dict:
    """Update checkpoint with current progress."""
    path = get_checkpoint_path(spec_name)

    if not path.exists():
        print(f"Error: No checkpoint found for {spec_name}. Run 'init' first.")
        sys.exit(1)

    with open(path, 'r') as f:
        checkpoint = json.load(f)

    checkpoint['current_index'] = index
    checkpoint['current_task'] = task
    checkpoint['last_updated'] = now_iso()

    if item_id:
        checkpoint['current_item_id'] = item_id
    if item_name:
        checkpoint['current_item_name'] = item_name

    with open(path, 'w') as f:
        json.dump(checkpoint, f, indent=2)

    print(f"Checkpoint updated: index={index}, task={task}, item={item_name or item_id or 'N/A'}")
    return checkpoint


def complete_item(spec_name: str, index: int, item_id: str | None = None) -> dict:
    """Mark an item as completed."""
    path = get_checkpoint_path(spec_name)

    if not path.exists():
        print(f"Error: No checkpoint found for {spec_name}. Run 'init' first.")
        sys.exit(1)

    with open(path, 'r') as f:
        checkpoint = json.load(f)

    # Add to completed list
    completed_entry = {
        "index": index,
        "item_id": item_id or checkpoint.get('current_item_id'),
        "completed_at": now_iso()
    }
    checkpoint['completed_items'].append(completed_entry)
    checkpoint['last_updated'] = now_iso()

    # Check if all done
    if len(checkpoint['completed_items']) >= checkpoint['total_items']:
        checkpoint['status'] = 'completed'
        print(f"All {checkpoint['total_items']} items completed!")
    else:
        remaining = checkpoint['total_items'] - len(checkpoint['completed_items'])
        print(f"Item {index} completed. {remaining} remaining.")

    with open(path, 'w') as f:
        json.dump(checkpoint, f, indent=2)

    return checkpoint


def fail_item(spec_name: str, index: int, item_id: str | None = None, reason: str = "") -> dict:
    """Mark an item as failed."""
    path = get_checkpoint_path(spec_name)

    if not path.exists():
        print(f"Error: No checkpoint found for {spec_name}. Run 'init' first.")
        sys.exit(1)

    with open(path, 'r') as f:
        checkpoint = json.load(f)

    failed_entry = {
        "index": index,
        "item_id": item_id or checkpoint.get('current_item_id'),
        "failed_at": now_iso(),
        "reason": reason
    }
    checkpoint['failed_items'].append(failed_entry)
    checkpoint['last_updated'] = now_iso()

    with open(path, 'w') as f:
        json.dump(checkpoint, f, indent=2)

    print(f"Item {index} marked as failed: {reason}")
    return checkpoint


def clear_checkpoint(spec_name: str, clear_canonical: bool = True):
    """Clear/delete a checkpoint file, decisions.md, and optionally the canonical TODO."""
    path = get_checkpoint_path(spec_name)

    if path.exists():
        path.unlink()
        print(f"Checkpoint cleared: {path}")
    else:
        print(f"No checkpoint to clear for: {spec_name}")

    # Clear decisions.md file
    decisions_path = CHECKPOINT_DIR / f"{spec_name}-decisions.md"
    if decisions_path.exists():
        decisions_path.unlink()
        print(f"Decisions file cleared: {decisions_path}")

    # Also clear canonical TODO file if requested
    if clear_canonical:
        canonical_path = Path(".claude/todo-canonical.json")
        if canonical_path.exists():
            canonical_path.unlink()
            print(f"Canonical TODO cleared: {canonical_path}")


def main():
    parser = argparse.ArgumentParser(description="Checkpoint management for SPEC execution")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # init
    init_parser = subparsers.add_parser('init', help='Initialize checkpoint')
    init_parser.add_argument('spec_name', help='Name of the SPEC')
    init_parser.add_argument('--total', type=int, required=True, help='Total items to process')
    init_parser.add_argument('--loop-phase', default='phase-2', help='Phase ID containing the loop')
    init_parser.add_argument('--spec-file', help='Path to SPEC.json (stored for hook reference)')

    # read
    read_parser = subparsers.add_parser('read', help='Read checkpoint status')
    read_parser.add_argument('spec_name', help='Name of the SPEC')

    # update
    update_parser = subparsers.add_parser('update', help='Update checkpoint progress')
    update_parser.add_argument('spec_name', help='Name of the SPEC')
    update_parser.add_argument('--index', type=int, required=True, help='Current item index (0-based)')
    update_parser.add_argument('--task', required=True, help='Current task ID (e.g., 2.5)')
    update_parser.add_argument('--item-id', help='Current item ID')
    update_parser.add_argument('--item-name', help='Current item name (for display)')

    # complete
    complete_parser = subparsers.add_parser('complete', help='Mark item as completed')
    complete_parser.add_argument('spec_name', help='Name of the SPEC')
    complete_parser.add_argument('--index', type=int, required=True, help='Completed item index')
    complete_parser.add_argument('--item-id', help='Completed item ID')

    # fail
    fail_parser = subparsers.add_parser('fail', help='Mark item as failed')
    fail_parser.add_argument('spec_name', help='Name of the SPEC')
    fail_parser.add_argument('--index', type=int, required=True, help='Failed item index')
    fail_parser.add_argument('--item-id', help='Failed item ID')
    fail_parser.add_argument('--reason', default='', help='Failure reason')

    # clear
    clear_parser = subparsers.add_parser('clear', help='Clear checkpoint')
    clear_parser.add_argument('spec_name', help='Name of the SPEC')
    clear_parser.add_argument('--keep-canonical', action='store_true',
                              help='Keep the canonical TODO file (default: clear it)')

    args = parser.parse_args()

    if args.command == 'init':
        init_checkpoint(args.spec_name, args.total, args.loop_phase, args.spec_file)
    elif args.command == 'read':
        checkpoint = read_checkpoint(args.spec_name)
        if checkpoint:
            # Also output JSON for machine parsing
            print(f"\nJSON:\n{json.dumps(checkpoint, indent=2)}")
    elif args.command == 'update':
        update_checkpoint(args.spec_name, args.index, args.task, args.item_id, args.item_name)
    elif args.command == 'complete':
        complete_item(args.spec_name, args.index, args.item_id)
    elif args.command == 'fail':
        fail_item(args.spec_name, args.index, args.item_id, args.reason)
    elif args.command == 'clear':
        clear_checkpoint(args.spec_name, clear_canonical=not args.keep_canonical)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
