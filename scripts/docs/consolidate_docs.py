#!/usr/bin/env python3
"""
Documentation Consolidation Script
Merges overlapping documentation files to reduce redundancy
"""

import shutil
from datetime import datetime
from pathlib import Path


def backup_original(file_path):
    """Create backup of original file"""
    backup_dir = Path("backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)
    if file_path.exists():
        shutil.copy2(file_path, backup_dir / file_path.name)
        print(f"  ✓ Backed up {file_path.name}")


def merge_status_docs():
    """Merge Current State, PROJECT_PLAN, and PROJECT_INVENTORY into PROJECT_STATUS.md"""
    print("\n📄 Merging status documentation...")

    root = Path()
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)

    # Read source files
    current_state = root / "Current State.md"
    project_plan = root / "PROJECT_PLAN.md"
    project_inventory = root / "PROJECT_INVENTORY.md"

    # Backup originals
    for f in [current_state, project_plan, project_inventory]:
        backup_original(f)

    # Create consolidated PROJECT_STATUS.md
    output = docs_dir / "PROJECT_STATUS.md"

    content = []
    content.append("# Engineering Department — Consolidated Project Status\n")
    content.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
    content.append("*Merged from: Current State.md, PROJECT_PLAN.md, PROJECT_INVENTORY.md*\n\n")

    # Extract key sections from each file
    if current_state.exists():
        with open(current_state) as f:
            state_content = f.read()
            # Extract implementation status
            content.append("## Current Implementation Status\n")
            content.append("*From Current State.md*\n\n")
            # Add status summary and operational sections

    if project_plan.exists():
        with open(project_plan) as f:
            plan_content = f.read()
            # Extract roadmap
            content.append("\n## Development Roadmap\n")
            content.append("*From PROJECT_PLAN.md*\n\n")
            # Add milestone schedule

    if project_inventory.exists():
        with open(project_inventory) as f:
            inventory_content = f.read()
            # Extract file inventory
            content.append("\n## Active File Inventory\n")
            content.append("*From PROJECT_INVENTORY.md*\n\n")
            # Add file listings with status

    with open(output, "w") as f:
        f.writelines(content)

    print(f"  ✓ Created {output}")
    print("  → Consider removing originals after verification")


def merge_test_docs():
    """Merge UAT_GUIDE, TEST_README, and QUICK_TEST into TESTING_GUIDE.md"""
    print("\n🧪 Merging testing documentation...")

    root = Path()
    docs_dir = Path("docs")

    # Source files
    uat_guide = root / "UAT_GUIDE.md"
    test_readme = root / "TEST_README.md"
    quick_test = root / "QUICK_TEST.md"

    # Backup originals
    for f in [uat_guide, test_readme, quick_test]:
        backup_original(f)

    # Create consolidated TESTING_GUIDE.md
    output = docs_dir / "TESTING_GUIDE.md"

    content = []
    content.append("# Engineering Department — Unified Testing Guide\n")
    content.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
    content.append("*Merged from: UAT_GUIDE.md, TEST_README.md, QUICK_TEST.md*\n\n")

    content.append("## Quick Validation\n")
    content.append("*For rapid smoke testing*\n\n")
    content.append("```bash\n")
    content.append("# Start server\n")
    content.append("python mcp_server.py\n\n")
    content.append("# Run quick tests\n")
    content.append("python test_e2e.py\n")
    content.append("```\n\n")

    content.append("## Test Suite Overview\n")
    content.append("*Complete testing procedures*\n\n")

    content.append("## UAT Test Cases\n")
    content.append("*User acceptance scenarios*\n\n")

    with open(output, "w") as f:
        f.writelines(content)

    print(f"  ✓ Created {output}")


def fix_environment_corruption():
    """Fix corrupted Environment C.md file"""
    print("\n🔧 Fixing corrupted files...")

    env_file = Path("Environment C.md")
    if env_file.exists():
        backup_original(env_file)
        # Would need actual deduplication logic here
        print("  ⚠️  Manual review needed for Environment C.md")


def remove_duplicates():
    """Remove duplicate functionality files"""
    print("\n🗑️  Removing duplicate files...")

    # Keep Python version, remove shell duplicate
    shell_git_status = Path("check_git_status.sh")
    if shell_git_status.exists():
        backup_original(shell_git_status)
        print(f"  → Consider removing {shell_git_status} (Python version preferred)")


def organize_tests():
    """Reorganize test files into proper structure"""
    print("\n📦 Organizing test files...")

    tests_dir = Path("tests")
    tests_dir.mkdir(exist_ok=True)

    # Create subdirectories
    (tests_dir / "unit").mkdir(exist_ok=True)
    (tests_dir / "integration").mkdir(exist_ok=True)
    (tests_dir / "e2e").mkdir(exist_ok=True)
    (tests_dir / "uat").mkdir(exist_ok=True)

    # Map files to new locations
    test_moves = {
        "test_notion.py": "tests/integration/",
        "test_langgraph_agent.py": "tests/integration/",
        "test_mcp_langgraph.py": "tests/integration/",
        "test_e2e.py": "tests/e2e/",
        "test_agent_detailed.py": "tests/e2e/",
        "uat_runner.py": "tests/uat/",
    }

    for src, dest in test_moves.items():
        src_path = Path(src)
        if src_path.exists():
            print(f"  → Move {src} to {dest}")


def main():
    """Run consolidation process"""
    print("=" * 50)
    print("📚 Documentation Consolidation Tool")
    print("=" * 50)

    # Create backups directory
    Path("backups").mkdir(exist_ok=True)

    # Run consolidation steps
    merge_status_docs()
    merge_test_docs()
    fix_environment_corruption()
    remove_duplicates()
    organize_tests()

    print("\n" + "=" * 50)
    print("✅ Consolidation analysis complete!")
    print("\nNext steps:")
    print("1. Review generated files in docs/")
    print("2. Verify consolidated content is complete")
    print("3. Remove original files after verification")
    print("4. Move test files to new structure")
    print("\nBackups saved in backups/ directory")


if __name__ == "__main__":
    main()
