# SPEC Execution Rules

These rules apply whenever working with SPEC files (SPEC.md or SPEC.json).

## Script Location

Plugin scripts are in `skills/spec-executor/scripts/`. Find the path:
```bash
SCRIPTS=$(dirname "$(find ~/.claude -name "count_tasks.py" -path "*/spec-executor/*" 2>/dev/null | head -1)")
```

## When to Use Skills

- **SPEC.md provided** → Use `read-spec` skill to generate SPEC.json
- **SPEC.json provided** → Use `spec-executor` skill to execute

## Mandatory Execution Process

1. **Count tasks first** (MANDATORY):
   ```bash
   python3 $SCRIPTS/count_tasks.py SPEC.json
   ```
   This outputs the exact number of tasks. Your TODO MUST match this count.

2. **Create granular TODO**: Each task ID (0.1, 0.2, 1.1, etc.) = ONE separate TODO item
   - **NEVER** combine tasks: "Phase 0: Setup" is WRONG
   - **ALWAYS** use task IDs: "0.1: Verify environment" is CORRECT

3. **Validate before proceeding**:
   ```
   Script says: "Total tasks: 47"
   Your TODO must have: 47 items
   If mismatch: STOP and recreate TODO
   ```

4. **Execute sequentially**: One task `in_progress` at a time. Complete and verify each.

5. **Never skip**: Follow the spec exactly - no batching, no summarizing.

## Stack Configuration

The SPEC.json contains `verification_commands` specific to the project's stack:
```json
{
  "verification_commands": {
    "typecheck": "npm run typecheck",
    "build": "npm run build",
    "db_sync": "npx prisma migrate dev"
  }
}
```

Use these commands for verification instead of assuming specific tools.

## Loop Recovery

When executing specs with loops (multiple items to process):

1. **Initialize checkpoint** before starting loop
2. **Update checkpoint** after each item completes
3. **After /compact**: Read checkpoint to resume from correct position

```bash
# Read checkpoint state
python3 $SCRIPTS/checkpoint.py read <spec-name>
```

## Anti-Patterns

- Executing SPEC.json without counting tasks first
- Creating TODO with fewer items than task count
- Combining multiple tasks into one TODO item
- Skipping tasks or "batching" similar ones
- Forgetting to update checkpoint during loops
- Hardcoding verification commands instead of using SPEC.json values
