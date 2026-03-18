# AI农业平台 API 文档

## 1. 概述

本文档详细描述了AI农业平台各服务的API端点、请求参数、返回值和使用示例。平台采用微服务架构，包含以下核心服务：

- **backend-core**: 后端核心服务，提供AI模型管理、推理等功能
- **api-gateway**: API网关，负责服务路由和请求转发
- **decision-service**: 决策服务，提供智能决策功能
- **frontend-web**: 前端Web服务，提供用户界面
- **edge-computing**: 边缘计算服务，提供边缘设备管理和数据处理
- **blockchain-integration**: 区块链集成服务，提供区块链数据交互
- **monitoring-service**: 监控和日志服务，提供系统监控和日志管理

## 2. 通用规范

### 2.1 基础URL

各服务的基础URL格式为：

```
http://<服务名称>:<端口号>/
```

例如：
- backend-core: http://backend-core:8000/
- api-gateway: http://api-gateway:8080/

### 2.2 响应格式

所有API响应采用JSON格式，包含以下字段：

- `success`: 布尔值，表示请求是否成功
- `data`: 任意类型，包含请求成功时的数据
- `error`: 对象，包含请求失败时的错误信息
- `message`: 字符串，包含响应消息

**成功响应示例：**

```json
{
  "success": true,
  "data": { "key": "value" },
  "error": null,
  "message": "操作成功"
}
```

**失败响应示例：**

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": 400,
    "message": "参数错误"
  },
  "message": "操作失败"
}
```

### 2.3 错误码

| 错误码 | 描述 |
|--------|------|
| 400 | 参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

## 3. 服务API文档

### 3.1 backend-core 服务

#### 3.1.1 健康检查

- **端点**: `/health`
- **方法**: GET
- **描述**: 检查服务健康状态
- **返回值**: 服务健康状态信息

#### 3.1.2 服务信息

- **端点**: `/info`
- **方法**: GET
- **描述**: 获取服务信息
- **返回值**: 服务名称、版本等信息

#### 3.1.3 模型管理

- **端点**: `/api/models`
- **方法**: GET
- **描述**: 获取模型列表
- **返回值**: 模型列表

- **端点**: `/api/models`
- **方法**: POST
- **描述**: 创建新模型
- **参数**: 模型名称、描述、类型等
- **返回值**: 创建的模型信息

- **端点**: `/api/models/{id}`
- **方法**: GET
- **描述**: 获取模型详情
- **参数**: 模型ID
- **返回值**: 模型详细信息

- **端点**: `/api/models/{id}`
- **方法**: PUT
- **描述**: 更新模型信息
- **参数**: 模型ID、更新的字段
- **返回值**: 更新后的模型信息

- **端点**: `/api/models/{id}`
- **方法**: DELETE
- **描述**: 删除模型
- **参数**: 模型ID
- **返回值**: 删除结果

#### 3.1.4 推理服务

- **端点**: `/api/inference`
- **方法**: POST
- **描述**: 执行模型推理
- **参数**: 模型ID、输入数据
- **返回值**: 推理结果

### 3.2 api-gateway 服务

#### 3.2.1 健康检查

- **端点**: `/health`
- **方法**: GET
- **描述**: 检查服务健康状态
- **返回值**: 服务健康状态信息

#### 3.2.2 服务信息

- **端点**: `/info`
- **方法**: GET
- **描述**: 获取服务信息
- **返回值**: 服务名称、版本等信息

#### 3.2.3 服务状态

- **端点**: `/api/services/status`
- **方法**: GET
- **描述**: 获取所有服务状态
- **返回值**: 各服务的状态信息

### 3.3 decision-service 服务

#### 3.3.1 健康检查

- **端点**: `/health`
- **方法**: GET
- **描述**: 检查服务健康状态
- **返回值**: 服务健康状态信息

#### 3.3.2 服务信息

- **端点**: `/info`
- **方法**: GET
- **描述**: 获取服务信息
- **返回值**: 服务名称、版本等信息

#### 3.3.3 决策接口

- **端点**: `/api/decision`
- **方法**: POST
- **描述**: 执行决策
- **参数**: 决策类型、输入数据
- **返回值**: 决策结果

### 3.4 edge-computing 服务

#### 3.4.1 健康检查

- **端点**: `/health`
- **方法**: GET
- **描述**: 检查服务健康状态
- **返回值**: 服务健康状态信息

#### 3.4.2 服务信息

- **端点**: `/info`
- **方法**: GET
- **描述**: 获取服务信息
- **返回值**: 服务名称、版本等信息

#### 3.4.3 边缘节点管理

- **端点**: `/api/edge/nodes`
- **方法**: GET
- **描述**: 获取边缘节点列表
- **返回值**: 边缘节点列表

- **端点**: `/api/edge/tasks`
- **方法**: GET
- **描述**: 获取边缘任务列表
- **返回值**: 边缘任务列表

### 3.5 blockchain-integration 服务

#### 3.5.1 健康检查

- **端点**: `/health`
- **方法**: GET
- **描述**: 检查服务健康状态
- **返回值**: 服务健康状态信息

#### 3.5.2 服务信息

- **端点**: `/info`
- **方法**: GET
- **描述**: 获取服务信息
- **返回值**: 服务名称、版本等信息

#### 3.5.3 区块链状态

- **端点**: `/api/blockchain/status`
- **方法**: GET
- **描述**: 获取区块链状态
- **返回值**: 区块链状态信息

### 3.6 monitoring-service 服务

#### 3.6.1 健康检查

- **端点**: `/health`
- **方法**: GET
- **描述**: 检查服务健康状态
- **返回值**: 服务健康状态信息

#### 3.6.2 服务信息

- **端点**: `/info`
- **方法**: GET
- **描述**: 获取服务信息
- **返回值**: 服务名称、版本等信息

#### 3.6.3 监控指标

- **端点**: `/api/monitoring/metrics`
- **方法**: GET
- **描述**: 获取监控指标
- **返回值**: 监控指标数据

#### 3.6.4 告警管理

- **端点**: `/api/monitoring/alerts`
- **方法**: GET
- **描述**: 获取告警列表
- **返回值**: 告警列表

## 4. 认证与授权

### 4.1 API密钥认证

部分API需要API密钥认证，通过请求头传递：

```
Authorization: Bearer <API_KEY>
```

### 4.2 权限管理

系统实现了基于角色的权限管理（RBAC），包含以下角色：

- **admin**: 管理员，拥有所有权限
- **user**: 普通用户，拥有基本操作权限
- **guest**: 访客，拥有只读权限

## 5. 速率限制

为防止滥用，API网关实现了速率限制：

- 每个IP地址：15分钟内最多100个请求
- 每个API密钥：15分钟内最多500个请求

## 6. 监控与日志

### 6.1 健康检查

所有服务提供 `/health` 端点，用于监控服务健康状态。

### 6.2 指标采集

所有服务暴露Prometheus指标，采集以下数据：

- 请求计数和响应时间
- 错误率和类型
- 系统资源使用情况

### 6.3 日志管理

系统使用结构化日志，包含以下字段：

- `timestamp`: 时间戳
- `service`: 服务名称
- `level`: 日志级别
- `message`: 日志消息
- `metadata`: 附加元数据

## 7. 部署与扩展

### 7.1 Docker部署

所有服务支持Docker容器化部署，使用 `docker-compose` 可以快速启动整个系统。

### 7.2 Kubernetes部署

系统提供Helm charts，支持在Kubernetes集群中部署和管理。

### 7.3 水平扩展

所有服务支持水平扩展，通过增加实例数来提高系统容量。

## 8. 最佳实践

### 8.1 客户端实现

- 使用HTTP客户端库（如axios、fetch）发送请求
- 实现重试机制，处理临时网络故障
- 实现超时设置，避免请求阻塞
- 处理错误响应，提供友好的用户提示

### 8.2 服务集成

- 使用服务发现机制，动态获取服务地址
- 实现熔断和限流，提高系统稳定性
- 使用异步通信，提高系统吞吐量
- 实现监控和告警，及时发现和解决问题

## 9. 示例代码

### 9.1 调用backend-core推理API

```javascript
const axios = require('axios');

async function runInference(modelId, inputData) {
  try {
    const response = await axios.post('http://backend-core:8000/api/inference', {
      modelId,
      inputData
    });
    return response.data;
  } catch (error) {
    console.error('推理失败:', error);
    throw error;
  }
}

// 使用示例
runInference('model-001', { temperature: 25, humidity: 60 })
  .then(result => console.log('推理结果:', result))
  .catch(error => console.error('错误:', error));
```

### 9.2 调用decision-service决策API

```javascript
const axios = require('axios');

async function makeDecision(decisionType, inputData) {
  try {
    const response = await axios.post('http://decision-service:8001/api/decision', {
      type: decisionType,
      data: inputData
    });
    return response.data;
  } catch (error) {
    console.error('决策失败:', error);
    throw error;
  }
}

// 使用示例
makeDecision('irrigation', { soilMoisture: 30, weather: 'sunny' })
  .then(result => console.log('决策结果:', result))
  .catch(error => console.error('错误:', error));
```

## 10. 常见问题

### 10.1 服务不可用

- 检查服务是否运行
- 检查网络连接是否正常
- 检查服务配置是否正确

### 10.2 认证失败

- 检查API密钥是否正确
- 检查用户权限是否足够
- 检查认证服务是否正常运行

### 10.3 推理失败

- 检查模型是否存在
- 检查输入数据格式是否正确
- 检查模型服务是否正常运行

### 10.4 决策结果不准确

- 检查输入数据是否完整
- 检查决策模型是否需要更新
- 检查决策规则是否正确配置

## 11. 联系与支持

如有问题或建议，请联系：

- **Email**: support@ai-agriculture-platform.com
- **GitHub**: https://github.com/ai-agriculture-platform
- **Documentation**: https://docs.ai-agriculture-platform.com
