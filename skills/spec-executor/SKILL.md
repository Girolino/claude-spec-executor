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

### 2. Generate TODO from SPEC

```bash
# Count tasks and set expected count
python3 $SCRIPTS/count_tasks.py SPEC.json
echo <count> > /tmp/claude-expected-todo-count

# Generate TODO structure (copy output for TodoWrite)
python3 $SCRIPTS/generate-todo.py --spec SPEC.json --base --format json
```

### 3. Create TODO

Copy the JSON output from generate-todo.py and use it in TodoWrite.

A hook validates the count matches. If mismatch, regenerate.

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

Use checkpoints **only if ALL** apply:
- Loop iterates over **5+ items**
- Expected execution time **> 30 minutes**

### Checkpoint Commands

```bash
# Initialize (after discovering total items)
python3 $SCRIPTS/checkpoint.py init <spec-name> --total <N> --spec-file SPEC.json

# Update (at START of each loop iteration)
python3 $SCRIPTS/checkpoint.py update <spec-name> --index <N> --task <task-id>

# Complete (at END of each loop iteration)
python3 $SCRIPTS/checkpoint.py complete <spec-name> --index <N>

# Read (to check state or resume)
python3 $SCRIPTS/checkpoint.py read <spec-name>

# Clear (after ALL verifications pass)
python3 $SCRIPTS/checkpoint.py clear <spec-name>
```

### Files Location

```
.claude/checkpoints/
├── <spec-name>.json           # Loop state
└── <spec-name>-decisions.md   # Execution context
```

---

## Resumption After /compact

1. Check checkpoint: `python3 $SCRIPTS/checkpoint.py read <spec-name>`
2. Read decisions.md: `.claude/checkpoints/<spec-name>-decisions.md`
3. Generate TODO: `python3 $SCRIPTS/generate-todo.py --spec SPEC.json`
4. Recreate TODO with correct status
5. Resume from next incomplete task

### Recovery Example

```bash
python3 $SCRIPTS/checkpoint.py read my-feature
# Output: current_index=15, current_task=2.3, completed=15/40

# Resume from item 16, task 2.0
```

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
