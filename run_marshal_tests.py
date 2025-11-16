#!/usr/bin/env python3
"""
Test runner for Marshal Agent unit tests.

Usage:
    python run_marshal_tests.py              # Run all tests
    python run_marshal_tests.py --verbose    # Verbose output
    python run_marshal_tests.py --coverage   # With coverage report
"""

import sys
import subprocess
from pathlib import Path


def run_tests(verbose=False, coverage=False):
    """Run Marshal Agent tests"""
    
    project_root = Path(__file__).parent
    test_file = project_root / "tests" / "unit" / "agents" / "test_marshal_agent.py"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return 1
    
    cmd = ["python", "-m", "pytest"]
    cmd.append(str(test_file))
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-v")  # Always verbose for better feedback
    
    if coverage:
        cmd.extend([
            "--cov=agents.marshal_agent",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
    
    # Add color and formatting
    cmd.extend([
        "--tb=short",
        "--color=yes"
    ])
    
    print(f"🧪 Running Marshal Agent tests...")
    print(f"   Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, cwd=project_root)
    
    return result.returncode


if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    coverage = "--coverage" in sys.argv or "--cov" in sys.argv
    
    exit_code = run_tests(verbose=verbose, coverage=coverage)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    
    sys.exit(exit_code)
