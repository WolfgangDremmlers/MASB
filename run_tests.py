#!/usr/bin/env python3
"""Test runner script for MASB."""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def run_tests(test_type="all", verbose=False, coverage=False, parallel=False):
    """Run specified tests."""
    base_cmd = ["python", "-m", "pytest"]
    
    if verbose:
        base_cmd.append("-v")
    
    if coverage:
        base_cmd.extend(["--cov=src", "--cov-report=term-missing", "--cov-report=html"])
    
    if parallel:
        base_cmd.extend(["-n", "auto"])
    
    success = True
    
    if test_type == "all" or test_type == "unit":
        cmd = base_cmd + ["tests/unit/", "-m", "not slow"]
        if not run_command(cmd, "Unit Tests"):
            success = False
    
    if test_type == "all" or test_type == "integration":
        cmd = base_cmd + ["tests/integration/", "-m", "integration"]
        if not run_command(cmd, "Integration Tests"):
            success = False
    
    if test_type == "all" or test_type == "api":
        cmd = base_cmd + ["tests/api/", "-m", "not external"]
        if not run_command(cmd, "API Tests"):
            success = False
    
    return success


def run_code_quality_checks():
    """Run code quality checks."""
    checks = [
        (["black", "--check", "--diff", "."], "Code Formatting (Black)"),
        (["flake8", "src", "tests", "--max-line-length=100"], "Linting (Flake8)"),
        (["mypy", "src", "--ignore-missing-imports"], "Type Checking (MyPy)"),
        (["bandit", "-r", "src", "-ll"], "Security Scan (Bandit)"),
        (["safety", "check"], "Dependency Scan (Safety)")
    ]
    
    success = True
    for cmd, description in checks:
        try:
            if not run_command(cmd, description):
                success = False
        except FileNotFoundError:
            print(f"⚠️  Skipping {description} - tool not installed")
    
    return success


def run_performance_tests(host="localhost:8080", users=10, spawn_rate=2, run_time="60s"):
    """Run performance tests with Locust."""
    cmd = [
        "locust",
        "-f", "tests/performance/locustfile.py",
        f"--host=http://{host}",
        f"--users={users}",
        f"--spawn-rate={spawn_rate}",
        f"--run-time={run_time}",
        "--headless",
        "--html=performance-report.html"
    ]
    
    return run_command(cmd, "Performance Tests")


def run_docker_tests():
    """Run Docker-related tests."""
    commands = [
        (["docker", "build", "-t", "masb:test", "."], "Docker Build"),
        (["docker", "run", "--rm", "--name", "masb-test", "-d", "-p", "8080:8080", "masb:test"], "Docker Run"),
    ]
    
    success = True
    container_id = None
    
    try:
        for cmd, description in commands:
            if not run_command(cmd, description):
                success = False
                break
            
            if "docker run" in " ".join(cmd):
                # Get container ID for cleanup
                result = subprocess.run(["docker", "ps", "-q", "--filter", "name=masb-test"], 
                                      capture_output=True, text=True)
                container_id = result.stdout.strip()
        
        if container_id:
            # Wait a bit for container to start
            import time
            time.sleep(10)
            
            # Test health endpoint
            health_cmd = ["curl", "-f", "http://localhost:8080/health"]
            if not run_command(health_cmd, "Docker Health Check"):
                success = False
    
    finally:
        # Cleanup
        if container_id:
            subprocess.run(["docker", "stop", container_id], capture_output=True)
            subprocess.run(["docker", "rm", container_id], capture_output=True)
    
    return success


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="MASB Test Runner")
    parser.add_argument("--type", choices=["all", "unit", "integration", "api", "performance", "docker", "quality"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    parser.add_argument("--parallel", "-p", action="store_true", help="Run tests in parallel")
    parser.add_argument("--host", default="localhost:8080", help="Host for performance tests")
    parser.add_argument("--users", type=int, default=10, help="Number of users for performance tests")
    parser.add_argument("--spawn-rate", type=int, default=2, help="Spawn rate for performance tests")
    parser.add_argument("--run-time", default="60s", help="Run time for performance tests")
    
    args = parser.parse_args()
    
    print("🚀 MASB Test Runner")
    print("=" * 50)
    
    success = True
    
    if args.type == "quality":
        success = run_code_quality_checks()
    elif args.type == "performance":
        success = run_performance_tests(args.host, args.users, args.spawn_rate, args.run_time)
    elif args.type == "docker":
        success = run_docker_tests()
    else:
        # Run regular tests
        success = run_tests(args.type, args.verbose, args.coverage, args.parallel)
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests completed successfully!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()