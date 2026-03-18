"""
高性能服务器配置
支持Gunicorn + Uvicorn的多进程部署
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import multiprocessing
import uvicorn


def get_worker_count():
    """计算工作进程数
    
    基于CPU核心数和系统负载计算最优工作进程数
    通常使用 (2 * CPU核心数) + 1 的公式
    """
    cpu_count = multiprocessing.cpu_count()
    return min(32, (2 * cpu_count) + 1)


def get_uvicorn_config():
    """获取Uvicorn配置"""
    return {
        "host": os.getenv("HOST", "0.0.0.0"),
        "port": int(os.getenv("PORT", "8001")),
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
        "access_log": True,
        "use_colors": True,
        "loop": "uvloop",  # 使用uvloop提高性能（需要安装）
        "http": "httptools",  # 使用httptools提高性能（需要安装）
        "workers": int(os.getenv("WORKERS", get_worker_count())),
        "limit_concurrency": int(os.getenv("MAX_CONNECTIONS", "1000")),
        "timeout_keep_alive": int(os.getenv("KEEP_ALIVE_TIMEOUT", "5")),
        "limit_max_request_size": int(os.getenv("MAX_REQUEST_SIZE", "16777216")),  # 16MB
    }


def run_development_server():
    """运行开发服务器（单进程）"""
    print("🚀 启动开发服务器...")
    print(f"📍 监听地址: {os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '8001')}")
    print(f"📊 工作进程: 1 (开发模式)")
    print(f"🔧 日志级别: {os.getenv('LOG_LEVEL', 'info').lower()}")
    
    uvicorn.run(
        "src.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8001")),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        reload=True,  # 开发模式启用热重载
        access_log=True,
        use_colors=True
    )


def run_production_server():
    """运行生产服务器（多进程）"""
    config = get_uvicorn_config()
    
    print("🚀 启动生产服务器...")
    print(f"📍 监听地址: {config['host']}:{config['port']}")
    print(f"📊 工作进程: {config['workers']}")
    print(f"🔧 日志级别: {config['log_level']}")
    print(f"⚡ 最大并发连接: {config['limit_concurrency']}")
    print(f"⏱️  Keep-Alive超时: {config['timeout_keep_alive']}秒")
    
    uvicorn.run(
        "src.main:app",
        host=config["host"],
        port=config["port"],
        log_level=config["log_level"],
        access_log=config["access_log"],
        use_colors=config["use_colors"],
        workers=config["workers"],
        limit_concurrency=config["limit_concurrency"],
        timeout_keep_alive=config["timeout_keep_alive"],
        limit_max_request_size=config["limit_max_request_size"],
        loop=config["loop"],
        http=config["http"]
    )


def run_gunicorn_server():
    """运行Gunicorn + Uvicorn服务器（最高性能）"""
    print("🚀 启动Gunicorn + Uvicorn服务器...")
    print(f"📍 监听地址: {os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '8001')}")
    print(f"📊 工作进程: {get_worker_count()}")
    print(f"⚡ 最大并发连接: {os.getenv('MAX_CONNECTIONS', '1000')}")
    print(f"🔧 日志级别: {os.getenv('LOG_LEVEL', 'info').lower()}")
    
    # Gunicorn配置
    gunicorn_config = {
        "bind": f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '8001')}",
        "workers": get_worker_count(),
        "worker_class": "uvicorn.workers.UvicornWorker",
        "worker_connections": int(os.getenv("MAX_CONNECTIONS", "1000")),
        "max_requests": int(os.getenv("MAX_REQUESTS_PER_WORKER", "1000")),
        "max_requests_jitter": int(os.getenv("MAX_REQUESTS_JITTER", "100")),
        "timeout": int(os.getenv("TIMEOUT", "30")),
        "keepalive": int(os.getenv("KEEP_ALIVE_TIMEOUT", "5")),
        "loglevel": os.getenv("LOG_LEVEL", "info").lower(),
        "accesslog": os.getenv("ACCESS_LOG", "-"),
        "errorlog": os.getenv("ERROR_LOG", "-"),
        "reload": os.getenv("ENVIRONMENT", "production").lower() == "development",
        "daemon": False,
        "pidfile": os.getenv("PID_FILE", "gunicorn.pid"),
        "umask": 0o007,
        "user": None,
        "group": None,
        "tmp_upload_dir": None,
        "limit_request_line": int(os.getenv("MAX_REQUEST_LINE", "4094")),
        "limit_request_fields": int(os.getenv("MAX_REQUEST_FIELDS", "100")),
        "limit_request_field_size": int(os.getenv("MAX_REQUEST_FIELD_SIZE", "8190")),
    }
    
    # 构建Gunicorn命令行参数
    gunicorn_args = []
    for key, value in gunicorn_config.items():
        if value is not None and value != "":
            if isinstance(value, bool):
                if value:
                    gunicorn_args.append(f"--{key}")
            else:
                gunicorn_args.append(f"--{key}={value}")
    
    gunicorn_args.append("src.main:app")
    
    # 执行Gunicorn命令
    import subprocess
    try:
        subprocess.run(["gunicorn"] + gunicorn_args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Gunicorn启动失败: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Gunicorn未安装，请运行: pip install gunicorn")
        print("🔄 回退到Uvicorn多进程模式...")
        run_production_server()


def main():
    """主函数"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    server_type = os.getenv("SERVER_TYPE", "uvicorn").lower()
    
    print(f"🌍 环境: {environment}")
    print(f"🖥️  服务器类型: {server_type}")
    
    if environment == "development":
        # 开发环境：使用Uvicorn单进程+热重载
        run_development_server()
    else:
        # 生产环境：根据配置选择服务器
        if server_type == "gunicorn":
            # 使用Gunicorn + Uvicorn（最高性能）
            run_gunicorn_server()
        elif server_type == "uvicorn":
            # 使用Uvicorn多进程
            run_production_server()
        else:
            print(f"❌ 未知的服务器类型: {server_type}")
            print("🔄 使用默认的Uvicorn多进程模式...")
            run_production_server()


if __name__ == "__main__":
    main()