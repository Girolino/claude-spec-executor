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
```

**For convenience**, you can set an alias in your shell or use the full path. Examples in this document use `$SCRIPTS` as shorthand.

---

## AUTONOMOUS EXECUTION MODE (CRITICAL)

**NEVER STOP. NEVER PAUSE. NEVER ASK FOR CONFIRMATION.**

Once SPEC execution begins, you MUST continue autonomously until:
1. ALL tasks are completed, OR
2. A blocking error occurs that genuinely requires human input

### If You Cannot Proceed With a Task

- DO NOT stop and wait
- DO NOT say "let me know if you want me to continue"
- DO use `AskUserQuestion` to get clarification
- THEN continue with execution

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

---

## File Format Preference

**Always prefer SPEC.json over SPEC.md** for execution:
- SPEC.json has structured `phases[].tasks[]` with explicit IDs
- Task counting is deterministic and reliable
- SPEC.md is kept as reference document (see `spec_reference` field in JSON)

If only SPEC.md exists, run `/read-spec` first to generate SPEC.json.

---

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

---

## UI Component Tasks (MANDATORY)

When working on UI components, you MUST follow this pattern:

### BEFORE Creating UI Component
Run `/frontend-design` to:
- Discover existing design system
- Get design guidance for the component
- Ensure consistency with project conventions

### AFTER Creating UI Component
Run `/visual-qa` to:
- Verify component renders correctly
- Check layout and spacing
- Test responsive behavior (if applicable)
- Validate interactive states

**Example flow for UI task:**
```
1. Run /frontend-design for ProfileCard
2. Create ProfileCard component
3. Run /visual-qa to verify ProfileCard renders correctly
```

---

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

---

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

---

## Dual-Document Strategy

| Document | Purpose | Update Frequency |
|----------|---------|------------------|
| SPEC.json | Task definitions (read-only during execution) | Never during execution |
| SPEC.md | Execution Log, decisions, findings | Every 10 tasks / phase boundary |
| TODO | Granular progress tracking | After every task |
| Checkpoint | Loop state for /compact recovery | Every loop iteration |
| decisions.md | Execution context for scope preservation | At phase transitions (task X.0) |

### Scripts Reference

| Script | Purpose |
|--------|---------|
| `count_tasks.py` | Count total tasks in SPEC.json |
| `generate-todo.py` | Generate TODO structure from SPEC |
| `checkpoint.py` | Manage loop state for /compact recovery |

---

## Decisions.md Pattern (FOR SCOPE PRESERVATION)

Every SPEC execution should maintain a `decisions.md` file to preserve execution context across `/compact`.

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

### Resumption After /compact

1. **Read checkpoint**: `checkpoint.py read <spec-name>`
2. **Get completed items**: Check `completed_items` array
3. **Skip completed**: In loop, skip items already in `completed_items`
4. **Resume from current**: Start at `current_index` and `current_task`

---

## Resumption Protocol

If session interrupted (including after `/compact`):

### Step 1: Check What Persisted on Disk

```bash
# Check for active checkpoint (loop state)
ls -la .claude/checkpoints/

# Read checkpoint if exists
python3 $SCRIPTS/checkpoint.py read <spec-name>

# Read decisions.md for context
cat .claude/checkpoints/<spec-name>-decisions.md
```

### Step 2: Regenerate TODO Structure

```bash
# Generate from SPEC
python3 $SCRIPTS/generate-todo.py --spec SPEC.json --base --format json

# If in a loop, generate with checkpoint context
python3 $SCRIPTS/generate-todo.py --spec SPEC.json --checkpoint <spec-name> --format json
```

### Step 3: Recreate TODO with Correct Status

Use the output from generate-todo.py, but update statuses based on:
1. SPEC.md Execution Log (what was completed)
2. Checkpoint data (loop position)
3. Verification commands (actual state)

---

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
