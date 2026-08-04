# AI Code Review System — Complete Documentation (Part 1)

# Project Overview & Architecture

---

## What Is This Project?

This is a **CI/CD-based automated code review system**. It is a GitHub repository containing:

1. **A sample React + TypeScript + Vite web application** (the "demo app" that gets reviewed).
2. **A Python-based AI code review bot** that runs inside GitHub Actions and reviews every code change using Google Gemini.

When a developer pushes code or opens a Pull Request, GitHub Actions automatically runs a Python script that:
- Extracts the changed lines (git diff)
- Sends them to Google Gemini for review
- Posts inline comments and a summary back to the PR/commit on GitHub

---

## Complete File Map

```
review_project/
├── .github/
│   └── workflows/
│       └── ai-code-review.yml      ← CI/CD trigger (GitHub Actions workflow)
├── src/
│   ├── code_review/                 ← Python AI review engine (the CORE)
│   │   ├── review.py                ← Main orchestrator
│   │   ├── diff_parser.py           ← Parses unified diffs
│   │   ├── gemini_service.py        ← Calls Google Gemini API
│   │   ├── github_client.py         ← Calls GitHub REST API
│   │   └── repository_service.py    ← Runs local git commands
│   ├── components/                  ← React UI components (demo app)
│   │   ├── Header.tsx               ← Navigation bar
│   │   ├── Counter.tsx              ← Counter widget
│   │   └── TodoList.tsx             ← Todo list widget
│   ├── App.tsx                      ← Root React component
│   ├── App.css                      ← All styles
│   ├── main.tsx                     ← React entry point
│   └── PROJECT_OVERVIEW.md          ← Internal project docs
├── review_prompt.md                 ← System prompt for Gemini
├── requirements.txt                 ← Python dependencies
├── package.json                     ← Node.js dependencies
├── tsconfig.json                    ← TypeScript compiler config
├── vite.config.ts                   ← Vite build tool config
├── index.html                       ← HTML entry point
└── README.md                        ← Repository documentation
```

---

# Complete Architecture

```
  ┌──────────────────────────────┐
  │        DEVELOPER             │
  │  (writes code, pushes it)    │
  └──────────────┬───────────────┘
                 │
                 │  git add . → git commit → git push
                 │  (or opens a Pull Request)
                 ▼
  ┌──────────────────────────────┐
  │        GITHUB.COM            │
  │  (receives the push/PR)      │
  │                              │
  │  Detects event type:         │
  │  • push to any branch        │
  │  • pull_request (opened,     │
  │    synchronize, reopened)    │
  └──────────────┬───────────────┘
                 │
                 │  Triggers .github/workflows/ai-code-review.yml
                 ▼
  ┌──────────────────────────────┐
  │    GITHUB ACTIONS RUNNER     │
  │    (ubuntu-latest VM)        │
  │                              │
  │  Step 1: Checkout code       │
  │    └─ actions/checkout@v4    │
  │    └─ fetch-depth: 0 (full)  │
  │                              │
  │  Step 2: Setup Python 3.11   │
  │    └─ actions/setup-python   │
  │                              │
  │  Step 3: pip install         │
  │    └─ requirements.txt       │
  │    └─ installs: requests     │
  │                              │
  │  Step 4: Run review.py       │
  │    └─ Env vars injected:     │
  │       GEMINI_API_KEY (secret)│
  │       GITHUB_TOKEN (auto)    │
  │       PR_NUMBER              │
  │       REPO_FULL_NAME         │
  │       BASE_REF, HEAD_REF    │
  │       EVENT_NAME             │
  │       COMMIT_SHA             │
  └──────────────┬───────────────┘
                 │
                 │  review.py starts executing
                 ▼
  ┌──────────────────────────────┐
  │       review.py (main)       │
  │                              │
  │  1. Read environment vars    │
  │  2. Detect: PR or Push?      │
  │  3. If PR → run_pr_review()  │
  │     If Push → run_push_      │
  │     review()                 │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │     github_client.py         │
  │                              │
  │  Calls GitHub REST API:      │
  │  GET /pulls/{n}/files        │
  │   or                         │
  │  GET /commits/{sha}          │
  │                              │
  │  Returns: list of changed    │
  │  files with patch (diff)     │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │     diff_parser.py           │
  │                              │
  │  1. Skip binary/lock files   │
  │  2. Parse unified diff       │
  │  3. Extract hunks            │
  │  4. Track added lines (+)    │
  │  5. Annotate: L42: +code     │
  │  6. Map line→diff position   │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │     gemini_service.py        │
  │                              │
  │  1. Load review_prompt.md    │
  │  2. Append diff text         │
  │  3. POST to Gemini API       │
  │  4. Parse JSON response:     │
  │     {                        │
  │       "summary": "...",      │
  │       "comments": [          │
  │         {path, line, body}   │
  │       ]                      │
  │     }                        │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │    review.py (validation)    │
  │                              │
  │  1. Build valid-lines map    │
  │     (only added lines are    │
  │      valid comment targets)  │
  │  2. For each AI comment:     │
  │     snap_to_valid_line()     │
  │     (±3 line tolerance)      │
  │  3. Filter invalid comments  │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │     github_client.py         │
  │                              │
  │  POST inline comments:       │
  │  • PR → POST /pulls/reviews  │
  │  • Push → POST /commits/     │
  │    {sha}/comments            │
  │                              │
  │  POST summary comment:       │
  │  • PR → POST /issues/        │
  │    {n}/comments              │
  │  • Push → POST /commits/     │
  │    {sha}/comments            │
  │                              │
  │  Duplicate detection:        │
  │  Update existing bot         │
  │  comments instead of         │
  │  creating new ones           │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │    GITHUB PR / COMMIT PAGE   │
  │                              │
  │  Developer sees:             │
  │  • Inline comments on exact  │
  │    changed lines             │
  │  • Summary comment with      │
  │    files reviewed, count,    │
  │    and AI analysis           │
  └──────────────────────────────┘
```

### Every Step Explained

| Step | What Happens | Why |
|------|-------------|-----|
| Developer pushes | Code changes are sent to GitHub | Normal development workflow |
| GitHub detects event | `push` or `pull_request` event fires | GitHub's built-in event system |
| Actions workflow starts | `ai-code-review.yml` triggers | Defined in `on:` section of the YAML |
| Checkout code | Full repository cloned (depth=0) | Needed to access files and git history |
| Setup Python | Python 3.11 installed on runner | The review bot is written in Python |
| Install deps | `pip install requests` | Only external Python library needed |
| Run review.py | Main script executes with env vars | Entry point to the entire review system |
| Fetch changed files | GitHub API returns file patches | Get the diff without running git locally |
| Parse diff | Unified diff parsed into structured data | Extract added lines, line numbers, positions |
| Send to Gemini | Annotated diff sent to AI model | AI generates review comments |
| Validate lines | AI's line numbers checked against diff | AI may hallucinate wrong line numbers |
| Snap to valid line | ±3 line tolerance for fuzzy matching | Handles minor AI mistakes gracefully |
| Post comments | GitHub API creates review comments | Final output visible to the developer |

---

# CI/CD Pipeline — GitHub Actions Deep-Dive

## The Workflow File: `ai-code-review.yml`

```yaml
name: AI Code Review                          # Display name in GitHub Actions UI

on:                                            # TRIGGER EVENTS
  push:
    branches: ["*"]                            # Any branch push triggers this
  pull_request:
    types: [opened, synchronize, reopened]     # PR events that trigger this

permissions:                                   # TOKEN PERMISSIONS
  contents: write                              # Read/write repo contents
  pull-requests: write                         # Post PR comments and reviews

jobs:
  review:
    runs-on: ubuntu-latest                     # VM operating system
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0                       # Full git history (not shallow)

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run AI Code Review
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PR_NUMBER: ${{ github.event.pull_request.number || '' }}
          REPO_FULL_NAME: ${{ github.repository }}
          BASE_REF: ${{ github.event.pull_request.base.sha || github.event.before }}
          HEAD_REF: ${{ github.event.pull_request.head.sha || github.sha }}
          EVENT_NAME: ${{ github.event_name }}
          COMMIT_SHA: ${{ github.sha }}
        run: python src/code_review/review.py
```

### Step-by-Step Breakdown

#### Step 1: `Checkout code`
- **Why:** The runner starts with an empty VM. It needs the code.
- **`fetch-depth: 0`:** Downloads the ENTIRE git history. Default is `1` (shallow clone). Full history is needed because `repository_service.py` may run `git diff` between arbitrary commits.
- **If removed:** The script would have no code to analyze.

#### Step 2: `Set up Python 3.11`
- **Why:** The review bot is Python code. The runner's default Python may not be 3.11.
- **If removed:** `python` command may fail or use an incompatible version.

#### Step 3: `Install dependencies`
- **Why:** Installs `requests` library (the only dependency in `requirements.txt`).
- **If removed:** `import requests` would fail with `ModuleNotFoundError`.

#### Step 4: `Run AI Code Review`
- **Why:** Executes the main orchestrator script.
- **Environment Variables:**

| Variable | Source | Purpose |
|----------|--------|---------|
| `GEMINI_API_KEY` | Repository secret (manual setup) | Authenticates with Google Gemini API |
| `GITHUB_TOKEN` | Auto-generated by GitHub | Authenticates with GitHub API for posting comments |
| `PR_NUMBER` | `github.event.pull_request.number` | Identifies which PR to review (empty for push events) |
| `REPO_FULL_NAME` | `github.repository` | e.g., `rajvardhan1110/Review_System` |
| `BASE_REF` | PR base SHA or `github.event.before` | The "before" commit (what we're comparing against) |
| `HEAD_REF` | PR head SHA or `github.sha` | The "after" commit (the new code) |
| `EVENT_NAME` | `github.event_name` | Either `"push"` or `"pull_request"` |
| `COMMIT_SHA` | `github.sha` | The specific commit being processed |

### Secrets

| Secret | How to Set | Used By |
|--------|-----------|---------|
| `GEMINI_API_KEY` | Repo → Settings → Secrets → Actions → New | `gemini_service.py` to call Google Gemini |
| `GITHUB_TOKEN` | **Auto-generated** by GitHub for every workflow run | `github_client.py` to call GitHub API |

> [!IMPORTANT]
> `GITHUB_TOKEN` is NOT a secret you need to create. GitHub automatically provides it for every Actions run. It has the permissions defined in the `permissions:` block.

### Remember This — CI/CD Pipeline
- The workflow runs on **every push** to any branch AND on PR events (opened/sync/reopen).
- `fetch-depth: 0` is critical — shallow clones break `git diff`.
- `GITHUB_TOKEN` is auto-provided; `GEMINI_API_KEY` must be manually added as a secret.
- The Python script is the final step — all previous steps prepare the environment.
- The workflow needs `pull-requests: write` permission to post review comments.

---

# Git Diff Analysis

## How Git Diff Works

`git diff` compares two versions of files and outputs only the **differences** (changes).

### Unified Diff Format

```diff
diff --git a/src/App.tsx b/src/App.tsx
index abc1234..def5678 100644
--- a/src/App.tsx                          ← "old" file
+++ b/src/App.tsx                          ← "new" file
@@ -10,6 +10,8 @@ function App() {           ← HUNK HEADER
   return (                                 ← context line (unchanged)
     <div className="app">                  ← context line (unchanged)
       <Header />                           ← context line (unchanged)
+      <h1>hey this is demo branch</h1>     ← ADDED line
+      <p>New paragraph</p>                 ← ADDED line
       <main className="main-content">      ← context line (unchanged)
```

### Key Concepts

| Term | Symbol | Meaning |
|------|--------|---------|
| Added line | `+` prefix | New code in the "new" file |
| Deleted line | `-` prefix | Code removed from the "old" file |
| Context line | ` ` (space) prefix | Unchanged line shown for context |
| Hunk header | `@@ ... @@` | Shows line ranges for old and new files |
| File header | `--- a/` and `+++ b/` | Identifies which file is being diffed |

### Hunk Header Decoded

```
@@ -10,6 +10,8 @@
     │  │   │  │
     │  │   │  └── 8 lines shown from new file
     │  │   └───── starting at line 10 in new file
     │  └───────── 6 lines shown from old file
     └──────────── starting at line 10 in old file
```

### How the Bot Uses Git Diff

The bot **only reviews changed code**, not the entire repository:

```
Full Repository (thousands of lines)
         │
         │  git diff (or GitHub API patch)
         ▼
Changed Lines Only (maybe 20-50 lines)
         │
         │  diff_parser.py
         ▼
Structured Data: {path, added_lines, positions}
         │
         │  Sent to Gemini
         ▼
AI Reviews Only Changed Code
```

**Why this matters:**
- **Speed:** Reviewing 30 lines is instant; reviewing 10,000 lines would be slow.
- **Cost:** LLM API tokens are proportional to input size. Smaller input = lower cost.
- **Relevance:** Comments on unchanged code would be noise.

### Position vs Line Number

This is a critical distinction:

- **Line Number:** The actual line number in the file (e.g., line 42 in `App.tsx`).
- **Diff Position:** The 1-based offset within the diff itself (e.g., the 5th line of the patch).

The GitHub API uses **diff position** for inline comments, not file line numbers. The `diff_parser.py` maps between the two.

### Remember This — Git Diff
- Git diff shows only changes, not entire files.
- `+` = added, `-` = removed, space = context (unchanged).
- `@@ -old_start,count +new_start,count @@` is the hunk header.
- The bot skips binary files, lock files, images, and fonts.
- "Diff position" ≠ "file line number" — the parser maps between them.
- GitHub's API returns the patch (diff) for each file in a PR.

---

# GitHub Review API

## How Inline Comments Work

GitHub has two types of comments on a PR:

### 1. Issue Comments (General/Summary)
- Endpoint: `POST /repos/{owner}/{repo}/issues/{pr_number}/comments`
- Appear in the **Conversation** tab.
- Just a text body — no file or line association.

### 2. Pull Request Review Comments (Inline)
- Endpoint: `POST /repos/{owner}/{repo}/pulls/{pr_number}/reviews`
- Appear in the **Files Changed** tab, **next to the specific line**.
- Require: `path`, `position` (or `line`), `body`.

### Key Fields for Inline Comments

| Field | Meaning | Example |
|-------|---------|---------|
| `path` | Relative file path | `src/App.tsx` |
| `position` | 1-based offset in the diff hunk | `5` (5th line of the diff) |
| `body` | Comment text | `"[Added] New header component"` |
| `event` | Review action | `"COMMENT"` (not APPROVE/REQUEST_CHANGES) |

### How Position Mapping Works

```
Diff output:                          Position:
@@ -10,6 +10,8 @@ function App()       1
   return (                            2
     <div className="app">             3
       <Header />                      4
+      <h1>demo branch</h1>            5  ← Comment at position=5
+      <p>New paragraph</p>            6
       <main>                          7
```

The bot's `diff_parser.py` tracks this position for every line, so when Gemini says "comment on line 13 of `App.tsx`", the bot looks up what diff position corresponds to line 13 and uses that position in the API call.

### Batch vs Individual Comments

The bot first tries to post all comments as a **batch review** (single API call):
```
POST /pulls/{n}/reviews
{
  "event": "COMMENT",
  "comments": [
    {"path": "...", "position": 5, "body": "..."},
    {"path": "...", "position": 12, "body": "..."}
  ]
}
```

If the batch fails (e.g., one invalid position causes the whole batch to fail), it falls back to posting comments **individually**.

### Commit Comments (for Push events)

When there's no PR (direct push), comments are posted on the commit:
- Endpoint: `POST /repos/{owner}/{repo}/commits/{sha}/comments`
- Fields: `body`, `path`, `position`

### Duplicate Prevention

Before posting a summary, the bot:
1. Fetches existing comments on the PR/commit.
2. Checks if any comment was posted by a `Bot` user AND contains `"AI Code Review Summary"`.
3. If found → **PATCH** (update) the existing comment.
4. If not found → **POST** a new comment.

### Remember This — GitHub Review API
- Inline comments use `position` (diff offset), NOT `line` (file line number).
- The bot posts reviews with event `"COMMENT"` (informational, not blocking).
- Batch review is preferred; individual fallback handles partial failures.
- Summary comments go to the Issues API (Conversation tab).
- Inline comments go to the Reviews API (Files Changed tab).
- Duplicate detection prevents spam from re-runs.

---

# End-to-End Execution

Here is **exactly** what happens from `git push` to review comments appearing:

## Phase 1: Developer Actions

```bash
# Developer makes changes
vim src/App.tsx                    # Edit a file

# Stage, commit, push
git add .
git commit -m "Add demo heading"
git push origin feature-branch
```

## Phase 2: GitHub Receives the Push

1. GitHub receives the pushed commits.
2. GitHub checks `.github/workflows/` for matching workflow files.
3. `ai-code-review.yml` matches because of `on: push: branches: ["*"]`.
4. GitHub queues a workflow run and allocates an `ubuntu-latest` runner.

## Phase 3: GitHub Actions Runner

1. **Runner boots** — a fresh Ubuntu VM starts (takes ~5-10 seconds).
2. **Checkout** — `actions/checkout@v4` clones the full repository (`fetch-depth: 0`).
3. **Python setup** — `actions/setup-python@v5` installs Python 3.11.
4. **Dependencies** — `pip install -r requirements.txt` installs the `requests` library.
5. **Environment variables are set** — GitHub injects secrets and context variables.

## Phase 4: review.py Executes

```
main()
  ├─ Read env vars: GEMINI_API_KEY, GITHUB_TOKEN, REPO_FULL_NAME, etc.
  ├─ Validate: all required vars present?
  ├─ Create GitHubClient(token, repo)
  ├─ Create GeminiService(api_key)
  ├─ Detect event type:
  │   ├─ EVENT_NAME == "pull_request" AND PR_NUMBER exists?
  │   │   └─ YES → run_pr_review()
  │   └─ NO → run_push_review()
  │
  ├─ [For PR review]:
  │   ├─ github.get_pr_files(pr_number)
  │   │   └─ GET https://api.github.com/repos/{repo}/pulls/{n}/files
  │   │   └─ Returns: [{filename, patch, status}, ...]
  │   │
  │   ├─ parse_diff(changed_files)
  │   │   ├─ For each file:
  │   │   │   ├─ Skip if status=="removed" or no patch
  │   │   │   ├─ Skip if should_skip_file() (locks, images, etc.)
  │   │   │   └─ parse_patch(patch):
  │   │   │       ├─ Split patch by lines
  │   │   │       ├─ Detect hunk headers: @@ -a,b +c,d @@
  │   │   │       ├─ For "+" lines: record line number + diff position
  │   │   │       ├─ Annotate: "L42: +some code"
  │   │   │       └─ Return chunks with added_lines, changed_lines maps
  │   │   └─ Return: [{path, status, chunks}, ...]
  │   │
  │   ├─ build_diff_text(diff_entries)
  │   │   └─ Format as markdown with annotated lines
  │   │
  │   ├─ gemini.review_code(diff_text)
  │   │   ├─ Load review_prompt.md
  │   │   ├─ Append diff_text to prompt
  │   │   ├─ POST https://generativelanguage.googleapis.com/v1beta/...
  │   │   ├─ Parse response → extract JSON
  │   │   └─ Return: {summary, comments: [{path, line, body}]}
  │   │
  │   ├─ build_valid_lines_map(diff_entries)
  │   │   └─ Map: {filepath → {line_number → diff_position}}
  │   │
  │   ├─ For each comment from Gemini:
  │   │   ├─ snap_to_valid_line(path, line, valid_lines)
  │   │   │   ├─ Exact match? Use it.
  │   │   │   ├─ Try ±1, ±2, ±3
  │   │   │   └─ No match? Skip this comment.
  │   │   └─ Add to valid_comments if matched
  │   │
  │   ├─ github.post_review(pr_number, valid_comments)
  │   │   ├─ POST /pulls/{n}/reviews (batch)
  │   │   └─ On failure: _post_comments_individually() (one by one)
  │   │
  │   └─ github.post_summary_comment(pr_number, summary_body)
  │       ├─ Check for existing bot summary → PATCH if found
  │       └─ Otherwise → POST /issues/{n}/comments
  │
  └─ [For Push review]:
      └─ (Same flow but uses commit API endpoints instead of PR endpoints)
```

## Phase 5: Results Appear

1. **Inline comments** appear in the PR's "Files Changed" tab, next to the specific changed lines.
2. **Summary comment** appears in the PR's "Conversation" tab.
3. The GitHub Actions workflow shows a green ✅ checkmark.
4. Developer receives a GitHub notification.

### Timeline

```
t=0s     Developer runs: git push
t=1s     GitHub receives push
t=2s     Workflow queued
t=5s     Runner VM starts
t=10s    Code checked out
t=15s    Python installed
t=18s    Dependencies installed
t=20s    review.py starts
t=22s    GitHub API: fetch changed files
t=23s    Diff parsed
t=25s    Gemini API called
t=30s    Response received and parsed
t=32s    Comments validated and posted
t=33s    Summary comment posted
t=35s    ✅ Workflow complete — developer sees comments
```

### Remember This — End-to-End
- Total time from push to comments: ~30-35 seconds.
- The bot never modifies code — it only reads diffs and posts comments.
- Two modes: PR review (uses PR API) and Push review (uses Commit API).
- Gemini may return wrong line numbers — the snap function handles this.
- If batch review fails, individual comment posting is the fallback.
- Existing bot comments are updated, not duplicated.
