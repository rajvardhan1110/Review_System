# GitHub Actions–Based AI Code Review Pipeline — Project Documentation

---

# 1. Problem Statement

In modern software development, code reviews are critical for maintaining code quality, catching bugs early, and enforcing best practices. However:

- **Manual code reviews are slow.** Developers often wait hours or days for a teammate to review their pull request.
- **Reviewers miss things.** Human reviewers can overlook subtle bugs, security vulnerabilities, or performance issues, especially in large diffs.
- **Inconsistent feedback.** Different reviewers focus on different aspects of the code, leading to inconsistent review quality.
- **Context switching cost.** Reviewers must pause their own work, understand the pull request context, and provide meaningful feedback.
- **Small teams suffer the most.** Teams with only one to three developers often have no dedicated reviewer available.

As a result:

- Bugs reach production.
- Pull requests remain unreviewed for long periods.
- Development slows down.
- Code quality becomes inconsistent.

---

# 2. Solution

This project provides an **AI-powered automated code review bot** that performs code reviews immediately after every push or pull request.

The bot:

- Reviews **only the changed lines**, not the entire repository.
- Generates **inline comments** on the exact modified lines.
- Creates an **overall summary** explaining what changed.
- Groups nearby issues into logical comments instead of commenting on every single line.
- Supports both **Push Events** and **Pull Request Events**.
- Runs completely inside **GitHub Actions**.
- Uses **Google Gemini Free API**, making the entire solution free to operate.

---

# 3. Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **CI/CD** | GitHub Actions | Automatically triggers reviews on Push and Pull Requests |
| **AI Model** | Google Gemini (`gemini-3.1-flash-lite-preview`) | Analyses code changes and generates review feedback |
| **Backend** | Python 3.11 | Parses diffs, calls APIs, validates responses, and posts comments |
| **HTTP Client** | `requests` | Communicates with GitHub API and Gemini API |
| **Version Control** | Git + GitHub REST API | Retrieves diffs and publishes review comments |
| **Sample Application** | React + TypeScript + Vite | Demo project reviewed by the bot |
| **Hosting** | GitHub | Repository, GitHub Actions, and review comments |

---

# 4. Why This Project is Powerful

## Zero Infrastructure

No servers, databases, Docker containers, or deployment pipelines are required.

Everything executes directly inside GitHub Actions.

---

## Zero Cost

The project uses only free services:

- GitHub Actions Free Tier
- Google Gemini Free API
- GitHub Repository

There are no hosting costs or monthly subscriptions.

---

## Instant Feedback

Developers receive review comments within **10–30 seconds** of pushing code.

There is no need to wait for another developer to become available.

---

## Context-Aware Reviews

Instead of reviewing entire files, the bot analyses only the code that changed.

This keeps feedback:

- Relevant
- Focused
- Fast
- Less expensive in API token usage

---

## Precise Line-Level Comments

The bot maps Git diffs to GitHub line positions, allowing comments to appear directly beside the affected code.

---

## Safe by Design

The bot never:

- modifies files
- creates commits
- changes source code

It only posts review comments.

---

## Deterministic Output

The AI temperature is fixed at **0**, ensuring consistent reviews for identical code changes.

---

## Language Independent

Since it reviews Git diffs instead of programming language syntax, it supports virtually every text-based language, including:

- Python
- Java
- JavaScript
- TypeScript
- Go
- Rust
- C++
- YAML
- Terraform
- Dockerfiles
- and many more.

---

# 5. Need for This Project

## Industry Challenges

Manual reviews consume significant engineering time and are often delayed.

Common problems include:

- Bugs escaping into production.
- Security vulnerabilities remaining unnoticed.
- Junior developers receiving little feedback.
- Technical debt increasing over time.

---

## Target Users

| Audience | Problem Solved |
|-----------|----------------|
| Solo Developers | No available reviewer |
| Small Startups | Limited engineering resources |
| Open Source Maintainers | Large number of pull requests |
| Students | Lack of experienced mentors |
| Enterprise Teams | Need consistent baseline reviews |

---

## Without Automated Reviews

Projects often experience:

- Production bugs
- Delayed pull requests
- Security issues
- Poor code consistency
- Increased maintenance costs

---

# 6. How the System Works

## Workflow

```text
Developer Pushes Code
        │
        ▼
GitHub Actions Triggered
        │
        ▼
Fetch Git Diff
        │
        ▼
Parse Changed Files
        │
        ▼
Annotate Diff with Line Numbers
(L12:, L13:, ...)
        │
        ▼
Send Prompt + Diff to Gemini AI
        │
        ▼
Gemini Returns
• Overall Summary
• Inline Review Comments
        │
        ▼
Validate Returned Line Numbers
        │
        ▼
Snap to Nearest Valid Line (±3)
        │
        ▼
Remove Duplicate Comments
        │
        ▼
Publish:
• Inline Comments
• Overall Summary
```

---

# 7. Key Design Decisions

| Design Decision | Reason |
|-----------------|--------|
| Review only changed lines | Faster analysis and lower API cost |
| Prefix each diff line with `L<number>:` | Enables accurate AI line references |
| Group nearby changes | Reduces notification spam |
| Snap comments to nearby valid lines | Handles minor AI line-number mistakes |
| Detect duplicate comments | Prevents repeated reviews |
| Separate Push and PR workflows | Uses the appropriate GitHub API |
| Temperature = 0 | Produces deterministic reviews |
| Structured JSON output | Simplifies reliable parsing |

---

# 8. Architecture

```text
                 +----------------------+
                 |    Developer Push    |
                 +----------+-----------+
                            |
                            ▼
                 +----------------------+
                 |   GitHub Actions     |
                 +----------+-----------+
                            |
                            ▼
                 +----------------------+
                 | Fetch Git Diff       |
                 +----------+-----------+
                            |
                            ▼
                 +----------------------+
                 | Diff Parser          |
                 | + Line Annotation    |
                 +----------+-----------+
                            |
                            ▼
                 +----------------------+
                 | Gemini AI API        |
                 +----------+-----------+
                            |
             +--------------+--------------+
             |                             |
             ▼                             ▼
+--------------------------+    +--------------------------+
| Overall Summary          |    | Inline Review Comments   |
+-------------+------------+    +-------------+------------+
              |                               |
              +---------------+---------------+
                              |
                              ▼
                 +---------------------------+
                 | Line Validation & Mapping |
                 +-------------+-------------+
                               |
                               ▼
                 +---------------------------+
                 | GitHub Review API         |
                 +-------------+-------------+
                               |
                               ▼
                 +---------------------------+
                 | PR / Commit Comments      |
                 +---------------------------+
```

---

# 9. Comparison with Existing Tools

| Feature | Our Bot | GitHub Copilot PR Review | CodeRabbit | SonarCloud |
|----------|---------|--------------------------|-------------|------------|
| Free | ✅ | ❌ | ❌ | Limited |
| Runs in GitHub Actions | ✅ | ❌ | ❌ | ❌ |
| Custom Prompt | ✅ | ❌ | Limited | ❌ |
| Inline Comments | ✅ | ✅ | ✅ | File-level only |
| Reviews Push Events | ✅ | ❌ | ❌ | ❌ |
| Vendor Independent | ✅ | ❌ | ❌ | ❌ |
| Easy Setup | ✅ (~5 min) | Medium | Medium | Complex |

---

# 10. Key Features

- Automated reviews on every push and pull request.
- Reviews only modified lines.
- Accurate inline comments.
- Overall change summary.
- Duplicate comment prevention.
- Line-number validation.
- Deterministic AI output.
- Zero infrastructure.
- Completely free.
- Works with any programming language.

---

# 11. Advantages

- Faster development cycle.
- Early bug detection.
- Improved code quality.
- Consistent review standards.
- Reduced reviewer workload.
- Easy integration into existing repositories.
- No maintenance overhead.
- Highly scalable.
- Easy to customise prompts.
- No vendor lock-in.

---

# 12. Future Enhancements

Potential future improvements include:

- Severity levels (Info, Warning, Critical)
- Security-focused review mode
- Performance optimisation suggestions
- Automatic code fix generation
- Support for multiple AI models
- Review history dashboard
- Team-specific coding standards
- Repository learning for contextual reviews
- Multi-language prompt optimisation

---

# 13. Conclusion

The **AI Code Review System** demonstrates that a production-ready automated review solution can be built using:

- **Python**
- **Google Gemini Free API**
- **GitHub Actions**
- **GitHub REST API**
- **Zero infrastructure**
- **Zero operational cost**

The system provides immediate, contextual, and line-level feedback on every code change, helping developers detect bugs early, improve code quality, and reduce manual review effort while fitting seamlessly into existing GitHub workflows.