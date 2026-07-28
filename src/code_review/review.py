import os
import sys

from github_client import GitHubClient
from diff_parser import parse_diff
from gemini_service import GeminiService
from repository_service import get_diff_between_refs


def main():
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    github_token = os.environ.get("GITHUB_TOKEN")
    repo_full_name = os.environ.get("REPO_FULL_NAME")
    event_name = os.environ.get("EVENT_NAME", "")
    pr_number = os.environ.get("PR_NUMBER", "")
    base_ref = os.environ.get("BASE_REF", "")
    head_ref = os.environ.get("HEAD_REF", "")
    commit_sha = os.environ.get("COMMIT_SHA", "")

    if not all([gemini_api_key, github_token, repo_full_name]):
        print("Error: Missing required environment variables.")
        print("Required: GEMINI_API_KEY, GITHUB_TOKEN, REPO_FULL_NAME")
        sys.exit(1)

    github = GitHubClient(github_token, repo_full_name)
    gemini = GeminiService(gemini_api_key)

    is_pr = event_name == "pull_request" and pr_number
    if is_pr:
        pr_number = int(pr_number)
        run_pr_review(github, gemini, pr_number)
    else:
        run_push_review(github, gemini, base_ref, head_ref, commit_sha)


def run_pr_review(github, gemini, pr_number):
    print(f"Reviewing PR #{pr_number} in {github.repo}")

    # Check for existing bot comments to avoid duplicates
    existing_comments = github.get_review_comments(pr_number)
    bot_comments = [c for c in existing_comments if c.get("user", {}).get("type") == "Bot"]
    if bot_comments:
        print("Bot has already commented on this PR. Checking if this is a new push...")

    # Get changed files from the PR
    changed_files = github.get_pr_files(pr_number)
    if not changed_files:
        print("No changed files found in this PR.")
        return

    # Parse diffs and review
    diff_entries = parse_diff(changed_files)
    if not diff_entries:
        print("No reviewable changes found in the diff.")
        return

    diff_text = build_diff_text(diff_entries)
    if not diff_text.strip():
        print("No meaningful diff content to review.")
        return

    print(f"Sending {len(diff_entries)} file(s) for review...")
    review_result = gemini.review_code(diff_text)
    if not review_result:
        print("Gemini did not return a valid review.")
        return

    summary = review_result.get("summary", "No summary provided.")
    comments = review_result.get("comments", [])

    valid_lines = build_valid_lines_map(diff_entries)
    valid_comments = []
    for comment in comments:
        path = comment.get("path", "")
        line = comment.get("line", 0)
        body = comment.get("body", "")
        if path in valid_lines and line in valid_lines[path] and body:
            valid_comments.append(comment)

    if valid_comments:
        print(f"Posting {len(valid_comments)} inline comment(s)...")
        github.post_review(pr_number, valid_comments)
    else:
        print("No inline comments to post.")

    files_reviewed = [entry["path"] for entry in diff_entries]
    summary_body = format_summary(summary, files_reviewed, len(valid_comments))
    github.post_summary_comment(pr_number, summary_body)
    print("Review complete.")


def run_push_review(github, gemini, base_ref, head_ref, commit_sha):
    print(f"Reviewing push commit {commit_sha[:8]} in {github.repo}")

    if not base_ref or base_ref == "0000000000000000000000000000000000000000":
        print("Initial commit or no base ref — skipping review.")
        return

    # Get commit diff via GitHub API
    changed_files = github.get_commit_files(commit_sha)
    if not changed_files:
        print("No changed files found in this commit.")
        return

    diff_entries = parse_diff(changed_files)
    if not diff_entries:
        print("No reviewable changes found in the diff.")
        return

    diff_text = build_diff_text(diff_entries)
    if not diff_text.strip():
        print("No meaningful diff content to review.")
        return

    print(f"Sending {len(diff_entries)} file(s) for review...")
    review_result = gemini.review_code(diff_text)
    if not review_result:
        print("Gemini did not return a valid review.")
        return

    summary = review_result.get("summary", "No summary provided.")
    comments = review_result.get("comments", [])

    valid_lines = build_valid_lines_map(diff_entries)
    valid_comments = []
    for comment in comments:
        path = comment.get("path", "")
        line = comment.get("line", 0)
        body = comment.get("body", "")
        if path in valid_lines and line in valid_lines[path] and body:
            comment["position"] = valid_lines[path][line]
            valid_comments.append(comment)

    if valid_comments:
        print(f"Posting {len(valid_comments)} inline comment(s) on commit...")
        github.post_commit_comments(commit_sha, valid_comments)
    else:
        print("No inline comments to post.")

    files_reviewed = [entry["path"] for entry in diff_entries]
    summary_body = format_summary(summary, files_reviewed, len(valid_comments))
    github.post_commit_comment(commit_sha, summary_body)
    print("Review complete.")


def build_diff_text(diff_entries):
    parts = []
    for entry in diff_entries:
        parts.append(f"## File: {entry['path']}")
        parts.append("```diff")
        for chunk in entry["chunks"]:
            for line in chunk["lines"]:
                parts.append(line)
        parts.append("```")
        parts.append("")
    return "\n".join(parts)


def build_valid_lines_map(diff_entries):
    valid = {}
    for entry in diff_entries:
        lines_map = {}  # line_number -> diff position
        for chunk in entry["chunks"]:
            for line_num, pos in chunk["changed_lines"].items():
                lines_map[line_num] = pos
        if lines_map:
            valid[entry["path"]] = lines_map
    return valid


def format_summary(summary, files_reviewed, inline_count):
    lines = [
        "## 🤖 AI Code Review Summary",
        "",
        f"**Files reviewed:** {len(files_reviewed)}",
        f"**Inline comments posted:** {inline_count}",
        "",
        "### Files Changed:",
        "",
    ]
    for f in files_reviewed:
        lines.append(f"- `{f}`")
    lines.append("")
    lines.append("### What Changed:")
    lines.append("")
    lines.append(summary)
    lines.append("")
    lines.append("---")
    lines.append("*This review was generated automatically by AI Code Review (Gemini).*")
    return "\n".join(lines)


if __name__ == "__main__":
    # Add the code_review directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
