#!/usr/bin/env python3
"""Run tests only for changed files in the current branch.

This script intelligently maps changed source files to their corresponding test files
and runs only the relevant tests. Used by pre-push hooks for faster feedback.
"""

import subprocess
import sys
from pathlib import Path


def get_changed_files(base_branch: str = "origin/main") -> list[Path]:
    """Get list of Python files changed compared to base branch."""
    try:
        result = subprocess.run(
            ["git", "diff", f"{base_branch}...HEAD", "--name-only", "--diff-filter=ACMR"],
            capture_output=True,
            text=True,
            check=True,
        )
        
        files = []
        for line in result.stdout.strip().split('\n'):
            if line.endswith('.py'):
                files.append(Path(line))
        
        return files
    except subprocess.CalledProcessError:
        # If origin/main doesn't exist, compare with HEAD~1
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD~1...HEAD", "--name-only", "--diff-filter=ACMR"],
                capture_output=True,
                text=True,
                check=True,
            )
            
            files = []
            for line in result.stdout.strip().split('\n'):
                if line.endswith('.py'):
                    files.append(Path(line))
            
            return files
        except subprocess.CalledProcessError:
            return []


def find_test_files(changed_files: list[Path]) -> list[Path]:
    """Map changed source files to their corresponding test files."""
    test_files = set()
    
    for file in changed_files:
        # If it's already a test file, include it
        if file.parts[0] == "tests":
            test_files.add(file)
            continue
        
        # If it's a source file, find corresponding test
        if file.parts[0] == "src":
            # Remove 'src' prefix and '.py' suffix
            module_path = Path(*file.parts[1:]).with_suffix('')
            
            # Try different test file naming patterns
            patterns = [
                Path("tests") / f"test_{module_path.name}.py",
                Path("tests") / module_path.parent / f"test_{module_path.name}.py",
                Path("tests") / f"{module_path}_test.py",
                Path("tests") / module_path.parent / f"{module_path.name}_test.py",
            ]
            
            for pattern in patterns:
                if pattern.exists():
                    test_files.add(pattern)
                    break
            else:
                # If no specific test file found, run tests in the same directory
                test_dir = Path("tests") / module_path.parent
                if test_dir.exists():
                    test_files.update(test_dir.glob("test_*.py"))
    
    return sorted(test_files)


def run_tests(test_files: list[Path]) -> int:
    """Run pytest on the specified test files."""
    if not test_files:
        print("No test files found for changed code.")
        return 0
    
    print(f"Running tests for {len(test_files)} file(s):")
    for file in test_files:
        print(f"  - {file}")
    
    cmd = ["uv", "run", "pytest"] + [str(f) for f in test_files]
    
    # Add flags for CI/CD vs local
    if sys.argv[1:] == ["--ci"]:
        # Full test run in CI
        cmd = ["uv", "run", "pytest", "tests/", "-v", "--cov=src", "--cov-report=term-missing"]
    else:
        # Quick run for pre-push
        cmd.extend(["-q", "--tb=short"])
    
    return subprocess.run(cmd).returncode


def main() -> int:
    """Main entry point."""
    if "--ci" in sys.argv:
        # In CI, run all tests with coverage
        return run_tests([])
    
    # For local development, only run tests for changed files
    changed_files = get_changed_files()
    
    if not changed_files:
        print("No Python files changed.")
        return 0
    
    test_files = find_test_files(changed_files)
    
    if not test_files:
        print("No test files found for changed code. Running all tests...")
        return subprocess.run(["uv", "run", "pytest", "tests/", "-q", "--tb=short"]).returncode
    
    return run_tests(test_files)


if __name__ == "__main__":
    sys.exit(main())