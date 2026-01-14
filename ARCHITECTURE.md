# SPEC Executor - Complete Architecture

```mermaid
flowchart TB
    %% ===== INPUT LAYER =====
    subgraph INPUT["📥 INPUT"]
        SPEC_MD["📄 SPEC.md\nHuman-readable requirements"]
    end

    %% ===== PLANNING PHASE =====
    subgraph PLANNING["🔍 PLANNING PHASE"]
        READ_SPEC["read-spec skill\n• Discovery\n• Interview\n• Stack detection"]
        SPEC_JSON["📋 SPEC.json\n• Structured phases\n• Task IDs\n• Verification commands"]
    end

    %% ===== VALIDATION LAYER =====
    subgraph VALIDATION["✅ VALIDATION LAYER"]
        COUNT["🔢 count_tasks.py\nCount: 75 tasks"]
        TODO_CREATE["📝 Claude creates\nTODO (75 items)"]
        HOOK["🔒 validate-todo.sh\nPostToolUse Hook"]
        DECISION{{"Count\nmatches?"}}
        BLOCK["❌ BLOCKED\nRecreate TODO"]
        PROCEED["✓ Proceed"]
    end

    %% ===== EXECUTION ENGINE =====
    subgraph EXECUTION["⚡ EXECUTION ENGINE"]
        direction TB

        subgraph REGULAR["Regular Tasks"]
            TASK_R["Execute task\n• Read files\n• Write code\n• Run commands"]
            VERIFY_R["Verify\n• typecheck\n• lint\n• test"]
            MARK_R["Mark complete\nUpdate TODO"]
        end

        subgraph LOOP["Loop Phase (Dynamic)"]
            INIT_CP["checkpoint.py init\n--total 40"]

            subgraph ITERATION["For each item (1..40)"]
                UPDATE_CP["checkpoint.py update\n--index N --task 2.x"]
                EXPAND["Expand TODO\n[5/40] Task 2.0\n[5/40] Task 2.1\n..."]
                EXEC_LOOP["Execute\nloop tasks"]
                COMPLETE_CP["checkpoint.py complete\n--index N"]
            end

            CLEAR_CP["checkpoint.py clear"]
        end
    end

    %% ===== PERSISTENCE LAYER =====
    subgraph STORAGE["💾 PERSISTENCE"]
        CP_FILE[(".claude/checkpoints/\nspec-name.json\n{\n  current_index: 15\n  current_task: 2.3\n  completed_items: [...]\n}")]
        EXEC_LOG["SPEC.md\nExecution Log\n• Decisions\n• Findings\n• Progress"]
    end

    %% ===== RECOVERY SYSTEM =====
    subgraph RECOVERY["🔄 RECOVERY (after /compact)"]
        CONTEXT_LOST["😵 Context Lost\nClaude forgets everything"]
        READ_CP["Read checkpoint\n→ Position restored"]
        READ_LOG["Read Execution Log\n→ History restored"]
        RECREATE["Recreate TODO\n• Mark completed\n• Resume from position"]
    end

    %% ===== OUTPUT =====
    subgraph OUTPUT["📤 OUTPUT"]
        COMPLETE["🎉 SPEC COMPLETE\n<promise>FEATURE_DONE</promise>"]
    end

    %% ===== CONNECTIONS =====

    %% Input to Planning
    SPEC_MD --> READ_SPEC
    READ_SPEC --> SPEC_JSON

    %% Planning to Validation
    SPEC_JSON --> COUNT
    COUNT --> TODO_CREATE
    TODO_CREATE --> HOOK
    HOOK --> DECISION
    DECISION -->|No| BLOCK
    BLOCK --> TODO_CREATE
    DECISION -->|Yes| PROCEED

    %% Validation to Execution
    PROCEED --> TASK_R
    TASK_R --> VERIFY_R
    VERIFY_R --> MARK_R
    MARK_R -->|"Has loop?"| INIT_CP
    MARK_R -->|"No loop"| COMPLETE

    %% Loop execution
    INIT_CP --> UPDATE_CP
    UPDATE_CP --> EXPAND
    EXPAND --> EXEC_LOOP
    EXEC_LOOP --> COMPLETE_CP
    COMPLETE_CP -->|"More items?"| UPDATE_CP
    COMPLETE_CP -->|"All done"| CLEAR_CP
    CLEAR_CP --> COMPLETE

    %% Persistence connections
    UPDATE_CP -.->|"Save"| CP_FILE
    COMPLETE_CP -.->|"Save"| CP_FILE
    MARK_R -.->|"Log"| EXEC_LOG

    %% Recovery connections
    CONTEXT_LOST -.->|"/compact"| READ_CP
    CP_FILE -.-> READ_CP
    EXEC_LOG -.-> READ_LOG
    READ_CP --> RECREATE
    READ_LOG --> RECREATE
    RECREATE -->|"Continue"| UPDATE_CP

    %% Styling
    style SPEC_MD fill:#e1f5fe
    style SPEC_JSON fill:#e8f5e9
    style HOOK fill:#fff3e0
    style BLOCK fill:#ffcdd2
    style PROCEED fill:#c8e6c9
    style CP_FILE fill:#f3e5f5
    style COMPLETE fill:#c8e6c9
    style CONTEXT_LOST fill:#ffcdd2
    style RECREATE fill:#fff9c4

    %% Subgraph styling
    style INPUT fill:#e3f2fd,stroke:#1976d2
    style PLANNING fill:#e8f5e9,stroke:#388e3c
    style VALIDATION fill:#fff3e0,stroke:#f57c00
    style EXECUTION fill:#fce4ec,stroke:#c2185b
    style STORAGE fill:#f3e5f5,stroke:#7b1fa2
    style RECOVERY fill:#fff8e1,stroke:#ffa000
    style OUTPUT fill:#e8f5e9,stroke:#388e3c
```

## Legend

| Symbol | Meaning |
|--------|---------|
| 📄 | Human-readable file |
| 📋 | Structured JSON |
| 🔢 | Script |
| 📝 | TODO list |
| 🔒 | Hook (automatic validation) |
| ⚡ | Execution |
| 💾 | Persistence |
| 🔄 | Recovery |
| ✓ | Success |
| ❌ | Blocked |

## Key Flows

### 1. Normal Execution (No Loops)
```
SPEC.md → read-spec → SPEC.json → count → TODO → hook ✓ → execute → complete
```

### 2. Loop Execution
```
... → enter loop → init checkpoint → [update → expand → execute → complete] × N → clear → ...
```

### 3. Recovery After /compact
```
context lost → read checkpoint → read log → recreate TODO → resume from saved position
```
