# Reference Guide

Quick reference for creating SPEC.json files.

## Glossary

| Term | Meaning |
|------|---------|
| **SPEC.md** | Human-readable feature specification |
| **SPEC.json** | Machine-readable execution plan |
| **Phase** | Group of related tasks (e.g., "Backend", "Frontend") |
| **Task** | Single unit of work with ID like `1.2` |
| **Checkpoint** | Persisted loop state for recovery |
| **decisions.md** | Execution context file for scope preservation |
| **completion_promise** | Token output when ALL tasks complete |

---

## Task ID Format

Format: `{phase}.{task}` (e.g., `0.1`, `1.3`, `2.0`)

- Phase 0: Pre-flight checks
- Phase 1+: Implementation phases
- Task X.0: Usually "Update decisions.md" at phase start

---

## UI Task Sequence

For any task that creates/modifies UI components:

```
1. Run /frontend-design for [Component]     # Get design guidance
2. Create [Component]                        # Implement
3. Run /visual-qa to verify [Component]     # Validate visually
```

---

## Guidelines

### DO
- Break phases into small tasks (15-30 min each)
- Include file paths for every task
- Order tasks by dependency
- Use `$verification_commands` references
- Add checkpoint tasks for loops with 5+ items

### DON'T
- Batch all tests at the end
- Create tasks without file paths
- Skip verification after schema changes
- Hardcode commands (use verification_commands)

---

## Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| Spec name | kebab-case | `user-auth`, `profile-sync` |
| Task ID | X.Y format | `0.1`, `1.3`, `2.0` |
| Checkpoint | Same as spec name | `user-auth` |
| completion_promise | UPPER_SNAKE | `AUTH_COMPLETE` |

---

## Common Verification Commands

```json
{
  "verification_commands": {
    "typecheck": "bun run typecheck",
    "lint": "bun run lint",
    "build": "bun run build",
    "dev": "bun run dev",
    "db_sync": "bunx convex dev --once",
    "test": "bun run test"
  }
}
```

Adjust for your stack (npm, pnpm, yarn, etc.)
