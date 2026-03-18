# 火山引擎 Terraform 配置
# 用于自动化创建VKE集群和相关资源

terraform {
  required_providers {
    volcengine = {
      source  = "volcengine/volcengine"
      version = "~> 0.0.1"
    }
  }
}

# 配置火山引擎Provider
provider "volcengine" {
  access_key = var.access_key_id
  secret_key = var.secret_key
  region     = var.region
}

# 变量定义
variable "access_key_id" {
  description = "火山引擎Access Key ID"
  type        = string
  default     = "[VOLCENGINE_ACCESS_KEY_ID]"
}

variable "secret_key" {
  description = "火山引擎Secret Key"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "地域"
  type        = string
  default     = "cn-beijing"
}

variable "cluster_name" {
  description = "VKE集群名称"
  type        = string
  default     = "ai-agriculture-cluster"
}

variable "namespace" {
  description = "Kubernetes命名空间"
  type        = string
  default     = "ai-agriculture"
}

# 获取默认VPC
 data "volcengine_vpcs" "default" {
  name_regex = "default"
}

# 获取默认子网
data "volcengine_subnets" "default" {
  vpc_id = data.volcengine_vpcs.default.vpcs[0].id
}

# 创建VKE集群
resource "volcengine_vke_cluster" "main" {
  name        = var.cluster_name
  description = "AI农业平台Kubernetes集群"
  
  # 集群配置
  kubernetes_version = "v1.28"
  
  # 网络配置
  # 避开常见 VPC 子网段（10.x, 172.16-31.x），使用独立网段
  pod_cidr     = "10.96.0.0/16"
  service_cidr = "10.112.0.0/16"
  
  # 日志配置
  logging_config {
    log_project_id = ""
    log_setups {
      enabled  = true
      log_type = "audit"
    }
  }
}

# 创建节点池
resource "volcengine_vke_node_pool" "main" {
  cluster_id = volcengine_vke_cluster.main.id
  name       = "default-node-pool"
  
  # 节点配置
  instance_type = "ecs.g2i.xlarge"  # 4核8G
  
  # 系统盘
  system_volume {
    type = "ESSD_PL0"
    size = 40
  }
  
  # 数据盘
  data_volumes {
    type = "ESSD_PL0"
    size = 100
  }
  
  # 网络配置
  subnet_ids = [data.volcengine_subnets.default.subnets[0].id]
  
  # 节点数量
  desired_nodes = 3
  min_nodes     = 3
  max_nodes     = 10
  
  # 标签
  labels {
    key   = "app"
    value = "ai-agriculture"
  }
  
  # 污点配置（可选）
  taints {
    key    = "dedicated"
    value  = "ai-agriculture"
    effect = "NoSchedule"
  }
}

# 创建容器镜像仓库命名空间
resource "volcengine_cr_namespace" "main" {
  name        = "ai-agriculture"
  description = "AI农业平台镜像仓库"
}

# 输出
output "cluster_id" {
  description = "VKE集群ID"
  value       = volcengine_vke_cluster.main.id
}

output "cluster_endpoint" {
  description = "集群API端点"
  value       = volcengine_vke_cluster.main.api_server_endpoint
}

output "kubeconfig_command" {
  description = "获取KubeConfig的命令"
  value       = "volcengine-cli vke cluster get-kubeconfig --cluster-id ${volcengine_vke_cluster.main.id}"
}

output "registry_endpoint" {
  description = "镜像仓库地址"
  value       = "cr.volcengine.com/ai-agriculture"
}
