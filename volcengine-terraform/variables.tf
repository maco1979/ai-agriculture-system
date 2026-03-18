# Terraform 变量定义

variable "access_key_id" {
  description = "火山引擎Access Key ID"
  type        = string
  default     = "AKLTZWM5Y2Y2MTZhMWI2NDNmNmExNzk2ZmYwNzhmOTFkYWY"
}

variable "secret_key" {
  description = "火山引擎Secret Key"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "火山引擎地域"
  type        = string
  default     = "cn-beijing"
}

variable "availability_zone" {
  description = "可用区"
  type        = string
  default     = "cn-beijing-a"
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

variable "node_instance_type" {
  description = "节点实例类型"
  type        = string
  default     = "ecs.g2i.xlarge"  # 4核8G
}

variable "min_nodes" {
  description = "最小节点数"
  type        = number
  default     = 3
}

variable "max_nodes" {
  description = "最大节点数"
  type        = number
  default     = 10
}

variable "desired_nodes" {
  description = "期望节点数"
  type        = number
  default     = 3
}

variable "system_disk_size" {
  description = "系统盘大小(GB)"
  type        = number
  default     = 40
}

variable "data_disk_size" {
  description = "数据盘大小(GB)"
  type        = number
  default     = 100
}

variable "enable_auto_scaling" {
  description = "启用自动扩缩容"
  type        = bool
  default     = true
}

variable "tags" {
  description = "资源标签"
  type        = map(string)
  default = {
    Project     = "ai-agriculture"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}
