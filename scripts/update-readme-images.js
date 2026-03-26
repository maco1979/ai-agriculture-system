#!/usr/bin/env node

/**
 * README图片链接更新助手
 * 
 * 使用方法：
 *   node update-readme-images.js
 * 
 * 交互式脚本，引导你完成图片上传和README更新
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// 颜色输出
const colors = {
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  red: '\x1b[31m',
  reset: '\x1b[0m'
};

function log(color, msg) {
  console.log(`${color}${msg}${colors.reset}`);
}

// 提问函数
function question(query) {
  return new Promise(resolve => {
    rl.question(query, resolve);
  });
}

// 主流程
async function main() {
  log(colors.blue, '\n🌾 AI农业决策系统 - README图片更新助手');
  log(colors.blue, '=' .repeat(60));

  // 步骤1: 检查截图文件
  const screenshotsDir = path.join(__dirname, '../screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    log(colors.red, '❌ 未找到截图目录');
    log(colors.yellow, '请先运行: npm run screenshot');
    rl.close();
    return;
  }

  const files = fs.readdirSync(screenshotsDir).filter(f => f.endsWith('.png'));
  if (files.length === 0) {
    log(colors.red, '❌ 截图目录中没有图片文件');
    rl.close();
    return;
  }

  log(colors.green, `✅ 找到 ${files.length} 个截图文件`);
  files.forEach(f => log(colors.blue, `   - ${f}`));

  // 步骤2: 指导用户上传
  log(colors.yellow, '\n📤 步骤1: 上传截图到GitHub');
  log(colors.yellow, '-' .repeat(60));
  log(colors.reset, '1. 访问: https://github.com/maco1979/ai-agriculture-system/issues');
  log(colors.reset, '2. 点击 "New Issue"');
  log(colors.reset, '3. 将所有截图文件拖拽到评论框');
  log(colors.reset, '4. 等待上传完成，复制生成的Markdown链接');
  log(colors.reset, '5. 不要提交Issue，直接关闭页面');

  await question('\n📝 按回车键继续...');

  // 步骤3: 收集图片链接
  log(colors.yellow, '\n🔗 步骤2: 输入图片链接');
  log(colors.yellow, '-' .repeat(60));
  
  const images = [];
  const expectedImages = [
    { key: 'dashboard', name: '仪表盘 (dashboard-full.png)' },
    { key: 'agriculture', name: '农业AI (agriculture-full.png)' },
    { key: 'community', name: 'AI社区 (community-full.png)' },
    { key: 'tasks', name: '任务管理 (tasks-full.png)' },
    { key: 'chat', name: '聊天助手 (chat-full.png)' },
  ];

  for (const img of expectedImages) {
    const url = await question(`\n📎 请输入 ${img.name} 的GitHub链接:\n`);
    if (url && url.includes('github.com/user-attachments')) {
      images.push({
        key: img.key,
        name: img.name,
        url: url.trim()
      });
      log(colors.green, '✅ 已记录');
    } else {
      log(colors.red, '⚠️  链接格式可能不正确，已跳过');
    }
  }

  // 步骤4: 生成新的README内容
  log(colors.yellow, '\n📝 步骤3: 生成README内容');
  log(colors.yellow, '-' .repeat(60));

  const readmeContent = generateReadmeSection(images);
  const outputPath = path.join(__dirname, '../screenshots/updated-readme-section.md');
  fs.writeFileSync(outputPath, readmeContent);

  log(colors.green, `✅ 已生成README片段: ${outputPath}`);

  // 步骤5: 指导用户更新README
  log(colors.yellow, '\n📋 步骤4: 更新README.md');
  log(colors.yellow, '-' .repeat(60));
  log(colors.reset, '1. 打开: README.md');
  log(colors.reset, '2. 找到 "## 🖼️ 界面预览" 部分');
  log(colors.reset, '3. 用上面生成的内容替换原有内容');
  log(colors.reset, '4. 保存文件');
  log(colors.reset, '5. 提交更改并推送');
  log(colors.reset, '   git add README.md');
  log(colors.reset, '   git commit -m "docs: 更新界面截图"');
  log(colors.reset, '   git push origin main');

  log(colors.blue, '\n🎉 完成！');
  log(colors.blue, '=' .repeat(60));

  rl.close();
}

// 生成README片段
function generateReadmeSection(images) {
  const imageSections = images.map(img => {
    const title = getImageTitle(img.key);
    const desc = getImageDescription(img.key);
    
    return `### ${title}
${desc}

<img src="${img.url}" width="800" alt="${title}"/>

---`;
  }).join('\n\n');

  return `## 🖼️ 界面预览

${imageSections}
`;
}

function getImageTitle(key) {
  const titles = {
    dashboard: '智能仪表盘 - 实时监控',
    agriculture: 'AI农业分析 - 智能决策',
    community: 'AI智能体社区 - 自主讨论',
    tasks: '任务管理 - 自动化工作流',
    chat: 'AI聊天助手'
  };
  return titles[key] || '界面截图';
}

function getImageDescription(key) {
  const descriptions = {
    dashboard: '显示农场实时数据、传感器状态、AI决策建议',
    agriculture: '光配方推荐、生长预测、种植计划、环境参数分析',
    community: '5个AI角色自动发帖、讨论、回答专业问题，形成知识社区',
    tasks: 'AI讨论后自动生成任务提案，推送微信等待用户审批',
    chat: '与AI助手对话，获取专业的农业技术建议'
  };
  return descriptions[key] || '';
}

// 运行
if (require.main === module) {
  main();
}

module.exports = { main, generateReadmeSection };
