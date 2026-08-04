# AI Code Review System — Part 4: Learning & Interview Guide

---

# Learning Notes

## Remember This — Overall System
- The system has TWO parts: a React demo app (reviewed code) and a Python bot (reviewer).
- The bot runs INSIDE GitHub Actions — no separate server needed.
- It reviews only CHANGED lines, not entire files.
- Two event types supported: `push` (any branch) and `pull_request`.
- Total cost: $0. Gemini API free tier + GitHub Actions free tier.
- The bot NEVER modifies code — it only reads diffs and posts comments.
- Line validation prevents wrong comments from appearing.
- Duplicate detection prevents spam on re-runs.
- The prompt in `review_prompt.md` is fully customizable.
- Batch review posting with individual fallback ensures robustness.

## Remember This — How Files Connect
- `ai-code-review.yml` → triggers → `review.py`
- `review.py` → uses → `github_client.py`, `diff_parser.py`, `gemini_service.py`
- `gemini_service.py` → reads → `review_prompt.md`
- `github_client.py` → talks to → GitHub REST API
- `gemini_service.py` → talks to → Google Gemini API
- `repository_service.py` → runs → local `git` commands (utility module)

## Remember This — Critical Design Choices
- `fetch-depth: 0` in checkout — without it, git history is incomplete.
- `temperature: 0` in Gemini — deterministic output, same code = same review.
- `position` vs `line` — GitHub API uses diff position, not file line number.
- Snap ±3 lines — handles AI's imperfect line number accuracy.
- `event: "COMMENT"` — bot comments, doesn't approve/reject PRs.
- Batch then fallback — tries one API call, falls back to individual.
- Annotated lines (`L42: +code`) — gives AI exact line numbers to reference.

---

# Final Revision Notes

## 1. Interview Explanation — 2 Minutes

"I built a CI/CD-based automated code review system that runs on GitHub Actions. When a developer pushes code or opens a pull request, a GitHub Actions workflow automatically triggers. It runs a Python script that fetches the changed files from the GitHub API, parses the unified diff to extract only the modified lines, and sends those changes to Google Gemini with a structured prompt. Gemini analyzes the code and returns JSON containing a summary and inline comments with specific line numbers. The script then validates each comment against the actual diff — because AI can sometimes give wrong line numbers — and posts the valid comments as inline review comments on the PR using GitHub's Review API. It also posts a summary comment. The entire system is free, requires zero infrastructure, and gives developers feedback within 30 seconds of pushing code."

## 2. Interview Explanation — 5 Minutes

"The project is an AI-powered automated code review bot that integrates into any GitHub repository.

**Architecture:** There are five Python modules orchestrated by a main `review.py` script, triggered by a GitHub Actions workflow file. The system handles both push events and pull request events.

**How it works:** When code is pushed, GitHub Actions runs the workflow. It checks out the code with full git history, installs Python and the `requests` library, and executes the main script with environment variables including API keys and event context.

**Diff Processing:** The script calls GitHub's API to get changed files with their patches. The `diff_parser.py` module parses the unified diff format — it identifies hunk headers, tracks added lines with their file line numbers AND diff positions, and creates annotated lines like `L42: +new code`. This annotation is crucial because it gives the AI model exact line numbers to reference in its feedback.

**AI Review:** The annotated diff is combined with a detailed prompt from `review_prompt.md` and sent to Google Gemini's REST API. The prompt instructs Gemini to return structured JSON with a summary and an array of comments, each targeting a specific file path and line number.

**Validation:** Gemini sometimes returns incorrect line numbers. The script builds a map of valid lines (only added lines in the diff) and uses a snap-to-valid-line function that searches ±3 lines for the nearest valid target. Comments that can't be mapped are silently skipped.

**Posting:** Valid comments are posted as a batch review using GitHub's Pull Request Reviews API. If the batch fails (perhaps one position is invalid), it falls back to posting comments individually. A summary comment is posted separately, with duplicate detection — if the bot already commented, it updates the existing comment instead of creating a new one.

**Key design decisions:** Temperature=0 for deterministic output, only reviewing changed lines for efficiency, and using diff position mapping for accurate inline comment placement."

## 3. Interview Explanation — 10 Minutes

*Include everything from the 5-minute version, then expand with:*

**Detailed diff parsing explanation:** "The unified diff format starts with hunk headers like `@@ -10,6 +10,8 @@` which tell us the old file starts at line 10 showing 6 lines, and the new file starts at line 10 showing 8 lines. Lines starting with `+` are additions, `-` are deletions, and a space means context. My parser tracks a `position` counter — this is a 1-based offset within the diff itself, separate from file line numbers. GitHub's API needs this position value, not the file line number, to place inline comments correctly.

The parser also creates two important mappings: `added_lines` is a list of line numbers that have `+` prefix (new code), and `changed_lines` maps each line number to its diff position. Only added lines are valid targets for comments — you can't comment on deleted lines or unchanged context in a PR review.

I also implemented file filtering — the `should_skip_file()` function checks against lists of extensions (`.lock`, `.png`, `.min.js`, `.woff2`) and filenames (`package-lock.json`, `yarn.lock`). These are either auto-generated or binary, and reviewing them wastes API tokens."

**Prompt engineering:** "The prompt in `review_prompt.md` is carefully crafted. Key instructions include: use exact line numbers from the `L<number>:` prefix (never calculate them), group consecutive changes into a single comment attached to the last `+` line, use semantic prefixes like `[Added]`, `[Modified]`, `[Issue]`, limit to 20 comments, skip formatting issues, and return pure JSON without markdown wrapping."

**Error handling:** "The system has multiple layers of error handling. Missing environment variables cause an immediate exit with code 1. Network failures (timeout, connection error) when calling Gemini return None, which causes the review to skip gracefully. HTTP errors from GitHub API are logged but don't crash the bot. Invalid JSON from Gemini falls back to returning the raw text as the summary with an empty comments array. And the snap-to-valid-line function handles AI inaccuracy by searching ±3 lines."

**Security considerations:** "API keys are stored as GitHub repository secrets, injected as environment variables at runtime. The `GITHUB_TOKEN` is auto-generated per workflow run and scoped to the repository. The bot never modifies source code — it's read-only except for posting comments."

---

# Common Interview Questions with Answers

### Q1: Why use git diff instead of cloning and analyzing the full repository?
**A:** Efficiency. A repository might have thousands of files and millions of lines. Git diff extracts only the changed lines — maybe 20-50 lines per commit. This makes the review faster, cheaper (fewer API tokens), and more relevant (no noise from unchanged code).

### Q2: Why use GitHub's Review API instead of Issue Comments for inline feedback?
**A:** The Review API places comments directly next to specific lines in the "Files Changed" tab. Issue Comments appear in the Conversation tab with no line association. Inline comments are far more useful — developers see the feedback right where the code is.

### Q3: How do inline review comments attach to the correct line?
**A:** Through the `position` field — a 1-based offset within the diff/patch. The `diff_parser.py` maps every line in the diff to its position. When Gemini says "comment on line 42 of file.py", the bot looks up line 42 in the valid_lines map to find the corresponding diff position, then uses that position in the API call.

### Q4: How does GitHub Actions authenticate with the GitHub API?
**A:** GitHub automatically generates a `GITHUB_TOKEN` for every workflow run. This token has the permissions defined in the workflow's `permissions:` block. It's injected as an environment variable and used as a Bearer token in API requests.

### Q5: How are secrets injected into GitHub Actions?
**A:** Secrets are stored in the repository settings (Settings → Secrets → Actions). In the workflow YAML, they're referenced as `${{ secrets.SECRET_NAME }}` and injected as environment variables. They're masked in logs — GitHub replaces their values with `***`.

### Q6: What happens if Gemini returns an incorrect line number?
**A:** The `snap_to_valid_line()` function searches ±3 lines from the returned number. If it finds a valid line (one that exists in the diff as an added line), it uses that instead. If no valid line is found within range, the comment is silently skipped.

### Q7: Why is temperature set to 0?
**A:** Temperature controls randomness in AI output. At 0, the model produces the most deterministic response — the same input always gives the same output. This ensures consistent reviews and reproducible behavior.

### Q8: What prevents the bot from posting duplicate comments?
**A:** Before posting a summary, the bot fetches existing comments and checks if any were posted by a `Bot` user with `"AI Code Review Summary"` in the body. If found, it PATCHes (updates) the existing comment instead of creating a new one.

### Q9: Why does the bot try batch review first, then fall back to individual?
**A:** Batch is efficient (one API call for all comments). But if one comment has an invalid position, the entire batch fails. The fallback posts each comment individually so valid comments still get posted even if some fail.

### Q10: Why use `fetch-depth: 0` in the checkout step?
**A:** `fetch-depth: 0` downloads the complete git history. The default (`fetch-depth: 1`) is a shallow clone with only the latest commit. Full history is needed because `git diff base_ref head_ref` requires both commits to be present locally.

### Q11: Can this bot review code in any programming language?
**A:** Yes. The bot reviews git diffs, not language-specific syntax. Since diffs are plain text, it works with Python, JavaScript, Java, Go, Rust, YAML, Dockerfiles, or any text-based file.

### Q12: What is the difference between `position` and `line` in the GitHub API?
**A:** `line` is the actual line number in the file (e.g., line 42 in `App.tsx`). `position` is the 1-based offset within the diff/patch hunk. GitHub's Review API uses `position` for placing inline comments, because the same file line might appear at different positions in different diffs.

---

# Glossary of Technical Terms

| Term | Definition |
|------|-----------|
| **CI/CD** | Continuous Integration / Continuous Delivery — automatically building, testing, and deploying code |
| **GitHub Actions** | GitHub's built-in CI/CD platform that runs workflows in response to events |
| **Workflow** | A YAML file in `.github/workflows/` that defines automated steps |
| **Runner** | The virtual machine (Ubuntu) where a workflow executes |
| **Unified Diff** | A text format showing differences between two file versions, using `+`, `-`, and context lines |
| **Hunk** | A section of a diff starting with `@@ ... @@`, showing one area of changes |
| **Hunk Header** | `@@ -old_start,count +new_start,count @@` — specifies line ranges |
| **Patch** | The diff text for a single file (GitHub API calls it `patch`) |
| **Diff Position** | 1-based offset within a patch hunk, used by GitHub's API for inline comments |
| **Pull Request (PR)** | A request to merge one branch into another, with a review interface |
| **Review** | A GitHub PR review containing comments and an action (COMMENT/APPROVE/REQUEST_CHANGES) |
| **Inline Comment** | A comment attached to a specific line in the "Files Changed" tab |
| **Issue Comment** | A general comment in the PR "Conversation" tab |
| **Bearer Token** | An authentication token sent in the `Authorization` header |
| **GITHUB_TOKEN** | An auto-generated token with scoped permissions for each Actions run |
| **Secret** | An encrypted variable stored in repository settings, injected at runtime |
| **LLM** | Large Language Model — AI model that generates text (here: Google Gemini) |
| **Temperature** | AI parameter controlling randomness; 0 = deterministic, 1 = creative |
| **REST API** | An HTTP-based API using GET/POST/PATCH/DELETE methods |
| **JSON** | JavaScript Object Notation — data format used for API communication |
| **Vite** | A fast frontend build tool for JavaScript/TypeScript projects |
| **JSX/TSX** | JavaScript/TypeScript syntax extension for writing HTML-like code in React |
| **useState** | React hook for managing component state |
| **StrictMode** | React development wrapper that enables additional checks and warnings |
| **`fetch-depth: 0`** | Git clone with full history (not shallow) |
| **`sys.exit(1)`** | Terminates the Python script with a non-zero exit code (indicates failure) |
| **`subprocess.run`** | Python function to execute shell commands |

---

# Sequence Diagram

```
Developer       GitHub.com       Actions Runner     review.py      diff_parser    gemini_service    github_client     Gemini API      GitHub API
    │               │                  │                │               │                │                │               │               │
    │──git push────▶│                  │                │               │                │                │               │               │
    │               │                  │                │               │                │                │               │               │
    │               │──trigger─────▶│                │               │                │                │               │               │
    │               │               workflow         │               │                │                │               │               │
    │               │                  │                │               │                │                │               │               │
    │               │                  │──checkout──▶│                │               │                │                │               │
    │               │                  │──python────▶│                │               │                │                │               │
    │               │                  │──pip────────▶│               │               │                │                │               │
    │               │                  │──run────────▶│               │               │                │                │               │
    │               │                  │                │               │                │                │               │               │
    │               │                  │                │──────────────────────────────────────────────────▶GET /pulls/files│               │
    │               │                  │                │◀─────────────────────────────────────────────────[files+patches]──│               │
    │               │                  │                │               │                │                │               │               │
    │               │                  │                │──parse_diff──▶│               │                │               │               │
    │               │                  │                │◀──entries─────│               │                │               │               │
    │               │                  │                │               │                │                │               │               │
    │               │                  │                │──review_code─────────────────▶│               │               │               │
    │               │                  │                │               │                │──POST────────────────────────▶│               │
    │               │                  │                │               │                │◀──JSON response───────────────│               │
    │               │                  │                │◀──{summary, comments}─────────│               │               │               │
    │               │                  │                │               │                │                │               │               │
    │               │                  │                │  validate & snap lines        │                │               │               │
    │               │                  │                │               │                │                │               │               │
    │               │                  │                │──────────────────────────────────────────────────▶POST /reviews  │               │
    │               │                  │                │──────────────────────────────────────────────────▶POST /comments │               │
    │               │                  │                │               │                │                │               │               │
    │◀──notification (review comments visible in PR)───────────────────────────────────────────────────────────────────────│               │
    │               │                  │                │               │                │                │               │               │
```

---

# Flowchart

```
                    ┌─────────────┐
                    │  START      │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ Read env    │
                    │ variables   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐     NO
                    │ All vars    ├────────────┐
                    │ present?    │            │
                    └──────┬──────┘     ┌──────▼──────┐
                      YES  │            │ EXIT(1)     │
                           │            └─────────────┘
                    ┌──────▼──────┐
                    │ Is PR       │
                    │ event?      │
                    └──┬──────┬───┘
                  YES  │      │  NO
           ┌───────────┘      └───────────┐
    ┌──────▼──────┐              ┌────────▼────────┐
    │ Get PR      │              │ Initial commit? │
    │ files       │              └───┬─────────┬───┘
    └──────┬──────┘             YES  │         │ NO
           │              ┌─────────▼┐  ┌─────▼──────┐
    ┌──────▼──────┐       │  SKIP    │  │Get commit  │
    │ Files       │ NO    └──────────┘  │files       │
    │ found?  ├────────► RETURN         └─────┬──────┘
    └──────┬──────┘                           │
      YES  │              ┌───────────────────┘
           │              │
    ┌──────▼──────────────▼───┐
    │     parse_diff()        │
    └──────┬──────────────────┘
           │
    ┌──────▼──────┐
    │ Entries     │ NO
    │ found?  ├────────► RETURN
    └──────┬──────┘
      YES  │
    ┌──────▼──────┐
    │ Build diff  │
    │ text        │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ Call Gemini │
    │ review_code │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ Result      │ NO
    │ valid?  ├────────► RETURN
    └──────┬──────┘
      YES  │
    ┌──────▼──────────────┐
    │ Build valid lines   │
    │ map (only + lines)  │
    └──────┬──────────────┘
           │
    ┌──────▼──────────────┐
    │ For each comment:   │
    │ snap_to_valid_line  │
    │ Keep valid, skip    │
    │ invalid             │
    └──────┬──────────────┘
           │
    ┌──────▼──────┐
    │ Post inline │
    │ comments    │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ Post summary│
    │ comment     │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │   DONE ✅   │
    └─────────────┘
```

---

# Cheat Sheet

```
┌─────────────────────────────────────────────────────────────────┐
│               AI CODE REVIEW SYSTEM — CHEAT SHEET               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TRIGGER:   Push to any branch OR PR opened/updated             │
│  WORKFLOW:  .github/workflows/ai-code-review.yml                │
│  ENTRY:     python src/code_review/review.py                    │
│  AI MODEL:  gemini-3.1-flash-lite-preview (free, temp=0)        │
│  PROMPT:    review_prompt.md (customizable)                     │
│                                                                 │
├──────────────────── KEY FILES ──────────────────────────────────┤
│                                                                 │
│  review.py          Main orchestrator (routing, validation)     │
│  diff_parser.py     Parses unified diffs → structured data      │
│  gemini_service.py  Calls Gemini API, parses JSON response      │
│  github_client.py   All GitHub API calls (fetch, post, dedup)   │
│  repository_service.py  Local git commands (utility)            │
│  review_prompt.md   System prompt for the AI                    │
│  ai-code-review.yml GitHub Actions workflow definition          │
│                                                                 │
├──────────────────── KEY CONCEPTS ───────────────────────────────┤
│                                                                 │
│  DIFF POSITION ≠ FILE LINE NUMBER                               │
│  position = 1-based offset in the diff patch                    │
│  line = actual line number in the file                          │
│  GitHub API needs POSITION for inline comments                  │
│                                                                 │
│  SNAP TO VALID LINE: ±3 tolerance for AI inaccuracy             │
│  VALID LINES: Only + (added) lines can receive comments         │
│  BATCH → FALLBACK: Try batch review, then individual comments   │
│  DEDUP: Check for existing bot summary → PATCH don't duplicate  │
│                                                                 │
├──────────────────── SECRETS ────────────────────────────────────┤
│                                                                 │
│  GEMINI_API_KEY  → Manual setup in repo Settings → Secrets      │
│  GITHUB_TOKEN    → Auto-generated by GitHub for each run        │
│                                                                 │
├──────────────────── ENV VARS ───────────────────────────────────┤
│                                                                 │
│  GEMINI_API_KEY     Google Gemini authentication                │
│  GITHUB_TOKEN       GitHub API authentication                   │
│  PR_NUMBER          Pull request number (empty for push)        │
│  REPO_FULL_NAME     owner/repo (e.g., user/Review_System)       │
│  BASE_REF           Base commit SHA (before changes)            │
│  HEAD_REF           Head commit SHA (after changes)             │
│  EVENT_NAME         "push" or "pull_request"                    │
│  COMMIT_SHA         Current commit SHA                          │
│                                                                 │
├──────────────────── QUICK SETUP ────────────────────────────────┤
│                                                                 │
│  1. Get Gemini API key from aistudio.google.com                 │
│  2. Add GEMINI_API_KEY as repository secret                     │
│  3. Push code or open a PR                                      │
│  4. Check Actions tab → Review comments appear!                 │
│                                                                 │
├──────────────────── WHAT IT REVIEWS ────────────────────────────┤
│                                                                 │
│  ✅ Changed/added lines       ❌ Deleted files                   │
│  ✅ Any text-based language   ❌ Binary files                    │
│  ✅ Code + config files       ❌ Lock files (package-lock, etc.) │
│  ✅ Push + PR events          ❌ Images, fonts, SVGs             │
│                                                                 │
├──────────────────── COMMON ISSUES ──────────────────────────────┤
│                                                                 │
│  "Error posting review: 422"                                    │
│  → Invalid diff position. Batch fallback handles this.          │
│                                                                 │
│  "No changed files found"                                       │
│  → Empty commit or all files are binary/skipped.                │
│                                                                 │
│  "Gemini API request timed out"                                 │
│  → API overloaded. Re-run the workflow.                         │
│                                                                 │
│  "Missing required environment variables"                       │
│  → GEMINI_API_KEY secret not configured.                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```
