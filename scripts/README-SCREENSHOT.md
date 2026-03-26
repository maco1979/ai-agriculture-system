# AI农业决策系统 - 截图更新指南

## 快速开始（3步完成）

### 步骤1: 安装依赖

```bash
cd d:\1.6\1.5\scripts
npm install
```

### 步骤2: 截取界面

确保前端服务正在运行：
```bash
cd d:\1.6\1.5\frontend
npm run dev
```

然后执行截图脚本：
```bash
cd d:\1.6\1.5\scripts
npm run screenshot
```

脚本会自动：
- ✅ 连接前端服务（http://localhost:3001）
- ✅ 截取所有关键页面
- ✅ 生成全屏截图
- ✅ 保存到 `screenshots/` 目录

**截图列表：**
- `dashboard-full.png` - 智能仪表盘
- `agriculture-full.png` - AI农业分析
- `community-full.png` - AI智能体社区
- `tasks-full.png` - 任务管理
- `chat-full.png` - AI聊天助手

### 步骤3: 更新README图片

交互式脚本，引导你完成：

```bash
node update-readme-images.js
```

脚本会：
1. ✅ 检查截图文件
2. ✅ 指导你上传图片到GitHub
3. ✅ 收集图片链接
4. ✅ 生成README片段
5. ✅ 指导你更新README

## 完整流程示例

```bash
# 1. 安装依赖
cd d:\1.6\1.5\scripts
npm install

# 2. 截图（确保前端在运行）
npm run screenshot

# 3. 按提示更新README
node update-readme-images.js

# 4. 提交更改
cd d:\1.6\1.5
git add README.md screenshots/
git commit -m "docs: 更新界面截图"
git push origin main
```

## 手动操作（备选方案）

如果自动化脚本有问题，可以手动操作：

### 1. 手动截图

- 打开浏览器访问 http://localhost:3001
- 使用系统截图工具（Windows: Win+Shift+S）
- 截取关键页面

### 2. 上传图片到GitHub

1. 访问 https://github.com/maco1979/ai-agriculture-system/issues
2. 新建 Issue
3. 拖拽图片到评论框
4. 复制生成的Markdown链接
5. 关闭 Issue（不提交）

### 3. 更新README

编辑 `README.md`，替换：

```markdown
## 🖼️ 界面预览

> 截图即将更新...
```

为实际图片：

```markdown
## 🖼️ 界面预览

### 智能仪表盘 - 实时监控
显示农场实时数据、传感器状态、AI决策建议

<img src="https://github.com/user-attachments/assets/xxxxx" width="800" alt="仪表盘"/>

### AI农业分析 - 智能决策
光配方推荐、生长预测、种植计划

<img src="https://github.com/user-attachments/assets/xxxxx" width="800" alt="农业AI"/>

### AI智能体社区 - 自主讨论
5个AI角色自动发帖、讨论、回答专业问题

<img src="https://github.com/user-attachments/assets/xxxxx" width="800" alt="AI社区"/>

### 任务管理 - 自动化工作流
AI讨论后自动生成任务提案，推送微信等待用户审批

<img src="https://github.com/user-attachments/assets/xxxxx" width="800" alt="任务管理"/>

### AI聊天助手
与AI助手对话，获取专业的农业技术建议

<img src="https://github.com/user-attachments/assets/xxxxx" width="800" alt="聊天助手"/>
```

## 常见问题

### Q1: 截图脚本无法连接前端服务

**错误：** `无法连接到前端服务`

**解决：**
```bash
# 确保前端服务已启动
cd d:\1.6\1.5\frontend
npm run dev

# 检查端口
# 默认是3001，如果改了需要修改scripts/take-screenshots.js中的baseUrl
```

### Q2: puppeteer安装失败

**错误：** `无法安装puppeteer`

**解决：**
```bash
# 使用淘宝镜像
npm config set registry https://registry.npmmirror.com
npm install puppeteer

# 或者使用puppeteer-core（需要手动安装Chrome）
npm install puppeteer-core
```

### Q3: 截图质量不好

**解决：** 修改 `take-screenshots.js`：

```javascript
const CONFIG = {
  viewport: { width: 1920, height: 1080 },  // 增大分辨率
  animationDelay: 3000,  // 增加等待时间
  // ...
};
```

### Q4: 如何添加更多页面

编辑 `take-screenshots.js`：

```javascript
const PAGES_TO_CAPTURE = [
  // ...现有页面
  {
    name: 'newpage',
    path: '/new-page',
    title: '新页面标题',
    description: '页面描述',
  },
];
```

## 脚本说明

### take-screenshots.js

主要功能：
- 自动启动浏览器
- 访问前端页面
- 等待加载和动画完成
- 截取全屏图片
- 保存到screenshots目录

### update-readme-images.js

主要功能：
- 检查截图文件
- 交互式引导上传图片
- 收集GitHub图片链接
- 生成README片段
- 提供更新指导

## 技术栈

- **Puppeteer**: Chrome自动化工具
- **Node.js**: 脚本运行环境

## 注意事项

1. 截图时确保前端服务正在运行
2. 确保数据已加载（有内容可显示）
3. 截图质量取决于前端渲染效果
4. GitHub图片链接永久有效（只要不删除Issue）
5. 建议定期更新截图以反映最新界面

## 相关文件

- `scripts/take-screenshots.js` - 截图主脚本
- `scripts/update-readme-images.js` - README更新助手
- `scripts/package.json` - 依赖配置
- `screenshots/` - 截图输出目录

## 需要帮助？

如果脚本有问题，可以：
1. 查看 `screenshots/` 目录中的日志
2. 手动截图并上传
3. 联系开发团队

---

**提示**: 截图是展示项目的重要方式，建议每次重大更新后都更新截图！
