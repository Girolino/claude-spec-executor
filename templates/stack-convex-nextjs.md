# Stack Template: Convex + Next.js (App Router)

This template provides stack-specific configuration for projects using Convex as the backend and Next.js with App Router.

## Stack Configuration

```json
{
  "stack": {
    "runtime": "bun",
    "framework": "nextjs",
    "database": "convex",
    "styling": "tailwind"
  }
}
```

## Verification Commands

```json
{
  "verification_commands": {
    "typecheck": "bunx tsc --noEmit",
    "lint": "bun run lint",
    "build": "bun run build",
    "dev": "bun run dev",
    "db_sync": "bunx convex dev --once",
    "db_query": "bunx convex run",
    "test": "bun test"
  }
}
```

## Common Verification Patterns

### After Schema Changes
```json
{
  "id": "X.Y",
  "task": "Verify schema syncs correctly",
  "verification": {
    "type": "cli",
    "command": "bunx convex dev --once",
    "success_criteria": "Schema syncs without errors"
  }
}
```

### After Convex Function Changes
```json
{
  "id": "X.Y",
  "task": "Test Convex function",
  "verification": {
    "type": "cli",
    "command": "bunx convex run functionName:functionName '{\"arg\": \"value\"}'",
    "success_criteria": "Function returns expected result"
  }
}
```

### Query Current State
```json
{
  "id": "X.Y",
  "task": "Query current data state",
  "command": "bunx convex run tableName:getAll",
  "note": "Use to verify data after mutations"
}
```

## Project Structure (Typical)

```json
{
  "context": {
    "component_directories": [
      "app/components/",
      "app/(dashboard)/*/components/"
    ],
    "related_files": [
      "convex/schema.ts",
      "convex/_generated/api.d.ts"
    ]
  }
}
```

## Phase Examples

### Database Schema Phase
```json
{
  "id": "phase-1",
  "name": "Database Schema",
  "tasks": [
    {
      "id": "1.1",
      "task": "Read existing convex/schema.ts",
      "files": ["convex/schema.ts"]
    },
    {
      "id": "1.2",
      "task": "Add new table to schema",
      "files": ["convex/schema.ts"],
      "verification": {
        "type": "cli",
        "command": "bunx convex dev --once",
        "success_criteria": "Schema syncs successfully"
      }
    }
  ]
}
```

### Convex Functions Phase
```json
{
  "id": "phase-2",
  "name": "Backend Functions",
  "tasks": [
    {
      "id": "2.1",
      "task": "Create query function",
      "files": ["convex/features.ts"],
      "verification": {
        "type": "cli",
        "command": "bunx convex run features:list",
        "success_criteria": "Returns empty array or existing data"
      }
    },
    {
      "id": "2.2",
      "task": "Create mutation function",
      "files": ["convex/features.ts"],
      "verification": {
        "type": "cli",
        "command": "bunx convex run features:create '{\"name\": \"test\"}'",
        "success_criteria": "Creates record and returns ID"
      }
    }
  ]
}
```

### UI Component Phase (Next.js App Router)
```json
{
  "id": "phase-3",
  "name": "UI Components",
  "tasks": [
    {
      "id": "3.1",
      "task": "Get design guidance",
      "pre_task": "Run /frontend-design skill"
    },
    {
      "id": "3.2",
      "task": "Create client component with Convex hooks",
      "files": ["app/(dashboard)/features/components/FeatureList.tsx"],
      "notes": "Use useQuery from convex/react for real-time data"
    },
    {
      "id": "3.3",
      "task": "Create page component",
      "files": ["app/(dashboard)/features/page.tsx"],
      "verification": {
        "type": "visual",
        "action": "Navigate to /features",
        "success_criteria": "Page renders with data from Convex"
      }
    }
  ]
}
```

## Convex-Specific Notes

1. **Real-time by default**: Convex queries automatically update when data changes
2. **Optimistic updates**: Use `.withOptimisticUpdate()` for mutations
3. **Type safety**: Import types from `convex/_generated/api`
4. **Validators**: Always use `v.` validators in function args
5. **Schema**: Define all tables in `convex/schema.ts`

## Example Context Section

```json
{
  "context": {
    "related_files": [
      "convex/schema.ts",
      "convex/_generated/api.d.ts",
      "lib/convex.ts"
    ],
    "reusable_components": [
      "app/components/ui/button.tsx",
      "app/components/ui/card.tsx"
    ],
    "component_directories": [
      "app/components/",
      "app/components/ui/"
    ],
    "dependencies": [
      "convex",
      "convex-helpers"
    ],
    "env_vars": [
      "CONVEX_DEPLOYMENT",
      "NEXT_PUBLIC_CONVEX_URL"
    ]
  }
}
```
