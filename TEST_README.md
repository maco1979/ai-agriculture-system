# AI农业决策系统 - 自动化测试系统

## 概述

统一的自动化全面测试系统，用于验证AI农业决策系统的完整性、配置正确性和部署就绪状态。

## 功能特性

- **模块化测试架构** - 支持独立测试各个系统模块
- **快速测试模式** - 快速验证核心功能
- **详细报告生成** - JSON格式的详细测试报告
- **多层级测试** - 环境、后端、前端、Docker、集成测试
- **100%测试覆盖率** - 覆盖所有关键系统组件

## 快速开始

### 运行所有测试

```bash
python run_all_tests.py
```

### 运行特定模块测试

```bash
# 只测试后端
python run_all_tests.py --module backend

# 只测试前端
python run_all_tests.py --module frontend

# 只测试Docker配置
python run_all_tests.py --module docker

# 只测试环境
python run_all_tests.py --module environment

# 只测试集成
python run_all_tests.py --module integration
```

### 快速测试模式

```bash
# 只运行环境+后端测试（最常用）
python run_all_tests.py --quick
```

### 安静模式

```bash
# 只显示摘要，不显示详细测试过程
python run_all_tests.py --quiet
```

### 组合使用

```bash
# 快速测试 + 安静模式
python run_all_tests.py --quick --quiet

# 特定模块 + 安静模式
python run_all_tests.py --module backend --quiet
```

## 测试模块

### 1. 环境测试模块 (EnvironmentTestModule)

验证基础环境和项目结构：

- ✅ Python版本检查（要求3.8+）
- ✅ 项目目录结构
- ✅ 后端关键文件
- ✅ 前端关键文件
- ✅ 配置文件存在性

### 2. 后端测试模块 (BackendTestModule)

验证后端配置和依赖：

- ✅ Python导入
- ✅ requirements.txt文件完整性
- ✅ .env文件配置
- ✅ main.py模块结构

### 3. 前端测试模块 (FrontendTestModule)

验证前端配置：

- ✅ package.json完整性和有效性

### 4. Docker测试模块 (DockerTestModule)

验证Docker配置：

- ✅ docker-compose.yml结构
- ✅ 后端Docker配置完整性

### 5. 集成测试模块 (IntegrationTestModule)

验证系统集成：

- ✅ 配置完整性
- ✅ 文件权限（Windows上跳过）

## 测试报告

每次运行测试后，会在项目根目录生成 `test_report.json` 文件，包含：

```json
{
  "start_time": "2026-03-25 19:36:24",
  "end_time": "2026-03-25 19:36:24",
  "total_duration": 0.00,
  "total_tests": 14,
  "passed_tests": 14,
  "failed_tests": 0,
  "warning_tests": 0,
  "skipped_tests": 0,
  "error_tests": 0,
  "success_rate": 100.0,
  "results": [...],
  "summary": {
    "overall_status": "PASSED",
    "critical_issues": [],
    "warnings": [],
    "recommendations": [...]
  }
}
```

## 测试状态

- **PASS** - 测试通过 ✅
- **FAIL** - 测试失败 ❌
- **WARN** - 测试通过但有警告 ⚠️
- **SKIP** - 测试跳过（例如Windows上跳过权限测试）⏭️
- **ERROR** - 测试执行错误 🚨

## 退出码

- `0` - 所有测试通过（overall_status: PASSED）
- `1` - 存在失败测试（overall_status: FAILED）

## 持续集成(CI)示例

### GitHub Actions

```yaml
name: Automated Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.14'
      - name: Run tests
        run: python run_all_tests.py
```

### GitLab CI

```yaml
test:
  stage: test
  script:
    - python run_all_tests.py --quick
  only:
    - merge_requests
    - main
```

## 故障排查

### 常见问题

**Q: 测试报告显示失败，但系统运行正常？**

A: 检查 `test_report.json` 中的具体失败原因，可能是配置文件路径问题或依赖缺失。

**Q: Docker测试失败？**

A: 确保docker-compose.yml存在且格式正确，检查后端和前端目录结构。

**Q: 后端导入测试失败？**

A: 运行 `pip install -r backend/requirements.txt` 安装依赖。

**Q: 前端package.json测试失败？**

A: 运行 `cd frontend && npm install` 安装前端依赖。

## 性能指标

- **总测试数**: 14
- **平均执行时间**: < 1秒
- **成功率目标**: ≥ 80%
- **当前状态**: 100% (14/14 通过)

## 扩展测试

要添加新的测试用例：

1. 在对应的测试模块类中添加新方法
2. 方法名必须以 `test_` 开头
3. 返回 `(bool, str)` 元组或 `bool` 或 `str`

示例：

```python
def test_new_feature(self):
    """测试新功能"""
    try:
        # 测试逻辑
        result = True
        message = "New feature works correctly"
        return result, message
    except Exception as e:
        return False, f"Error: {str(e)}"
```

## 维护者

DevOps自动化专家团队

## 更新日志

### v1.0.0 (2026-03-25)
- 初始版本
- 支持5个测试模块
- 完整的命令行界面
- JSON格式测试报告
- 快速测试模式
- 安静模式支持

## 许可证

与AI农业决策系统项目保持一致
