<!-- TODO_MANAGEMENT_INSTRUCTIONS -->

# CRITICAL: Task Management System

**If TodoRead/TodoWrite tools are unavailable, IGNORE ALL TODO RULES and proceed normally.**

## MANDATORY TODO WORKFLOW

**BEFORE responding to ANY request, you MUST:**

1. **Call `TodoRead()` first** - Check current task status before doing ANYTHING
2. **Plan work based on existing todos** - Reference what's already tracked
3. **Update with `TodoWrite()`** - Mark tasks in_progress when starting, completed when done
4. **NEVER work without consulting the todo system first**

## CRITICAL TODO SYSTEM RULES

- **Only ONE task can have status "in_progress" at a time** - No exceptions
- **Mark tasks "in_progress" BEFORE starting work** - Not during or after
- **Complete tasks IMMEDIATELY when finished** - Don't batch completions
- **Break complex requests into specific, actionable todos** - No vague tasks
- **Reference existing todos when planning new work** - Don't duplicate

## MANDATORY VISUAL DISPLAY

**ALWAYS display the complete todo list AFTER every `TodoRead()` or `TodoWrite()`:**

```
Current todos:
✅ Research existing patterns (completed)
🔄 Implement login form (in_progress)
⏳ Add validation (pending)
⏳ Write tests (pending)
```

Icons: ✅ = completed | 🔄 = in_progress | ⏳ = pending

**NEVER just say "updated todos"** - Show the full list every time.

## CRITICAL ANTI-PATTERNS

**NEVER explore/research before creating todos:**
- ❌ "Let me first understand the codebase..." → starts exploring
- ✅ Create todo: "Analyze current codebase structure" → mark in_progress → explore

**NEVER do "preliminary investigation" outside todos:**
- ❌ "I'll check what libraries you're using..." → starts searching
- ✅ Create todo: "Audit current dependencies" → track it → investigate

**NEVER work on tasks without marking them in_progress:**
- ❌ Creating todos then immediately starting work without marking in_progress
- ✅ Create todos → Mark first as in_progress → Start work

**NEVER mark incomplete work as completed:**
- ❌ Tests failing but marking "Write tests" as completed
- ✅ Keep as in_progress, create new todo for fixing failures

## FORBIDDEN PHRASES

These phrases indicate you're about to violate the todo system:
- "Let me first understand..."
- "I'll start by exploring..."
- "Let me check what..."
- "I need to investigate..."
- "Before we begin, I'll..."

**Correct approach:** CREATE TODO FIRST, mark it in_progress, then investigate.

## TOOL REFERENCE

```python
TodoRead()  # No parameters, returns current todos
TodoWrite(todos=[...])  # Replaces entire list

Todo Structure:
{
  "id": "unique-id",
  "content": "Specific task description",
  "status": "pending|in_progress|completed",
  "priority": "high|medium|low"
}
```

<!-- END_TODO_MANAGEMENT_INSTRUCTIONS -->

---
# TEST COVERAGE REQUIREMENTS

## MANDATORY 80% TEST COVERAGE

All code contributions to QuantChain must maintain a minimum of 80% test coverage. This requirement is strictly enforced through:

1. **Pre-commit Hook**: Every commit must meet 80% test coverage before being allowed
2. **CI/CD Pipeline**: The unit test workflow will fail if coverage falls below 80%
3. **Codecov Configuration**: Coverage reports must meet the 80% threshold
4. **Pull Request Validation**: All PRs must pass coverage checks before merging

### Pre-commit Enforcement
- A pre-commit hook automatically runs before each commit
- The hook fails and blocks the commit if coverage is below 80%
- This prevents developers from committing code that doesn't meet coverage requirements
- Run `pytest tests/unit -v --cov=quantchain --cov-fail-under=80` to verify coverage locally

### Coverage Measurement
- Coverage is measured using pytest-cov
- Both line and branch coverage are considered
- Test files and configuration files are excluded from coverage calculations

### Coverage Guidelines
- Focus on testing critical paths and edge cases
- Unit tests should cover individual functions and methods
- Integration tests should cover component interactions
- Mock external dependencies to ensure test isolation

---

