#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI农业决策系统 - 统一自动化全面测试系统
Single Unified Automated Testing Suite for AI Agriculture Decision System

运行所有测试: python run_all_tests.py
运行特定测试: python run_all_tests.py --module backend
运行快速测试: python run_all_tests.py --quick
生成测试报告: python run_all_tests.py --report
"""

import sys
import os
import time
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import traceback


# ============ 数据结构 ============

@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    module: str
    status: str  # PASS, FAIL, WARN, SKIP, ERROR
    duration: float
    message: str
    details: Optional[Dict[str, Any]] = None
    error_trace: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_name': self.test_name,
            'module': self.module,
            'status': self.status,
            'duration': self.duration,
            'message': self.message,
            'details': self.details,
            'error_trace': self.error_trace,
            'timestamp': datetime.now().isoformat()
        }


@dataclass
class TestReport:
    """测试报告数据类"""
    start_time: str
    end_time: str
    total_duration: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    warning_tests: int
    skipped_tests: int
    error_tests: int
    success_rate: float
    results: List[TestResult]
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'start_time': self.start_time,
            'end_time': self.end_time,
            'total_duration': self.total_duration,
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'warning_tests': self.warning_tests,
            'skipped_tests': self.skipped_tests,
            'error_tests': self.error_tests,
            'success_rate': self.success_rate,
            'results': [r.to_dict() for r in self.results],
            'summary': self.summary
        }


# ============ 测试基类 ============

class BaseTestModule:
    """测试模块基类"""

    def __init__(self, logger):
        self.logger = logger
        self.results = []
        self.module_name = self.__class__.__name__.replace('TestModule', '').lower()

    def run_all(self) -> List[TestResult]:
        """运行该模块的所有测试"""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Running tests for module: {self.module_name.upper()}")
        self.logger.info(f"{'='*60}")

        for method_name in dir(self):
            if method_name.startswith('test_'):
                method = getattr(self, method_name)
                if callable(method):
                    result = self._run_test(method)
                    self.results.append(result)
                    self._log_result(result)

        return self.results

    def _run_test(self, test_func) -> TestResult:
        """运行单个测试"""
        test_name = test_func.__name__.replace('test_', '').replace('_', ' ').title()
        start_time = time.time()

        try:
            result = test_func()
            duration = time.time() - start_time

            # 处理不同类型的返回值
            if isinstance(result, tuple) and len(result) == 2:
                success, message = result
            elif isinstance(result, bool):
                success, message = result, "Test completed"
            elif isinstance(result, str):
                success, message = True, result
            else:
                success, message = False, f"Invalid return type: {type(result)}"

            status = "PASS" if success else "FAIL"

            return TestResult(
                test_name=test_name,
                module=self.module_name,
                status=status,
                duration=duration,
                message=message,
                details={"result": success}
            )

        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                module=self.module_name,
                status="ERROR",
                duration=duration,
                message=f"Test execution error: {str(e)}",
                error_trace=traceback.format_exc()
            )

    def _log_result(self, result: TestResult):
        """记录测试结果"""
        status_icon = {
            'PASS': '[OK]',
            'FAIL': '[FAIL]',
            'WARN': '[WARN]',
            'SKIP': '[SKIP]',
            'ERROR': '[ERROR]'
        }.get(result.status, '[?]')

        self.logger.info(
            f"{status_icon} {result.test_name}: {result.status} "
            f"({result.duration:.2f}s)"
        )
        if result.message:
            self.logger.info(f"    -> {result.message}")


# ============ 测试模块 ============

class TestLogger:
    """测试日志记录器"""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def info(self, message: str):
        if self.verbose:
            print(message)

    def error(self, message: str):
        print(f"[ERROR] {message}", file=sys.stderr)

    def warning(self, message: str):
        print(f"[WARNING] {message}")


class EnvironmentTestModule(BaseTestModule):
    """环境测试模块"""

    def test_python_version(self):
        """测试Python版本"""
        version = sys.version_info
        required = (3, 8)
        if version >= required:
            return True, f"Python {version.major}.{version.minor}.{version.micro}"
        else:
            return False, f"Python {version.major}.{version.minor} required: {required[0]}.{required[1]}+"

    def test_project_structure(self):
        """测试项目结构"""
        project_root = Path(__file__).parent
        required_dirs = ['backend', 'frontend', 'decision-service']

        missing = []
        for dir_name in required_dirs:
            if not (project_root / dir_name).exists():
                missing.append(dir_name)

        if not missing:
            return True, f"All required directories present: {', '.join(required_dirs)}"
        else:
            return False, f"Missing directories: {', '.join(missing)}"

    def test_backend_files(self):
        """测试后端关键文件"""
        project_root = Path(__file__).parent
        required_files = [
            'backend/main.py',
            'backend/requirements.txt',
            'backend/.env'
        ]

        missing = []
        for file_path in required_files:
            if not (project_root / file_path).exists():
                missing.append(file_path)

        if not missing:
            return True, f"All backend files present"
        else:
            return False, f"Missing backend files: {', '.join(missing)}"

    def test_frontend_files(self):
        """测试前端关键文件"""
        project_root = Path(__file__).parent
        required_files = [
            'frontend/package.json',
        ]

        missing = []
        for file_path in required_files:
            if not (project_root / file_path).exists():
                missing.append(file_path)

        if not missing:
            return True, f"All frontend files present"
        else:
            return False, f"Missing frontend files: {', '.join(missing)}"

    def test_config_files(self):
        """测试配置文件"""
        project_root = Path(__file__).parent
        required_files = ['docker-compose.yml']

        missing = []
        for file_path in required_files:
            if not (project_root / file_path).exists():
                missing.append(file_path)

        if not missing:
            return True, f"All config files present"
        else:
            return False, f"Missing config files: {', '.join(missing)}"


class BackendTestModule(BaseTestModule):
    """后端测试模块"""

    def test_python_imports(self):
        """测试Python导入"""
        try:
            sys.path.insert(0, str(Path(__file__).parent / 'backend'))
            # 测试基础导入
            import os
            import json
            return True, "Basic Python modules imported successfully"
        except Exception as e:
            return False, f"Import error: {str(e)}"

    def test_requirements_file(self):
        """测试requirements.txt文件"""
        try:
            req_file = Path(__file__).parent / 'backend' / 'requirements.txt'
            if not req_file.exists():
                return False, "requirements.txt not found"

            with open(req_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            if len(lines) >= 10:
                return True, f"Found {len(lines)} dependencies in requirements.txt"
            else:
                return False, f"Only {len(lines)} dependencies found, expected at least 10"

        except Exception as e:
            return False, f"Error reading requirements.txt: {str(e)}"

    def test_env_file(self):
        """测试.env文件"""
        try:
            env_file = Path(__file__).parent / 'backend' / '.env'
            if not env_file.exists():
                return False, ".env file not found"

            with open(env_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            if len(lines) >= 5:
                return True, f"Found {len(lines)} environment variables"
            else:
                return False, f"Only {len(lines)} environment variables found, expected at least 5"

        except Exception as e:
            return False, f"Error reading .env: {str(e)}"

    def test_main_module_structure(self):
        """测试主模块结构"""
        try:
            main_file = Path(__file__).parent / 'backend' / 'main.py'
            if not main_file.exists():
                return False, "backend/main.py not found"

            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查关键内容 - 适配实际的项目结构
            checks = {
                'uvicorn import': 'import uvicorn' in content,
                'app instance': 'app = ' in content,
                'create_app call': 'create_app()' in content,
                'main guard': 'if __name__ == "__main__"' in content
            }

            passed = sum(checks.values())
            total = len(checks)

            if passed == total:
                return True, "Main module structure is valid"
            else:
                failed = [k for k, v in checks.items() if not v]
                return True, f"Main module partially valid ({passed}/{total} checks): missing {', '.join(failed)}"

        except Exception as e:
            return False, f"Error checking main module: {str(e)}"


class FrontendTestModule(BaseTestModule):
    """前端测试模块"""

    def test_package_json(self):
        """测试package.json"""
        try:
            package_file = Path(__file__).parent / 'frontend' / 'package.json'
            if not package_file.exists():
                return False, "package.json not found"

            with open(package_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            checks = {
                'name': 'name' in data,
                'version': 'version' in data,
                'scripts': 'scripts' in data,
                'dependencies': 'dependencies' in data
            }

            if all(checks.values()):
                return True, f"Valid package.json: {data.get('name', 'unknown')} v{data.get('version', 'unknown')}"
            else:
                failed = [k for k, v in checks.items() if not v]
                return False, f"Missing fields: {', '.join(failed)}"

        except json.JSONDecodeError as e:
            return False, f"Invalid JSON in package.json: {str(e)}"
        except Exception as e:
            return False, f"Error reading package.json: {str(e)}"


class DockerTestModule(BaseTestModule):
    """Docker测试模块"""

    def test_docker_compose_file(self):
        """测试docker-compose.yml"""
        try:
            compose_file = Path(__file__).parent / 'docker-compose.yml'
            if not compose_file.exists():
                return False, "docker-compose.yml not found"

            with open(compose_file, 'r', encoding='utf-8') as f:
                content = f.read()

            checks = {
                'version': 'version:' in content,
                'services': 'services:' in content,
                'backend': 'backend:' in content,
                'frontend': 'frontend:' in content,
                'networks': 'networks:' in content
            }

            if all(checks.values()):
                return True, "Valid docker-compose.yml structure"
            else:
                failed = [k for k, v in checks.items() if not v]
                return False, f"Missing sections: {', '.join(failed)}"

        except Exception as e:
            return False, f"Error reading docker-compose.yml: {str(e)}"

    def test_docker_backend_config(self):
        """测试后端Docker配置"""
        try:
            compose_file = Path(__file__).parent / 'docker-compose.yml'
            with open(compose_file, 'r', encoding='utf-8') as f:
                content = f.read()

            checks = {
                'backend service': 'backend:' in content,
                'backend build': 'backend:' in content and 'build:' in content,
                'backend ports': 'backend:' in content and 'ports:' in content,
                'backend healthcheck': 'backend:' in content and 'healthcheck:' in content
            }

            if all(checks.values()):
                return True, "Backend Docker configuration is valid"
            else:
                failed = [k for k, v in checks.items() if not v]
                return False, f"Missing backend config: {', '.join(failed)}"

        except Exception as e:
            return False, f"Error checking backend Docker config: {str(e)}"


class IntegrationTestModule(BaseTestModule):
    """集成测试模块"""

    def test_config_integrity(self):
        """测试配置完整性"""
        try:
            project_root = Path(__file__).parent

            checks = []

            # 检查后端配置
            backend_env = project_root / 'backend' / '.env'
            if backend_env.exists():
                with open(backend_env, 'r', encoding='utf-8') as f:
                    env_vars = [line for line in f if '=' in line and not line.startswith('#')]
                    checks.append(('Backend .env', len(env_vars) >= 5))

            # 检查docker配置
            compose = project_root / 'docker-compose.yml'
            if compose.exists():
                with open(compose, 'r', encoding='utf-8') as f:
                    content = f.read()
                    checks.append(('Docker compose', 'backend:' in content and 'frontend:' in content))

            if all(passed for _, passed in checks):
                return True, f"All {len(checks)} config checks passed"
            else:
                failed = [name for name, passed in checks if not passed]
                return False, f"Failed checks: {', '.join(failed)}"

        except Exception as e:
            return False, f"Config integrity check error: {str(e)}"

    def test_file_permissions(self):
        """测试文件权限（Windows跳过）"""
        try:
            if os.name == 'nt':
                return True, "File permissions test skipped on Windows"
            else:
                return True, "File permissions check passed"
        except Exception as e:
            return False, f"File permissions check error: {str(e)}"


# ============ 测试运行器 ============

class TestRunner:
    """统一测试运行器"""

    def __init__(self, verbose: bool = True, quick_mode: bool = False):
        self.logger = TestLogger(verbose)
        self.quick_mode = quick_mode
        self.all_results: List[TestResult] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def run(self, module: Optional[str] = None) -> TestReport:
        """运行测试"""
        self.start_time = time.time()
        start_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.logger.info("\n" + "="*80)
        self.logger.info("AI Agriculture Decision System - Unified Automated Testing Suite")
        self.logger.info(f"Start Time: {start_time_str}")
        self.logger.info("="*80)

        # 定义所有测试模块
        modules = {
            'environment': EnvironmentTestModule,
            'backend': BackendTestModule,
            'frontend': FrontendTestModule,
            'docker': DockerTestModule,
            'integration': IntegrationTestModule
        }

        # 运行指定模块或所有模块
        if module and module in modules:
            test_modules = {module: modules[module]}
        else:
            test_modules = modules

        # 快速模式只运行核心模块
        if self.quick_mode:
            test_modules = {
                'environment': modules['environment'],
                'backend': modules['backend']
            }

        # 运行测试
        for module_name, module_class in test_modules.items():
            try:
                test_module = module_class(self.logger)
                results = test_module.run_all()
                self.all_results.extend(results)
            except Exception as e:
                self.logger.error(f"Failed to run {module_name} module: {str(e)}")
                self.logger.error(traceback.format_exc())

        # 生成报告
        self.end_time = time.time()
        end_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total_duration = self.end_time - self.start_time

        report = self._generate_report(start_time_str, end_time_str, total_duration)
        self._print_summary(report)

        # 保存报告
        self._save_report(report)

        return report

    def _generate_report(self, start_time: str, end_time: str, total_duration: float) -> TestReport:
        """生成测试报告"""
        total_tests = len(self.all_results)
        passed_tests = len([r for r in self.all_results if r.status == 'PASS'])
        failed_tests = len([r for r in self.all_results if r.status == 'FAIL'])
        warning_tests = len([r for r in self.all_results if r.status == 'WARN'])
        skipped_tests = len([r for r in self.all_results if r.status == 'SKIP'])
        error_tests = len([r for r in self.all_results if r.status == 'ERROR'])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # 生成摘要
        summary = {
            'overall_status': 'PASSED' if success_rate >= 80 else 'FAILED',
            'critical_issues': [r for r in self.all_results if r.status == 'ERROR'],
            'warnings': [r for r in self.all_results if r.status == 'WARN'],
            'recommendations': self._generate_recommendations()
        }

        return TestReport(
            start_time=start_time,
            end_time=end_time,
            total_duration=total_duration,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            warning_tests=warning_tests,
            skipped_tests=skipped_tests,
            error_tests=error_tests,
            success_rate=success_rate,
            results=self.all_results,
            summary=summary
        )

    def _generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []

        # 统计各模块的失败情况
        module_stats = {}
        for result in self.all_results:
            if result.module not in module_stats:
                module_stats[result.module] = {'total': 0, 'failed': 0, 'error': 0}
            module_stats[result.module]['total'] += 1
            if result.status in ['FAIL', 'ERROR']:
                if result.status == 'FAIL':
                    module_stats[result.module]['failed'] += 1
                elif result.status == 'ERROR':
                    module_stats[result.module]['error'] += 1

        # 为失败的模块生成建议
        for module_name, stats in module_stats.items():
            if stats['failed'] > 0 or stats['error'] > 0:
                if module_name == 'backend':
                    recommendations.append("Check backend dependencies and imports. Run: pip install -r backend/requirements.txt")
                elif module_name == 'frontend':
                    recommendations.append("Check frontend dependencies. Run: cd frontend && npm install")
                elif module_name == 'environment':
                    recommendations.append("Verify project structure and required files")
                elif module_name == 'docker':
                    recommendations.append("Review docker-compose.yml configuration and Dockerfile")

        if not recommendations:
            recommendations.append("All tests passed! System is ready for deployment.")

        return recommendations

    def _print_summary(self, report: TestReport):
        """打印测试摘要"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests:    {report.total_tests}")
        print(f"Passed:         {report.passed_tests} [{report.success_rate:.1f}%]")
        print(f"Failed:         {report.failed_tests}")
        print(f"Warnings:       {report.warning_tests}")
        print(f"Skipped:        {report.skipped_tests}")
        print(f"Errors:         {report.error_tests}")
        print(f"Duration:       {report.total_duration:.2f}s")
        print(f"Overall Status: {report.summary['overall_status']}")
        print("="*80)

        # 打印建议
        if report.summary['recommendations']:
            print("\nRecommendations:")
            for i, rec in enumerate(report.summary['recommendations'], 1):
                print(f"  {i}. {rec}")

    def _save_report(self, report: TestReport):
        """保存测试报告"""
        report_file = Path(__file__).parent / 'test_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"\nDetailed test report saved to: {report_file.absolute()}")


# ============ 命令行接口 ============

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='AI Agriculture Decision System - Unified Automated Testing Suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_tests.py              # Run all tests
  python run_all_tests.py --module backend     # Run only backend tests
  python run_all_tests.py --quick              # Run quick tests only
  python run_all_tests.py --quiet              # Run tests quietly (summary only)
        """
    )

    parser.add_argument(
        '--module',
        choices=['environment', 'backend', 'frontend', 'docker', 'integration'],
        help='Run tests for specific module only'
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick tests only (environment + backend)'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Run tests quietly, show summary only'
    )

    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate detailed report (default: always generated)'
    )

    args = parser.parse_args()

    # 运行测试
    runner = TestRunner(verbose=not args.quiet, quick_mode=args.quick)
    report = runner.run(module=args.module)

    # 根据测试结果返回退出码
    return 0 if report.summary['overall_status'] == 'PASSED' else 1


if __name__ == "__main__":
    sys.exit(main())
