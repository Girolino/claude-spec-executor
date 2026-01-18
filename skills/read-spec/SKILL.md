---
name: read-spec
description: Plan long-running tasks. Interview stakeholders, discover project architecture, then generate detailed SPEC.json with granular tasks and verification steps.
---

# Read Spec

Transform SPEC.md into an executable SPEC.json with granular tasks.

---

## Phase 1: Discovery

Before interviewing, understand the project:

### What to Discover

| Area | How |
|------|-----|
| Components | `Glob("**/components/**/*.{tsx,jsx}")` |
| Hooks | `Glob("**/hooks/**/*.{ts,tsx}")` |
| Structure | `LS("src/")` or `LS("app/")` |
| Stack | Check package.json, tsconfig.json, next.config.* |

### Stack Detection

Identify from config files:
- **Runtime:** npm, bun, pnpm, yarn
- **Framework:** Next.js, Express, Fastify
- **Database:** Convex, Prisma, Drizzle
- **Styling:** Tailwind, CSS Modules

Document findings - they inform the SPEC.json context.

---

## Phase 2: Interview

Read @SPEC.md and interview the user about:
- Technical implementation details
- UI/UX decisions
- Edge cases and error handling
- Integration with existing features

### Required Questions

Use `AskUserQuestion` to gather:
1. Build/typecheck command
2. Lint command
3. Database sync command (if applicable)
4. How to run dev server
5. Test command (if applicable)

Don't ask questions you can answer from discovery.

---

## Phase 3: Generate SPEC.json

### Core Principles

1. **Autonomous Execution** - Executor runs end-to-end, returns only when complete
2. **Granular Tasks** - Break every phase into small, verifiable tasks (15-30 min each)
3. **Quality Over Speed** - Production-ready code, not quick hacks
4. **Testing Throughout** - Verify after each task, not batched at end

### UI Task Pattern

For any UI component:
```
1. Run /frontend-design for [Component]
2. Create [Component]
3. Run /visual-qa to verify [Component]
```

### Checkpoints (for loops only)

Add checkpoint tasks if:
- Loop iterates over 5+ items
- Expected time > 30 minutes

See [CHECKPOINT_GUIDE.md](../shared/CHECKPOINT_GUIDE.md) for details.

### SPEC.json Structure

```json
{
  "feature": "Feature Name",
  "completion_promise": "FEATURE_COMPLETE",
  "stack": { "runtime": "bun", "framework": "nextjs", ... },
  "verification_commands": { "typecheck": "...", "build": "..." },
  "phases": [
    {
      "id": "phase-0",
      "name": "Pre-Flight",
      "tasks": [
        { "id": "0.0", "task": "Create decisions.md" },
        { "id": "0.1", "task": "Verify typecheck passes" }
      ]
    }
  ]
}
```

For complete schema, see [SCHEMA.md](SCHEMA.md).
For examples, see [EXAMPLES.md](../shared/EXAMPLES.md).

---

## Phase 4: Prepare SPEC.md

Add these sections to SPEC.md:

### Status Table

```markdown
## Status

| Phase | Goal | Status |
|-------|------|--------|
| Phase 0 | Pre-flight | pending |
| Phase 1 | ... | pending |
```

### Execution Log

```markdown
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

1. Write `SPEC.json` with all phases and tasks
2. Verify count: `python3 $SCRIPTS/count_tasks.py SPEC.json`
3. Update SPEC.md with Status and Execution Log sections
4. Report task count to user

For reference material:
- [SCHEMA.md](SCHEMA.md) - Full JSON schema
- [REFERENCE.md](REFERENCE.md) - Task types, glossary
- [EXAMPLES.md](../shared/EXAMPLES.md) - Real execution traces
- [CHECKPOINT_GUIDE.md](../shared/CHECKPOINT_GUIDE.md) - Loop recovery
