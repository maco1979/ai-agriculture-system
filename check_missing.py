import subprocess
import sys
import os

print("=" * 60)
print("项目缺失检查报告")
print("=" * 60)

# 检查Python依赖
print("\n【1. Python依赖检查】")
required_packages = [
    ('fastapi', 'Web框架'),
    ('uvicorn', 'ASGI服务器'),
    ('pydantic', '数据验证'),
    ('sqlalchemy', 'ORM'),
    ('psycopg2', 'PostgreSQL驱动'),
    ('redis', 'Redis客户端'),
    ('jax', 'JAX框架'),
    ('flax', 'Flax神经网络'),
    ('numpy', '数值计算'),
    ('pandas', '数据处理'),
    ('grpc', 'gRPC'),
    ('cryptography', '加密'),
    ('pyjwt', 'JWT'),
    ('opencv-python', 'OpenCV'),
    ('pyserial', '串口通信'),
]

missing_packages = []
for pkg, desc in required_packages:
    try:
        __import__(pkg.replace('-', '_').replace('opencv-python', 'cv2'))
        print(f"  [OK] {pkg} ({desc})")
    except ImportError:
        print(f"  [MISSING] {pkg} ({desc})")
        missing_packages.append(pkg)

# 检查外部服务
print("\n【2. 外部服务检查】")
services = [
    ('PostgreSQL', 5432),
    ('Redis', 6379),
]

for service, port in services:
    print(f"  ? {service} (端口 {port}) - 需要手动检查")

# 检查文件和目录
print("\n【3. 项目结构检查】")
required_paths = [
    ('backend/src', '后端源码'),
    ('backend/simple_api.py', '简化API'),
    ('frontend/src', '前端源码'),
    ('frontend/package.json', '前端配置'),
    ('frontend/node_modules', '前端依赖'),
]

for path, desc in required_paths:
    full_path = os.path.join(os.path.dirname(__file__), path)
    if os.path.exists(full_path):
        print(f"  [OK] {path} ({desc})")
    else:
        print(f"  [MISSING] {path} ({desc})")

# 检查关键配置文件
print("\n【4. 配置文件检查】")
config_files = [
    ('backend/.env', '后端环境配置'),
    ('frontend/.env', '前端环境配置'),
    ('backend/requirements.txt', 'Python依赖'),
    ('frontend/package.json', 'Node依赖'),
]

for path, desc in config_files:
    full_path = os.path.join(os.path.dirname(__file__), path)
    if os.path.exists(full_path):
        print(f"  [OK] {path} ({desc})")
    else:
        print(f"  [MISSING] {path} ({desc})")

# 总结
print("\n" + "=" * 60)
print("检查完成")
print("=" * 60)

if missing_packages:
    print(f"\n缺失的Python包: {', '.join(missing_packages)}")
    print("安装命令: pip install " + " ".join(missing_packages))
else:
    print("\n所有核心依赖已安装")

print("\n注意: PostgreSQL和Redis需要单独安装和配置")
