# AI Code Review System — File Documentation (Part 2: Core Engine)

---

# File 1: `ai-code-review.yml`

## 1. Purpose
The GitHub Actions workflow definition. It tells GitHub **when** to run the review bot and **how** to set up the environment. Without this file, GitHub would never trigger any automated review.

## 2. Location
**Path:** `.github/workflows/ai-code-review.yml`
GitHub mandates this exact directory for workflow files. Any YAML in `.github/workflows/` is auto-discovered.

## 3. Dependencies
- **Uses:** `actions/checkout@v4`, `actions/setup-python@v5`
- **Calls:** `python src/code_review/review.py`
- **Secrets:** `GEMINI_API_KEY` (manual), `GITHUB_TOKEN` (auto)

## 4. Code Walkthrough

| Line(s) | Code | What & Why |
|---------|------|------------|
| 1 | `name: AI Code Review` | Display name in Actions UI |
| 3-7 | `on: push/pull_request` | Triggers: any branch push + PR open/sync/reopen |
| 9-11 | `permissions:` | Grants `contents: write` and `pull-requests: write` to `GITHUB_TOKEN` |
| 15 | `runs-on: ubuntu-latest` | Free Linux VM for execution |
| 18-20 | `actions/checkout@v4` + `fetch-depth: 0` | Full clone (not shallow) — needed for git diff across commits |
| 22-25 | `actions/setup-python@v5` | Installs Python 3.11 |
| 27-28 | `pip install -r requirements.txt` | Installs `requests` library |
| 30-40 | `Run AI Code Review` | Executes `review.py` with 8 environment variables injected |

**If `fetch-depth: 0` were removed:** Default shallow clone (depth=1) would break `git diff` between non-adjacent commits.

**If `permissions` were removed:** `GITHUB_TOKEN` would have read-only access and posting comments would fail with 403.

## 5. Data Flow
```
GitHub Event → Workflow YAML → Runner VM → Python Script
```

## 6. Inputs
- GitHub event payload (push or pull_request)
- Repository secrets (`GEMINI_API_KEY`)
- GitHub context variables (`github.repository`, `github.sha`, etc.)

## 7. Outputs
- A configured runner environment where `review.py` can execute
- Environment variables available to the Python process

## 8. Execution Flow
Runs automatically when GitHub detects a matching event. It is the **first thing** that executes.

## 9. Summary
- Defines when the bot runs (push + PR events)
- Sets up Python 3.11 and installs dependencies
- Injects secrets and context as environment variables
- Calls `review.py` as the final step
- `fetch-depth: 0` is critical for full git history

---

# File 2: `review.py`

## 1. Purpose
The **main orchestrator** — the entry point of the entire review system. It coordinates all other modules: fetches changed files, parses diffs, calls Gemini, validates results, and posts comments. Without this file, nothing runs.

## 2. Location
**Path:** `src/code_review/review.py`  
Lives in `code_review/` because it's the core review engine, separate from the React demo app.

## 3. Dependencies

| Imports | From |
|---------|------|
| `os`, `sys` | Python stdlib |
| `GitHubClient` | `github_client.py` |
| `parse_diff` | `diff_parser.py` |
| `GeminiService` | `gemini_service.py` |
| `get_diff_between_refs` | `repository_service.py` |

**Called by:** The workflow YAML (`python src/code_review/review.py`)

## 4. Code Walkthrough

### Lines 1-7: Imports
```python
import os, sys
from github_client import GitHubClient
from diff_parser import parse_diff
from gemini_service import GeminiService
from repository_service import get_diff_between_refs
```
- `os` — reads environment variables
- `sys` — `sys.exit(1)` for error exits, `sys.path` for import resolution
- The four local imports bring in each module's functionality

### Lines 10-18: `main()` — Environment Variable Reading
```python
gemini_api_key = os.environ.get("GEMINI_API_KEY")
github_token = os.environ.get("GITHUB_TOKEN")
# ... etc
```
All configuration comes from environment variables (set by the workflow YAML). No hardcoded values.

**If removed:** The script would have no API keys or context.

### Lines 20-23: Validation
```python
if not all([gemini_api_key, github_token, repo_full_name]):
    print("Error: Missing required environment variables.")
    sys.exit(1)
```
Fails fast if critical variables are missing. `sys.exit(1)` makes the Actions step show ❌.

### Lines 25-26: Client Initialization
```python
github = GitHubClient(github_token, repo_full_name)
gemini = GeminiService(gemini_api_key)
```
Creates the two service objects that handle external API communication.

### Lines 28-33: Event Routing
```python
is_pr = event_name == "pull_request" and pr_number
if is_pr:
    run_pr_review(github, gemini, pr_number)
else:
    run_push_review(github, gemini, base_ref, head_ref, commit_sha)
```
The critical decision: PR events use the Pull Request API; push events use the Commit API.

### Lines 36-96: `run_pr_review()`

**Step-by-step:**
1. **Check for existing bot comments** (lines 40-43) — deduplication
2. **Fetch changed files** via `github.get_pr_files()` (line 46)
3. **Parse diffs** via `parse_diff()` (line 52)
4. **Build diff text** for Gemini (line 57)
5. **Call Gemini** via `gemini.review_code()` (line 63)
6. **Build valid lines map** — only `+` lines are valid targets (line 71)
7. **Snap each comment** to nearest valid line ±3 (lines 73-85)
8. **Post inline comments** via `github.post_review()` (line 89)
9. **Post summary** via `github.post_summary_comment()` (line 95)

### Lines 99-156: `run_push_review()`
Same logic as `run_pr_review()` but:
- Uses `github.get_commit_files(commit_sha)` instead of `get_pr_files()`
- Posts via `github.post_commit_comments()` and `github.post_commit_comment()`
- Skips initial commits (`0000...0000` base ref)

### Lines 159-169: `build_diff_text()`
Formats diff entries into markdown for Gemini:
```
## File: src/App.tsx
```diff
L10: +new code here
L11: +more code
```
```

### Lines 172-183: `build_valid_lines_map()`
Creates: `{filepath → {line_number → diff_position}}`  
Only added lines (`+`) are included — you can't comment on unchanged or deleted lines.

### Lines 186-198: `snap_to_valid_line()`
If Gemini says "comment on line 42" but line 42 isn't in the diff, try lines 43, 41, 44, 40, 45, 39. Returns the first match within ±3 lines. This handles AI line-number inaccuracy gracefully.

### Lines 201-220: `format_summary()`
Builds the summary comment markdown:
```
## 🤖 AI Code Review Summary
**Files reviewed:** 3
**Inline comments posted:** 5
### Files Changed:
- `src/App.tsx`
### What Changed:
[AI-generated summary]
---
*This review was generated automatically by AI Code Review (Gemini).*
```

### Lines 223-226: `__main__` block
```python
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
```
Adds the `code_review/` directory to Python's import path so sibling modules can be found.

## 5. Data Flow
```
Env Vars → main() → [PR or Push decision]
                          │
            GitHub API ← get files
                          │
            diff_parser ← parse
                          │
            Gemini API ← review
                          │
            Validation ← snap lines
                          │
            GitHub API ← post comments
```

## 6. Inputs
| Input | Type | Source |
|-------|------|--------|
| `GEMINI_API_KEY` | string | Repository secret |
| `GITHUB_TOKEN` | string | Auto-generated |
| `REPO_FULL_NAME` | string | `github.repository` |
| `EVENT_NAME` | string | `"push"` or `"pull_request"` |
| `PR_NUMBER` | string | PR number or empty |
| `BASE_REF` | string | Base commit SHA |
| `HEAD_REF` | string | Head commit SHA |
| `COMMIT_SHA` | string | Current commit SHA |

## 7. Outputs
- Inline review comments on PR/commit
- Summary comment on PR/commit
- Console logs (visible in Actions)
- Exit code 0 (success) or 1 (missing vars)

## 8. Error Handling
- Missing env vars → `sys.exit(1)`
- No changed files → early return with log message
- No reviewable changes → early return
- Gemini returns nothing → early return
- Invalid line numbers → skipped with log message

## 9. Real Example

**Git diff contains an unused import:**
```diff
+import os   # unused
+def hello():
+    print("hi")
```

**Gemini returns:**
```json
{
  "summary": "Added hello function with unused os import",
  "comments": [{"path": "app.py", "line": 1, "body": "[Issue] Unused import 'os'"}]
}
```

**Validation:** Line 1 is in valid_lines → comment posted at correct diff position.

## 10. Interview Questions
1. Why does `snap_to_valid_line` use ±3 tolerance?
2. Why are only `+` lines valid targets for comments?
3. What happens if Gemini returns a line number outside the diff?
4. Why is event routing (PR vs Push) needed?
5. How does the bot prevent duplicate summary comments?

## 11. Possible Improvements
- **Retry logic** for Gemini API failures (currently no retries)
- **Configurable snap range** (currently hardcoded ±3)
- **Parallel file review** for large PRs (currently sequential)
- **Severity filtering** (only post critical issues)
- **Rate limiting** awareness for GitHub API

## 12. Summary
- Entry point and orchestrator for the entire system
- Routes between PR review and Push review modes
- Validates Gemini's line numbers against the actual diff
- Snap-to-valid-line handles AI inaccuracy (±3 tolerance)
- Posts both inline comments and a summary comment
- Fails fast on missing configuration

---

# File 3: `diff_parser.py`

## 1. Purpose
Parses unified diff (patch) output from the GitHub API into structured data. Converts raw text like `@@ -10,6 +10,8 @@` and `+new code` into Python dicts with line numbers, diff positions, and annotated lines.

## 2. Location
**Path:** `src/code_review/diff_parser.py`  
In `code_review/` as a supporting module for the review engine.

## 3. Dependencies
- **Imports:** `re` (Python stdlib — regular expressions)
- **Used by:** `review.py` (imports `parse_diff`)
- **No external libraries**

## 4. Code Walkthrough

### Lines 1: `import re`
Python's regex module. Used to match hunk headers like `@@ -10,6 +10,8 @@`.

### Lines 4-28: `parse_diff(changed_files)`
The main function. Iterates over files from the GitHub API response.

```python
for file_data in changed_files:
    filename = file_data.get("filename", "")
    patch = file_data.get("patch", "")
    status = file_data.get("status", "")
```
Each `file_data` comes from GitHub's `GET /pulls/{n}/files` API.

**Filtering:**
- `status == "removed"` → skip deleted files (nothing to review)
- `not patch` → skip binary files (no textual diff)
- `should_skip_file(filename)` → skip lock files, images, fonts

### Lines 31-76: `parse_patch(patch)`
The core diff parsing algorithm:

```python
position = 0  # 1-based position in diff (for GitHub API)
```

**For each line in the patch:**
1. **Hunk header match:** `re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)`
   - Captures the new-file start line number
   - Starts a new chunk
2. **Added line** (`+` prefix, not `+++`):
   - Records in `added_lines` list
   - Maps `line_number → diff_position` in `changed_lines`
   - Creates annotated line: `L42: +some code`
   - Increments `current_new_line`
3. **Deleted line** (`-` prefix, not `---`):
   - Annotated as `     : -old code` (no line number — deleted lines don't exist in new file)
   - Does NOT increment `current_new_line`
4. **Context line** (space prefix):
   - Maps to position (context lines are valid comment targets too)
   - Increments `current_new_line`

**Critical concept:** `position` increments for EVERY line in the patch (including hunk headers). This is the value GitHub's API needs for placing inline comments.

### Lines 79-98: `should_skip_file(filename)`
Two filter lists:
- `skip_extensions`: `.lock`, `.min.js`, `.png`, `.woff2`, etc.
- `skip_files`: `package-lock.json`, `yarn.lock`, `Cargo.lock`, etc.

**Why:** These files are auto-generated or binary. Reviewing them wastes API tokens and produces noise.

### Lines 101-105: `_splitext(filename)`
Custom file extension extraction using `rfind(".")`. More predictable than `os.path.splitext` for filenames like `.env` or `file.min.js`.

## 5. Data Flow
```
GitHub API Response          parse_diff()         Structured Entries
[{filename, patch,    →    parse_patch()    →    [{path, status,
  status}, ...]            should_skip()           chunks: [{
                                                     added_lines,
                                                     changed_lines,
                                                     annotated_lines
                                                   }]
                                                 }]
```

## 6. Inputs
List of dicts from GitHub API, each containing:
- `filename`: relative path (`src/App.tsx`)
- `patch`: unified diff text
- `status`: `"added"`, `"modified"`, `"removed"`, `"renamed"`

## 7. Outputs
List of diff entries:
```python
{
  "path": "src/App.tsx",
  "status": "modified",
  "chunks": [{
    "lines": ["raw diff lines..."],
    "added_lines": [10, 11, 12],           # line numbers of + lines
    "changed_lines": {10: 3, 11: 4, 12: 5}, # line_number → diff_position
    "annotated_lines": ["L10: +code", ...]  # for Gemini
  }]
}
```

## 8. Real Example

**Input patch:**
```
@@ -5,3 +5,5 @@ function hello() {
   console.log("hi")
+  console.log("debug")
+  return true
 }
```

**Output:**
```python
{
  "added_lines": [6, 7],
  "changed_lines": {5: 2, 6: 3, 7: 4, 8: 5},
  "annotated_lines": [
    "L5:  console.log(\"hi\")",
    "L6: +  console.log(\"debug\")",
    "L7: +  return true",
    "L8:  }"
  ]
}
```

## 9. Interview Questions
1. Why does `position` start at 0 and increment before use (1-based)?
2. Why are deleted lines not assigned a line number?
3. What's the difference between `added_lines` and `changed_lines`?
4. Why skip `.min.js` files?
5. Why use `rfind(".")` instead of `os.path.splitext`?

## 10. Summary
- Parses unified diff format into structured Python dicts
- Tracks both file line numbers AND diff positions
- Annotates lines with `L<number>:` prefix for Gemini
- Filters out binary files, lock files, images, fonts
- Context lines are tracked for position mapping but not as added lines

---

# File 4: `gemini_service.py`

## 1. Purpose
Handles all communication with the Google Gemini API. Loads the prompt template, sends the diff, and parses the JSON response. Isolates LLM concerns from the rest of the system.

## 2. Location
**Path:** `src/code_review/gemini_service.py`

## 3. Dependencies
- **Imports:** `json`, `os` (stdlib), `requests` (external)
- **Files:** Reads `review_prompt.md` from project root
- **External:** Google Generative AI REST API
- **Used by:** `review.py`

## 4. Code Walkthrough

### Lines 6-11: `__init__`
```python
self.api_key = api_key
self.model = "gemini-3.1-flash-lite-preview"
self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
self.prompt_template = self._load_prompt()
```
- Model is `gemini-3.1-flash-lite-preview` — free tier, fast, lightweight
- URL follows Google's REST API pattern
- Prompt loaded once at init (not per-request)

### Lines 13-24: `_load_prompt()`
Navigates from `src/code_review/` up two directories to find `review_prompt.md`.
```python
prompt_path = os.path.join(os.path.dirname(...), "..", "..", "review_prompt.md")
```
**Fallback:** If file not found, uses `_default_prompt()` — a hardcoded basic prompt.

### Lines 33-59: `review_code(diff_text)`
```python
prompt = self.prompt_template + "\n\n## Code Diff to Review:\n\n" + diff_text
payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"temperature": 0},
}
response = requests.post(self.url, params={"key": self.api_key}, json=payload, timeout=60)
```

**Key decisions:**
- `temperature: 0` → deterministic output (same input = same output)
- `timeout=60` → prevents hanging if Gemini is slow
- API key passed as query parameter (Google's REST API convention)

**Error handling:**
- `requests.exceptions.Timeout` → return None
- `requests.exceptions.RequestException` → return None
- HTTP status ≠ 200 → log error, return None

### Lines 61-78: `_parse_response(response_data)`
Navigates Gemini's response structure:
```
response_data → candidates[0] → content → parts[0] → text
```
This deeply nested structure is Gemini's standard response format.

### Lines 80-111: `_extract_json(text)`
Gemini sometimes wraps JSON in markdown code blocks. This method handles three cases:
1. ` ```json ... ``` ` → extract between markers
2. ` ``` ... ``` ` → extract between markers (no language tag)
3. Raw text → try parsing directly

**Fallback:** If JSON parsing fails entirely, returns `{"summary": raw_text[:500], "comments": []}`. The bot still posts a summary even if comments can't be extracted.

## 5. Data Flow
```
review_prompt.md + diff_text
        │
        ▼
  Combined prompt string
        │
        ▼
  POST → Gemini API
        │
        ▼
  JSON response: {candidates: [{content: {parts: [{text: "..."}]}}]}
        │
        ▼
  _extract_json() → {summary: "...", comments: [...]}
```

## 6. Inputs
- `api_key` (string): Google Gemini API key
- `diff_text` (string): Formatted diff with annotated line numbers

## 7. Outputs
```python
{
  "summary": "Overall description of changes",
  "comments": [
    {"path": "src/App.tsx", "line": 14, "body": "[Added] New heading element"}
  ]
}
```
Or `None` on any failure.

## 8. Interview Questions
1. Why is temperature set to 0?
2. Why load the prompt from a file instead of hardcoding?
3. Why does `_extract_json` handle markdown code blocks?
4. What happens if Gemini returns invalid JSON?
5. Why is the timeout 60 seconds?
6. How does the fallback prompt differ from `review_prompt.md`?

## 9. Summary
- Single class encapsulating all Gemini API communication
- Loads customizable prompt from `review_prompt.md`
- Temperature=0 for deterministic reviews
- Handles JSON wrapped in markdown code fences
- Graceful fallback when JSON parsing fails
- 60-second timeout prevents hanging

---

# File 5: `github_client.py`

## 1. Purpose
Encapsulates ALL GitHub REST API communication. Fetches PR files, commit files, posts reviews, posts comments, checks for duplicates, and handles batch/individual fallback.

## 2. Location
**Path:** `src/code_review/github_client.py`

## 3. Dependencies
- **Imports:** `requests` (external)
- **External service:** GitHub REST API (`api.github.com`)
- **Used by:** `review.py`

## 4. Code Walkthrough

### Lines 4-12: `__init__`
```python
self.token = token
self.repo = repo_full_name
self.base_url = f"https://api.github.com/repos/{repo_full_name}"
self.headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json",
}
```
- Bearer token auth (standard for GitHub Apps and `GITHUB_TOKEN`)
- `v3+json` Accept header ensures stable API responses

### Lines 14-30: `get_pr_files(pr_number)` — Paginated
```python
while True:
    response = requests.get(url, params={"per_page": 100, "page": page})
    if not data: break
    files.extend(data)
    page += 1
```
GitHub returns max 100 items per page. This loops until all files are fetched. **Critical for large PRs** with >100 changed files.

### Lines 40-60: `post_review(pr_number, comments)` — Batch
Posts all comments in a single API call using GitHub's Reviews API:
```python
body = {"event": "COMMENT", "comments": review_comments}
response = requests.post(url, headers=self.headers, json=body)
```
- `event: "COMMENT"` means informational only (not APPROVE or REQUEST_CHANGES)
- On failure → calls `_post_comments_individually()` as fallback

### Lines 62-76: `_post_comments_individually()` — Fallback
If batch fails (e.g., one invalid position), posts each comment separately. Counts successes and logs failures.

### Lines 78-100: `post_summary_comment(pr_number, body)` — Dedup
1. Fetches existing issue comments
2. Looks for Bot user + "AI Code Review Summary" text
3. If found → PATCH (update) existing comment
4. If not found → POST new comment

**Why:** Prevents multiple summary comments when the bot re-runs (e.g., new push to same PR).

### Lines 109-115: `get_commit_files(commit_sha)`
```python
response = requests.get(f"{self.base_url}/commits/{commit_sha}")
return response.json().get("files", [])
```
GitHub's commit endpoint returns the full commit object including `files` array with patches.

### Lines 117-154: Commit comment methods
Mirror the PR comment methods but use commit endpoints:
- `post_commit_comment()` — summary on commit
- `post_commit_comments()` — inline comments on commit
- Both include deduplication logic

## 5. Data Flow
```
review.py
  │
  ├─ get_pr_files() ────→ GET /pulls/{n}/files ────→ [{filename, patch, status}]
  │
  ├─ post_review() ─────→ POST /pulls/{n}/reviews ──→ inline comments on PR
  │     └─ fallback ────→ POST /pulls/{n}/comments ─→ individual comments
  │
  └─ post_summary_comment() → GET existing → PATCH or POST /issues/{n}/comments
```

## 6. Interview Questions
1. Why paginate `get_pr_files()`?
2. Why use batch review API instead of individual comments?
3. Why fall back to individual comments on batch failure?
4. How does duplicate detection work for summary comments?
5. Why use `Bearer` auth instead of `token` prefix?
6. What's the difference between `/issues/` and `/pulls/` comment endpoints?

## 7. Summary
- Complete GitHub API client for reviews
- Pagination handles PRs with >100 files
- Batch review posting with individual fallback
- Duplicate comment detection and update (PATCH)
- Separate methods for PR and commit workflows
- All errors logged but don't crash the bot

---

# File 6: `repository_service.py`

## 1. Purpose
Runs local `git` commands via `subprocess`. Provides functions to get diffs and changed file lists using the actual git binary. This is an **alternative** to using the GitHub API for diff retrieval.

## 2. Location
**Path:** `src/code_review/repository_service.py`

## 3. Dependencies
- **Imports:** `subprocess`, `os` (stdlib)
- **Used by:** `review.py` (imported but currently only the GitHub API path is used for PR reviews)

## 4. Code Walkthrough

### Lines 5-19: `get_diff_between_refs(base_ref, head_ref)`
```python
result = subprocess.run(
    ["git", "diff", base_ref, head_ref, "--unified=3"],
    capture_output=True, text=True,
    cwd=os.environ.get("GITHUB_WORKSPACE", "."),
)
```
- `--unified=3` → show 3 lines of context around changes
- `GITHUB_WORKSPACE` → directory where Actions checked out the code
- Returns raw diff text or empty string on error

### Lines 22-36: `get_changed_files(base_ref, head_ref)`
```python
["git", "diff", "--name-only", base_ref, head_ref]
```
Returns just filenames (no patch content). Useful for knowing which files changed without the full diff.

## 5. Summary
- Thin wrapper around `git diff` subprocess calls
- Uses `GITHUB_WORKSPACE` for correct working directory
- Two functions: full diff and file-names-only
- Error handling returns empty results (doesn't crash)
- Currently a utility module; main flow uses GitHub API for diffs

---

# File 7: `review_prompt.md`

## 1. Purpose
The **system prompt** sent to Google Gemini before every review. It instructs the AI on exactly how to analyze code, what format to return, and what to focus on. This is the "brain" that shapes review quality.

## 2. Location
**Path:** `review_prompt.md` (project root)
At root level for easy discoverability and editing. Not in `code_review/` because it's a configuration file, not code.

## 3. Key Instructions to Gemini

| Instruction | Why |
|------------|-----|
| Use exact `L<number>:` line numbers from the diff | Prevents AI from guessing/calculating wrong line numbers |
| Group consecutive changes into one comment | Reduces notification spam |
| Attach comment to last `+` line of a block | Consistent placement |
| Don't comment on formatting/imports | Those are linter concerns |
| Max 20 comments per review | Keeps reviews manageable |
| Respond with JSON only | Enables reliable parsing |
| Use prefixes: [Added], [Modified], [Issue], [Suggestion] | Structured, scannable feedback |

## 4. Response Format Required
```json
{
  "summary": "Overall description",
  "comments": [
    {"path": "file.ext", "line": 15, "body": "[Added] Description"}
  ]
}
```

## 5. Summary
- Customizable prompt that shapes all AI review output
- Enforces exact line numbers from annotated diff
- Groups related changes to reduce noise
- Limits to 20 comments maximum
- Requires pure JSON output (no markdown wrapping)
- Uses semantic prefixes for comment categorization
