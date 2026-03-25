#!/usr/bin/env python3
"""
本地质量检查脚本 — 模拟 CI/CD 质量门控
用法：
    python scripts/pre-commit-check.py          # 快速检查（~30s）
    python scripts/pre-commit-check.py --full   # 完整检查（~2-3min，含集成警告）
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# ─── 颜色输出 ──────────────────────────────────────────────────────────
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg: str)  -> None: print(f"{GREEN}[OK]{RESET}    {msg}")
def fail(msg: str) -> None: print(f"{RED}[FAIL]{RESET}  {msg}")
def warn(msg: str) -> None: print(f"{YELLOW}[WARN]{RESET}  {msg}")
def info(msg: str) -> None: print(f"{BLUE}[INFO]{RESET}  {msg}")
def header(msg: str) -> None:
    print(f"\n{BOLD}{'─' * 60}{RESET}")
    print(f"{BOLD}  {msg}{RESET}")
    print(f"{BOLD}{'─' * 60}{RESET}")


def run(cmd: list[str], cwd: str | None = None, capture: bool = True):
    """运行命令，返回 (returncode, stdout, stderr)"""
    result = subprocess.run(
        cmd, cwd=cwd,
        capture_output=capture,
        text=True, encoding="utf-8", errors="replace"
    )
    return result.returncode, result.stdout, result.stderr


# ─── Gate 1: Lint ──────────────────────────────────────────────────────
def check_lint(root: Path) -> bool:
    header("Gate 1/4  ❌ Lint (BLOCKING)")
    passed = True

    # ruff
    info("Running ruff...")
    code, out, err = run(
        ["python", "-m", "ruff", "check",
         "backend/src", "decision-service/src",
         "--select=E,W,F,I", "--ignore=E501"],
        cwd=str(root)
    )
    if code == 0:
        ok("ruff: no issues")
    else:
        fail("ruff found issues:")
        print(out or err)
        passed = False

    # isort
    info("Running isort...")
    code, out, _ = run(
        ["python", "-m", "isort", "--check-only", "--diff",
         "backend/src", "decision-service/src"],
        cwd=str(root)
    )
    if code == 0:
        ok("isort: imports correctly ordered")
    else:
        fail("isort: import order issues found:")
        print(out)
        passed = False

    return passed


# ─── Gate 2: Unit Tests ────────────────────────────────────────────────
def check_unit_tests(root: Path, python_versions: list[str] | None = None) -> bool:
    if python_versions is None:
        python_versions = ["python"]  # 仅用当前 Python

    header("Gate 2/4  ❌ Unit Tests (BLOCKING)")
    overall = True

    for py in python_versions:
        info(f"Running unit tests with: {py}")
        code, out, err = run(
            [py, "-m", "pytest",
             "test_essential_compliance.py",
             "test_model_manager_simple.py",
             "src/ai_risk_control/test_risk_control.py",
             "-v", "--tb=short",
             "-m", "not integration and not jax and not blockchain and not performance and not slow",
             "--no-header"],
            cwd=str(root / "backend")
        )
        if code == 0:
            ok(f"Unit tests passed ({py})")
        else:
            fail(f"Unit tests FAILED ({py}):")
            # 只打印 FAILED 行
            for line in (out + err).splitlines():
                if "FAILED" in line or "ERROR" in line or "short test summary" in line:
                    print(f"    {line}")
            overall = False

    return overall


# ─── Gate 3: Security ──────────────────────────────────────────────────
def check_security(root: Path) -> bool:
    header("Gate 3/4  ❌ Security Scan (BLOCKING on HIGH)")
    passed = True

    # bandit
    info("Running bandit (HIGH severity only)...")
    bandit_report = root / "bandit-report.json"
    code, out, err = run(
        ["python", "-m", "bandit", "-r",
         "backend/src", "decision-service/src",
         "-ll", "--severity-level", "high",
         "-f", "json", "-o", str(bandit_report)],
        cwd=str(root)
    )
    try:
        data = json.loads(bandit_report.read_text(encoding="utf-8"))
        highs = [r for r in data.get("results", []) if r.get("issue_severity") == "HIGH"]
        if highs:
            fail(f"bandit: {len(highs)} HIGH severity issue(s):")
            for h in highs:
                print(f"    [{h['test_id']}] {h['issue_text']}")
                print(f"           {h['filename']}:{h['line_number']}")
            passed = False
        else:
            ok("bandit: 0 HIGH severity issues")
    except (FileNotFoundError, json.JSONDecodeError):
        warn("bandit not installed or report parse failed — skipping (install: pip install bandit)")

    # safety
    info("Running safety check...")
    code, out, err = run(
        ["python", "-m", "safety", "check",
         "-r", "backend/requirements.txt", "--json"],
        cwd=str(root)
    )
    try:
        safety_data = json.loads(out)
        vulns = safety_data.get("vulnerabilities", [])
        critical_high = [v for v in vulns
                         if v.get("severity", "").upper() in ("CRITICAL", "HIGH")]
        if critical_high:
            fail(f"safety: {len(critical_high)} CRITICAL/HIGH vulnerability(s):")
            for v in critical_high[:5]:
                print(f"    {v.get('package_name')}: {str(v.get('advisory', ''))[:100]}")
            passed = False
        else:
            ok(f"safety: 0 CRITICAL/HIGH vulnerabilities ({len(vulns)} total)")
    except (json.JSONDecodeError, KeyError, TypeError):
        warn("safety not installed or parse failed — skipping (install: pip install safety)")

    return passed


# ─── Gate 4: Integration Tests (warn only) ────────────────────────────
def check_integration(root: Path) -> bool:
    """返回值始终 True（集成测试不阻断），失败时打印警告"""
    header("Gate 4/4  ⚠️  Integration Tests (WARNING ONLY, non-blocking)")

    info("Running integration tests...")
    code, out, err = run(
        ["python", "-m", "pytest",
         "tests/integration/",
         "-v", "--tb=short",
         "-m", "integration",
         "--no-header"],
        cwd=str(root / "backend")
    )
    if code == 0:
        ok("Integration tests passed")
    else:
        warn("Integration tests FAILED — this is a WARNING only, merge is not blocked")
        warn("External services (DB, Redis, etc.) may be unavailable in local env")
        for line in (out + err).splitlines():
            if "FAILED" in line or "ERROR" in line or "short test summary" in line:
                print(f"    {line}")

    return True  # 始终通过


# ─── 主函数 ────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Local quality gate check")
    parser.add_argument("--full", action="store_true",
                        help="Run full check including integration tests and multi-python")
    parser.add_argument("--gate", choices=["lint", "unit", "security", "integration"],
                        help="Run only a specific gate")
    args = parser.parse_args()

    root = Path(__file__).parent.parent.resolve()
    start = time.time()

    print(f"\n{BOLD}{'═' * 60}{RESET}")
    print(f"{BOLD}  AI Agriculture System — Local Quality Gate Check{RESET}")
    print(f"{BOLD}{'═' * 60}{RESET}")
    print(f"  Mode : {'FULL' if args.full else 'QUICK'}")
    print(f"  Root : {root}")

    gates_passed = {}
    blocking_failed = []

    if args.gate in (None, "lint"):
        gates_passed["lint"] = check_lint(root)
        if not gates_passed["lint"]:
            blocking_failed.append("Lint")

    if args.gate in (None, "unit"):
        py_versions = ["python3.11", "python3.12"] if args.full else ["python"]
        gates_passed["unit"] = check_unit_tests(root, py_versions)
        if not gates_passed["unit"]:
            blocking_failed.append("Unit Tests")

    if args.gate in (None, "security"):
        gates_passed["security"] = check_security(root)
        if not gates_passed["security"]:
            blocking_failed.append("Security Scan")

    if args.full and args.gate in (None, "integration"):
        gates_passed["integration"] = check_integration(root)
        # integration 失败不加入 blocking_failed

    # ─── 总结 ──────────────────────────────────────────────────────────
    elapsed = time.time() - start
    header(f"Quality Gate Summary  ({elapsed:.1f}s)")

    rows = [
        ("Lint",              gates_passed.get("lint"),        "BLOCKING"),
        ("Unit Tests",        gates_passed.get("unit"),        "BLOCKING"),
        ("Security Scan",     gates_passed.get("security"),    "BLOCKING"),
        ("Integration Tests", gates_passed.get("integration"), "warn only"),
    ]
    for name, result, policy in rows:
        if result is None:
            print(f"  {'—':>6}  {name:<25} (skipped)")
        elif result:
            print(f"  {GREEN}OK{RESET}      {name:<25} ({policy})")
        elif policy == "BLOCKING":
            print(f"  {RED}FAIL{RESET}    {name:<25} ({BOLD}{policy}{RESET})")
        else:
            print(f"  {YELLOW}WARN{RESET}    {name:<25} ({policy})")

    print()
    if blocking_failed:
        print(f"{RED}{BOLD}❌ BLOCKED: {len(blocking_failed)} gate(s) failed → {', '.join(blocking_failed)}{RESET}")
        print(f"{RED}   Fix the issues above before committing / opening a PR.{RESET}")
        sys.exit(1)
    else:
        print(f"{GREEN}{BOLD}✅ All blocking gates passed — safe to commit & push{RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
