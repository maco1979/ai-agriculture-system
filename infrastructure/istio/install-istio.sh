#!/bin/bash

# Istio安装脚本

set -e

echo "========================================"
echo "开始安装Istio服务网格"
echo "========================================"

# 检查是否安装了kubectl
if ! command -v kubectl &> /dev/null; then
    echo "错误: kubectl 未安装"
    exit 1
fi

# 检查Kubernetes集群状态
echo "检查Kubernetes集群状态..."
kubectl cluster-info

# 下载Istio
echo "下载Istio..."
curl -L https://istio.io/downloadIstio | sh -

# 进入Istio目录
ISTIO_DIR=$(find . -name "istio-*" -type d | head -1)
if [ -z "$ISTIO_DIR" ]; then
    echo "错误: 找不到Istio目录"
    exit 1
fi

echo "进入Istio目录: $ISTIO_DIR"
cd "$ISTIO_DIR"

export PATH="$PWD/bin:$PATH"

# 检查Istio版本
echo "检查Istio版本..."
istioctl version

# 安装Istio
echo "安装Istio (demo配置)..."
istioctl install --set profile=demo -y

# 验证安装
echo "验证Istio安装..."
kubectl get pods -n istio-system

# 启用自动Sidecar注入
echo "启用默认命名空间的自动Sidecar注入..."
kubectl label namespace default istio-injection=enabled

# 验证标签
echo "验证命名空间标签..."
kubectl get namespace default -L istio-injection

echo "========================================"
echo "Istio安装完成!"
echo "========================================"
echo ""
echo "下一步操作:"
echo "1. 部署你的应用到Kubernetes集群"
echo "2. 应用将自动获得Istio sidecar"
echo "3. 使用 istioctl dashboard grafana 查看监控"
echo "4. 使用 istioctl dashboard kiali 查看服务网格拓扑"
