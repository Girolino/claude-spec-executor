# SPEC Execution Examples

Real examples of SPEC.json structure and execution traces.

---

## Example 1: Simple Feature (No Loop)

### Feature: Like Button

A simple feature with 18 tasks across 4 phases.

### SPEC.json Outline

```json
{
  "feature": "Like Button",
  "completion_promise": "LIKE_BUTTON_COMPLETE",
  "phases": [
    {
      "id": "phase-0",
      "name": "Pre-Flight",
      "tasks": [
        { "id": "0.0", "task": "Create decisions.md" },
        { "id": "0.1", "task": "Verify typecheck passes" },
        { "id": "0.2", "task": "Verify build passes" }
      ]
    },
    {
      "id": "phase-1",
      "name": "Database",
      "tasks": [
        { "id": "1.0", "task": "Update decisions.md for Phase 1" },
        { "id": "1.1", "task": "Add likes table to schema" },
        { "id": "1.2", "task": "Run db sync" },
        { "id": "1.3", "task": "Create toggleLike mutation" },
        { "id": "1.4", "task": "Create getLikeCount query" }
      ]
    },
    {
      "id": "phase-2",
      "name": "Frontend",
      "tasks": [
        { "id": "2.0", "task": "Update decisions.md for Phase 2" },
        { "id": "2.1", "task": "Run /frontend-design for LikeButton" },
        { "id": "2.2", "task": "Create LikeButton component" },
        { "id": "2.3", "task": "Run /visual-qa for LikeButton" },
        { "id": "2.4", "task": "Integrate LikeButton in PostCard" }
      ]
    },
    {
      "id": "phase-3",
      "name": "Verification",
      "tasks": [
        { "id": "3.0", "task": "Update decisions.md for Phase 3" },
        { "id": "3.1", "task": "Test like/unlike flow" },
        { "id": "3.2", "task": "Verify optimistic update works" },
        { "id": "3.3", "task": "Final typecheck and build" }
      ]
    }
  ]
}
```

### Expected TODO (18 items)

```
[ ] 0.0: Create decisions.md
[ ] 0.1: Verify typecheck passes
[ ] 0.2: Verify build passes
[ ] 1.0: Update decisions.md for Phase 1
[ ] 1.1: Add likes table to schema
[ ] 1.2: Run db sync
[ ] 1.3: Create toggleLike mutation
[ ] 1.4: Create getLikeCount query
[ ] 2.0: Update decisions.md for Phase 2
[ ] 2.1: Run /frontend-design for LikeButton
[ ] 2.2: Create LikeButton component
[ ] 2.3: Run /visual-qa for LikeButton
[ ] 2.4: Integrate LikeButton in PostCard
[ ] 3.0: Update decisions.md for Phase 3
[ ] 3.1: Test like/unlike flow
[ ] 3.2: Verify optimistic update works
[ ] 3.3: Final typecheck and build
```

### Execution Trace

```
[x] 0.0: Create decisions.md
[x] 0.1: Verify typecheck passes
[x] 0.2: Verify build passes
[x] 1.0: Update decisions.md for Phase 1
[x] 1.1: Add likes table to schema
[x] 1.2: Run db sync
[~] 1.3: Create toggleLike mutation    <- current
[ ] 1.4: Create getLikeCount query
...
```

---

## Example 2: Loop Feature (With Checkpoints)

### Feature: Profile Migration

Migrate 40 user profiles from legacy system. Uses checkpoints for recovery.

### SPEC.json Outline

```json
{
  "feature": "Profile Migration",
  "completion_promise": "MIGRATION_COMPLETE",
  "phases": [
    {
      "id": "phase-0",
      "name": "Pre-Flight",
      "tasks": [
        { "id": "0.0", "task": "Create decisions.md" },
        { "id": "0.1", "task": "Verify database connection" }
      ]
    },
    {
      "id": "phase-1",
      "name": "Discovery",
      "tasks": [
        { "id": "1.0", "task": "Update decisions.md" },
        { "id": "1.1", "task": "Fetch all profiles from legacy API" },
        { "id": "1.2", "task": "Initialize checkpoint with total count" },
        { "id": "1.3", "task": "Check existing checkpoint (for resumption)" }
      ]
    },
    {
      "id": "phase-2",
      "name": "Process Profiles",
      "loop": {
        "over": "profiles from phase-1",
        "checkpoint_spec": "profile-migration",
        "tasks": [
          { "id": "2.0", "task": "Update checkpoint: starting profile" },
          { "id": "2.1", "task": "Fetch profile details" },
          { "id": "2.2", "task": "Transform to new schema" },
          { "id": "2.3", "task": "Insert into new database" },
          { "id": "2.4", "task": "Verify insertion" },
          { "id": "2.5", "task": "Mark profile complete in checkpoint" }
        ]
      }
    },
    {
      "id": "phase-3",
      "name": "Verification",
      "tasks": [
        { "id": "3.0", "task": "Update decisions.md" },
        { "id": "3.1", "task": "Count migrated profiles" },
        { "id": "3.2", "task": "Spot check 5 random profiles" },
        { "id": "3.3", "task": "Clear checkpoint" }
      ]
    }
  ]
}
```

### Expected TODO (15 template items)

```
[ ] 0.0: Create decisions.md
[ ] 0.1: Verify database connection
[ ] 1.0: Update decisions.md
[ ] 1.1: Fetch all profiles from legacy API
[ ] 1.2: Initialize checkpoint with total count
[ ] 1.3: Check existing checkpoint
[ ] 2.0: Update checkpoint: starting profile
[ ] 2.1: Fetch profile details
[ ] 2.2: Transform to new schema
[ ] 2.3: Insert into new database
[ ] 2.4: Verify insertion
[ ] 2.5: Mark profile complete in checkpoint
[ ] 3.0: Update decisions.md
[ ] 3.1: Count migrated profiles
[ ] 3.2: Spot check 5 random profiles
[ ] 3.3: Clear checkpoint
```

**Note:** Loop tasks (2.0-2.5) appear ONCE but execute 40 times.

### TODO During Loop (Profile 12/40)

```
[x] 0.x: Pre-Flight completed
[x] 1.x: Discovery completed
[~] 2.loop: Process Profiles (11/40)
  [x] 2.0: [12/40] Update checkpoint
  [x] 2.1: [12/40] Fetch profile details
  [~] 2.2: [12/40] Transform to new schema    <- current
  [ ] 2.3: [12/40] Insert into new database
  [ ] 2.4: [12/40] Verify insertion
  [ ] 2.5: [12/40] Mark profile complete
[ ] 3.1: Count migrated profiles
[ ] 3.2: Spot check 5 random profiles
[ ] 3.3: Clear checkpoint
```

### Checkpoint State

```json
{
  "spec_name": "profile-migration",
  "status": "in_progress",
  "total_items": 40,
  "current_index": 11,
  "current_item_id": "user-012",
  "current_item_name": "John Doe",
  "current_task": "2.2",
  "completed_items": [
    "user-001", "user-002", "user-003", "user-004", "user-005",
    "user-006", "user-007", "user-008", "user-009", "user-010",
    "user-011"
  ]
}
```

### Recovery After /compact

```bash
# 1. Read checkpoint
python3 $SCRIPTS/checkpoint.py read profile-migration
# Output: current_index=11, current_task=2.2, completed=11/40

# 2. Generate TODO
python3 $SCRIPTS/generate-todo.py --spec SPEC.json --checkpoint profile-migration

# 3. Resume from profile 12 (index 11), task 2.2
```

---

## Example 3: UI-Heavy Feature

### Feature: User Settings Page

Multiple UI components requiring design/visual validation.

### Task Sequence Pattern

```
[ ] 2.1: Run /frontend-design for SettingsLayout
[ ] 2.2: Create SettingsLayout component
[ ] 2.3: Run /visual-qa for SettingsLayout
[ ] 2.4: Run /frontend-design for ProfileSection
[ ] 2.5: Create ProfileSection component
[ ] 2.6: Run /visual-qa for ProfileSection
[ ] 2.7: Run /frontend-design for NotificationSettings
[ ] 2.8: Create NotificationSettings component
[ ] 2.9: Run /visual-qa for NotificationSettings
```

**Pattern:** For each UI component:
1. `/frontend-design` - Get design guidance
2. Create component - Implement
3. `/visual-qa` - Verify visually

---

## SPEC.md Execution Log Example

```markdown
## Execution Log

### Progress Summary
- **Total tasks**: 18
- **Completed**: 7
- **Current phase**: Phase 1 (Database)

### Session Log
| Timestamp | Phase | Task | Notes |
|-----------|-------|------|-------|
| 10:30 | Phase 0 | 0.0-0.2 | Pre-flight complete, all checks pass |
| 10:45 | Phase 1 | 1.0-1.2 | Schema updated, db synced |
| 11:00 | Phase 1 | 1.3 | Working on toggleLike mutation |
```

---

## decisions.md Example

```markdown
# Execution Context: Like Button

## Objective
Add like/unlike functionality to posts. Users can like posts, see like count, and toggle their like.

## Key Constraints
- Must use optimistic updates for instant feedback
- Must work with existing PostCard component
- No changes to post schema, only new likes table

## Success Criteria
- Like button shows current state (liked/not liked)
- Like count updates immediately on click
- Persists to database correctly

---

## Phase 0 Decisions
- Verified environment: typecheck and build pass

## Phase 1 Decisions
- Using separate `likes` table with userId + postId composite key
- toggleLike mutation handles both like and unlike

## Current State
Phase: 1
Last completed: 1.2
Next: 1.3
```
