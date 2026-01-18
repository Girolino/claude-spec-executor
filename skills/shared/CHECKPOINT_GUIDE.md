# Checkpoint Guide

Checkpoints persist loop state to disk, enabling recovery after `/compact` or session interruption.

## When to Use Checkpoints

Add checkpoint tasks **only if ALL** of these apply:
- SPEC has a loop phase iterating over **5+ items**
- Expected execution time **> 30 minutes**
- Risk of session interruption

**Without checkpoints:** Loop state is lost after `/compact`, forcing restart from item 1.
**With checkpoints:** Loop state persists to disk, resume from where you left off.

If your SPEC doesn't meet these criteria, skip checkpoints entirely.

---

## Checkpoint Commands

```bash
# Find scripts path
SCRIPTS=$(dirname "$(find ~/.claude -name "count_tasks.py" -path "*/spec-executor/*" 2>/dev/null | head -1)")

# Initialize (after discovering total items)
python3 $SCRIPTS/checkpoint.py init <spec-name> --total <N> --spec-file SPEC.json

# Update (at START of each loop iteration)
python3 $SCRIPTS/checkpoint.py update <spec-name> \
  --index <N> --task <task-id> --item-id <id> --item-name '<name>'

# Complete (at END of each loop iteration)
python3 $SCRIPTS/checkpoint.py complete <spec-name> --index <N>

# Read (to check state or resume)
python3 $SCRIPTS/checkpoint.py read <spec-name>

# Clear (after ALL verifications pass)
python3 $SCRIPTS/checkpoint.py clear <spec-name>
```

---

## Required Tasks in SPEC.json

### Before the loop (in discovery phase):
```json
{ "id": "1.N", "task": "Initialize checkpoint", "command": "checkpoint.py init ..." }
{ "id": "1.N+1", "task": "Check existing checkpoint (for resumption)" }
```

### In loop phase (first and last):
```json
{ "id": "2.0", "task": "Update checkpoint: starting this item" }
// ... actual work tasks ...
{ "id": "2.LAST", "task": "Mark item complete in checkpoint" }
```

### After loop (in verification phase):
```json
{ "id": "3.N", "task": "Clear checkpoint (execution complete)" }
```

---

## File Location

```
.claude/checkpoints/
├── <spec-name>.json           # Loop state
└── <spec-name>-decisions.md   # Execution context
```

---

## Resumption After /compact

1. **Read checkpoint:** `checkpoint.py read <spec-name>`
2. **Check completed_items:** Array of finished item IDs
3. **Skip completed:** In loop, skip items already in completed_items
4. **Resume:** Start at `current_index` from `current_task`

### Example Recovery

```bash
python3 $SCRIPTS/checkpoint.py read my-feature
# Output: current_index=15, current_task=2.3, completed=15/40

# Resume from item 16, task 2.0
```

---

## Decisions.md Pattern

Every SPEC execution should maintain a `decisions.md` file at `.claude/checkpoints/<spec-name>-decisions.md`.

### Purpose
After `/compact`, Claude forgets the "why" behind decisions. This file preserves:
- Objective summary
- Key constraints
- Decisions made per phase
- Current state (phase, last task, next task)

### When to Update
- **Task 0.0:** Create with objective from SPEC.md
- **Task X.0 (each phase):** Update with previous phase decisions + current phase objectives

### Cleanup
Deleted automatically when `checkpoint.py clear` runs.
