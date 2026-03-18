#!/bin/bash

# 火山引擎部署脚本
# 用于将AI农业平台部署到火山引擎容器服务(VKE)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
REGISTRY="cr.volcengine.com/ai-agriculture"
NAMESPACE="ai-agriculture"
VOLCENGINE_USERNAME="volcen"
VOLCENGINE_PASSWORD="WmpJNVl6QXpORGt6TXpoak5HWTJZemt3T1RaaU1HVmxPRFV3WkRZNVlUQQ=="

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  AI农业平台 - 火山引擎部署脚本${NC}"
echo -e "${BLUE}========================================${NC}"

# 检查必需工具（兼容 Windows Git Bash：同时检查带/不带 .exe 后缀）
echo -e "\n${YELLOW}[1/8] 检查必需工具...${NC}"
has_cmd() { command -v "$1" >/dev/null 2>&1 || command -v "$1.exe" >/dev/null 2>&1; }
has_cmd docker || { echo -e "${RED}错误: 需要Docker但未安装${NC}" >&2; exit 1; }
has_cmd kubectl || { echo -e "${RED}错误: 需要kubectl但未安装${NC}" >&2; exit 1; }
echo -e "${GREEN}✓ 所有必需工具已安装${NC}"

# 登录火山引擎镜像仓库
echo -e "\n${YELLOW}[2/8] 登录火山引擎镜像仓库...${NC}"
# 兼容 Linux (base64 -d) 和 macOS/Windows Git Bash (base64 -D)
DECODED_PWD=$(echo "$VOLCENGINE_PASSWORD" | base64 -d 2>/dev/null || echo "$VOLCENGINE_PASSWORD" | base64 -D 2>/dev/null)
echo "$DECODED_PWD" | docker login cr.volcengine.com -u "$VOLCENGINE_USERNAME" --password-stdin
echo -e "${GREEN}✓ 镜像仓库登录成功${NC}"

# 构建后端核心镜像
echo -e "\n${YELLOW}[3/8] 构建后端核心镜像...${NC}"
docker build -t $REGISTRY/backend-core:latest -f backend/Dockerfile backend/
docker tag $REGISTRY/backend-core:latest $REGISTRY/backend-core:$(date +%Y%m%d-%H%M%S)
echo -e "${GREEN}✓ 后端核心镜像构建完成${NC}"

# 构建API网关镜像
echo -e "\n${YELLOW}[4/8] 构建API网关镜像...${NC}"
if [ -d "microservices/api-gateway" ]; then
    docker build -t $REGISTRY/api-gateway:latest microservices/api-gateway/
    docker tag $REGISTRY/api-gateway:latest $REGISTRY/api-gateway:$(date +%Y%m%d-%H%M%S)
    echo -e "${GREEN}✓ API网关镜像构建完成${NC}"
else
    echo -e "${YELLOW}⚠ API网关目录不存在，跳过${NC}"
fi

# 构建前端镜像
echo -e "\n${YELLOW}[5/8] 构建前端镜像...${NC}"
if [ -d "microservices/frontend-web" ]; then
    docker build -t $REGISTRY/frontend-web:latest microservices/frontend-web/
    docker tag $REGISTRY/frontend-web:latest $REGISTRY/frontend-web:$(date +%Y%m%d-%H%M%S)
    echo -e "${GREEN}✓ 前端镜像构建完成${NC}"
else
    echo -e "${YELLOW}⚠ 前端目录不存在，跳过${NC}"
fi

# 构建决策服务镜像
echo -e "\n${YELLOW}[6/8] 构建决策服务镜像...${NC}"
if [ -d "decision-service" ]; then
    docker build -t $REGISTRY/decision-service:latest decision-service/
    docker tag $REGISTRY/decision-service:latest $REGISTRY/decision-service:$(date +%Y%m%d-%H%M%S)
    echo -e "${GREEN}✓ 决策服务镜像构建完成${NC}"
else
    echo -e "${YELLOW}⚠ 决策服务目录不存在，跳过${NC}"
fi

# 推送镜像到火山引擎
echo -e "\n${YELLOW}[7/8] 推送镜像到火山引擎镜像仓库...${NC}"
docker push $REGISTRY/backend-core:latest
echo -e "${GREEN}✓ 后端核心镜像推送完成${NC}"

if [ -d "microservices/api-gateway" ]; then
    docker push $REGISTRY/api-gateway:latest
    echo -e "${GREEN}✓ API网关镜像推送完成${NC}"
fi

if [ -d "microservices/frontend-web" ]; then
    docker push $REGISTRY/frontend-web:latest
    echo -e "${GREEN}✓ 前端镜像推送完成${NC}"
fi

if [ -d "decision-service" ]; then
    docker push $REGISTRY/decision-service:latest
    echo -e "${GREEN}✓ 决策服务镜像推送完成${NC}"
fi

# 部署到Kubernetes
echo -e "\n${YELLOW}[8/8] 部署到火山引擎Kubernetes集群...${NC}"

# 检查kubectl是否能连接到集群
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo -e "${RED}错误: 无法连接到Kubernetes集群${NC}"
    echo -e "${YELLOW}请确保:${NC}"
    echo -e "  1. 已配置kubectl访问火山引擎VKE集群"
    echo -e "  2. 已运行: kubectl config use-context <your-vke-cluster>"
    exit 1
fi

echo -e "${BLUE}当前集群:${NC}"
kubectl cluster-info

# 应用部署配置
echo -e "\n${BLUE}应用Kubernetes配置...${NC}"
kubectl apply -f volcengine-deployment.yaml

echo -e "${GREEN}✓ Kubernetes配置已应用${NC}"

# 等待部署完成
echo -e "\n${BLUE}等待部署完成...${NC}"
sleep 10

# 检查部署状态
echo -e "\n${YELLOW}部署状态检查:${NC}"
echo -e "\n${BLUE}Pods:${NC}"
kubectl get pods -n $NAMESPACE

echo -e "\n${BLUE}Services:${NC}"
kubectl get services -n $NAMESPACE

echo -e "\n${BLUE}Deployments:${NC}"
kubectl get deployments -n $NAMESPACE

echo -e "\n${BLUE}Ingress:${NC}"
kubectl get ingress -n $NAMESPACE

# 获取访问地址
echo -e "\n${YELLOW}访问地址:${NC}"
INGRESS_IP=$(kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "等待分配...")
echo -e "  前端地址: http://$INGRESS_IP"
echo -e "  API地址: http://$INGRESS_IP/api"
echo -e "  文档地址: http://$INGRESS_IP/docs"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  部署完成!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${YELLOW}常用命令:${NC}"
echo -e "  查看Pod日志: ${BLUE}kubectl logs -n $NAMESPACE <pod-name>${NC}"
echo -e "  进入Pod: ${BLUE}kubectl exec -it -n $NAMESPACE <pod-name> -- /bin/sh${NC}"
echo -e "  查看所有资源: ${BLUE}kubectl get all -n $NAMESPACE${NC}"
echo -e "  删除部署: ${BLUE}kubectl delete -f volcengine-deployment.yaml${NC}"
