#!/usr/bin/env python3
"""
Git Status Validator for Engineering Department Project
Checks all files are committed and provides actionable commands
"""

import os
import subprocess
from pathlib import Path


# Color codes for terminal output
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def run_git_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a git command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            ["git"] + cmd,
            check=False,
            capture_output=True,
            text=True,
            cwd="/Users/nate/Development/1. Projects/Engineering Department",
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def check_git_status() -> dict:
    """Get comprehensive git status."""
    status = {
        "branch": "",
        "untracked": [],
        "modified": [],
        "staged": [],
        "unpushed": 0,
        "behind": 0,
        "has_remote": False,
    }

    # Get current branch
    code, stdout, _ = run_git_command(["branch", "--show-current"])
    status["branch"] = stdout if code == 0 else "unknown"

    # Get untracked files
    code, stdout, _ = run_git_command(["ls-files", "--others", "--exclude-standard"])
    if code == 0 and stdout:
        status["untracked"] = stdout.splitlines()

    # Get modified files
    code, stdout, _ = run_git_command(["diff", "--name-only"])
    if code == 0 and stdout:
        status["modified"] = stdout.splitlines()

    # Get staged files
    code, stdout, _ = run_git_command(["diff", "--staged", "--name-only"])
    if code == 0 and stdout:
        status["staged"] = stdout.splitlines()

    # Check remote status
    code, stdout, _ = run_git_command(["rev-parse", "@{u}"])
    if code == 0:
        status["has_remote"] = True
        # Check if ahead/behind
        code, stdout, _ = run_git_command(["rev-list", "--count", "@{u}..HEAD"])
        if code == 0:
            status["unpushed"] = int(stdout) if stdout else 0

        code, stdout, _ = run_git_command(["rev-list", "--count", "HEAD..@{u}"])
        if code == 0:
            status["behind"] = int(stdout) if stdout else 0

    return status


def check_critical_files() -> dict[str, str]:
    """Check status of critical project files."""
    critical_files = [
        # Core implementation
        "mcp_server.py",
        "mcp/schemas.py",
        "mcp/tools/__init__.py",
        "mcp/tools/notion.py",
        "mcp/tools/github.py",
        "mcp/tools/audit.py",
        # Agents
        "agent/simple_pm.py",
        "agent/pm_graph.py",
        # Tests
        "test_e2e.py",
        "uat_runner.py",
        # Documentation
        "README.md",
        "PROJECT_INVENTORY.md",
        "Current State.md",
        "PROJECT_PLAN.md",
        "UAT_GUIDE.md",
        "TEST_README.md",
        # Docs directory
        "docs/POC_PERSONAS_USE_CASES.md",
        "docs/PROD_PERSONAS_USE_CASES.md",
        "docs/POC_TO_PROD_DELTA.md",
        "docs/TESTING_FRAMEWORK.md",
        # Configuration
        "requirements.txt",
        ".gitignore",
        # Scripts
        "start_server.sh",
        "run_tests.sh",
    ]

    file_status = {}
    base_dir = Path("/Users/nate/Development/1. Projects/Engineering Department")

    for file in critical_files:
        file_path = base_dir / file
        if file_path.exists():
            # Check if tracked
            code, _, _ = run_git_command(["ls-files", "--error-unmatch", file])
            if code == 0:
                # Check if modified
                code, stdout, _ = run_git_command(["diff", "--name-only", file])
                if stdout:
                    file_status[file] = "modified"
                else:
                    file_status[file] = "committed"
            else:
                file_status[file] = "untracked"
        else:
            file_status[file] = "missing"

    return file_status


def print_status_report():
    """Print comprehensive status report."""
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}Git Repository Status Check{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}\n")

    # Get status
    status = check_git_status()
    file_status = check_critical_files()

    # Print branch info
    print(f"🌿 Branch: {Colors.BLUE}{status['branch']}{Colors.RESET}")

    # Print remote status
    if status["has_remote"]:
        if status["unpushed"] > 0:
            print(f"⬆️  {Colors.YELLOW}{status['unpushed']} commits to push{Colors.RESET}")
        if status["behind"] > 0:
            print(f"⬇️  {Colors.YELLOW}{status['behind']} commits behind remote{Colors.RESET}")
        if status["unpushed"] == 0 and status["behind"] == 0:
            print(f"✅ {Colors.GREEN}In sync with remote{Colors.RESET}")
    else:
        print(f"❌ {Colors.RED}No remote configured{Colors.RESET}")

    print(f"\n{Colors.BOLD}Uncommitted Changes:{Colors.RESET}")

    # Print untracked files
    if status["untracked"]:
        print(f"\n❌ {Colors.RED}Untracked files ({len(status['untracked'])}): {Colors.RESET}")
        for file in status["untracked"][:10]:  # Show first 10
            print(f"   - {file}")
        if len(status["untracked"]) > 10:
            print(f"   ... and {len(status['untracked']) - 10} more")

    # Print modified files
    if status["modified"]:
        print(f"\n⚠️  {Colors.YELLOW}Modified files ({len(status['modified'])}): {Colors.RESET}")
        for file in status["modified"]:
            print(f"   - {file}")

    # Print staged files
    if status["staged"]:
        print(f"\n🔄 {Colors.BLUE}Staged files ({len(status['staged'])}): {Colors.RESET}")
        for file in status["staged"]:
            print(f"   - {file}")

    # If all clean
    if not (status["untracked"] or status["modified"] or status["staged"]):
        print(f"\n✅ {Colors.GREEN}All files committed!{Colors.RESET}")

    # Critical files check
    print(f"\n{Colors.BOLD}Critical Files Status:{Colors.RESET}")

    committed = [f for f, s in file_status.items() if s == "committed"]
    modified = [f for f, s in file_status.items() if s == "modified"]
    untracked = [f for f, s in file_status.items() if s == "untracked"]
    missing = [f for f, s in file_status.items() if s == "missing"]

    print(f"✅ Committed: {len(committed)}/{len(file_status)}")
    if modified:
        print(f"⚠️  Modified: {len(modified)} files")
        for f in modified[:5]:
            print(f"   - {f}")
    if untracked:
        print(f"❌ Untracked: {len(untracked)} files")
        for f in untracked[:5]:
            print(f"   - {f}")
    if missing:
        print(f"❓ Missing: {len(missing)} files")
        for f in missing[:5]:
            print(f"   - {f}")

    # Provide commands
    print(f"\n{Colors.BOLD}Suggested Commands:{Colors.RESET}")

    if status["untracked"] or status["modified"]:
        print("\n# Stage all changes:")
        print(f"{Colors.BLUE}git add .{Colors.RESET}")
        print("\n# Or stage specific files:")
        print(f"{Colors.BLUE}git add mcp/ agent/ test_e2e.py uat_runner.py{Colors.RESET}")
        print(f"{Colors.BLUE}git add docs/ *.md *.sh{Colors.RESET}")

        print("\n# Then commit:")
        print(f'{Colors.BLUE}git commit -m "feat: Complete Phase 3 implementation"{Colors.RESET}')

    if status["staged"]:
        print("\n# Commit staged changes:")
        print(f'{Colors.BLUE}git commit -m "feat: Update project files"{Colors.RESET}')

    if status["unpushed"] > 0 or (not status["untracked"] and not status["modified"] and not status["staged"]):
        print("\n# Push to remote:")
        print(f"{Colors.BLUE}git push origin {status['branch']}{Colors.RESET}")

    # Summary
    total_issues = len(status["untracked"]) + len(status["modified"]) + len(status["staged"])

    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    if total_issues == 0:
        if status["unpushed"] > 0:
            print(f"📤 {Colors.YELLOW}Ready to push {status['unpushed']} commits{Colors.RESET}")
        else:
            print(f"✅ {Colors.GREEN}Everything is committed and pushed!{Colors.RESET}")
    else:
        print(f"⚠️  {Colors.YELLOW}Found {total_issues} uncommitted changes{Colors.RESET}")
        print("   Run the commands above to commit and push")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}\n")


if __name__ == "__main__":
    try:
        print_status_report()
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        print("\nTrying alternative method...")

        # Fallback to basic git status
        os.system('cd "/Users/nate/Development/1. Projects/Engineering Department" && git status')
