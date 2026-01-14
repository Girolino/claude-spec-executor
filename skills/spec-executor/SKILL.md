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
python3 $SCRIPTS/count_tasks.py SPEC.json
# Output: "Total tasks: 22"

echo 22 > /tmp/claude-expected-todo-count
```

### Step 2: Create COMPLETE TODO upfront
**IMMEDIATELY** call TodoWrite with ALL tasks from ALL phases.

**AUTOMATIC VALIDATION**: A PostToolUse hook will automatically validate that your TODO has EXACTLY the expected number of items. If counts don't match, the hook will BLOCK and show an error message. You MUST recreate the TODO until validation passes.

### Step 3: Only THEN start execution
After hook validation passes (no error message), begin executing tasks sequentially.

---

**CRITICAL**: The TODO must be created BEFORE any execution starts. Not incrementally. Not lazily. ALL items UPFRONT in a SINGLE TodoWrite call.

## Automatic Hook Validation

A PostToolUse hook runs after every TodoWrite call and:
1. Reads expected count from `/tmp/claude-expected-todo-count`
2. Counts actual TODO items created
3. If mismatch: **BLOCKS** with error message
4. If match: Passes silently and clears the expectation file

**If you see this error:**
```
=== TODO VALIDATION FAILED ===
Expected: 22 items
Actual: 7 items

You MUST recreate the TODO with EXACTLY 22 items.
Do NOT proceed until counts match.
===============================
```

**Action required**: Delete the TODO and recreate with ALL tasks. The hook will re-validate automatically.

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
| SPEC.json | Task definitions (read-only during execution) | Never during execution |
| SPEC.md | Execution Log, decisions, findings | Every 10 tasks / phase boundary |
| TODO | Granular progress tracking | After every task |
| Checkpoint | Loop state for /compact recovery | Every loop iteration |

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

`.claude/checkpoints/<spec-name>.json`

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

### For SPECs WITHOUT loops:
1. Run `count_tasks.py SPEC.json` to get total
2. Read SPEC.md Execution Log for last completed phase/task
3. Query current state using project's verification commands
4. Recreate TODO from SPEC.json
5. Mark completed tasks as `completed`
6. Resume from next incomplete task

### For SPECs WITH loops (checkpoint-enabled):
1. **First**: Read checkpoint file
   ```bash
   python3 $SCRIPTS/checkpoint.py read <spec-name>
   ```
2. Note `current_index`, `current_task`, and `completed_items`
3. Recreate TODO from SPEC.json
4. Mark pre-loop tasks as completed (Phase 0, 1)
5. For loop phase: skip items in `completed_items`
6. Resume at `current_index` from `current_task`

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
