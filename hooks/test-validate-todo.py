#!/usr/bin/env python3
"""
Test scenarios for validate-todo.py

Run: python3 test-validate-todo.py
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def run_hook(hook_input: dict, project_dir: Path) -> tuple[int, str, str]:
    """Run the validate-todo.py hook with given input."""
    hook_path = Path(__file__).parent / "validate-todo.py"

    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)

    result = subprocess.run(
        ["python3", str(hook_path)],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True,
        env=env,
        cwd=str(project_dir)
    )

    return result.returncode, result.stdout, result.stderr


def create_hook_input(todos: list[dict], cwd: str = "/tmp/test") -> dict:
    """Create a mock hook input."""
    return {
        "session_id": "test-session",
        "hook_event_name": "PostToolUse",
        "tool_name": "TodoWrite",
        "tool_input": {
            "todos": todos
        },
        "tool_response": {"success": True},
        "cwd": cwd
    }


def test_scenario(
    name: str,
    todos: list[dict],
    project_dir: Path,
    expected_decision: str | None = None,  # "block" or None (allow)
    setup_canonical: list[dict] | None = None,
    setup_expected_count: int | None = None,
    cleanup: bool = False
) -> bool:
    """
    Run a test scenario.

    Args:
        name: Test name
        todos: TODOs to validate
        project_dir: Project directory for canonical file
        expected_decision: Expected decision ("block" or None for allow)
        setup_canonical: If provided, create canonical file with these todos first
        setup_expected_count: If provided, create expected count file
        cleanup: If True, clean up canonical file before test
    """
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")

    # Setup
    canonical_path = project_dir / ".claude" / "todo-canonical.json"
    expected_count_path = Path("/tmp/claude-expected-todo-count")

    if cleanup and canonical_path.exists():
        canonical_path.unlink()

    if setup_canonical is not None:
        canonical_path.parent.mkdir(parents=True, exist_ok=True)
        with open(canonical_path, "w") as f:
            task_ids = []
            for t in setup_canonical:
                content = t.get("content", "")
                if ":" in content:
                    task_ids.append(content.split(":")[0].strip())
            json.dump({
                "task_count": len(setup_canonical),
                "task_ids": task_ids,
                "todos": setup_canonical
            }, f, indent=2)
        print(f"  Setup: Created canonical with {len(setup_canonical)} tasks")

    if setup_expected_count is not None:
        expected_count_path.write_text(str(setup_expected_count))
        print(f"  Setup: Created expected count file = {setup_expected_count}")

    # Run hook
    hook_input = create_hook_input(todos, str(project_dir))
    returncode, stdout, stderr = run_hook(hook_input, project_dir)

    # Parse output
    decision = None
    reason = None
    if stdout.strip():
        try:
            output = json.loads(stdout)
            decision = output.get("decision")
            reason = output.get("reason", "")
        except json.JSONDecodeError:
            pass

    # Check result
    passed = (decision == expected_decision)

    if passed:
        print(f"  {GREEN}✓ PASSED{RESET}")
    else:
        print(f"  {RED}✗ FAILED{RESET}")
        print(f"    Expected: {expected_decision or 'allow'}")
        print(f"    Got: {decision or 'allow'}")

    if reason:
        print(f"  Reason: {reason[:200]}...")

    if stderr.strip():
        print(f"  Stderr: {stderr[:200]}")

    # Cleanup expected count file if it was created
    if expected_count_path.exists():
        expected_count_path.unlink()

    return passed


def main():
    print(f"\n{YELLOW}Starting validate-todo.py tests{RESET}")

    # Create temp directory for tests
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        (project_dir / ".claude").mkdir(parents=True, exist_ok=True)

        results = []

        # ============================================
        # Scenario 1: First write (no canonical exists)
        # ============================================
        results.append(test_scenario(
            name="First write - should create canonical and allow",
            todos=[
                {"content": "0.1: Setup", "status": "pending", "activeForm": "Setting up"},
                {"content": "0.2: Config", "status": "pending", "activeForm": "Configuring"},
                {"content": "1.1: Build", "status": "pending", "activeForm": "Building"},
            ],
            project_dir=project_dir,
            expected_decision=None,  # Allow
            cleanup=True
        ))

        # ============================================
        # Scenario 2: Valid status change
        # ============================================
        canonical_todos = [
            {"content": "0.1: Setup", "status": "pending", "activeForm": "Setting up"},
            {"content": "0.2: Config", "status": "pending", "activeForm": "Configuring"},
            {"content": "1.1: Build", "status": "pending", "activeForm": "Building"},
        ]

        results.append(test_scenario(
            name="Status change - should allow",
            todos=[
                {"content": "0.1: Setup", "status": "completed", "activeForm": "Setting up"},
                {"content": "0.2: Config", "status": "in_progress", "activeForm": "Configuring"},
                {"content": "1.1: Build", "status": "pending", "activeForm": "Building"},
            ],
            project_dir=project_dir,
            expected_decision=None,  # Allow
            setup_canonical=canonical_todos
        ))

        # ============================================
        # Scenario 3: Task removal - should BLOCK
        # ============================================
        results.append(test_scenario(
            name="Task removal - should BLOCK",
            todos=[
                {"content": "0.1: Setup", "status": "completed", "activeForm": "Setting up"},
                # Missing 0.2!
                {"content": "1.1: Build", "status": "pending", "activeForm": "Building"},
            ],
            project_dir=project_dir,
            expected_decision="block",
            setup_canonical=canonical_todos
        ))

        # ============================================
        # Scenario 4: Phase collapse (valid)
        # ============================================
        original_todos = [
            {"content": "0.1: Setup", "status": "pending", "activeForm": "Setting up"},
            {"content": "0.2: Config", "status": "pending", "activeForm": "Configuring"},
            {"content": "0.3: Verify", "status": "pending", "activeForm": "Verifying"},
            {"content": "1.1: Build", "status": "pending", "activeForm": "Building"},
            {"content": "1.2: Test", "status": "pending", "activeForm": "Testing"},
        ]

        results.append(test_scenario(
            name="Valid phase collapse (0.x) - should allow",
            todos=[
                {"content": "0.x: Pre-Flight completed ✓", "status": "completed", "activeForm": "Done"},
                {"content": "1.1: Build", "status": "in_progress", "activeForm": "Building"},
                {"content": "1.2: Test", "status": "pending", "activeForm": "Testing"},
            ],
            project_dir=project_dir,
            expected_decision=None,  # Allow - phase properly collapsed
            setup_canonical=original_todos
        ))

        # ============================================
        # Scenario 5: Invalid collapse (missing tasks, no collapse marker)
        # ============================================
        results.append(test_scenario(
            name="Invalid collapse (no marker) - should BLOCK",
            todos=[
                {"content": "0.1: Setup", "status": "completed", "activeForm": "Done"},
                # Missing 0.2, 0.3 without proper collapse
                {"content": "1.1: Build", "status": "in_progress", "activeForm": "Building"},
                {"content": "1.2: Test", "status": "pending", "activeForm": "Testing"},
            ],
            project_dir=project_dir,
            expected_decision="block",
            setup_canonical=original_todos
        ))

        # ============================================
        # Scenario 6: Expected count validation (initial)
        # ============================================
        results.append(test_scenario(
            name="Expected count matches - should allow and create canonical",
            todos=[
                {"content": "0.1: Task A", "status": "pending", "activeForm": "A"},
                {"content": "0.2: Task B", "status": "pending", "activeForm": "B"},
                {"content": "0.3: Task C", "status": "pending", "activeForm": "C"},
            ],
            project_dir=project_dir,
            expected_decision=None,  # Allow
            cleanup=True,
            setup_expected_count=3
        ))

        # ============================================
        # Scenario 7: Expected count mismatch - should BLOCK
        # ============================================
        results.append(test_scenario(
            name="Expected count mismatch - should BLOCK",
            todos=[
                {"content": "0.1: Task A", "status": "pending", "activeForm": "A"},
                {"content": "0.2: Task B", "status": "pending", "activeForm": "B"},
            ],
            project_dir=project_dir,
            expected_decision="block",
            cleanup=True,
            setup_expected_count=5  # Expected 5, got 2
        ))

        # ============================================
        # Scenario 8: Loop expansion (adding tasks is OK)
        # ============================================
        loop_canonical = [
            {"content": "0.1: Setup", "status": "pending", "activeForm": "Setup"},
            {"content": "2.0: Update checkpoint", "status": "pending", "activeForm": "Checkpoint"},
            {"content": "2.1: Process item", "status": "pending", "activeForm": "Process"},
            {"content": "3.1: Verify", "status": "pending", "activeForm": "Verify"},
        ]

        results.append(test_scenario(
            name="Loop expansion (adding context) - should allow",
            todos=[
                {"content": "0.1: Setup", "status": "completed", "activeForm": "Setup"},
                {"content": "2.0: [1/40] Update checkpoint", "status": "in_progress", "activeForm": "Checkpoint"},
                {"content": "2.1: [1/40] Process item", "status": "pending", "activeForm": "Process"},
                {"content": "3.1: Verify", "status": "pending", "activeForm": "Verify"},
            ],
            project_dir=project_dir,
            expected_decision=None,  # Allow - same IDs, just added context
            setup_canonical=loop_canonical
        ))

        # ============================================
        # Summary
        # ============================================
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")

        passed = sum(results)
        total = len(results)

        if passed == total:
            print(f"{GREEN}All {total} tests passed!{RESET}")
        else:
            print(f"{RED}{passed}/{total} tests passed{RESET}")
            print(f"{RED}{total - passed} tests failed{RESET}")

        return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
