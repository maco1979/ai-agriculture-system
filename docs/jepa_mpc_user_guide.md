# JEPA预测与自主MPC集成系统用户指南

## 1. 系统简介

JEPA预测与自主MPC集成系统是一种先进的智能控制解决方案，结合了深度学习预测能力和模型预测控制的优化能力，实现了更准确、更稳健的控制系统。

### 1.1 核心功能

- **JEPA预测**：基于深度学习的序列预测，能够捕获系统的复杂动态特性
- **MPC控制**：基于模型的预测控制，实现最优控制决策
- **智能融合**：将JEPA预测与MPC预测进行智能融合，提高预测准确性
- **自适应调整**：根据系统动态特性自动调整控制参数
- **鲁棒控制**：增强系统对扰动和不确定性的抵抗能力

### 1.2 系统要求

- **操作系统**：Windows 10/11, Linux, macOS
- **Python**：Python 3.12或更高版本
- **依赖库**：PyTorch, NumPy, SciPy, FastAPI, Uvicorn
- **硬件**：至少4GB RAM，推荐8GB以上

## 2. 快速开始

### 2.1 环境搭建

1. **安装Python 3.12**：从官网下载并安装Python 3.12
2. **克隆代码库**：`git clone <repository_url>`
3. **安装依赖**：
   ```bash
   cd <repository_directory>
   pip install -r requirements.txt
   ```

### 2.2 启动服务

1. **启动后端服务**：
   ```bash
   cd backend
   python start_server.py
   ```
   服务默认运行在 `http://localhost:8000`

2. **验证服务**：打开浏览器访问 `http://localhost:8000/docs`，查看API文档

## 3. API使用指南

### 3.1 激活控制器

**端点**：`POST /jepa-dtmpc/activate`

**请求示例**：

```json
{
  "controller_params": {
    "control_switch": true,
    "robust_control_switch": true,
    "adaptive_horizon_enabled": true
  },
  "mv_params": {
    "operation_range": [-100, 100],
    "rate_limits": [-10, 10],
    "action_cycle": 1.0
  },
  "cv_params": {
    "setpoint": 10.0,
    "safety_range": [-50, 50],
    "weights": 1.0
  },
  "model_params": {
    "prediction_horizon": 20,
    "control_horizon": 10,
    "system_gain": 2.0,
    "time_constant": 10,
    "time_delay": 1,
    "sampling_time": 1.0,
    "model_type": "fopdt"
  },
  "jepa_params": {
    "enabled": true,
    "embedding_dim": 10,
    "input_dim": 3,
    "output_dim": 1,
    "prediction_horizon": 20,
    "training_steps": 100
  }
}
```

**响应示例**：

```json
{
  "success": true,
  "message": "JEPA-DT-MPC控制器激活成功",
  "controller_info": {
    "jepa_enabled": true,
    "jepa_trained": false,
    "jepa_embedding_dim": 10,
    "jepa_input_dim": 3,
    "jepa_output_dim": 1,
    "jepa_prediction_horizon": 20,
    "mpc_prediction_horizon": 20,
    "mpc_control_horizon": 10
  }
}
```

### 3.2 训练模型

**端点**：`POST /jepa-dtmpc/train`

**请求示例**：

```json
{
  "training_data": {
    "description": "训练数据示例"
  },
  "training_steps": 100
}
```

**响应示例**：

```json
{
  "success": true,
  "message": "JEPA模型训练完成，共执行100步",
  "training_result": {
    "average_loss": 0.1234,
    "min_loss": 0.0567,
    "max_loss": 0.2345,
    "losses": [0.1567, 0.1432, ...]
  }
}
```

### 3.3 获取预测结果

**端点**：`GET /jepa-dtmpc/prediction`

**响应示例**：

```json
{
  "success": true,
  "message": "获取JEPA预测结果成功",
  "data": {
    "cv_prediction": [10.1, 10.2, 10.3, 10.4, 10.5],
    "jepa_prediction": [10.05, 10.15, 10.25, 10.35, 10.45],
    "fused_prediction": [10.1, 10.2, 10.3, 10.4, 10.5],
    "energy": 0.0876,
    "weight": 0.9154,
    "prediction_quality": 0.9154,
    "system_dynamics": {
      "rise_time": 5.2,
      "settling_time": 15.3,
      "overshoot": 2.1
    },
    "timestamp": 1702780860.123456
  }
}
```

### 3.4 获取控制器状态

**端点**：`GET /jepa-dtmpc/status`

**响应示例**：

```json
{
  "success": true,
  "message": "JEPA-DT-MPC控制器状态",
  "controller_status": {
    "jepa_enabled": true,
    "jepa_trained": true,
    "jepa_current_training_step": 100,
    "jepa_training_steps": 100,
    "mpc_state": {
      "prediction_horizon": 20,
      "control_horizon": 10,
      "current_state": [[10.1]]
    }
  }
}
```

### 3.5 保存模型

**端点**：`POST /jepa-dtmpc/model/save`

**请求示例**：

```json
{
  "model_name": "my_jepa_model",
  "description": "训练好的JEPA模型"
}
```

**响应示例**：

```json
{
  "success": true,
  "message": "模型保存成功: my_jepa_model",
  "model_path": "backend/jepa_models/my_jepa_model.pt"
}
```

### 3.6 加载模型

**端点**：`POST /jepa-dtmpc/model/load`

**请求示例**：

```json
{
  "model_name": "my_jepa_model"
}
```

**响应示例**：

```json
{
  "success": true,
  "message": "模型加载成功: my_jepa_model",
  "model_info": {
    "description": "训练好的JEPA模型",
    "timestamp": 1702780860.123456
  }
}
```

### 3.7 获取模型列表

**端点**：`GET /jepa-dtmpc/model/list`

**响应示例**：

```json
{
  "success": true,
  "message": "获取模型列表成功",
  "models": [
    {
      "name": "my_jepa_model",
      "description": "训练好的JEPA模型",
      "timestamp": 1702780860.123456,
      "size": 1234567,
      "jepa_params": {
        "enabled": true,
        "embedding_dim": 10,
        "input_dim": 3,
        "output_dim": 1,
        "prediction_horizon": 20,
        "trained": true,
        "training_steps": 100
      }
    }
  ]
}
```

## 4. 系统配置

### 4.1 控制器参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| control_switch | bool | true | 控制开关 |
| robust_control_switch | bool | true | 鲁棒控制开关 |
| adaptive_horizon_enabled | bool | false | 自适应时域开关 |
| prbs_amplitude | float | 20.0 | PRBS信号幅度 |
| prbs_period | int | 5 | PRBS信号周期 |
| prbs_steps | int | 100 | 自动测试总步数 |

### 4.2 MV参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| operation_range | array | [-100, 100] | 操作范围 |
| rate_limits | array | [-10, 10] | 速率限制 |
| action_cycle | float | 1.0 | 动作周期 |

### 4.3 CV参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| setpoint | float | 0.0 | 设定值 |
| safety_range | array | [-200, 200] | 安全范围 |
| weights | float | 1.0 | 权重 |

### 4.4 模型参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| prediction_horizon | int | 20 | 预测时域 |
| control_horizon | int | 10 | 控制时域 |
| system_gain | float | 1.0 | 系统增益 |
| time_constant | float | 5 | 时间常数 |
| time_delay | int | 1 | 时滞 |
| sampling_time | float | 1.0 | 采样时间 |
| model_type | string | "fopdt" | 模型类型 (fopdt/sopdt) |

### 4.5 JEPA参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| enabled | bool | true | JEPA启用开关 |
| embedding_dim | int | 10 | 嵌入维度 |
| input_dim | int | 3 | 输入维度 |
| output_dim | int | 1 | 输出维度 |
| prediction_horizon | int | 20 | 预测时域 |
| training_steps | int | 100 | 训练步数 |
| pretrained | bool | false | 是否预训练 |

## 5. 示例应用

### 5.1 工业温度控制

**场景**：控制工业炉温，设定值为800℃

**配置**：

```json
{
  "controller_params": {
    "control_switch": true,
    "robust_control_switch": true,
    "adaptive_horizon_enabled": true
  },
  "mv_params": {
    "operation_range": [0, 100],
    "rate_limits": [-5, 5],
    "action_cycle": 1.0
  },
  "cv_params": {
    "setpoint": 800.0,
    "safety_range": [700, 900],
    "weights": 1.0
  },
  "model_params": {
    "prediction_horizon": 30,
    "control_horizon": 15,
    "system_gain": 2.5,
    "time_constant": 20,
    "time_delay": 2,
    "sampling_time": 1.0,
    "model_type": "sopdt"
  },
  "jepa_params": {
    "enabled": true,
    "embedding_dim": 15,
    "input_dim": 3,
    "output_dim": 1,
    "prediction_horizon": 30,
    "training_steps": 200
  }
}
```

### 5.2 机器人轨迹控制

**场景**：控制机械臂末端执行器的位置

**配置**：

```json
{
  "controller_params": {
    "control_switch": true,
    "robust_control_switch": true,
    "adaptive_horizon_enabled": true
  },
  "mv_params": {
    "operation_range": [-10, 10],
    "rate_limits": [-2, 2],
    "action_cycle": 0.1
  },
  "cv_params": {
    "setpoint": 0.0,
    "safety_range": [-20, 20],
    "weights": 1.0
  },
  "model_params": {
    "prediction_horizon": 50,
    "control_horizon": 25,
    "system_gain": 1.5,
    "time_constant": 0.5,
    "time_delay": 0,
    "sampling_time": 0.1,
    "model_type": "sopdt"
  },
  "jepa_params": {
    "enabled": true,
    "embedding_dim": 20,
    "input_dim": 3,
    "output_dim": 1,
    "prediction_horizon": 50,
    "training_steps": 300
  }
}
```

## 6. 故障排除

### 6.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 服务启动失败 | 端口被占用 | 检查端口8000是否被占用，或修改配置文件使用其他端口 |
| API调用失败 | 控制器未激活 | 先调用 `/jepa-dtmpc/activate` 激活控制器 |
| 预测结果不准确 | JEPA模型未训练 | 先调用 `/jepa-dtmpc/train` 训练模型 |
| 模型保存失败 | 目录权限不足 | 确保 `jepa_models` 目录存在且有写入权限 |
| 系统响应缓慢 | 计算负载过高 | 减小预测时域或控制时域，或使用更强大的硬件 |

### 6.2 日志查看

后端服务日志默认输出到控制台，可以通过以下方式查看：

```bash
# 在启动服务的终端查看
# 或查看日志文件（如果配置了日志文件）
```

### 6.3 调试模式

启用调试模式可以查看更详细的日志：

```bash
# 修改 start_server.py 文件，设置 debug=True
uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)
```

## 7. 性能优化

### 7.1 模型优化

- **JEPA模型**：调整嵌入维度、隐藏层大小和训练步数
- **MPC模型**：根据系统特性选择合适的模型类型（FOPDT或SOPDT）
- **融合策略**：根据预测质量动态调整融合权重

### 7.2 算法优化

- **MPC求解**：使用更高效的优化算法
- **时域选择**：根据系统动态特性调整预测和控制时域
- **并行计算**：考虑使用多线程或GPU加速

### 7.3 硬件优化

- **CPU**：使用多核CPU提高计算性能
- **GPU**：如果有NVIDIA GPU，安装CUDA版本的PyTorch加速深度学习计算
- **内存**：确保有足够的内存存储模型和数据

## 8. 高级功能

### 8.1 多变量控制

系统支持扩展为多变量控制，需要修改以下配置：

1. **增加输入维度**：修改JEPA的 `input_dim` 参数
2. **增加输出维度**：修改JEPA的 `output_dim` 参数
3. **调整MPC模型**：使用多变量状态空间模型
4. **修改API接口**：支持多变量输入和输出

### 8.2 模型集成

可以将训练好的JEPA模型集成到其他系统中：

1. **导出模型**：使用 `torch.onnx.export` 导出为ONNX格式
2. **部署模型**：在其他平台或语言中加载和使用模型
3. **边缘部署**：将模型部署到边缘设备，实现本地控制

### 8.3 自定义预测模型

可以通过继承 `JEPA` 类自定义预测模型：

```python
class CustomJEPA(JEPA):
    def __init__(self, input_dim, embedding_dim, output_dim, prediction_horizon):
        super().__init__(input_dim, embedding_dim, output_dim, prediction_horizon)
        # 添加自定义层或修改现有层
    
    def forward(self, x, future_x=None):
        # 自定义前向传播逻辑
        pass
```

## 9. 总结

JEPA预测与自主MPC集成系统是一种先进的智能控制解决方案，结合了深度学习的预测能力和模型预测控制的优化能力，为各种控制场景提供了更准确、更稳健的控制效果。

通过本指南，您应该已经了解了系统的基本架构、API使用方法和配置选项。如果您有任何问题或需要进一步的帮助，请参考系统文档或联系开发团队。

祝您使用愉快！