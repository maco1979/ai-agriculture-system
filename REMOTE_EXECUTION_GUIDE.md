# Remote Command Execution System - A2A Guide

## Overview

The Remote Command Execution System implements **A2A (Agent-to-Agent)** secure cross-machine command execution, similar to OpenClaw's architecture. This allows the main agricultural AI control center to remotely manage and control edge devices (cameras, sensors, compute nodes).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Main Control Center                          │
│                    (Agricultural AI System)                      │
│                         Port: 8001                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Remote Execution API  (/api/v1/remote/*)               │   │
│  │  - Execute commands on edge nodes                       │   │
│  │  - Batch execution across multiple nodes                │   │
│  │  - Command presets for common operations                │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ A2A Secure Transport
                           │ (Encrypted + Signed)
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Edge Node 1  │ │ Edge Node 2  │ │ Edge Node 3  │
│  Camera      │ │  Sensor      │ │  Compute     │
│  Port: 18790 │ │  Port: 18791 │ │  Port: 18792 │
└──────────────┘ └──────────────┘ └──────────────┘
```

## Security Features

### 1. Command Whitelist
Commands are categorized by permission levels:
- **READONLY**: `whoami`, `ls`, `cat`, `ps`, `top`, `df`, `free`
- **OPERATOR**: `systemctl restart`, `docker restart`, `git pull`
- **ADMIN**: `useradd`, `apt-get`, `chmod`, `iptables`
- **ROOT**: All commands allowed

### 2. Secure Transport (A2A)
- **Encryption**: Payloads are encrypted with HMAC-SHA256
- **Digital Signatures**: Commands are signed to verify authenticity
- **Replay Protection**: Timestamp-based nonce prevents replay attacks
- **Timeout**: 5-minute message validity window

### 3. Permission Validation
- Commands are validated against whitelist before execution
- Permission level is checked for each command
- Unauthorized commands are rejected with detailed logging

## API Endpoints

### Execute Remote Command
```http
POST /api/v1/remote/execute
Content-Type: application/json

{
  "target_node": "edge_001",
  "command": "python",
  "args": ["-c", "print('Hello from edge node')"],
  "timeout": 60,
  "require_sudo": false,
  "permission_level": "operator",
  "working_dir": "/opt/agriculture",
  "env_vars": {"LOG_LEVEL": "debug"}
}
```

**Response:**
```json
{
  "success": true,
  "command_id": "uuid-1234",
  "target_node": "edge_001",
  "status": "success",
  "stdout": "Hello from edge node\n",
  "stderr": "",
  "exit_code": 0,
  "execution_time": 0.523,
  "timestamp": "2026-03-26T12:00:00"
}
```

### Batch Execution
```http
POST /api/v1/remote/execute/batch
Content-Type: application/json

{
  "target_nodes": ["edge_001", "edge_002", "edge_003"],
  "command": "systemctl",
  "args": ["restart", "agriculture-agent"],
  "parallel": true,
  "permission_level": "operator"
}
```

### List Registered Nodes
```http
GET /api/v1/remote/nodes
```

### Get Node Status
```http
GET /api/v1/remote/nodes/{node_id}/status
```

### Execute Preset Command
```http
POST /api/v1/remote/presets/{preset_name}/execute?target_node=edge_001
```

### List Preset Commands
```http
GET /api/v1/remote/presets
```

## Available Presets

| Name | Description | Permission |
|------|-------------|------------|
| `查看系统状态` | System load, memory, disk usage | readonly |
| `查看磁盘空间` | Disk usage with `df -h` | readonly |
| `查看内存使用` | Memory usage with `free -h` | readonly |
| `查看GPU状态` | NVIDIA GPU status with `nvidia-smi` | readonly |
| `重启服务` | Restart a service with systemctl | operator |
| `查看服务日志` | View service logs | readonly |
| `清理临时文件` | Clean /tmp directory | operator |
| `获取摄像头快照` | Capture camera image | operator |
| `运行病虫害检测` | Run pest detection model | operator |
| `校准传感器` | Calibrate sensors | operator |
| `查看传感器数据` | Get latest sensor readings | readonly |

## Quick Start

### 1. Start the Main Server
```bash
cd D:\1.6\1.5\backend
python main.py
```
Server will start on http://localhost:8001

### 2. Start Edge Node Agent
```bash
cd D:\1.6\1.5\edge-computing\src\core
python edge_agent.py --node-id edge_001 --node-name "Greenhouse Camera 1"
```
Agent will start on http://localhost:18790

### 3. Register the Edge Node
```bash
curl -X POST http://localhost:8001/api/edge/nodes/register \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "edge_001",
    "address": "http://localhost:18790",
    "capabilities": {
      "device_type": "camera",
      "location": "Greenhouse A",
      "supports_inference": true
    }
  }'
```

### 4. Execute a Remote Command
```bash
# Using preset
curl -X POST "http://localhost:8001/api/v1/remote/presets/查看传感器数据/execute?target_node=edge_001"

# Custom command
curl -X POST http://localhost:8001/api/v1/remote/execute \
  -H "Content-Type: application/json" \
  -d '{
    "target_node": "edge_001",
    "command": "python",
    "args": ["-c", "print(\"Hello from edge!\")"],
    "permission_level": "operator"
  }'
```

### 5. Execute Batch Commands
```bash
curl -X POST http://localhost:8001/api/v1/remote/execute/batch \
  -H "Content-Type: application/json" \
  -d '{
    "target_nodes": ["edge_001", "edge_002", "edge_003"],
    "command": "systemctl",
    "args": ["status", "agriculture-agent"],
    "parallel": true,
    "permission_level": "readonly"
  }'
```

## Files Created

1. **`backend/src/services/remote_command.py`**
   - Core A2A secure transport
   - Command whitelist management
   - Remote command executor
   - Client SDK

2. **`edge-computing/src/core/edge_agent.py`**
   - Edge node agent
   - HTTP server for receiving commands
   - Heartbeat to main server
   - Command execution with security

3. **`backend/src/api/routes/remote_execution.py`**
   - REST API endpoints
   - Batch execution support
   - Command presets
   - Node management

4. **`test_remote_execution.py`**
   - Comprehensive test suite

5. **`demo_remote_execution.py`**
   - Interactive demonstration

## Configuration

### Environment Variables
```bash
# Secret key for A2A encryption (change in production!)
export REMOTE_EXECUTION_SECRET="your-secret-key-here"

# Main server URL (for edge agents)
export MAIN_SERVER_URL="http://localhost:8001"
```

### Edge Agent Configuration
Edit `edge_agent.py` or use command-line arguments:
```bash
python edge_agent.py \
  --node-id edge_001 \
  --node-name "Greenhouse Camera 1" \
  --server http://localhost:8001 \
  --secret your-secret-key \
  --port 18790
```

## Integration with WeChat/ClawBot

You can now send remote commands via WeChat messages:

```
/remote edge_001 "查看传感器数据"
```

Or use preset commands:
```
/status edge_001
/restart edge_001 agriculture-agent
/snapshot edge_001
```

## Troubleshooting

### Node Not Found
- Ensure the node is registered: `POST /api/edge/nodes/register`
- Check node heartbeat: nodes must send heartbeat every 30 seconds

### Command Rejected
- Check permission level matches command whitelist
- Use higher permission level if needed

### Timeout Errors
- Increase `timeout` parameter (default: 60s, max: 3600s)
- Check network connectivity between main server and edge node

### Security Errors
- Verify secret key matches between main server and edge agent
- Check command signatures are valid
- Ensure timestamps are within 5-minute window

## Demo Output

```
======================================================================
   Remote Command Execution System - A2A Demo
======================================================================

[1] Testing Command Whitelist...
    'whoami' with readonly: ALLOWED
    'ls -la' with readonly: ALLOWED
    'rm -rf /' with readonly: DENIED
    'systemctl restart' with operator: ALLOWED

[2] Testing Secure Transport (A2A Encryption)...
    Original: {'command': 'whoami', 'target': 'edge_001'}
    Encrypted: 1774498360:dba7a883aca454f2:{"command": "whoami", ...
    Decrypted: {'command': 'whoami', 'target': 'edge_001'}
    Match: True

[3] Testing Local Command Execution...
    Status: success
    Output: Hello from Remote Execution!

[4] Testing Python Command Execution...
    Status: success
    Output: Python 3.14
Remote execution works!

[5] Testing Remote Command Client...
    Created command for edge_001
    Command ID: 4e9230c0-0751-4e4c-84ed-c57c0c107b22
    Signature: 950a45d74e2c41a7939a72b5bae169...

[6] Command History...
    Total commands executed: 2

======================================================================
   Demo Complete!
======================================================================
```

## Next Steps

1. Start the backend server
2. Start one or more edge agents
3. Register the edge nodes
4. Send commands via API or WeChat integration
5. Monitor execution through logs and heartbeats

For more details, see:
- `demo_remote_execution.py` - Interactive demo
- `test_remote_execution.py` - Full test suite
- OpenAPI docs at http://localhost:8001/docs
