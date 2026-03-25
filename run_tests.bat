@echo off
chcp 65001 > nul
echo ================================================================================
echo   AI农业决策系统 - 快速测试启动器
echo ================================================================================
echo.

cd /d "%~dp0"

REM 菜单选择
echo 请选择要执行的测试：
echo.
echo [1] 运行所有测试
echo [2] 快速测试（环境+后端）
echo [3] 仅后端测试
echo [4] 仅前端测试
echo [5] 仅Docker测试
echo [6] 查看帮助
echo [0] 退出
echo.

set /p choice="请输入选项 (0-6): "

echo.

if "%choice%"=="1" (
    echo 运行所有测试...
    python run_all_tests.py
) else if "%choice%"=="2" (
    echo 运行快速测试...
    python run_all_tests.py --quick
) else if "%choice%"=="3" (
    echo 运行后端测试...
    python run_all_tests.py --module backend
) else if "%choice%"=="4" (
    echo 运行前端测试...
    python run_all_tests.py --module frontend
) else if "%choice%"=="5" (
    echo 运行Docker测试...
    python run_all_tests.py --module docker
) else if "%choice%"=="6" (
    echo 显示帮助信息...
    python run_all_tests.py --help
) else if "%choice%"=="0" (
    echo 退出...
    exit /b 0
) else (
    echo 无效选项，请重新运行脚本。
    pause
    exit /b 1
)

echo.
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo   测试完成！查看 test_report.html 获取详细报告
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo   测试发现失败或错误，请检查详细输出
    echo ================================================================================
)

echo.
pause
