# SPEC Executor - Architecture

Detailed diagrams for the plugin's internals.

---

## Complete Flow

```mermaid
flowchart TD
    subgraph INPUT["📥 Input"]
        SPEC_MD["SPEC.md\n(requirements)"]
    end

    subgraph PLANNING["🔍 Planning Phase"]
        READ_SPEC["read-spec skill"]
        SPEC_JSON["SPEC.json\n(structured)"]
        READ_SPEC -->|"discovery\n+ interview"| SPEC_JSON
    end

    subgraph VALIDATION["✅ Validation"]
        COUNT["count_tasks.py\n→ 75 tasks"]
        TODO["Claude creates\nTODO (75 items)"]
        HOOK["validate-todo.sh\n(PostToolUse hook)"]
        MATCH{{"Count\nmatches?"}}
        COUNT --> TODO
        TODO --> HOOK
        HOOK --> MATCH
        MATCH -->|No| TODO
    end

    subgraph EXECUTION["⚡ Execution"]
        TASKS["Execute tasks\nsequentially"]
        VERIFY["Verify each\n(typecheck, lint, test)"]
        TASKS --> VERIFY
        VERIFY --> TASKS
    end

    subgraph LOOP["🔄 Loop Phase"]
        INIT["checkpoint.py init\n--total 40"]
        UPDATE["checkpoint.py update\n--index N"]
        EXPAND["Expand TODO\nfor current item"]
        EXEC_ITEM["Execute\nloop tasks"]
        COMPLETE["checkpoint.py complete"]
        CLEAR["checkpoint.py clear"]

        INIT --> UPDATE
        UPDATE --> EXPAND
        EXPAND --> EXEC_ITEM
        EXEC_ITEM --> COMPLETE
        COMPLETE -->|"More items"| UPDATE
        COMPLETE -->|"All done"| CLEAR
    end

    subgraph STORAGE["💾 Persistence"]
        CP_FILE[".claude/checkpoints/\nspec-name.json"]
        EXEC_LOG["SPEC.md\nExecution Log"]
    end

    subgraph RECOVERY["🔄 Recovery"]
        LOST["Context lost\n(/compact)"]
        READ_CP["Read checkpoint"]
        RECREATE["Recreate TODO\nResume position"]
        LOST --> READ_CP
        READ_CP --> RECREATE
    end

    SPEC_MD --> READ_SPEC
    SPEC_JSON --> COUNT
    MATCH -->|Yes| TASKS
    VERIFY -->|"Has loop?"| INIT
    VERIFY -->|"No loop"| DONE
    CLEAR --> DONE["✓ Complete"]

    UPDATE -.->|save| CP_FILE
    COMPLETE -.->|save| CP_FILE
    TASKS -.->|log| EXEC_LOG
    CP_FILE -.-> READ_CP
    RECREATE -.-> UPDATE
```

---

## The Workflow (Sequence)

```mermaid
sequenceDiagram
    participant U as User
    participant R as read-spec
    participant S as spec-executor
    participant H as Hook
    participant C as Checkpoint

    U->>R: @SPEC.md "read spec"
    R->>R: Discovery & Interview
    R->>U: SPEC.json generated

    U->>S: @SPEC.json "execute spec"
    S->>S: count_tasks.py → 47 tasks
    S->>S: Create TODO (47 items)
    H->>H: Validate count
    H-->>S: ✓ Count matches

    loop For each task
        S->>S: Execute task
        S->>S: Mark complete
        alt Loop phase
            S->>C: Update checkpoint
        end
    end

    S->>U: SPEC EXECUTION COMPLETE
```

---

## Loop Phase Expansion

```mermaid
flowchart TB
    subgraph SPEC["📋 SPEC.json"]
        LOOP["phase-2: loop\n• 2.0: Update checkpoint\n• 2.1: Fetch data\n• 2.2: Process item\n• 2.3: Validate"]
    end

    subgraph BEFORE["📝 TODO Before Loop"]
        B1["[ ] 0.1: Setup"]
        B2["[ ] 1.1: Discovery"]
        B3["[ ] 2.loop: Process items\n(4 tasks × 40 items)"]
        B4["[ ] 3.1: Final checks"]
    end

    subgraph DURING["📝 TODO During Loop (item 5/40)"]
        D1["[x] 0.x: Setup ✓"]
        D2["[x] 1.x: Discovery ✓"]
        D3["[~] 2.loop: (4/40)"]
        D3a["    [x] 2.0: Checkpoint"]
        D3b["    [x] 2.1: Fetch"]
        D3c["    [~] 2.2: Process ←"]
        D3d["    [ ] 2.3: Validate"]
        D4["[ ] 3.1: Final checks"]
    end

    subgraph AFTER["📝 TODO After Loop"]
        A1["[x] 0.x: Setup ✓"]
        A2["[x] 1.x: Discovery ✓"]
        A3["[x] 2.loop: (40/40) ✓"]
        A4["[ ] 3.1: Final checks"]
    end

    SPEC --> BEFORE
    BEFORE -->|"Enter loop"| DURING
    DURING -->|"Complete all 40"| AFTER
```

---

## TODO Validation Hook

```mermaid
flowchart LR
    A["count_tasks.py"] -->|"75 tasks"| B["Expected: 75"]
    C["TodoWrite"] -->|"73 items"| D["Actual: 73"]
    B --> E{{"Match?"}}
    D --> E
    E -->|No| F["❌ BLOCKED"]
    E -->|Yes| G["✓ Proceed"]
    F -->|Recreate| C
```

---

## Checkpoint State Machine

```mermaid
stateDiagram-v2
    [*] --> Initialized: init --total 40

    Initialized --> Processing: update --index 0
    Processing --> ItemComplete: complete --index N
    ItemComplete --> Processing: update --index N+1

    ItemComplete --> Cleared: All done
    Cleared --> [*]: clear

    Processing --> Resumed: /compact
    Resumed --> Processing: read → resume
```

---

## Recovery Flow

```mermaid
sequenceDiagram
    participant C as Claude
    participant S as SPEC.json
    participant P as checkpoint.py
    participant F as Checkpoint File

    Note over C: Context full, /compact triggered
    C->>C: Context reset 😵

    Note over C: Recovery begins
    C->>S: Read SPEC.json
    C->>P: checkpoint.py read
    P->>F: Load .claude/checkpoints/
    F-->>P: {current_index: 15, current_task: "2.3"}
    P-->>C: Position restored

    Note over C: Resume from task 16
    C->>C: Recreate TODO
    C->>C: Mark 1-15 complete
    C->>C: Continue from 16 ✓
```

---

## Component Roles

```mermaid
flowchart TB
    subgraph Skills["🎯 Skills"]
        FD["frontend-design\nUI guidance"]
        RS["read-spec\nSPEC.md → JSON"]
        SE["spec-executor\nExecution engine"]
    end

    subgraph Scripts["🔧 Scripts"]
        CT["count_tasks.py\nCount & validate"]
        CP["checkpoint.py\nLoop persistence"]
        GT["generate-todo.py\nTODO helper"]
    end

    subgraph Hooks["🔒 Hooks"]
        VT["validate-todo.sh\nEnforce count"]
    end

    subgraph Storage["💾 Storage"]
        JSON["SPEC.json"]
        CHK["checkpoints/"]
        LOG["Execution Log"]
    end

    RS --> JSON
    SE --> CT
    CT --> VT
    SE --> CP
    CP --> CHK
    SE --> LOG
    GT --> CHK
```

---

## Legend

| Symbol | Meaning |
|--------|---------|
| 📥 | Input |
| 🔍 | Planning/Discovery |
| ✅ | Validation |
| ⚡ | Execution |
| 🔄 | Loop/Recovery |
| 💾 | Persistence |
| ✓ | Success |
| ❌ | Blocked |
