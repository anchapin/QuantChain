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
# DROID TOOLS REFERENCE

## DROID-SPECIFIC TOOLS

### File Operations
- **Read**: `Read(file_path, offset=0, limit=2400)`
  - Reads file contents. Use absolute paths
  - For image files, returns actual image content
  - Example: `Read("/path/to/file.py")`

- **Edit**: `Edit(file_path, old_str, new_str, change_all=False)`
  - Edits file by finding and replacing text
  - Must call Read tool first
  - old_str must be unique or use change_all=True
  - Example: `Edit("/path/to/file.py", "old code", "new code")`

- **Create**: `Create(file_path, content)`
  - Creates new file with specified content
  - Use absolute paths
  - Example: `Create("/path/to/new_file.py", "print('hello')")`

- **LS**: `LS(directory_path, ignorePatterns=[])`
  - Lists directory contents with optional filtering
  - Use absolute paths
  - Example: `LS("/path/to/dir")`

### Search Operations
- **Grep**: `Grep(pattern, path=None, glob_pattern=None, output_mode="file_paths", ...)`
  - High-performance file content search using ripgrep
  - Supports regex, file type filtering, context lines
  - Example: `Grep("import numpy", type="py", line_numbers=True)`

- **Glob**: `Glob(patterns, excludePatterns=[], folder=None)`
  - Advanced file path search using glob patterns
  - Example: `Glob(["*.py", "*.js"], excludePatterns=["node_modules/**"])`

### Execution
- **Execute**: `Execute(command, timeout=60, riskLevel="high", riskLevelReason="")`
  - Runs shell commands in isolated environment
  - Risk levels: low (read-only), medium (file changes), high (system-wide changes)
  - Each command runs in new shell - must chain related commands
  - Example: `Execute("python3 --version", riskLevel="low", riskLevelReason="Display version info only")`

### Project Management
- **TodoWrite**: `TodoWrite(todos=[...])`
  - Creates/manages task list for complex work
  - Structure: `{"id": "unique", "content": "task", "status": "pending|in_progress|completed", "priority": "high|medium|low"}`
  - Only ONE task can be "in_progress" at a time

- **ExitSpecMode**: `ExitSpecMode(plan, title=None)`
  - Used when ready to code after planning phase

### Web & API Tools
- **WebSearch**: `WebSearch(query, category=None, includeDomains=[], excludeDomains=[], ...)`
  - Searches web for current information
  - Use for factual information, trends, documentation
  - Example: `WebSearch("Python async patterns", category="research paper")`

- **FetchUrl**: `FetchUrl(url)`
  - Scrapes content from provided URLs
  - Avoid local/private network URLs
  - Example: `FetchUrl("https://docs.example.com/api")`

- **context7_resolve-library-id**: `context7_resolve-library_id(libraryName)`
  - Resolves package names to Context7-compatible library IDs
  - Must call before context7_get-library-docs

- **context7_get-library-docs**: `context7_get-library-docs(context7CompatibleLibraryID, topic=None, tokens=5000)`
  - Fetches up-to-date library documentation

## CLI TOOLS REFERENCE

### Git & GitHub
- **git**: Basic operations
  - `git status` - Check repository state
  - `git diff` - Show unstaged changes
  - `git diff --cached` - Show staged changes
  - `git log --oneline -5` - Recent commits
  - `git rev-parse --abbrev-ref HEAD` - Current branch

- **gh**: GitHub CLI
  - `gh pr create` - Create pull request
  - `gh issue create` - Create issue
  - `gh workflow list` - List workflows
  - `gh run list` - List workflow runs

### Search & Filtering
- **rg** (ripgrep): Fast text search
  - `rg "pattern" --type py` - Search Python files
  - `rg "pattern" -C 3` - Show 3 lines context
  - `rg "pattern" --glob "*.js"` - Glob pattern filtering

- **grep**: Traditional grep (avoid, use rg instead)
- **find**: File search (avoid, use Glob tool instead)
- **ls**: Directory listing (avoid, use LS tool instead)

### Development Tools
- **curl**: HTTP requests
  - `curl -X GET https://api.example.com` - GET request
  - `curl -H "Authorization: Bearer $TOKEN" https://api.example.com` - With headers

- **jq**: JSON processing
  - `echo '{"key": "value"}' | jq .key` - Extract value
  - `curl ... | jq '.items[] | select(.name=="test")'` - Filter response

### Python Tools
- **python3**: Python interpreter
  - `python3 -m pip install package` - Install package
  - `python3 -m pytest tests/` - Run tests
  - `python3 -m venv venv` - Create virtual environment

- **pytest**: Test runner
  - `pytest tests/ -v --cov=quantchain` - Verbose with coverage
  - `pytest tests/ -k "test_specific"` - Run specific tests

- **pip**: Package manager (use python3 -m pip for consistency)

### System Tools
- **which**: Command location
- **uname**: System information
- **pwd**: Current directory
- **cat**: View files (avoid, use Read tool instead)

## BEST PRACTICES

### Tool Selection
- **Prefer Droid tools over shell commands**: Use Read over cat, LS over ls, Grep over grep
- **Use absolute paths**: Avoid relative path issues
- **Chain Execute commands**: Each command runs in new shell environment
- **Quote paths with spaces**: Use double quotes for paths with special characters

### Security & Risk
- **Always provide riskLevelReason** for Execute tool
- **Never expose secrets** in logs or outputs
- **Check for sensitive data** before git commits
- **Avoid destructive commands** like rm -rf without confirmation

### Performance
- **Use parallel tool calls** when exploring codebase
- **Search efficiently** with Grep/Glob tools
- **Read only necessary file portions** with offset/limit parameters
- **Cache results** when possible for repeated operations

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

