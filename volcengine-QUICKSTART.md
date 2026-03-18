# 火山引擎快速部署指南

## 准备工作

### 1. 获取访问凭证

你已经提供了:
- **Access Key ID**: `[VOLCENGINE_ACCESS_KEY_ID]`
- **控制台地址**: https://console.volcengine.com/iam/keymanage

**你需要准备**:
- Secret Key (在控制台查看)
- 镜像仓库密码 (用于docker login)

### 2. 安装工具

```powershell
# 安装 Chocolatey (如果未安装)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 安装必需工具
choco install docker-desktop kubernetes-cli terraform -y
```

## 部署方式

### 方式一: 使用 PowerShell 脚本 (推荐)

#### 步骤1: 配置环境
```powershell
cd d:\1.6\1.5
.\volcengine-cli-setup.ps1
```
按提示输入Secret Key和KubeConfig文件路径。

#### 步骤2: 执行部署
```powershell
.\volcengine-deploy.ps1
```

### 方式二: 使用 Terraform (基础设施即代码)

#### 步骤1: 初始化Terraform
```powershell
cd d:\1.6\1.5\volcengine-terraform
terraform init
```

#### 步骤2: 配置变量
创建 `terraform.tfvars` 文件:
```hcl
secret_key = "你的SecretKey"
region     = "cn-beijing"
```

#### 步骤3: 创建基础设施
```powershell
terraform plan
terraform apply
```

#### 步骤4: 获取KubeConfig
```powershell
volcengine-cli vke cluster get-kubeconfig --cluster-id <cluster-id>
```

#### 步骤5: 部署应用
```powershell
cd d:\1.6\1.5
kubectl apply -f volcengine-deployment.yaml
```

### 方式三: 手动部署

#### 步骤1: 登录镜像仓库
```powershell
$password = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("WmpJNVl6QXpORGt6TXpoak5HWTJZemt3T1RaaU1HVmxPRFV3WkRZNVlUQQ=="))
docker login cr.volcengine.com -u volcen -p $password
```

#### 步骤2: 构建镜像
```powershell
cd d:\1.6\1.5

# 后端
docker build -t cr.volcengine.com/ai-agriculture/backend-core:latest -f backend/Dockerfile backend/

# API网关 (如果存在)
docker build -t cr.volcengine.com/ai-agriculture/api-gateway:latest microservices/api-gateway/

# 前端 (如果存在)
docker build -t cr.volcengine.com/ai-agriculture/frontend-web:latest microservices/frontend-web/
```

#### 步骤3: 推送镜像
```powershell
docker push cr.volcengine.com/ai-agriculture/backend-core:latest
docker push cr.volcengine.com/ai-agriculture/api-gateway:latest
docker push cr.volcengine.com/ai-agriculture/frontend-web:latest
```

#### 步骤4: 配置kubectl
```powershell
# 设置KubeConfig路径
$env:KUBECONFIG = "C:\path\to\your\kubeconfig"

# 验证连接
kubectl cluster-info
```

#### 步骤5: 部署到Kubernetes
```powershell
kubectl apply -f volcengine-deployment.yaml
```

## 验证部署

```powershell
# 查看所有资源
kubectl get all -n ai-agriculture

# 查看Pod状态
kubectl get pods -n ai-agriculture -w

# 查看服务
kubectl get svc -n ai-agriculture

# 查看Ingress
kubectl get ingress -n ai-agriculture
```

## 访问应用

获取访问地址:
```powershell
kubectl get ingress -n ai-agriculture
```

输出示例:
```
NAME                    CLASS   HOSTS   ADDRESS         PORTS   AGE
ai-agriculture-ingress  alb     *       180.x.x.x       80      5m
```

访问地址:
- 前端: `http://180.x.x.x/`
- API: `http://180.x.x.x/api`
- 文档: `http://180.x.x.x/docs`

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
kubectl describe ingress -n ai-agriculture ai-agriculture-ingress
```

## 清理资源

```powershell
# 删除Kubernetes部署
kubectl delete -f volcengine-deployment.yaml

# 使用Terraform销毁基础设施
cd volcengine-terraform
terraform destroy
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `volcengine-deployment.yaml` | Kubernetes部署配置 |
| `volcengine-deploy.ps1` | Windows部署脚本 |
| `volcengine-cli-setup.ps1` | CLI环境配置脚本 |
| `volcengine-config.yaml` | 部署参数配置 |
| `volcengine-terraform/` | Terraform基础设施代码 |
| `VOLCENGINE_DEPLOY_GUIDE.md` | 详细部署指南 |

## 技术支持

- 火山引擎文档: https://www.volcengine.com/docs/
- VKE文档: https://www.volcengine.com/docs/6460/
- 镜像仓库文档: https://www.volcengine.com/docs/6563/
