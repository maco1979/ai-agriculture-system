#!/usr/bin/env python3
"""
项目启动脚本 - 正确配置并启动AI农业决策系统
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_step(step_num, total_steps, message):
    """打印步骤信息"""
    print(f"\n{Colors.BLUE}[{step_num}/{total_steps}]{Colors.END} {message}")

def print_success(message):
    """打印成功信息"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_warning(message):
    """打印警告信息"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_error(message):
    """打印错误信息"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print_error("需要Python 3.10或更高版本")
        return False
    print_success(f"Python版本检查通过: {version.major}.{version.minor}.{version.micro}")
    return True

def check_node_version():
    """检查Node.js版本"""
    try:
        result = subprocess.run(
            ['node', '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        version = result.stdout.strip()
        print_success(f"Node.js版本: {version}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_warning("Node.js未安装或版本过低")
        return False

def setup_backend():
    """配置后端环境"""
    print_step(1, 5, "配置后端环境")
    
    backend_dir = Path(__file__).parent / "backend"
    venv_dir = backend_dir / "venv312"
    
    # 检查虚拟环境
    if not venv_dir.exists():
        print_warning("创建Python虚拟环境...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        print_success("虚拟环境创建完成")
    else:
        print_success("虚拟环境已存在")
    
    print_success("后端环境配置完成")
    return True

def setup_frontend():
    """配置前端环境"""
    print_step(2, 5, "配置前端环境")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    if not (frontend_dir / "node_modules").exists():
        print_warning("安装前端依赖...")
        result = subprocess.run(
            ["npm", "install", "--registry", "https://registry.npmmirror.com"],
            cwd=str(frontend_dir),
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_success("前端依赖安装完成")
        else:
            print_error("前端依赖安装失败")
            return False
    else:
        print_success("前端依赖已存在")
    
    return True

def create_env_files():
    """创建环境配置文件"""
    print_step(3, 5, "创建环境配置文件")
    
    # 后端环境配置
    backend_env = Path(__file__).parent / "backend" / ".env"
    if not backend_env.exists():
        backend_env.write_text("""# 环境配置
ENVIRONMENT=development
LOG_LEVEL=INFO

# 服务器配置
HOST=0.0.0.0
PORT=8001

# 数据库配置 (可选)
# DATABASE_URL=postgresql://ai_user:ai_password@localhost:5432/ai_platform
# REDIS_URL=redis://localhost:6379/0

# 安全配置
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 硬件配置
SERIAL_PORT=COM1
BAUD_RATE=9600
""")
        print_success("后端环境配置文件创建完成")
    else:
        print_success("后端环境配置文件已存在")
    
    # 前端环境配置
    frontend_env = Path(__file__).parent / "frontend" / ".env"
    if not frontend_env.exists():
        frontend_env.write_text("""# 前端环境配置
VITE_API_BASE_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001

# 应用配置
VITE_APP_NAME=AI农业决策系统
VITE_APP_VERSION=1.0.0
VITE_DEBUG_MODE=true
""")
        print_success("前端环境配置文件创建完成")
    else:
        print_success("前端环境配置文件已存在")
    
    return True

def start_backend():
    """启动后端服务"""
    print_step(4, 5, "启动后端服务")
    
    backend_dir = Path(__file__).parent / "backend"
    venv_dir = backend_dir / "venv312"
    python_path = venv_dir / "Scripts" / "python.exe" if os.name == 'nt' else venv_dir / "bin" / "python"
    
    # 使用简单API启动
    simple_api = backend_dir / "simple_api.py"
    if simple_api.exists():
        print_warning("启动后端API服务 (端口: 8001)...")
        process = subprocess.Popen(
            [str(python_path), str(simple_api)],
            cwd=str(backend_dir),
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        print_success(f"后端服务已启动 (PID: {process.pid})")
        time.sleep(2)
        return process
    else:
        print_warning("simple_api.py不存在，尝试启动main.py...")
        main_py = backend_dir / "main.py"
        if main_py.exists():
            process = subprocess.Popen(
                [str(python_path), str(main_py)],
                cwd=str(backend_dir),
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            print_success(f"后端服务已启动 (PID: {process.pid})")
            time.sleep(2)
            return process
    
    print_error("无法找到后端启动文件")
    return None

def start_frontend():
    """启动前端服务"""
    print_step(5, 5, "启动前端服务")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    print_warning("启动前端开发服务器 (端口: 3000)...")
    process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(frontend_dir),
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
    )
    print_success(f"前端服务已启动 (PID: {process.pid})")
    return process

def print_access_info():
    """打印访问信息"""
    print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}  项目配置完成！{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"\n{Colors.BLUE}访问地址:{Colors.END}")
    print(f"  前端界面: http://localhost:3000")
    print(f"  后端API:  http://localhost:8001")
    print(f"  API文档:  http://localhost:8001/docs")
    print(f"\n{Colors.YELLOW}按 Ctrl+C 停止服务{Colors.END}")

def main():
    """主函数"""
    print(f"{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}  AI农业决策系统 - 项目配置与启动{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}")
    
    # 检查环境
    if not check_python_version():
        return 1
    check_node_version()
    
    # 配置项目
    setup_backend()
    setup_frontend()
    create_env_files()
    
    # 启动服务
    backend_process = start_backend()
    if not backend_process:
        print_error("后端服务启动失败")
        return 1
    
    frontend_process = start_frontend()
    if not frontend_process:
        print_error("前端服务启动失败")
        return 1
    
    # 打印访问信息
    print_access_info()
    
    # 等待用户中断
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}正在停止服务...{Colors.END}")
        backend_process.terminate()
        frontend_process.terminate()
        print_success("服务已停止")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
