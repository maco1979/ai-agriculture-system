#!/usr/bin/env python3
"""
AI 农业平台 - 火山引擎一键部署脚本
用法: python deploy-volcengine-auto.py [--skip-build] [--skip-push] [--dry-run]
"""

import argparse
import base64
import os
import subprocess
import sys
from pathlib import Path

# ─── 配置区（按需修改）─────────────────────────────────────────────
REGISTRY        = "cr.volcengine.com"
NAMESPACE_REPO  = "ai-agriculture"
REGISTRY_USER   = "volcen"
REGISTRY_PASS   = ""          # 留空则运行时提示输入（更安全）
K8S_NAMESPACE   = "ai-agriculture"
DEPLOYMENT_YAML = "volcengine-deployment.yaml"

# 生产环境配置（建议通过环境变量覆盖）
PROD_DB_URL   = os.getenv("PROD_DATABASE_URL",
                "postgresql://ai_user:ai_password@ai-agriculture-postgres:5432/ai_platform")
PROD_SECRET   = os.getenv("PROD_SECRET_KEY",
                "change-this-in-production-use-32chars!")
PROD_PG_PASS  = os.getenv("PROD_POSTGRES_PASSWORD", "ai_password")

IMAGES = {
    "backend-core": {
        "dockerfile": "backend/Dockerfile",
        "context":    "backend",
    },
    "api-gateway": {
        "dockerfile": "microservices/api-gateway/Dockerfile",
        "context":    "microservices/api-gateway",
    },
    "frontend-web": {
        "dockerfile": "microservices/frontend-web/Dockerfile",
        "context":    "microservices/frontend-web",
    },
}

# ─── 工具函数 ──────────────────────────────────────────────────────

def run(cmd: str, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    print(f"  $ {cmd}")
    return subprocess.run(
        cmd, shell=True, check=check,
        capture_output=capture, text=True
    )


def b64(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


def check_tool(name: str) -> bool:
    result = subprocess.run(f"where {name}", shell=True,
                            capture_output=True, text=True)
    ok = result.returncode == 0
    status = "OK" if ok else "NG"
    print(f"  [{status}] {name}")
    return ok


def patch_secrets():
    """在内存中替换 volcengine-deployment.yaml 中的占位 base64 值"""
    yaml_path = Path(DEPLOYMENT_YAML)
    content = yaml_path.read_text(encoding="utf-8")

    db_b64  = b64(PROD_DB_URL)
    sk_b64  = b64(PROD_SECRET)
    pg_b64  = b64(PROD_PG_PASS)

    # 替换占位符（与 YAML 中注释的 base64 占位值匹配）
    content = content.replace(
        "cG9zdGdyZXNxbDovL2FpX3VzZXI6YWlfcGFzc3dvcmRAYWktYWdyaWN1bHR1cmUtcG9zdGdyZXM6NTQzMi9haV9wbGF0Zm9ybQ==",
        db_b64
    )
    content = content.replace(
        "Y2hhbmdlLXRoaXMtaW4tcHJvZHVjdGlvbi0zMmNoYXJzKys=",
        sk_b64
    )
    content = content.replace(
        "YWlfcGFzc3dvcmQ=",
        pg_b64
    )

    patched_path = Path("volcengine-deployment-patched.yaml")
    patched_path.write_text(content, encoding="utf-8")
    print(f"  [OK] 生产 Secret 已写入 {patched_path}")
    return str(patched_path)


# ─── 部署步骤 ──────────────────────────────────────────────────────

def step_check_tools():
    print("\n[1/6] 检查依赖工具...")
    missing = []
    for tool in ["docker", "kubectl"]:
        if not check_tool(tool):
            missing.append(tool)
    if missing:
        print(f"\n[ERROR] 缺少工具: {missing}")
        print("  Docker: https://www.docker.com/products/docker-desktop")
        print("  kubectl: https://kubernetes.io/docs/tasks/tools/")
        sys.exit(1)

    # 检查 kubeconfig
    kube = Path.home() / ".kube" / "config"
    if not kube.exists():
        print(f"\n[WARN] 未找到 KubeConfig: {kube}")
        print("  请前往火山引擎控制台下载: https://console.volcengine.com/vke/cluster")
        print("  下载后保存到上述路径，kubectl 将自动识别")
    else:
        print(f"  [OK] kubeconfig: {kube}")

    # 验证 kubectl 连接
    result = run("kubectl cluster-info", check=False, capture=True)
    if result.returncode != 0:
        print("[WARN] 无法连接到 K8s 集群，请确认 KubeConfig 配置正确。继续执行...")
    else:
        print("  [OK] K8s 集群连接正常")


def step_registry_login(password: str):
    print(f"\n[2/6] 登录镜像仓库 {REGISTRY}...")
    run(f"docker login {REGISTRY} -u {REGISTRY_USER} -p {password}")
    print(f"  [OK] 镜像仓库登录成功")


def step_build_images(dry_run: bool):
    print("\n[3/6] 构建 Docker 镜像...")
    base = Path(__file__).parent
    for name, cfg in IMAGES.items():
        df   = base / cfg["dockerfile"]
        ctx  = base / cfg["context"]
        tag  = f"{REGISTRY}/{NAMESPACE_REPO}/{name}:latest"

        if not df.exists():
            print(f"  [SKIP] {name}: Dockerfile 不存在 ({df})")
            continue

        print(f"  构建 {name}...")
        cmd = f'docker build -t {tag} -f "{df}" "{ctx}"'
        if dry_run:
            print(f"  [DRY-RUN] {cmd}")
        else:
            run(cmd)
        print(f"  [OK] {name} 构建完成")


def step_push_images(dry_run: bool):
    print("\n[4/6] 推送镜像到火山引擎镜像仓库...")
    fmt = "{{.Repository}}:{{.Tag}}"
    result = run(f"docker images --format {fmt}", capture=True, check=False)
    existing = result.stdout.splitlines() if result.returncode == 0 else []

    for name in IMAGES:
        tag = f"{REGISTRY}/{NAMESPACE_REPO}/{name}:latest"
        if not any(tag in line for line in existing):
            print(f"  [SKIP] {name}: 本地镜像不存在，跳过推送")
            continue

        print(f"  推送 {name}...")
        cmd = f"docker push {tag}"
        if dry_run:
            print(f"  [DRY-RUN] {cmd}")
        else:
            run(cmd)
        print(f"  [OK] {name} 推送完成")


def step_create_registry_secret(password: str, dry_run: bool):
    print("\n  创建镜像仓库 Secret...")
    cmd = (
        f"kubectl create secret docker-registry registry-credentials"
        f" --docker-server={REGISTRY}"
        f" --docker-username={REGISTRY_USER}"
        f" --docker-password={password}"
        f" -n {K8S_NAMESPACE}"
        f" --dry-run=client -o yaml | kubectl apply -f -"
    )
    if dry_run:
        print(f"  [DRY-RUN] kubectl create secret docker-registry registry-credentials ...")
    else:
        run(cmd)
    print(f"  [OK] registry-credentials Secret 就绪")


def step_deploy(dry_run: bool):
    print(f"\n[5/6] 部署到 Kubernetes 集群（命名空间: {K8S_NAMESPACE}）...")

    patched_yaml = patch_secrets()

    cmd = f"kubectl apply -f {patched_yaml}"
    if dry_run:
        print(f"  [DRY-RUN] {cmd}")
        print(f"  [DRY-RUN] kubectl apply --dry-run=client -f {patched_yaml}")
        run(f"kubectl apply --dry-run=client -f {patched_yaml}", check=False)
    else:
        run(cmd)
    print(f"  [OK] 部署命令已执行")

    # 清理临时文件
    Path(patched_yaml).unlink(missing_ok=True)


def step_verify():
    print("\n[6/6] 等待 Pod 就绪（最多 120 秒）...")
    run(f"kubectl rollout status deployment/ai-agriculture-backend"
        f" -n {K8S_NAMESPACE} --timeout=120s", check=False)

    print("\n─── 部署状态 ─────────────────────────────────────────────")
    run(f"kubectl get pods -n {K8S_NAMESPACE}")
    print()
    run(f"kubectl get services -n {K8S_NAMESPACE}")
    print()
    run(f"kubectl get ingress -n {K8S_NAMESPACE}")

    # 获取 Ingress IP
    result = run(
        f'kubectl get ingress -n {K8S_NAMESPACE}'
        f' -o jsonpath="{{.items[0].status.loadBalancer.ingress[0].ip}}"',
        capture=True, check=False
    )
    ip = result.stdout.strip().strip('"')
    if ip:
        print(f"\n{'='*50}")
        print(f"  前端地址:  http://{ip}/")
        print(f"  API 地址:  http://{ip}/api/v1")
        print(f"  API 文档:  http://{ip}/docs")
        print(f"  健康检查:  http://{ip}/health")
        print(f"{'='*50}")
    else:
        print("\n  [INFO] Ingress IP 尚未分配，稍后运行:")
        print(f"  kubectl get ingress -n {K8S_NAMESPACE}")


# ─── 入口 ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI 农业平台 - 火山引擎一键部署")
    parser.add_argument("--skip-build", action="store_true", help="跳过镜像构建步骤")
    parser.add_argument("--skip-push",  action="store_true", help="跳过镜像推送步骤")
    parser.add_argument("--dry-run",    action="store_true", help="演练模式，不实际部署")
    parser.add_argument("--password",   default="",          help="镜像仓库密码（不传则提示输入）")
    args = parser.parse_args()

    print("=" * 55)
    print("  AI 农业平台 - 火山引擎 VKE 部署")
    print("=" * 55)
    if args.dry_run:
        print("  [!] DRY-RUN 模式: 不会实际修改集群")

    # 获取密码
    password = args.password or REGISTRY_PASS
    if not password and not args.dry_run:
        import getpass
        password = getpass.getpass(f"  请输入镜像仓库 {REGISTRY} 密码: ")

    step_check_tools()
    if not args.dry_run:
        step_registry_login(password)
    if not args.skip_build:
        step_build_images(args.dry_run)
    if not args.skip_push:
        step_push_images(args.dry_run)
    step_create_registry_secret(password, args.dry_run)
    step_deploy(args.dry_run)
    step_verify()

    print("\n[OK] 部署完成！")
    print("\n常用命令:")
    print(f"  查看 Pod 状态:  kubectl get pods -n {K8S_NAMESPACE}")
    print(f"  查看 Pod 日志:  kubectl logs -n {K8S_NAMESPACE} <pod-name> -f")
    print(f"  删除所有资源:   kubectl delete -f {DEPLOYMENT_YAML}")
    print(f"  扩容 backend:   kubectl scale deployment/ai-agriculture-backend"
          f" --replicas=3 -n {K8S_NAMESPACE}")


if __name__ == "__main__":
    main()
