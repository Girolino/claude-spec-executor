---
name: read-spec
description: Read the spec, interview the human, and generate SPEC.json for Long Execution Plan
---

# Phase 1: Discovery

Before asking questions, run discovery to understand the project:

## 1.1 Project Structure Discovery

Use Glob and LS to discover:
- **Component directories**: Find where components live (e.g., `src/components/`, `app/components/`, `components/`)
- **Feature organization**: How features are structured (by domain, by type)
- **Shared utilities**: Location of hooks, helpers, utils
- **Configuration files**: package.json, tsconfig.json, etc.

```bash
# Example discovery commands
Glob("**/components/**/*.{tsx,jsx}")
Glob("**/hooks/**/*.{ts,tsx}")
LS("src/") or LS("app/")
```

## 1.2 Stack Detection

Identify the project's tech stack from configuration files:
- **Runtime**: Look at package.json scripts (npm, bun, pnpm)
- **Framework**: Next.js (next.config), Express, Fastify, etc.
- **Database**: Convex, Prisma, Drizzle, etc.
- **Styling**: Tailwind, CSS Modules, styled-components

## 1.3 Existing Patterns

Search for existing patterns to maintain consistency:
- How are similar features implemented?
- What abstractions exist that can be reused?
- Naming conventions and file organization

Document all findings - they inform the interview and SPEC generation.

---

# Phase 2: Interview

Read @SPEC.md and interview the user in detail using AskUserQuestionTool about:
- Technical implementation details
- UI & UX decisions
- Edge cases and error handling
- Tradeoffs and concerns
- Integration with existing features
- **Stack-specific commands** (build, test, database sync)

Rules:
- Don't ask obvious questions you could answer from discovery
- Be very in-depth and continue until complete
- Challenge assumptions when needed
- **Ask about verification commands** for the specific stack

### Required Interview Questions

At minimum, gather:
1. Build/typecheck command (e.g., `npm run build`, `bun run build`)
2. Lint command (e.g., `npm run lint`)
3. Database sync/migration command (if applicable)
4. How to run the development server
5. Any stack-specific verification commands

---

# Phase 3: Generate SPEC.json

After the interview, generate `SPEC.json` following this schema.

## Core Principles (CRITICAL)

### 1. End-to-End Autonomous Execution
The SPEC will be executed in a new Claude Code session. Claude must execute the entire implementation end-to-end, returning to the human ONLY when the feature is fully complete and validated. If blocked, attempt alternative approaches before asking for help.

### 2. Extensive TODO Generation (MANDATORY)
The executing session may run for HOURS. The SPEC must instruct Claude to create a SUPER DETAILED TODO list before coding:
- Break every phase into granular sub-tasks
- Include specific file paths, function names, and expected outcomes
- Update TODO status in real-time as work progresses
- Mark tasks complete ONLY when fully validated

**CRITICAL**: The executor will use `/spec-executor` skill which runs `count_tasks.py` to count tasks. The TODO must have EXACTLY that many items. Each task ID (0.1, 0.2, 1.1, etc.) = ONE TODO item.

### 3. Quality Over Speed (NON-NEGOTIABLE)
We are NOT in a hurry. An extensive TODO with multiple tests, validations, and execution steps optimized for quality is ALWAYS preferable to quick, less precise execution. The goal is PRODUCTION-READY code.

### 4. Granular Testing Throughout (NOT JUST AT THE END)
Each phase MUST include inline validation tasks. Tests are sequential throughout the implementation, NOT batched at the end:

- **After schema changes**: Database sync/migration verification
- **After backend functions**: API/function tests
- **After each UI component**: Visual verification + interaction testing (if browser automation available)
- **After each feature milestone**: E2E flow test
- **Before marking ANY task complete**: Confirm it works

### 5. Reusability First
Before creating ANY new component:
1. Check existing components discovered in Phase 1
2. Check feature-specific components in the same domain
3. If creating a new reusable component, place it in the shared components directory
4. Follow existing patterns and prop interfaces

### 6. UI Component Validation (MANDATORY)
For any task that creates or modifies UI components:

**BEFORE creating the component:**
- Run `/frontend-design` to discover existing design system and get guidance

**AFTER creating the component:**
- Run `/visual-qa` to verify it renders correctly

**Example task sequence for UI work:**
```json
{
  "id": "1.1",
  "task": "Run /frontend-design for ProfileCard component"
},
{
  "id": "1.2",
  "task": "Create ProfileCard component",
  "files": ["components/ProfileCard.tsx"]
},
{
  "id": "1.3",
  "task": "Run /visual-qa to verify ProfileCard renders correctly"
}
```

### 7. Checkpoint Pattern for Loops (CRITICAL FOR LONG TASKS)
When a SPEC has a **loop phase** (iterating over dynamic items like profiles, files, etc.), you MUST add checkpoint tasks to survive `/compact`:

**Why**: Loop tasks can run for HOURS. After `/compact`, Claude loses context. Checkpoints persist state externally.

**When to add checkpoints**:
- Phase iterates over items discovered at runtime (e.g., "for each item")
- Expected loop iterations > 5
- Expected execution time > 30 minutes

**Required checkpoint tasks**:
1. **In discovery phase** (before loop):
   - `X.N`: Initialize checkpoint with total count
   - `X.N+1`: Check existing checkpoint (for resumption)

2. **In loop phase** (first and last tasks):
   - `Y.0`: Update checkpoint at START of each iteration
   - `Y.LAST`: Mark item complete at END of each iteration

3. **In verification phase** (after loop):
   - `Z.N`: Clear checkpoint after all verifications pass

### 8. Decisions.md Pattern (FOR SCOPE PRESERVATION)
Every phase should have a `X.0` task to update `decisions.md`. This file preserves execution context across `/compact`.

**Why**: After `/compact`, Claude forgets the "why" behind the implementation. Re-reading the entire SPEC.md bloats context. The decisions.md is a compact checkpoint of objectives and decisions.

**Required tasks**:
- **Phase 0, task 0.0**: Create decisions.md with objective from SPEC.md
- **Every subsequent phase, task X.0**: Update decisions.md with previous phase decisions and current phase objectives

**File location**:
```
.claude/checkpoints/<spec-name>-decisions.md
```

**Template** (task 0.0 creates this):
```markdown
# Execution Context: <Feature Name>

## Objective
[Summary of SPEC.md goal - what we're building and why]

## Key Constraints
[From SPEC.md - things that must NOT change]

## Success Criteria
[How we know we're done]

---

## Phase 0 Decisions
- [Decision]: [Rationale]

## Current State
Phase: 0
Last completed: 0.0
Next: 0.1
```

---

## SPEC.json Schema

```json
{
  "feature": "Feature Name",
  "description": "Brief description",
  "completion_promise": "FEATURE_COMPLETE",
  "created_at": "ISO timestamp",
  "spec_reference": "SPEC.md",

  "execution_guidelines": {
    "mode": "autonomous_end_to_end",
    "return_to_human": "only_when_fully_complete",
    "quality_priority": "production_ready_over_speed",
    "todo_detail_level": "extensive_and_granular",
    "testing_approach": "sequential_throughout_not_batched",
    "critical_notes": [
      "Run /spec-executor skill which counts tasks first",
      "TODO must have EXACTLY the task count from count_tasks.py",
      "Update SPEC.md Execution Log every 10 tasks or at phase boundaries",
      "Run /frontend-design BEFORE creating UI components",
      "Run /visual-qa AFTER creating UI components"
    ]
  },

  "stack": {
    "runtime": "npm | bun | pnpm | yarn",
    "framework": "nextjs | express | fastify | etc",
    "database": "convex | prisma | drizzle | none",
    "styling": "tailwind | css-modules | styled-components"
  },

  "context": {
    "related_files": ["paths to key existing files"],
    "reusable_components": ["existing components to leverage"],
    "component_directories": ["discovered component paths"],
    "dependencies": ["external packages needed"],
    "env_vars": ["environment variables needed"]
  },

  "verification_commands": {
    "typecheck": "your typecheck command",
    "lint": "your lint command",
    "build": "your build command",
    "dev": "your dev server command",
    "db_sync": "your database sync command (if applicable)",
    "test": "your test command (if applicable)"
  },

  "phases": [
    {
      "id": "phase-0",
      "name": "Pre-Flight Checks",
      "description": "Verify environment and dependencies",
      "status": "pending",
      "depends_on": [],
      "tasks": [
        {
          "id": "0.0",
          "task": "Create decisions.md with execution objective from SPEC.md",
          "files": [".claude/checkpoints/<spec-name>-decisions.md"],
          "notes": "Write: objective summary, key constraints, success criteria."
        },
        {
          "id": "0.1",
          "task": "Verify development environment",
          "verification": {
            "type": "cli",
            "command": "$verification_commands.typecheck",
            "success_criteria": "No errors"
          }
        }
      ]
    },
    {
      "id": "phase-1",
      "name": "Phase Name",
      "description": "What this phase accomplishes",
      "status": "pending",
      "depends_on": ["phase-0"],
      "tasks": [
        {
          "id": "1.0",
          "task": "Update decisions.md: Record Phase 0 decisions and Phase 1 objectives",
          "files": [".claude/checkpoints/<spec-name>-decisions.md"]
        },
        {
          "id": "1.1",
          "task": "Run /frontend-design for ProfileCard component",
          "notes": "Get design guidance before creating UI"
        },
        {
          "id": "1.2",
          "task": "Create ProfileCard component",
          "files": ["components/ProfileCard.tsx"]
        },
        {
          "id": "1.3",
          "task": "Run /visual-qa to verify ProfileCard renders correctly",
          "notes": "Verify UI after creation"
        },
        {
          "id": "1.4",
          "task": "Implement getUserById query",
          "files": ["convex/users.ts"]
        },
        {
          "id": "1.5",
          "task": "Initialize checkpoint for loop tracking",
          "command": "python3 $SCRIPTS/checkpoint.py init <spec-name> --total <ITEM_COUNT>",
          "notes": "Only if next phase has a loop. Replace <ITEM_COUNT> with actual count."
        }
      ]
    },
    {
      "id": "phase-2",
      "name": "Process Items (Loop Phase)",
      "description": "For each item, execute tasks 2.0-2.N. Update checkpoint for /compact recovery.",
      "loop": {
        "over": "items from phase-1",
        "checkpoint_spec": "<spec-name>",
        "tasks": [
          {
            "id": "2.0",
            "task": "Update checkpoint: starting this item",
            "command": "python3 $SCRIPTS/checkpoint.py update <spec-name> --index <INDEX> --task 2.0 --item-id <ITEM_ID> --item-name '<ITEM_NAME>'",
            "notes": "MUST run at START of each loop iteration"
          },
          {
            "id": "2.1",
            "task": "First actual task for this item"
          },
          {
            "id": "2.N",
            "task": "Last actual task for this item"
          },
          {
            "id": "2.N+1",
            "task": "Mark item complete in checkpoint",
            "command": "python3 $SCRIPTS/checkpoint.py complete <spec-name> --index <INDEX> --item-id <ITEM_ID>",
            "notes": "MUST run at END of each loop iteration"
          }
        ]
      }
    },
    {
      "id": "phase-3",
      "name": "Verification",
      "tasks": [
        {
          "id": "3.1",
          "task": "Verify results"
        },
        {
          "id": "3.2",
          "task": "Clear checkpoint (execution complete)",
          "command": "python3 $SCRIPTS/checkpoint.py clear <spec-name>",
          "notes": "Only after ALL verifications pass"
        }
      ]
    }
  ],

  "definition_of_done": [
    "All phases completed with status: completed",
    "All granular tests passed throughout execution",
    "TypeScript/type checking passes",
    "Linting passes",
    "Build succeeds",
    "Final verification completed",
    "No console errors",
    "No regressions in existing features",
    "SPEC.md Execution Log updated with final results"
  ],

  "instructions_for_executor": {
    "first_action": "Run /spec-executor skill OR run count_tasks.py",
    "scripts_location": "Find via: dirname $(find ~/.claude -name 'count_tasks.py' -path '*/spec-executor/*' 2>/dev/null | head -1)",
    "todo_requirements": [
      "Include ALL tasks from ALL phases",
      "Each task ID (0.1, 0.2, etc.) = ONE separate TODO item",
      "TODO count must EXACTLY match count_tasks.py output",
      "If count doesn't match, recreate TODO before proceeding"
    ],
    "ui_workflow": [
      "BEFORE creating UI: Run /frontend-design",
      "AFTER creating UI: Run /visual-qa"
    ],
    "during_execution": [
      "Update TODO status in real-time",
      "Run verification after each task",
      "Do not proceed if verification fails",
      "Update SPEC.md Execution Log every 10 tasks or at phase boundaries"
    ],
    "resume_strategy": [
      "If SPEC has loops: read checkpoint first",
      "Read SPEC.md Execution Log for last completed task",
      "Query current state via verification commands",
      "Recreate TODO from SPEC.json, mark completed tasks",
      "For loops: skip items in checkpoint's completed_items array"
    ],
    "checkpoint_commands": {
      "init": "python3 $SCRIPTS/checkpoint.py init <spec-name> --total <N>",
      "update": "python3 $SCRIPTS/checkpoint.py update <spec-name> --index <N> --task <id> --item-id <id> --item-name '<name>'",
      "complete": "python3 $SCRIPTS/checkpoint.py complete <spec-name> --index <N>",
      "read": "python3 $SCRIPTS/checkpoint.py read <spec-name>",
      "clear": "python3 $SCRIPTS/checkpoint.py clear <spec-name>"
    },
    "completion": "Only output <promise>COMPLETION_PROMISE</promise> when ALL tasks verified"
  }
}
```

## Task Status Values
- `pending` - Not started
- `in_progress` - Currently being worked on
- `completed` - Done and verified
- `blocked` - Waiting on dependency
- `failed` - Attempted but needs retry

## Verification Types
- `cli` - Shell command verification (typecheck, build, db sync)
- `visual` - Visual/interaction verification (if browser automation available)
- `e2e` - End-to-end flow test with multiple steps
- `file` - File existence or content check
- `manual` - Requires human verification

## Guidelines
- The SPEC.json should be LONG and ROBUST - completeness over brevity
- Break phases into small, verifiable tasks (15-30 min each)
- Include file paths for every task
- Order tasks by dependency
- Keep completion_promise short and uppercase (e.g., "AUTH_COMPLETE", "GALLERY_DONE")
- Include `instructions_for_executor` section with TODO requirements
- **For loops**: ALWAYS add checkpoint tasks (init, update, complete, clear)
- **Checkpoint naming**: Use kebab-case spec name (e.g., "data-migration", "profile-sync")
- **Use $verification_commands references** instead of hardcoding commands
- **For UI tasks**: Include /frontend-design and /visual-qa in the task sequence

---

# Phase 4: Prepare SPEC.md for Execution

After generating SPEC.json, update SPEC.md to add/ensure these sections exist:

## Required SPEC.md Sections

### Status Table
```markdown
## Status

| Phase | Goal | Status | Output |
|-------|------|--------|--------|
| Phase 0 | Pre-flight checks | pending | ... |
| Phase 1 | ... | pending | ... |
```

### Execution Log
```markdown
## Execution Log

*Updated during execution. Add entries as work progresses.*

### Progress Summary
- **Total tasks**: (from count_tasks.py)
- **Completed**: 0
- **Current phase**: Not started

### Session Log
| Timestamp | Phase | Task | Notes |
|-----------|-------|------|-------|
```

### Interview Decisions (if not present)
```markdown
## Interview Decisions

Document key decisions made during the interview here.
```

---

## Final Output

### Step 1: Write SPEC.json
Write `SPEC.json` with all phases and tasks.

### Step 2: Verify Count
```bash
python3 $SCRIPTS/count_tasks.py SPEC.json
```

### Step 3: Update SPEC.md
Add Status table and Execution Log sections.

### Final Files
1. `SPEC.json` - Execution plan
2. `SPEC.md` - Updated with Status table and Execution Log

Report the task count to the user so they know what to expect.
