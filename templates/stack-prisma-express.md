# Stack Template: Prisma + Express

This template provides stack-specific configuration for projects using Prisma as the ORM and Express.js as the web framework.

## Stack Configuration

```json
{
  "stack": {
    "runtime": "npm",
    "framework": "express",
    "database": "prisma",
    "styling": "none"
  }
}
```

## Verification Commands

```json
{
  "verification_commands": {
    "typecheck": "npx tsc --noEmit",
    "lint": "npm run lint",
    "build": "npm run build",
    "dev": "npm run dev",
    "db_sync": "npx prisma migrate dev",
    "db_generate": "npx prisma generate",
    "db_studio": "npx prisma studio",
    "db_seed": "npx prisma db seed",
    "test": "npm test"
  }
}
```

## Common Verification Patterns

### After Schema Changes
```json
{
  "id": "X.Y",
  "task": "Apply database migration",
  "verification": {
    "type": "cli",
    "command": "npx prisma migrate dev --name feature_name",
    "success_criteria": "Migration applied successfully"
  }
}
```

### After Prisma Schema Changes
```json
{
  "id": "X.Y",
  "task": "Generate Prisma client",
  "verification": {
    "type": "cli",
    "command": "npx prisma generate",
    "success_criteria": "Client generated without errors"
  }
}
```

### Query Database State
```json
{
  "id": "X.Y",
  "task": "Verify data in database",
  "command": "npx prisma studio",
  "note": "Opens browser to inspect database"
}
```

## Project Structure (Typical)

```json
{
  "context": {
    "component_directories": [
      "src/routes/",
      "src/controllers/",
      "src/services/"
    ],
    "related_files": [
      "prisma/schema.prisma",
      "src/lib/prisma.ts"
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
      "task": "Read existing prisma/schema.prisma",
      "files": ["prisma/schema.prisma"]
    },
    {
      "id": "1.2",
      "task": "Add new model to schema",
      "files": ["prisma/schema.prisma"],
      "verification": {
        "type": "cli",
        "command": "npx prisma validate",
        "success_criteria": "Schema is valid"
      }
    },
    {
      "id": "1.3",
      "task": "Create and apply migration",
      "verification": {
        "type": "cli",
        "command": "npx prisma migrate dev --name add_feature_table",
        "success_criteria": "Migration created and applied"
      }
    },
    {
      "id": "1.4",
      "task": "Generate Prisma client",
      "verification": {
        "type": "cli",
        "command": "npx prisma generate",
        "success_criteria": "Client generated"
      }
    }
  ]
}
```

### Service Layer Phase
```json
{
  "id": "phase-2",
  "name": "Service Layer",
  "tasks": [
    {
      "id": "2.1",
      "task": "Create service with Prisma queries",
      "files": ["src/services/featureService.ts"],
      "notes": "Import PrismaClient from @prisma/client"
    },
    {
      "id": "2.2",
      "task": "Add CRUD operations",
      "files": ["src/services/featureService.ts"],
      "verification": {
        "type": "cli",
        "command": "npx tsc --noEmit",
        "success_criteria": "No type errors"
      }
    },
    {
      "id": "2.3",
      "task": "Write unit tests for service",
      "files": ["src/services/__tests__/featureService.test.ts"],
      "verification": {
        "type": "cli",
        "command": "npm test -- --grep 'featureService'",
        "success_criteria": "All tests pass"
      }
    }
  ]
}
```

### API Routes Phase
```json
{
  "id": "phase-3",
  "name": "API Routes",
  "tasks": [
    {
      "id": "3.1",
      "task": "Create Express router",
      "files": ["src/routes/features.ts"]
    },
    {
      "id": "3.2",
      "task": "Implement GET /features endpoint",
      "files": ["src/routes/features.ts"],
      "verification": {
        "type": "cli",
        "command": "curl http://localhost:3000/api/features",
        "success_criteria": "Returns JSON array"
      }
    },
    {
      "id": "3.3",
      "task": "Implement POST /features endpoint",
      "files": ["src/routes/features.ts"],
      "verification": {
        "type": "cli",
        "command": "curl -X POST http://localhost:3000/api/features -H 'Content-Type: application/json' -d '{\"name\":\"test\"}'",
        "success_criteria": "Creates and returns new record"
      }
    },
    {
      "id": "3.4",
      "task": "Register router in app",
      "files": ["src/app.ts"],
      "verification": {
        "type": "cli",
        "command": "npm run build",
        "success_criteria": "Build succeeds"
      }
    }
  ]
}
```

## Prisma-Specific Notes

1. **Client singleton**: Create single PrismaClient instance in `src/lib/prisma.ts`
2. **Migrations**: Always use `prisma migrate dev` in development, `prisma migrate deploy` in production
3. **Type safety**: Prisma generates types automatically from schema
4. **Relations**: Use `include` or `select` for eager loading relations
5. **Transactions**: Use `prisma.$transaction()` for atomic operations

## Example Context Section

```json
{
  "context": {
    "related_files": [
      "prisma/schema.prisma",
      "src/lib/prisma.ts",
      "src/types/index.ts"
    ],
    "reusable_components": [
      "src/middleware/auth.ts",
      "src/middleware/validation.ts",
      "src/utils/errors.ts"
    ],
    "component_directories": [
      "src/routes/",
      "src/controllers/",
      "src/services/",
      "src/middleware/"
    ],
    "dependencies": [
      "@prisma/client",
      "express",
      "zod"
    ],
    "env_vars": [
      "DATABASE_URL",
      "PORT"
    ]
  }
}
```

## Testing Patterns

### Integration Tests with Test Database
```json
{
  "id": "X.Y",
  "task": "Run integration tests",
  "verification": {
    "type": "cli",
    "command": "DATABASE_URL='postgresql://test' npm run test:integration",
    "success_criteria": "All integration tests pass"
  }
}
```

### API Endpoint Tests
```json
{
  "id": "X.Y",
  "task": "Test API endpoints",
  "verification": {
    "type": "cli",
    "command": "npm run test:api",
    "success_criteria": "All API tests pass"
  }
}
```
