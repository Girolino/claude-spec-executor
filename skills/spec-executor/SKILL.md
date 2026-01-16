---
name: spec-executor
description: |
  Execute SPEC.json or SPEC.md files with guaranteed granular TODO tracking.

  TRIGGERS - Use this skill when:
  - User provides @SPEC.json or @SPEC.md file
  - User says "execute spec", "run spec", "plan and execute"
  - User mentions long-running task with detailed specification

  AUTONOMOUS EXECUTION (NON-NEGOTIABLE):
  - NEVER stop to ask for confirmation
  - NEVER pause after completing a task or sub-skill
  - IMMEDIATELY continue to next task after each completion
  - Only stop when ALL tasks done OR blocking error requires human input

  CRITICAL REQUIREMENTS (BLOCKING - DO NOT SKIP):
  1. Run count_tasks.py FIRST to get exact task count
  2. Create TODO with ALL tasks in SINGLE TodoWrite call BEFORE any execution
  3. Validate TODO count matches script output
  4. IF MISMATCH: Delete and recreate TODO until counts match
  5. Only THEN start executing tasks

  NEVER create TODO incrementally. NEVER start work before TODO is complete and validated.
---

# SPEC Executor

## Script Location

Scripts are located in the plugin's `skills/spec-executor/scripts/` directory.

**Finding scripts path:**
```bash
# If installed as plugin, scripts are at:
# ~/.claude/plugins/spec-executor/skills/spec-executor/scripts/

# Find the exact path:
SCRIPTS=$(dirname "$(find ~/.claude -name "count_tasks.py" -path "*/spec-executor/*" 2>/dev/null | head -1)")

# Or if using plugin in development mode, check the plugin directory
```

**For convenience**, you can set an alias in your shell or use the full path. Examples in this document use `$SCRIPTS` as shorthand.

---

## AUTONOMOUS EXECUTION MODE (CRITICAL)

**NEVER STOP. NEVER PAUSE. NEVER ASK FOR CONFIRMATION.**

Once SPEC execution begins, you MUST continue autonomously until:
1. ALL tasks are completed, OR
2. A blocking error occurs that genuinely requires human input

## COMPLETION RULES (NON-NEGOTIABLE)

You MUST NOT stop until ALL TODO items are marked `completed`.

**A Stop hook will block premature stops.** If you try to stop with pending tasks, the hook will block and instruct you to continue.

### If You Cannot Proceed With a Task

- DO NOT stop and wait
- DO NOT say "let me know if you want me to continue"
- DO use `AskUserQuestion` to get clarification
- THEN continue with execution

### Your Only Options Are

1. **Continue** with the next pending task
2. **Use AskUserQuestion** if genuinely blocked and need human input

The Stop hook + AskUserQuestion pattern prevents infinite loops while ensuring completion.

### Rules for Continuous Execution

| Situation | Action |
|-----------|--------|
| Task completed | **Immediately** start next task |
| Sub-skill finished (e.g., `/frontend-design`) | **Immediately** continue with next TODO item |
| Phase completed | **Immediately** start next phase |
| Verification passed | **Immediately** move on |
| Minor error (fixable) | Fix it and continue |
| Loop iteration done | **Immediately** start next iteration |

### FORBIDDEN Behaviors

- "Let me know if you want me to continue"
- "Should I proceed with the next task?"
- "I've completed X, what would you like me to do next?"
- Stopping after running a sub-skill
- Waiting for user acknowledgment between tasks
- Summarizing progress and pausing

### REQUIRED Behavior

- Complete task -> Update TODO -> Start next task (no pause)
- Run sub-skill -> Sub-skill returns -> Continue immediately
- Finish loop iteration -> Start next iteration (no pause)
- Only output final summary when ALL tasks are done

### After Sub-Skills

When a task requires running another skill (like `/frontend-design`):
1. Run the skill
2. Apply its output/guidance
3. **IMMEDIATELY** mark task complete and start the next one
4. Do NOT pause to explain what the skill returned

---

## File Format Preference

**Always prefer SPEC.json over SPEC.md** for execution:
- SPEC.json has structured `phases[].tasks[]` with explicit IDs
- Task counting is deterministic and reliable
- SPEC.md is kept as reference document (see `spec_reference` field in JSON)

If only SPEC.md exists, run `/read-spec` first to generate SPEC.json.

## MANDATORY First Action (BLOCKING)

**STOP. DO NOT PROCEED** until you complete these steps IN ORDER:

### Step 0: Expand tasks (if not already expanded)
Check if SPEC.json has `_expansion.expanded: true`. If not:
```bash
# Expand task types to verification tasks
python3 $SCRIPTS/expand-tasks.py SPEC.json
```

This auto-generates pre/post tasks based on `type` field:
- `ui` → 3 tasks (skills + main + visual QA)
- `backend`/`func` → 2 tasks (main + test)
- `docs` → 2 tasks (main + verify)

### Step 1: Count tasks AND set expectation
```bash
# Count tasks and save expectation for hook validation
python3 $SCRIPTS/count_tasks.py SPEC.json

# CRITICAL: Save expected count for automatic hook validation
echo <NUMBER> > /tmp/claude-expected-todo-count
```

Replace `<NUMBER>` with the exact count from count_tasks.py output.

**Example:**
```bash
python3 $SCRIPTS/expand-tasks.py SPEC.json  # If not expanded
python3 $SCRIPTS/count_tasks.py SPEC.json
# Output: "Total tasks: 35"

echo 35 > /tmp/claude-expected-todo-count
```

### Step 2: Create COMPLETE TODO upfront
**IMMEDIATELY** call TodoWrite with ALL tasks from ALL phases.

**AUTOMATIC VALIDATION**: A PostToolUse hook will automatically validate that your TODO has EXACTLY the expected number of items. If counts don't match, the hook will BLOCK and show an error message. You MUST recreate the TODO until validation passes.

### Step 3: Only THEN start execution
After hook validation passes (no error message), begin executing tasks sequentially.

---

**CRITICAL**: The TODO must be created BEFORE any execution starts. Not incrementally. Not lazily. ALL items UPFRONT in a SINGLE TodoWrite call.

## Automatic Hook Validation (Continuous)

A PostToolUse hook runs after **EVERY** TodoWrite call throughout execution:

### Phase 1: Initial Count Validation
1. Reads expected count from `/tmp/claude-expected-todo-count`
2. If mismatch: **BLOCKS** with error message
3. If match: Creates `.claude/todo-canonical.json` as reference

### Phase 2: Continuous Structure Validation
After the initial TODO is created, the hook validates **every subsequent TodoWrite**:
1. Compares against `.claude/todo-canonical.json`
2. **Allows**: Status changes (pending → in_progress → completed)
3. **Allows**: Phase collapse with proper markers (e.g., `0.x: Pre-Flight ✓`)
4. **BLOCKS**: Task removal without proper collapse
5. **BLOCKS**: Reducing task count without justification

### Why This Matters
Without continuous validation, Claude tends to "drift" during long executions:
- Collapsing tasks to "simplify" the TODO
- Removing completed tasks entirely
- Grouping multiple tasks into one

The canonical file persists on disk and survives `/compact`, ensuring structure is preserved.

### If Validation Fails

**Count mismatch (initial):**
```
=== TODO COUNT VALIDATION FAILED ===
Expected: 22 items
Actual: 7 items

You MUST recreate the TODO with EXACTLY 22 items.
Do NOT proceed until counts match.
===============================
```

**Structure mismatch (during execution):**
```
=== TODO VALIDATION FAILED ===

Task removal not allowed. Missing: ['2.3', '2.4', '2.5']

TO RECOVER, regenerate the TODO from SPEC:

  # Option 1: Use generate-todo.py
  python3 $SCRIPTS/generate-todo.py --spec SPEC.json --base --format json

  # Option 2: Read canonical directly
  cat .claude/todo-canonical.json

Then recreate TodoWrite with ALL original task IDs.
===============================
```

**Action required**: Regenerate TODO from SPEC.json or read the canonical file, then recreate with ALL task IDs.

## TODO Creation Rules

### NEVER DO THIS (Anti-patterns)

```
BAD: "Phase 0: Setup schema" (combines multiple tasks)
BAD: "Implement database mutations" (too vague)
BAD: "Complete Phase 1-3" (batching phases)
BAD: "I'll expand the TODO later when I know how many items" (FORBIDDEN)
```

### ALWAYS DO THIS (Required pattern)

```
GOOD: "0.1: Read existing schema file"
GOOD: "0.2: Add new table to schema"
GOOD: "2.0: Update checkpoint: starting this item"
GOOD: "2.10: Mark item complete in checkpoint"
```

Each task ID from the SPEC (0.1, 0.2, 1.1, 1.2, etc.) = ONE separate TODO item.

### Loop Tasks Are TEMPLATE Tasks

**IMPORTANT**: For loop phases, create TODO items for each task ID (2.0, 2.1, ..., 2.10) ONCE.

During execution, these template tasks are executed MULTIPLE TIMES (once per loop item). The TODO tracks the TEMPLATE, not the expansion.

Example for a SPEC with 22 tasks including a loop:
- TODO has 22 items (matching count_tasks.py output)
- Loop tasks 2.0-2.10 appear ONCE in TODO
- During execution: mark 2.0 in_progress -> complete -> 2.1 in_progress -> complete -> ... -> repeat for next item
- Checkpoint tracks which ITEM you're on (external state)
- TODO tracks which TASK ID you're on (internal state)

**DO NOT** think "I'll expand to 22 + (11 x N items) later". The TODO has EXACTLY the count from count_tasks.py. Period.

## Execution Flow

### Step 1: Count Tasks

```bash
python3 $SCRIPTS/count_tasks.py SPEC.json
# Output: "Total tasks: 47"
```

### Step 2: Create TODO

Create TodoWrite with EXACTLY that many items. Format each as:
- `{task_id}: {task_description}`

Example for 47 tasks:
```
0.1: Verify development environment
0.2: Check existing project structure
...
3.5: Output completion summary
```

### Step 3: Validate Count

After creating TODO, verify:
```
Script says: "Total tasks: 47"
Your TODO has: 47 items
```

**If counts don't match, STOP and recreate the TODO.** Do not proceed until counts match exactly.

### Step 4: Execute Sequentially

- Mark current task `in_progress`
- Complete the task
- Mark task `completed`
- Move to next task

Never have more than 1 task `in_progress` at a time.

### Step 5: Update SPEC.md Execution Log

Every 10 tasks OR at phase boundaries, update SPEC.md's Execution Log section:
- Current phase and task
- Key findings or decisions made
- Any blockers encountered

This enables session resumption if interrupted.

## Dual-Document Strategy

| Document | Purpose | Update Frequency |
|----------|---------|------------------|
| SPEC.json | Task definitions (expanded, read-only during execution) | Never during execution |
| SPEC.md | Execution Log, decisions, findings | Every 10 tasks / phase boundary |
| TODO | Granular progress tracking | After every task |
| Checkpoint | Loop state for /compact recovery | Every loop iteration |
| **todo-canonical.json** | **Reference for TODO validation** | **Created once, never modified** |
| **decisions.md** | **Execution context for scope preservation** | **At phase transitions (task X.0)** |

### Scripts Reference

| Script | Purpose |
|--------|---------|
| `expand-tasks.py` | Expand task types to verification tasks |
| `count_tasks.py` | Count total tasks in SPEC.json |
| `generate-todo.py` | Generate TODO structure from SPEC |
| `checkpoint.py` | Manage loop state for /compact recovery |

### Canonical TODO (.claude/todo-canonical.json)

This file is created automatically on the first TodoWrite and serves as the **immutable reference** for all subsequent validations.

**Structure:**
```json
{
  "created_at": "2024-01-15T10:30:00Z",
  "spec_file": "SPEC.json",
  "task_count": 22,
  "task_ids": ["0.1", "0.2", "1.1", ...],
  "todos": [...]
}
```

**Rules:**
- Created once when TODO is first written
- Never modified during execution
- Survives `/compact`
- Cleared only when `checkpoint.py clear` is called (execution complete)

## Decisions.md Pattern (CRITICAL FOR SCOPE PRESERVATION)

Every SPEC execution must maintain a `decisions.md` file to preserve execution context across `/compact`.

### Why This Matters

After `/compact`:
- Claude forgets the "why" behind implementation decisions
- Re-reading entire SPEC.md bloats context
- Scope drift happens when Claude focuses on tasks but loses the objective

### Required Tasks

Every phase has a `X.0` task to update decisions.md:
- **Task 0.0**: Create decisions.md with objective, constraints, success criteria
- **Task 1.0, 2.0, etc.**: Update with previous phase decisions and current phase objectives

### File Location

`.claude/checkpoints/<spec-name>-decisions.md`

### What to Write

**At task 0.0** (creation):
- Objective summary from SPEC.md
- Key constraints (what must NOT change)
- Success criteria (how we know we're done)

**At task X.0** (updates):
- Key decisions made in previous phase with rationale
- What current phase will accomplish
- Current state (phase, last completed task, next task)

### Cleanup

The file is deleted automatically when `checkpoint.py clear` runs at execution end.

---

## Task Types (Auto-Expansion)

Tasks with a `type` field are auto-expanded by `expand-tasks.py` into visible verification tasks.

### Expansion Rules

| Type | Expands To | Example |
|------|------------|---------|
| `ui` | pre (skills) + main + post (visual QA) | `1.2a` + `1.2` + `1.2b` |
| `backend` | main + post (test) | `1.3` + `1.3a` |
| `func` | main + post (test) | `1.4` + `1.4a` |
| `docs` | main + post (verify) | `1.0` + `1.0a` |
| (none) | main only | `1.5` |

### Why Visible Tasks

After `/compact`, Claude forgets to run design skills and visual QA. Making them explicit TODO items ensures they happen.

### Expanded Task Examples

**UI task (type: ui):**
```
1.2a: Run /frontend-design and /vercel-design-guidelines for ProfileCard
1.2: Create ProfileCard component
1.2b: Visual QA: Verify ProfileCard with Claude in Chrome
```

**Backend task (type: backend):**
```
2.1: Implement getUserById query
2.1a: Test getUserById - verify returns correct data and handles errors
```

### Checking Expansion Status

The SPEC.json has `_expansion.expanded: true` after expansion. The script skips already-expanded files.

---

## Checkpoint Pattern for Loops

**CRITICAL for long-running tasks**: SPECs with loops (e.g., processing 40 items) can run for HOURS. After `/compact`, context is lost. Checkpoints persist loop state externally.

### When to Use Checkpoints

Use checkpoints when SPEC has:
- A `loop` phase that iterates over dynamic items
- Expected execution time > 30 minutes
- Risk of context compaction during execution

### Checkpoint Script

```bash
# Initialize (after discovery phase knows item count)
# --spec-file stores the path so hooks can find it without guessing
python3 $SCRIPTS/checkpoint.py init <spec-name> --total <N> --spec-file SPEC.json

# Update (at START of each loop iteration)
python3 $SCRIPTS/checkpoint.py update <spec-name> \
  --index <N> --task <task-id> --item-id <id> --item-name '<name>'

# Complete (at END of each loop iteration)
python3 $SCRIPTS/checkpoint.py complete <spec-name> --index <N>

# Read (to check state or resume)
python3 $SCRIPTS/checkpoint.py read <spec-name>

# Clear (after successful completion)
python3 $SCRIPTS/checkpoint.py clear <spec-name>
```

### Checkpoint File Location

```
.claude/checkpoints/
├── <spec-name>.json           # Loop state
└── <spec-name>-decisions.md   # Execution context
```

### SPEC Schema for Loops with Checkpoints

```json
{
  "id": "phase-1",
  "tasks": [
    { "id": "1.1", "task": "Discover items to process" },
    { "id": "1.2", "task": "Initialize checkpoint", "command": "checkpoint.py init ..." },
    { "id": "1.3", "task": "Check existing checkpoint (for resumption)" }
  ]
},
{
  "id": "phase-2",
  "loop": {
    "over": "items from phase-1",
    "checkpoint_spec": "<spec-name>",
    "tasks": [
      { "id": "2.0", "task": "Update checkpoint: starting item" },
      { "id": "2.1", "task": "First actual task" },
      ...
      { "id": "2.N", "task": "Mark item complete in checkpoint" }
    ]
  }
}
```

### Resumption After /compact

1. **Read checkpoint**: `checkpoint.py read <spec-name>`
2. **Get completed items**: Check `completed_items` array
3. **Skip completed**: In loop, skip items already in `completed_items`
4. **Resume from current**: Start at `current_index` and `current_task`

## Loop Execution Flow (DETERMINISTIC)

**CRITICAL**: When executing a loop phase, you MUST follow this exact flow for EVERY item transition.

### Phase 1: Initial TODO (Before Loop)

```bash
# 1. Count and set expectation
python3 $SCRIPTS/count_tasks.py SPEC.json
echo 22 > /tmp/claude-expected-todo-count

# 2. Create TODO with all 22 template tasks
TodoWrite([...22 items...])  # Hook validates count
```

### Phase 2: Enter Loop (First Item)

```bash
# 3. Initialize checkpoint with total items and spec path
python3 $SCRIPTS/checkpoint.py init <spec-name> --total 40 --spec-file SPEC.json

# 4. Update checkpoint for first item
python3 $SCRIPTS/checkpoint.py update <spec-name> \
  --index 0 --task 2.0 --item-id "item-001" --item-name "Item Alpha"

# 5. Generate expanded TODO
python3 $SCRIPTS/generate-todo.py \
  --spec SPEC.json --checkpoint <spec-name> --format json

# 6. Recreate TODO with expansion
TodoWrite([...expanded for item 1/40...])  # Hook validates structure
```

### Phase 3: Execute Item Tasks

```
Execute 2.0 -> 2.1 -> 2.2 -> ... -> 2.10 for current item
Mark each task in TODO as completed
```

### Phase 4: Item Transition (MANDATORY STEPS)

**After completing ALL tasks for an item, you MUST execute these 4 steps IN ORDER:**

```bash
# Step 1: Mark item complete in checkpoint
python3 $SCRIPTS/checkpoint.py complete <spec-name> --index <N>

# Step 2: Update checkpoint for NEXT item
python3 $SCRIPTS/checkpoint.py update <spec-name> \
  --index <N+1> --task 2.0 --item-id "item-002" --item-name "Item Beta"

# Step 3: Generate new TODO with next item expanded
python3 $SCRIPTS/generate-todo.py \
  --spec SPEC.json --checkpoint <spec-name> --format json

# Step 4: Recreate TODO
TodoWrite([...expanded for item N+1...])
```

**The hook will BLOCK if:**
- TODO doesn't have the current item expanded (e.g., missing `[5/40]`)
- TODO count doesn't match expectation

### Phase 5: Loop Complete

```bash
# After last item (40/40):
python3 $SCRIPTS/checkpoint.py complete <spec-name> --index 39

# Execute verification phase tasks
# Then clear checkpoint
python3 $SCRIPTS/checkpoint.py clear <spec-name>
```

### Visual Flow

```
Item 1/40:
  checkpoint.py update --index 0
  generate-todo.py -> TodoWrite
  Execute 2.0-2.10
  checkpoint.py complete --index 0
       |
       v
Item 2/40:
  checkpoint.py update --index 1
  generate-todo.py -> TodoWrite
  Execute 2.0-2.10
  checkpoint.py complete --index 1
       |
       v
  ... repeat for 3-39 ...
       |
       v
Item 40/40:
  checkpoint.py update --index 39
  generate-todo.py -> TodoWrite
  Execute 2.0-2.10
  checkpoint.py complete --index 39
       |
       v
Verification Phase:
  Execute 3.1-3.4
  checkpoint.py clear
```

### TODO States During Loop

**Before loop:**
```
[ ] 0.1: Verify environment
[ ] 0.2: Check dependencies
... (22 template items)
```

**During loop (item 5/40):**
```
[x] 0.x: Pre-Flight completed
[x] 1.x: Discovery completed
[~] 2.loop: Process items (4/40)
  [x] 2.0: [5/40] Update checkpoint
  [x] 2.1: [5/40] Fetch item data
  [~] 2.2: [5/40] Process item    <- current
  [ ] 2.3: [5/40] Validate result
  ...
  [ ] 2.10: [5/40] Mark complete
[ ] 3.1: Verify all items
...
```

**After loop:**
```
[x] 0.x: Pre-Flight completed
[x] 1.x: Discovery completed
[x] 2.loop: Process items (40/40) completed
[ ] 3.1: Verify all items
[ ] 3.2: Run final checks
[ ] 3.3: Spot check samples
[ ] 3.4: Clear checkpoint
```

## Resumption Protocol

If session interrupted (including after `/compact`):

### Step 1: Check What Persisted on Disk

```bash
# Check for canonical TODO (your reference)
cat .claude/todo-canonical.json

# Check for active checkpoint (loop state)
ls -la .claude/checkpoints/

# Read checkpoint if exists
python3 $SCRIPTS/checkpoint.py read <spec-name>
```

### Step 2: Regenerate TODO Structure

**IMPORTANT**: The validation hook will BLOCK any TODO that doesn't match the canonical structure.

```bash
# Option A: Generate from SPEC (recommended)
python3 $SCRIPTS/generate-todo.py --spec SPEC.json --base --format json

# Option B: If in a loop, generate with checkpoint context
python3 $SCRIPTS/generate-todo.py --spec SPEC.json --checkpoint <spec-name> --format json
```

### Step 3: Recreate TODO with Correct Status

Use the output from generate-todo.py, but update statuses based on:
1. SPEC.md Execution Log (what was completed)
2. Checkpoint data (loop position)
3. Verification commands (actual state)

### For SPECs WITHOUT loops:
1. Read `.claude/todo-canonical.json` for original structure
2. Read SPEC.md Execution Log for last completed task
3. Recreate TODO with original structure
4. Mark completed tasks as `completed`
5. Resume from next incomplete task

### For SPECs WITH loops (checkpoint-enabled):
1. Read checkpoint: `checkpoint.py read <spec-name>`
2. Note `current_index`, `current_task`, and `completed_items`
3. Generate TODO: `generate-todo.py --spec SPEC.json --checkpoint <spec-name>`
4. Recreate TODO with expanded loop tasks for current item
5. Resume at `current_index` from `current_task`

### Recovery Example

```bash
# 1. Check state
python3 $SCRIPTS/checkpoint.py read my-feature
# Output: current_index=15, current_task=2.3, completed=15/40

# 2. Generate correct TODO
python3 $SCRIPTS/generate-todo.py \
  --spec SPEC.json \
  --checkpoint my-feature \
  --format preview

# 3. Recreate TODO with TodoWrite using the generated structure
# Hook will validate it matches canonical
```

## Validation Checkpoints

Every 10 tasks, verify:
1. TODO progress matches actual work done
2. No tasks were skipped
3. Verification steps were executed (not just marked done)
4. SPEC.md Execution Log is updated

## Error Handling

- If task fails: Keep it `in_progress`, fix issue, then complete
- If blocked: Add blocking issue as new TODO, proceed to unblocked tasks
- If SPEC unclear: Ask user before assuming

## Output on Completion

When all tasks complete, output:
```
SPEC EXECUTION COMPLETE

Summary:
- Total tasks: X
- Completed: X
- Phases completed: Y/Z
- Key outputs: [list main deliverables]

<promise>COMPLETION_PROMISE_FROM_SPEC</promise>
```
