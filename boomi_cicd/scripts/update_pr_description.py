#!/usr/bin/env python3
import os
import sys
import re
from pathlib import Path
from typing import Optional, Tuple

import requests

# Configuration constants
SUCCESS_MESSAGE = """

**Code Quality Report**

### ✅ Static Code Validation
No issues were found during analysis. Great job!"""

GITHUB_API_BASE = "https://api.github.com"

VALIDATION_SECTION_PATTERN = r'(?:\n)?\*\*Code Quality Report\*\*.*?(?=\n## |\Z)|(?:\n)?## Code Quality Report.*?(?=\n## |\Z)'

def get_required_env_var(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} environment variable is required")
    return value


def parse_repository_info() -> Tuple[str, str, str]:
    repository = get_required_env_var("GITHUB_REPOSITORY")
    ref = get_required_env_var("GITHUB_REF")
    
    try:
        owner, repo = repository.split("/", 1)
    except ValueError:
        raise ValueError(f"Invalid repository format: {repository}")
    
    branch = ref.replace("refs/heads/", "")
    
    return owner, repo, branch


def create_github_headers() -> dict:
    token = get_required_env_var("GITHUB_TOKEN")
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "PR-Comment-Updater/1.0"
    }


def find_pull_request(owner: str, repo: str, branch: str, headers: dict) -> Optional[dict]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls"
    params = {
        "head": f"{owner}:{branch}",
        "state": "open"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        pulls = response.json()
        return pulls[0] if pulls else None
        
    except requests.RequestException as e:
        print(f"Error finding pull request: {e}")
        return None


def read_report_file() -> Optional[str]:
    runner_temp = os.getenv("RUNNER_TEMP")
    if not runner_temp:
        print("RUNNER_TEMP environment variable not set")
        return None
    
    report_path = Path(runner_temp) / "components" / "report.md"
    
    if not report_path.exists():
        print(f"Report file not found at: {report_path}")
        return None
    
    try:
        return report_path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"Error reading report file: {e}")
        return None


def remove_old_validation_section(pr_body: str) -> str:
    # Remove all validation sections - this pattern captures everything from the title 
    # until the next section or end of string
    cleaned_body = re.sub(VALIDATION_SECTION_PATTERN, '', pr_body, flags=re.DOTALL)
    
    # Clean up any excessive newlines that might remain
    cleaned_body = re.sub(r'\n{3,}', '\n\n', cleaned_body)
    
    return cleaned_body.rstrip()


def generate_validation_content(markdown: str) -> str:
    # Check if there are actual table rows (more than just headers)
    table_rows = [line for line in markdown.split("\n") if line.strip().startswith("|")]
    has_content = len(table_rows) > 2  # Header + separator + at least one data row
    
    if has_content:
        # Ensure the markdown starts with proper formatting (just newlines, no horizontal rules)
        if not markdown.startswith('\n'):
            markdown = '\n' + markdown
        return markdown
    else:
        return SUCCESS_MESSAGE


def update_pr_description(
    owner: str, 
    repo: str, 
    pr_number: int, 
    new_body: str, 
    headers: dict
) -> bool:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}"
    
    try:
        data = {"body": new_body}
        response = requests.patch(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        print(f"✅ Updated PR description #{pr_number}")
        return True
        
    except requests.RequestException as e:
        print(f"❌ Error updating PR description #{pr_number}: {e}")
        return False


def main():
    try:
        print("🔹 Starting PR description update process...")
        
        # Parse repository info
        owner, repo, branch = parse_repository_info()
        print(f"✅ Repository: {owner}/{repo}, Branch: {branch}")
        
        # Create GitHub API headers
        headers = create_github_headers()
        
        # Find associated pull request
        pull_request = find_pull_request(owner, repo, branch, headers)
        
        if not pull_request:
            print("❌ No open pull request found for this branch")
            return
        
        pr_number = pull_request["number"]
        pr_title = pull_request["title"]
        pr_body = pull_request["body"] or ""
        print(f"✅ Found PR #{pr_number}: {pr_title}")
        
        # Read report file
        report_markdown = read_report_file()
        
        if not report_markdown:
            print("❌ No report content available to update")
            return
        # Remove old validation section from PR description
        cleaned_body = remove_old_validation_section(pr_body)
        # Generate validation content
        validation_content = generate_validation_content(report_markdown)
        # Append new validation content
        updated_body = cleaned_body + validation_content
        
        # Update the PR description
        success = update_pr_description(owner, repo, pr_number, updated_body, headers)
        
        if success:
            print("✅ PR description update completed successfully")
        else:
            print("❌ Failed to update PR description")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
