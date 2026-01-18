# SPEC.json Schema Reference

Complete schema for generating SPEC.json files.

## Top-Level Structure

```json
{
  "feature": "Feature Name",
  "description": "Brief description of what this feature does",
  "completion_promise": "FEATURE_COMPLETE",
  "created_at": "2024-01-15T10:30:00Z",
  "spec_reference": "SPEC.md",

  "execution_guidelines": { ... },
  "stack": { ... },
  "context": { ... },
  "verification_commands": { ... },
  "phases": [ ... ],
  "definition_of_done": [ ... ],
  "instructions_for_executor": { ... }
}
```

---

## Field Details

### execution_guidelines

```json
{
  "execution_guidelines": {
    "mode": "autonomous_end_to_end",
    "return_to_human": "only_when_fully_complete",
    "quality_priority": "production_ready_over_speed",
    "todo_detail_level": "extensive_and_granular",
    "testing_approach": "sequential_throughout_not_batched",
    "critical_notes": [
      "Run /spec-executor skill which counts tasks first",
      "TODO must have EXACTLY the task count from count_tasks.py",
      "Run /frontend-design BEFORE creating UI components",
      "Run /visual-qa AFTER creating UI components"
    ]
  }
}
```

### stack

```json
{
  "stack": {
    "runtime": "npm | bun | pnpm | yarn",
    "framework": "nextjs | express | fastify | etc",
    "database": "convex | prisma | drizzle | none",
    "styling": "tailwind | css-modules | styled-components"
  }
}
```

### context

```json
{
  "context": {
    "related_files": ["src/lib/auth.ts", "convex/users.ts"],
    "reusable_components": ["Button", "Card", "Modal"],
    "component_directories": ["src/components/ui", "src/features"],
    "dependencies": ["@tanstack/react-query", "zod"],
    "env_vars": ["DATABASE_URL", "AUTH_SECRET"]
  }
}
```

### verification_commands

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

---

## Phase Structure

```json
{
  "id": "phase-1",
  "name": "Backend Implementation",
  "description": "Create database schema and API endpoints",
  "status": "pending",
  "depends_on": ["phase-0"],
  "tasks": [
    {
      "id": "1.0",
      "task": "Update decisions.md with Phase 1 objectives",
      "files": [".claude/checkpoints/my-feature-decisions.md"]
    },
    {
      "id": "1.1",
      "task": "Run /frontend-design for UserCard component",
      "notes": "Get design guidance before creating UI"
    },
    {
      "id": "1.2",
      "task": "Create UserCard component",
      "files": ["src/components/UserCard.tsx"]
    },
    {
      "id": "1.3",
      "task": "Run /visual-qa to verify UserCard",
      "notes": "Verify component renders correctly"
    }
  ]
}
```

### Task Fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique task ID (format: `X.Y`) |
| `task` | Yes | Task description |
| `files` | No | Files to create/modify |
| `notes` | No | Additional context |
| `command` | No | Shell command to run |
| `verification` | No | How to verify completion |

### Verification Object

```json
{
  "verification": {
    "type": "cli",
    "command": "$verification_commands.typecheck",
    "success_criteria": "No errors"
  }
}
```

---

## Loop Phase Structure

For phases that iterate over dynamic items:

```json
{
  "id": "phase-2",
  "name": "Process Items",
  "description": "For each item, execute tasks 2.0-2.N",
  "loop": {
    "over": "items discovered in phase-1",
    "checkpoint_spec": "my-feature",
    "tasks": [
      {
        "id": "2.0",
        "task": "Update checkpoint: starting this item",
        "command": "python3 $SCRIPTS/checkpoint.py update my-feature --index <INDEX>"
      },
      {
        "id": "2.1",
        "task": "Process item data"
      },
      {
        "id": "2.2",
        "task": "Validate item result"
      },
      {
        "id": "2.3",
        "task": "Mark item complete in checkpoint",
        "command": "python3 $SCRIPTS/checkpoint.py complete my-feature --index <INDEX>"
      }
    ]
  }
}
```

---

## instructions_for_executor

```json
{
  "instructions_for_executor": {
    "first_action": "Run /spec-executor skill OR run count_tasks.py",
    "scripts_location": "Find via: dirname $(find ~/.claude -name 'count_tasks.py' -path '*/spec-executor/*' 2>/dev/null | head -1)",
    "todo_requirements": [
      "Include ALL tasks from ALL phases",
      "Each task ID = ONE separate TODO item",
      "TODO count must EXACTLY match count_tasks.py output"
    ],
    "ui_workflow": [
      "BEFORE creating UI: Run /frontend-design",
      "AFTER creating UI: Run /visual-qa"
    ],
    "checkpoint_commands": {
      "init": "python3 $SCRIPTS/checkpoint.py init <spec-name> --total <N>",
      "update": "python3 $SCRIPTS/checkpoint.py update <spec-name> --index <N>",
      "complete": "python3 $SCRIPTS/checkpoint.py complete <spec-name> --index <N>",
      "read": "python3 $SCRIPTS/checkpoint.py read <spec-name>",
      "clear": "python3 $SCRIPTS/checkpoint.py clear <spec-name>"
    },
    "completion": "Only output <promise>COMPLETION_PROMISE</promise> when ALL tasks verified"
  }
}
```

---

## definition_of_done

```json
{
  "definition_of_done": [
    "All phases completed with status: completed",
    "TypeScript/type checking passes",
    "Linting passes",
    "Build succeeds",
    "No console errors",
    "No regressions in existing features",
    "SPEC.md Execution Log updated"
  ]
}
```

---

## Task Status Values

| Status | Meaning |
|--------|---------|
| `pending` | Not started |
| `in_progress` | Currently being worked on |
| `completed` | Done and verified |
| `blocked` | Waiting on dependency |
| `failed` | Attempted but needs retry |

## Verification Types

| Type | When to Use |
|------|-------------|
| `cli` | Shell command (typecheck, build, db sync) |
| `visual` | UI verification with browser automation |
| `e2e` | End-to-end flow test |
| `file` | File existence or content check |
| `manual` | Requires human verification |
