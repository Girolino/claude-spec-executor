---
name: spec-executor
description: Execute SPEC.json files with granular TODO tracking, checkpoint recovery, and automated verification. Use when provided @SPEC.json or @SPEC.md files.
---

# SPEC Executor

Execute SPEC.json with granular TODO tracking and continuous progress.

---

## Before You Start

### 1. Find Scripts

```bash
SCRIPTS=$(dirname "$(find ~/.claude -name "count_tasks.py" -path "*/spec-executor/*" 2>/dev/null | head -1)")
```

### 2. Count Tasks

```bash
python3 $SCRIPTS/count_tasks.py SPEC.json
# Output: "Total tasks: 35"

echo 35 > /tmp/claude-expected-todo-count
```

### 3. Create Complete TODO

Call TodoWrite with **ALL tasks from ALL phases** in one call.

A hook validates the count matches. If mismatch, recreate until it passes.

---

## Execution Philosophy

Continue executing tasks sequentially until:
1. ALL tasks are completed, OR
2. A blocking error requires human input (missing credentials, permission denied)

### Non-Blocking Issues (fix and continue)
- TypeScript warnings
- Minor test failures
- Formatting issues

### Blocking Issues (use AskUserQuestion)
- Missing environment variables
- Permission denied errors
- Unclear requirements

After clarification, resume immediately.

---

## TODO Rules

### Format
Each task ID = ONE TODO item: `{id}: {description}`

```
0.1: Create decisions.md
0.2: Verify typecheck passes
1.0: Update decisions.md for Phase 1
1.1: Run /frontend-design for UserCard
```

### Anti-Patterns (NEVER do)
```
BAD: "Phase 0: Setup" (combines tasks)
BAD: "Implement backend" (too vague)
BAD: "Complete Phase 1-3" (batching)
```

### Loop Tasks
Loop tasks (2.0, 2.1, ...) appear ONCE in TODO but execute multiple times.
Checkpoint tracks which item; TODO tracks which task ID.

---

## UI Component Workflow

For any UI task:

```
1. Run /frontend-design for [Component]   # Design guidance
2. Create [Component]                      # Implement
3. Run /visual-qa for [Component]         # Visual verification
```

---

## Execution Flow

1. Mark task `in_progress`
2. Complete the task
3. Mark task `completed`
4. **Immediately** start next task (no pause)

Never have more than 1 task `in_progress`.

### Every 10 Tasks
Update SPEC.md Execution Log:
- Current phase and task
- Key decisions made
- Any blockers encountered

---

## Checkpoints (Loops Only)

For SPECs with loops over 5+ items, use checkpoints for recovery.

See [CHECKPOINT_GUIDE.md](../shared/CHECKPOINT_GUIDE.md) for:
- When to use
- Commands (init, update, complete, read, clear)
- Resumption protocol

---

## Resumption After /compact

1. Check checkpoint: `python3 $SCRIPTS/checkpoint.py read <spec-name>`
2. Read decisions.md: `.claude/checkpoints/<spec-name>-decisions.md`
3. Generate TODO: `python3 $SCRIPTS/generate-todo.py --spec SPEC.json`
4. Recreate TODO with correct status
5. Resume from next incomplete task

---

## On Completion

```
SPEC EXECUTION COMPLETE

Summary:
- Total tasks: X
- Completed: X
- Phases: Y/Z

<promise>COMPLETION_PROMISE</promise>
```

---

## Reference

- [CHECKPOINT_GUIDE.md](../shared/CHECKPOINT_GUIDE.md) - Loop recovery
- [EXAMPLES.md](../shared/EXAMPLES.md) - Execution traces
