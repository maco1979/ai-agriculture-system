# 火山引擎部署指南

## 概述

本指南帮助你将AI农业平台部署到火山引擎容器服务(VKE)。

## 前置要求

### 1. 安装必需工具

#### Windows PowerShell (管理员权限)

```powershell
# 安装 Docker Desktop
# 下载地址: https://www.docker.com/products/docker-desktop

# 安装 kubectl
# 方法1: 使用 Chocolatey
choco install kubernetes-cli

# 方法2: 直接下载
# 下载地址: https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/

# 验证安装
docker --version
kubectl version --client
```

### 2. 火山引擎准备工作

1. **注册火山引擎账号**
   - 访问: https://www.volcengine.com/
   - 完成实名认证

2. **创建容器镜像服务(CR)**
   - 进入火山引擎控制台 → 容器镜像服务
   - 创建命名空间: `ai-agriculture`
   - 记录访问凭证

3. **创建容器服务(VKE)**
   - 进入火山引擎控制台 → 容器服务
   - 创建Kubernetes集群
   - 选择地域: 建议北京(cn-beijing)
   - 节点配置: 建议至少3个节点，ecs.g2i.xlarge规格

4. **配置kubectl访问**
   ```powershell
   # 在VKE控制台下载kubeconfig文件
   # 设置环境变量
   $env:KUBECONFIG = "C:\path\to\your\kubeconfig"
   
   # 验证连接
   kubectl cluster-info
   ```

## 部署步骤

### 方式一: 使用自动化脚本 (推荐)

1. **打开 PowerShell，进入项目目录**
   ```powershell
   cd d:\1.6\1.5
   ```

2. **运行部署脚本**
   ```powershell
   # 使用 PowerShell 执行
   .\volcengine-deploy.ps1
   
   # 或使用 Git Bash
   bash volcengine-deploy.sh
   ```

### 方式二: 手动部署

#### 步骤1: 登录火山引擎镜像仓库

```powershell
# 解码密码并登录
$password = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("WmpJNVl6QXpORGt6TXpoak5HWTJZemt3T1RaaU1HVmxPRFV3WkRZNVlUQQ=="))
docker login cr.volcengine.com -u volcen -p $password
```

#### 步骤2: 构建Docker镜像

```powershell
# 构建后端核心镜像
docker build -t cr.volcengine.com/ai-agriculture/backend-core:latest -f backend/Dockerfile backend/

# 构建API网关镜像(如果存在)
docker build -t cr.volcengine.com/ai-agriculture/api-gateway:latest microservices/api-gateway/

# 构建前端镜像(如果存在)
docker build -t cr.volcengine.com/ai-agriculture/frontend-web:latest microservices/frontend-web/

# 构建决策服务镜像(如果存在)
docker build -t cr.volcengine.com/ai-agriculture/decision-service:latest decision-service/
```

#### 步骤3: 推送镜像到火山引擎

```powershell
# 推送所有镜像
docker push cr.volcengine.com/ai-agriculture/backend-core:latest
docker push cr.volcengine.com/ai-agriculture/api-gateway:latest
docker push cr.volcengine.com/ai-agriculture/frontend-web:latest
docker push cr.volcengine.com/ai-agriculture/decision-service:latest
```

#### 步骤4: 部署到Kubernetes

```powershell
# 应用部署配置
kubectl apply -f volcengine-deployment.yaml

# 查看部署状态
kubectl get pods -n ai-agriculture
kubectl get services -n ai-agriculture
kubectl get ingress -n ai-agriculture
```

## 验证部署

### 1. 检查Pod状态

```powershell
kubectl get pods -n ai-agriculture
```

所有Pod应该显示 `Running` 状态。

### 2. 检查服务

```powershell
kubectl get services -n ai-agriculture
```

### 3. 获取访问地址

```powershell
# 查看Ingress分配的IP
kubectl get ingress -n ai-agriculture
```

访问地址格式:
- 前端: `http://<INGRESS_IP>/`
- API: `http://<INGRESS_IP>/api`
- 文档: `http://<INGRESS_IP>/docs`

## 故障排查

### Pod无法启动

```powershell
# 查看Pod日志
kubectl logs -n ai-agriculture <pod-name>

# 查看Pod详细状态
kubectl describe pod -n ai-agriculture <pod-name>
```

### 镜像拉取失败

```powershell
# 检查镜像仓库密钥
kubectl get secrets -n ai-agriculture

# 重新创建密钥
kubectl create secret docker-registry volcengine-registry-secret `
  --docker-server=cr.volcengine.com `
  --docker-username=volcen `
  --docker-password=<解码后的密码> `
  --namespace=ai-agriculture
```

### 服务无法访问

```powershell
# 检查服务状态
kubectl get svc -n ai-agriculture

# 检查Ingress状态
kubectl get ingress -n ai-agriculture
kubectl describe ingress -n ai-agriculture ai-agriculture-ingress
```

## 常用命令

```powershell
# 查看所有资源
kubectl get all -n ai-agriculture

# 进入Pod容器
kubectl exec -it -n ai-agriculture <pod-name> -- /bin/sh

# 扩缩容
kubectl scale deployment backend-core -n ai-agriculture --replicas=5

# 查看HPA状态
kubectl get hpa -n ai-agriculture

# 删除部署
kubectl delete -f volcengine-deployment.yaml
```

## 配置文件说明

| 文件 | 说明 |
|------|------|
| `volcengine-deployment.yaml` | Kubernetes部署配置 |
| `volcengine-deploy.sh` | Linux/Mac部署脚本 |
| `volcengine-deploy.ps1` | Windows PowerShell部署脚本 |
| `volcengine-config.yaml` | 部署参数配置 |

## 安全注意事项

1. **API密钥管理**: 生产环境请使用火山引擎密钥管理服务(KMS)
2. **数据库密码**: 建议定期更换，使用强密码
3. **网络隔离**: 配置安全组规则，限制访问来源
4. **HTTPS**: 生产环境务必配置SSL证书

## 成本优化建议

1. **使用抢占式实例**: 非关键服务可使用抢占式实例降低成本
2. **自动扩缩容**: 已配置HPA，根据负载自动调整
3. **定时伸缩**: 可配置定时任务，在低峰期减少节点

## 技术支持

- 火山引擎文档: https://www.volcengine.com/docs/
- VKE文档: https://www.volcengine.com/docs/6460/
- 镜像仓库文档: https://www.volcengine.com/docs/6563/
