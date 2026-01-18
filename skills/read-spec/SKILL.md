---
name: read-spec
description: Plan long-running tasks. Interview stakeholders, discover project architecture, then generate detailed SPEC.json with granular tasks and verification steps.
---

# Read Spec

Transform SPEC.md into an executable SPEC.json with granular tasks.

---

## Phase 1: Discovery

Explore the **codebase** to understand:
1. Project structure and relevant existing code
2. Stack and tooling (package.json, config files)
3. Patterns and conventions already in use

This informs SPEC.json `stack` and `verification_commands`.

---

## Phase 2: Interview

Read @SPEC.md and use `AskUserQuestion` to gather:
1. Build/typecheck command
2. Lint command
3. Database sync command (if applicable)
4. How to run dev server
5. Test command (if applicable)

Also clarify: technical implementation details, UI/UX decisions, edge cases.

Don't ask questions you can answer from discovery.

---

## Phase 3: Generate SPEC.json

### Core Principles

1. **Autonomous Execution** - Executor runs end-to-end, returns only when complete
2. **Granular Tasks** - Small, verifiable tasks (15-30 min each)
3. **Quality Over Speed** - Production-ready code, not quick hacks

### UI Task Pattern

For any UI component, always create 3 tasks:
```
1. Run /frontend-design for [Component]
2. Create [Component]
3. Run /visual-qa to verify [Component]
```

### SPEC.json Schema

```json
{
  "feature": "Feature Name",
  "description": "Brief description",
  "completion_promise": "FEATURE_COMPLETE",
  "spec_reference": "SPEC.md",

  "stack": {
    "runtime": "bun | npm | pnpm | yarn",
    "framework": "nextjs | express | etc",
    "database": "convex | prisma | none",
    "styling": "tailwind | css-modules | etc"
  },

  "verification_commands": {
    "typecheck": "bun run typecheck",
    "lint": "bun run lint",
    "build": "bun run build",
    "dev": "bun run dev",
    "db_sync": "bunx convex dev --once",
    "test": "bun run test"
  },

  "phases": [
    {
      "id": "phase-0",
      "name": "Pre-Flight",
      "tasks": [
        { "id": "0.0", "task": "Create decisions.md", "files": [".claude/checkpoints/<spec>-decisions.md"] },
        { "id": "0.1", "task": "Verify typecheck passes" },
        { "id": "0.2", "task": "Verify build passes" }
      ]
    },
    {
      "id": "phase-1",
      "name": "Implementation",
      "tasks": [
        { "id": "1.0", "task": "Update decisions.md for Phase 1" },
        { "id": "1.1", "task": "Run /frontend-design for UserCard" },
        { "id": "1.2", "task": "Create UserCard component", "files": ["src/components/UserCard.tsx"] },
        { "id": "1.3", "task": "Run /visual-qa for UserCard" }
      ]
    }
  ],

  "definition_of_done": [
    "All phases completed",
    "TypeScript passes",
    "Build succeeds",
    "No console errors"
  ]
}
```

### Task ID Format

- Format: `{phase}.{task}` (e.g., `0.1`, `1.3`, `2.0`)
- Phase 0: Pre-flight checks
- Task X.0: Usually "Update decisions.md"

### Loop Phases (for 5+ items)

When iterating over dynamic items, add checkpoint tasks:

```json
{
  "id": "phase-2",
  "name": "Process Items",
  "loop": {
    "over": "items from phase-1",
    "checkpoint_spec": "my-feature",
    "tasks": [
      { "id": "2.0", "task": "Update checkpoint: starting item" },
      { "id": "2.1", "task": "Process item" },
      { "id": "2.2", "task": "Verify item" },
      { "id": "2.3", "task": "Mark item complete in checkpoint" }
    ]
  }
}
```

---

## Phase 4: Prepare SPEC.md

Add these sections to SPEC.md:

```markdown
## Status

| Phase | Goal | Status |
|-------|------|--------|
| Phase 0 | Pre-flight | pending |
| Phase 1 | ... | pending |

## Execution Log

### Progress
- **Total tasks**: (from count_tasks.py)
- **Completed**: 0
- **Current phase**: Not started

### Session Log
| Timestamp | Phase | Task | Notes |
|-----------|-------|------|-------|
```

---

## Final Output

1. Write `SPEC.json` following the schema above
2. Count tasks:
   ```bash
   SCRIPTS=$(dirname "$(find ~/.claude -name "count_tasks.py" -path "*/spec-executor/*" 2>/dev/null | head -1)")
   python3 $SCRIPTS/count_tasks.py SPEC.json
   ```
3. Update SPEC.md with Status and Execution Log
4. Report task count to user
