# AI农业决策系统 × OpenClaw 接入指南

## 快速安装（3步）

### 步骤 1 — 安装 OpenClaw

```powershell
# Windows（PowerShell）
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

```bash
# macOS / Linux
curl -sSL https://openclaw.ai/install.sh | bash
openclaw onboard --install-daemon
```

> **前提**：Node.js 22+。OpenClaw 本身免费开源（MIT），AI 调用费用取决于你配置的模型服务商。

---

### 步骤 2 — 安装本项目 Skills

```bash
# 预览（不修改文件）
python openclaw-integration/install-to-openclaw.py --dry-run

# 正式安装
python openclaw-integration/install-to-openclaw.py
```

安装程序会自动将 5 个技能复制到 `~/.openclaw/workspace/skills/`。

---

### 步骤 3 — 启动后端服务

```bash
cd backend
python simple_api.py
# 服务运行在 http://localhost:8001
```

---

## 技能列表

| 技能 | 目录 | 触发场景示例 |
|------|------|------------|
| `ai-agriculture-system` | 系统总入口 | "检查农业系统状态"、"系统有什么功能" |
| `agriculture` | 农业决策 | "给番茄开花期生成光配方"、"预测生菜72小时生长" |
| `camera-ptz` | 摄像头/云台 | "转动摄像头向左"、"开始作物识别"、"设置预置位" |
| `ai-models` | AI模型管理 | "启动OrganicCore模型"、"用LightGBM做风险推理" |
| `system-monitor` | 系统/区块链/联邦 | "查看CPU使用率"、"区块链网络状态"、"注册联邦客户端" |

---

## 与 OpenClaw 对话示例

```
你：检查AI农业系统是否正常运行
OpenClaw：调用 check-system 脚本...
          ✅ 服务在线 | CPU 34% | 内存 58% | 7个模型就绪

你：给温室番茄（开花期，温度26℃，湿度60%）生成光配方
OpenClaw：调用农业API...
          红光 65%、蓝光 25%、绿光 10%
          推荐光强 300 PPFD，光周期 14小时

你：把摄像头01转到预置位3号（主要种植区）
OpenClaw：调用PTZ接口...
          ✅ 已跳转预置位 3（主要种植区）

你：查看区块链上 organic_core 模型的历史
OpenClaw：查询区块链...
          共 3 个版本：v1.0.0 → v1.1.0 → v1.2.0

你：把2个边缘节点注册为联邦学习客户端，然后开始训练
OpenClaw：注册 node_001、node_002...
          开始轮次 round_2026031501，目标模型：organic_core
```

---

## 目录结构

```
openclaw-integration/
├── install-to-openclaw.py     ← 一键安装脚本
├── openclaw-skills.json       ← skills配置片段（供手动合并）
├── README.md                  ← 本文档
└── skills/
    ├── ai-agriculture-system/ ← 系统总入口 + check脚本
    │   ├── SKILL.md
    │   ├── scripts/check-system.py
    │   └── references/api-reference.md
    ├── agriculture/           ← 农业决策
    │   ├── SKILL.md
    │   └── scripts/agriculture-api.py
    ├── camera-ptz/            ← 摄像头/PTZ
    │   ├── SKILL.md
    │   └── scripts/camera-control.py
    ├── ai-models/             ← AI模型管理
    │   ├── SKILL.md
    │   └── scripts/model-manager.py
    └── system-monitor/        ← 系统/区块链/联邦
        ├── SKILL.md
        └── scripts/
            ├── sysmon.py
            ├── blockchain.py
            └── federated.py
```

---

## 手动安装（不用安装脚本）

将 `skills/` 下的5个目录复制到你的 OpenClaw 工作区：

| 系统 | OpenClaw Skills 目录 |
|------|----------------------|
| Windows | `%USERPROFILE%\.openclaw\workspace\skills\` |
| macOS / Linux | `~/.openclaw/workspace/skills/` |

复制完成后重启 OpenClaw：`openclaw gateway restart`

---

## 常见问题

**Q: 后端服务未运行时，技能还能用吗？**  
A: OpenClaw 会提示服务不可达，并告知启动命令。

**Q: 没有真实摄像头/PTZ云台怎么办？**  
A: 系统自动降级为模拟模式，所有功能正常，返回仿真数据。

**Q: 区块链功能显示503？**  
A: Hyperledger Fabric 节点未启动，系统切换模拟模式，区块数据为随机生成，不影响其他功能。

**Q: 如何更新技能？**  
A: 重新运行 `python install-to-openclaw.py` 即可覆盖更新。
