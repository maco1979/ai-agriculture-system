#!/bin/bash

# 部署脚本 - 构建和部署所有微服务

set -e

echo "=== AI农业平台微服务部署脚本 ==="

# 定义变量
REGISTRY="ai-platform"
NAMESPACE="ai-platform"

# 创建命名空间
echo "\n1. 创建命名空间..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# 创建密钥
echo "\n2. 创建密钥..."
kubectl create secret generic ai-platform-secrets \
  --namespace=$NAMESPACE \
  --from-literal=database-url=postgresql://ai_user:password@ai-platform-postgres:5432/ai_platform \
  --from-literal=redis-url=redis://ai-platform-redis:6379 \
  --from-literal=api-key=your-api-key-here \
  --from-literal=blockchain-api-key=your-blockchain-api-key-here \
  --from-literal=elasticsearch-url=http://ai-platform-elasticsearch:9200 \
  --dry-run=client -o yaml | kubectl apply -f -

# 构建和部署后端核心服务
echo "\n3. 构建和部署后端核心服务..."
docker build -t $REGISTRY/backend-core:latest ./backend-core
docker push $REGISTRY/backend-core:latest
kubectl apply -f ./infrastructure/kubernetes/microservices/backend-core-deployment.yaml

# 构建和部署API网关服务
echo "\n4. 构建和部署API网关服务..."
docker build -t $REGISTRY/api-gateway:latest ./api-gateway
docker push $REGISTRY/api-gateway:latest
kubectl apply -f ./infrastructure/kubernetes/microservices/api-gateway-deployment.yaml

# 构建和部署决策服务
echo "\n5. 构建和部署决策服务..."
docker build -t $REGISTRY/decision-service:latest ./decision-service
docker push $REGISTRY/decision-service:latest
kubectl apply -f ./infrastructure/kubernetes/microservices/decision-service-deployment.yaml

# 构建和部署边缘计算服务
echo "\n6. 构建和部署边缘计算服务..."
docker build -t $REGISTRY/edge-computing:latest ./edge-computing
docker push $REGISTRY/edge-computing:latest
kubectl apply -f ./infrastructure/kubernetes/microservices/edge-computing-deployment.yaml

# 构建和部署区块链集成服务
echo "\n7. 构建和部署区块链集成服务..."
docker build -t $REGISTRY/blockchain-integration:latest ./blockchain-integration
docker push $REGISTRY/blockchain-integration:latest
kubectl apply -f ./infrastructure/kubernetes/microservices/blockchain-integration-deployment.yaml

# 构建和部署监控服务
echo "\n8. 构建和部署监控服务..."
docker build -t $REGISTRY/monitoring-service:latest ./monitoring-service
docker push $REGISTRY/monitoring-service:latest
kubectl apply -f ./infrastructure/kubernetes/microservices/monitoring-service-deployment.yaml

# 构建和部署前端服务
echo "\n9. 构建和部署前端服务..."
docker build -t $REGISTRY/frontend-web:latest ./frontend-web
docker push $REGISTRY/frontend-web:latest
kubectl apply -f ./infrastructure/kubernetes/microservices/frontend-web-deployment.yaml

# 验证部署
echo "\n10. 验证部署..."
sleep 30
echo "\n查看所有Pod状态:"
kubectl get pods -n $NAMESPACE
echo "\n查看所有服务状态:"
kubectl get services -n $NAMESPACE
echo "\n查看所有HPA状态:"
kubectl get hpa -n $NAMESPACE
echo "\n=== 部署完成 ==="
