# Drift Problems in Long SPEC Executions

## Problem 1: Scope Drift

### Symptom
Claude follows the TODO but implements something different from what SPEC.md defines. The "why" gets lost over time.

### Why it happens
- Context window fills up, older context gets compressed
- After /compact, SPEC.md context is lost
- Claude focuses on immediate task, loses sight of bigger picture

### Chosen Solution: decisions.md with TODO-enforced updates

After discussion, the best approach is:

1. **decisions.md as temporary checkpoint file**
2. **Explicit tasks in TODO** to update it at phase transitions
3. **read-spec generates these tasks** automatically

#### File Location

```
.claude/checkpoints/
├── <spec-name>.json           # loop position
└── <spec-name>-decisions.md   # execution context
```

Cleaned up by `checkpoint.py clear` at the end.

#### SPEC.json Structure

Each phase gets an explicit "update decisions" task:

```json
{
  "phases": [
    {
      "id": "phase-0",
      "tasks": [
        {
          "id": "0.0",
          "task": "Create decisions.md with execution objective from SPEC.md",
          "files": [".claude/checkpoints/<spec>-decisions.md"],
          "notes": "Write: objective summary, key constraints, success criteria"
        },
        {
          "id": "0.1",
          "task": "Actual first task..."
        }
      ]
    },
    {
      "id": "phase-1",
      "tasks": [
        {
          "id": "1.0",
          "task": "Update decisions.md: Record Phase 0 decisions and Phase 1 objectives",
          "files": [".claude/checkpoints/<spec>-decisions.md"],
          "notes": "Add: key decisions from Phase 0, what Phase 1 will accomplish"
        },
        {
          "id": "1.1",
          "task": "Actual first task of phase 1..."
        }
      ]
    }
  ]
}
```

#### decisions.md Template

```markdown
# Execution Context: <Feature Name>

## Objective
[Written in task 0.0 - summary of SPEC.md goal]

## Key Constraints
[From SPEC.md - things that must not change]

## Success Criteria
[How we know we're done]

---

## Phase 0 Decisions
- [Decision]: [Rationale]

## Phase 1 Decisions
- [Decision]: [Rationale]

## Current State
Phase: X
Last completed: task Y.Z
Next: task Y.W
```

#### Why This Works

| Problem | How it's solved |
|---------|-----------------|
| Claude forgets to update | Task is in TODO, deterministic |
| Lost after /compact | decisions.md persists on disk |
| Context bloat from re-reading SPEC.md | decisions.md is compact summary |
| Pollutes project | Cleaned up with checkpoint |

#### Implementation Required

1. **read-spec skill**: Generate `X.0` tasks for each phase
2. **SKILL.md**: Document decisions.md format and purpose
3. **checkpoint.py**: Already cleans `.claude/checkpoints/`, no changes needed

#### Technical Notes (from Claude Code investigation)

Hooks **cannot** enforce decisions.md updates because:
- Hooks are observers, cannot write files
- No pattern-based triggers on TODO content
- Cannot interrupt Claude mid-execution

Therefore, **explicit TODO tasks are the only reliable approach**.

Hooks *could* detect phase transitions and inject reminders, but this is fragile and non-deterministic. The TODO-based approach is simpler and guaranteed to work.

---

## Problem 2: Premature Stop

### Symptom
Claude stops execution before all TODO items are complete. Session ends with pending tasks.

### Why it happens
- Claude "decides" it's done (misreads completion state)
- Hits perceived blocker and gives up
- Context limit triggers early wrap-up behavior
- Ambiguous end state (thinks it's waiting for user)

### Chosen Solution: Stop hook + AskUserQuestion escape valve

After investigation, the `Stop` hook **does support blocking** with `{"decision": "block", "reason": "..."}`.

The elegant solution:

```
Claude tries to stop
    │
    └─► Stop hook fires
            │
            ├─► Read TODO → pending tasks?
            │       │
            │       ├─► YES → Block + "Continue. Use AskUserQuestion if blocked."
            │       │
            │       └─► NO → Allow (execution complete)
            │
            └─► Claude either:
                    ├─► Continues with next task
                    └─► Uses AskUserQuestion if genuinely stuck
```

#### Why This Works

| Scenario | What happens |
|----------|--------------|
| Claude tries to stop early | Hook blocks, tells to continue |
| Claude is genuinely stuck | Uses AskUserQuestion → user helps |
| Claude ignores and loops | AskUserQuestion is the escape valve |
| All tasks done | Hook allows stop |

**No infinite loop** because Claude always has an exit:
- Continue working, OR
- Ask user for help via AskUserQuestion

#### Implementation

**hooks.json:**
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/check-pending-todos.py"
          }
        ]
      }
    ]
  }
}
```

**check-pending-todos.py:**
```python
#!/usr/bin/env python3
"""
Stop hook that prevents premature execution stops.

Blocks stopping if there are pending TODO items.
Claude must either continue or use AskUserQuestion if stuck.
"""

import json
import sys
from pathlib import Path


def get_pending_todos() -> list[str]:
    """Read TODO state and return pending items."""
    # TODO: Implement reading from Claude's internal TODO state
    # For now, read from canonical if exists
    canonical_path = Path(".claude/todo-canonical.json")

    if not canonical_path.exists():
        return []

    try:
        with open(canonical_path) as f:
            canonical = json.load(f)

        todos = canonical.get("todos", [])
        pending = [t["content"] for t in todos if t.get("status") != "completed"]
        return pending
    except (json.JSONDecodeError, IOError):
        return []


def main():
    # Read hook input
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        return  # Allow stop if can't parse input

    pending = get_pending_todos()

    if pending:
        print(json.dumps({
            "decision": "block",
            "reason": (
                f"{len(pending)} tasks still pending. "
                "Continue execution with the next pending task. "
                "If you are blocked or need clarification, use AskUserQuestion."
            )
        }))
    else:
        # No pending tasks, allow stop
        print(json.dumps({
            "decision": "allow"
        }))


if __name__ == "__main__":
    main()
```

#### SKILL.md Addition

Also add explicit rules to SKILL.md:

```markdown
## COMPLETION RULES (NON-NEGOTIABLE)

You MUST NOT stop until ALL TODO items are marked `completed`.

If you cannot proceed with a task:
- DO NOT stop and wait
- DO NOT say "let me know if you want me to continue"
- DO use AskUserQuestion to get clarification
- THEN continue with execution

The Stop hook will block premature stops. Your only options are:
1. Continue with next pending task
2. Use AskUserQuestion if genuinely blocked
```

#### Technical Notes

The `Stop` hook input includes `stop_hook_active: true/false`:
- `false` = First stop attempt
- `true` = Claude already blocked before, trying again

We don't need complex loop detection because `AskUserQuestion` is the escape valve. If Claude is stuck and keeps trying to stop, the repeated block message tells it to use AskUserQuestion.

### Alternative Solutions (Not Chosen)

#### A. Stronger SKILL.md only
Just add rules to SKILL.md without hook enforcement.

**Why not:** Claude might ignore instructions.

#### B. LLM-based Stop hook
Use `type: "prompt"` for smart evaluation.

**Why not:** Extra API calls, non-deterministic, slower.

#### C. Completion promise validation only
Validate promise was output post-hoc.

**Why not:** Doesn't prevent stopping, just reports failure.

---

## Implementation Roadmap

### Phase 1: decisions.md (Problem 1)

1. [ ] Update `read-spec` skill to generate `X.0` tasks for decisions.md
2. [ ] Add decisions.md template to SKILL.md documentation
3. [ ] Test with a sample SPEC

### Phase 2: Stop Hook (Problem 2)

1. [ ] Implement `check-pending-todos.py` hook
2. [ ] Add Stop hook to `hooks.json`
3. [ ] Update SKILL.md with completion rules
4. [ ] Test blocking behavior with pending tasks
5. [ ] Verify AskUserQuestion escape valve works

### Phase 3: Integration Testing (Problems 1 & 2)

1. [ ] Run full SPEC execution with both solutions enabled
2. [ ] Verify decisions.md is created and updated at phase transitions
3. [ ] Verify stop hook blocks premature stops
4. [ ] Verify cleanup at end (checkpoint.py clear)

### Phase 4: Task Types (Problem 3)

1. [ ] Update SPEC.json schema to include `type` field
2. [ ] Implement task expansion logic in read-spec
3. [ ] Add warning for alternating UI patterns per phase
4. [ ] Update count_tasks.py to handle expanded tasks
5. [ ] Document task types in SKILL.md
6. [ ] Test with sample SPEC containing ui/backend/docs types

---

## Problem 3: Verification Drift

### Symptom
Claude forgets to run verification steps after `/compact`. UI components aren't visually tested, backend functions aren't validated, design guidelines aren't checked.

### Why it happens
- Verification steps are "implicit" expectations, not explicit TODO items
- After `/compact`, Claude focuses on completing tasks, skips quality checks
- Manual verification instructions in SPEC.md get lost

### Chosen Solution: Task `type` field with auto-expanded verification tasks

Add a `type` field to tasks that automatically expands into visible verification tasks in the TODO.

#### Task Types

| Type | Pre-task (visible) | Post-task (visible) | Implicit |
|------|---------------------|----------------------|----------|
| `ui` | `/frontend-design` + `/vercel-design-guidelines` | Visual QA with Claude in Chrome | - |
| `docs` | - | Verify file exists | - |
| `backend` | - | Run tests for function/module | - |
| `func` | - | Run tests, verify passes | - |
| (default) | - | - | Typecheck |

**Note:** `test` and `db` operations are implicit (part of verification commands), not separate task types.

#### SPEC.json → TODO Expansion

**UI tasks expand to 3 items:** pre (both skills) → main → post (visual QA)

```
SPEC.json (compact)                    TODO (expanded, visible)
───────────────────────────────────────────────────────────────
{
  "id": "1.3",                         1.3a: Run /frontend-design and /vercel-design-guidelines for ProfileCard
  "type": "ui",                        1.3: Create ProfileCard component
  "task": "Create ProfileCard",        1.3b: Visual QA: Verify ProfileCard with Claude in Chrome
  "files": ["ProfileCard.tsx"]
}
```

**Backend/func tasks expand to 2 items:** main → post (test)

```
{
  "id": "2.1",                         2.1: Implement getUserById query
  "type": "backend",                   2.1a: Test getUserById - verify returns correct data
  "task": "Implement getUserById",
  "files": ["convex/users.ts"]
}
```

**Docs tasks expand to 2 items:** main → post (verify)

```
{
  "id": "3.0",                         3.0: Update decisions.md with Phase 2 decisions
  "type": "docs",                      3.0a: Verify decisions.md exists and updated
  "task": "Update decisions.md",
  "files": [".claude/checkpoints/..."]
}
```

#### Why Visible Tasks

After the 5th `/compact`, Claude forgets implicit expectations. Visible TODO items are **deterministic** - Claude MUST complete them.

Same principle as decisions.md: if it's not in the TODO, it won't happen reliably.

#### Warning for Alternating UI Tasks (Per Phase)

During SPEC generation, `read-spec` should warn if a phase has alternating task types:

```
⚠️ Phase 2 has alternating UI tasks: 2.1(ui) → 2.2(backend) → 2.3(ui) → 2.4(backend)
   Consider grouping UI tasks together to reduce repeated visual validations.
   This is a suggestion, not a blocker.
```

Validation is per-phase, not global, to avoid noise.

#### Implementation Required

1. **read-spec skill**:
   - Accept `type` field in task schema
   - Auto-generate pre/post tasks based on type
   - Emit warning for alternating UI patterns per phase

2. **count_tasks.py**:
   - Count expanded tasks (including auto-generated ones)
   - Or: read-spec outputs already-expanded SPEC.json

3. **SKILL.md**:
   - Document task types and their expansions

#### Open Questions

1. ~~Should `read-spec` output expanded SPEC.json or expand at execution time?~~ **Expand at read-spec generation time**
2. ~~Naming convention for sub-tasks: `1.3a`, `1.3b` or `1.3.1`, `1.3.2`?~~ **Use `X.Ya`, `X.Yb` (letter suffix)**
3. Should Visual QA tasks specify what to check, or be generic?

---

## Resolved Questions

1. ~~Can `Stop` hook actually block continuation?~~ **YES, confirmed**
2. ~~Should decisions.md be structured (JSON) or freeform (MD)?~~ **MD for readability**
3. ~~How verbose should phase transition tasks be in the TODO?~~ **N/A - read-spec generates X.0 tasks automatically**
4. ~~Should we validate decisions.md content (not just existence)?~~ **No - trust Claude executed the task**
5. ~~How to read Claude's internal TODO state from the hook?~~ **canonical file stays in sync via validate-todo.py**
