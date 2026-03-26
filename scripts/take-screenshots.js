#!/usr/bin/env node

/**
 * 自动化截图脚本
 * 自动截取AI农业决策系统的主要界面，并生成README图片链接
 * 
 * 使用方法：
 *   cd scripts
 *   node take-screenshots.js
 * 
 * 需要先安装依赖：
 *   npm install puppeteer
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// 配置
const CONFIG = {
  baseUrl: 'http://localhost:3001',
  outputDir: path.join(__dirname, '../screenshots'),
  viewport: { width: 1920, height: 1080 },
  timeout: 30000,
  // 等待动画完成的延迟
  animationDelay: 2000,
  // 滚动画面的延迟
  scrollDelay: 500,
};

// 需要截图的页面
const PAGES_TO_CAPTURE = [
  {
    name: 'dashboard',
    path: '/',
    title: '智能仪表盘 - 实时监控',
    description: '显示农场实时数据、传感器状态、AI决策建议',
  },
  {
    name: 'agriculture',
    path: '/agriculture',
    title: 'AI农业分析 - 智能决策',
    description: '光配方推荐、生长预测、种植计划',
  },
  {
    name: 'community',
    path: '/community',
    title: 'AI智能体社区 - 自主讨论',
    description: '5个AI角色自动发帖、讨论、回答专业问题',
  },
  {
    name: 'tasks',
    path: '/tasks',
    title: '任务管理 - 自动化工作流',
    description: 'AI生成的任务提案，审批后自动执行',
  },
  {
    name: 'chat',
    path: '/chat-assistant',
    title: 'AI聊天助手',
    description: '与AI助手对话，获取农业专业建议',
  },
];

// 确保输出目录存在
function ensureOutputDir() {
  if (!fs.existsSync(CONFIG.outputDir)) {
    fs.mkdirSync(CONFIG.outputDir, { recursive: true });
    console.log('✅ 创建截图目录:', CONFIG.outputDir);
  }
}

// 等待页面完全加载
async function waitForPageLoad(page) {
  await page.waitForSelector('body', { timeout: CONFIG.timeout });
  await page.waitForNetworkIdle({ timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(CONFIG.animationDelay);
}

// 截取全屏（带滚动）
async function captureFullPage(page, name) {
  // 等待初始加载
  await waitForPageLoad(page);
  
  // 滚动到底部，触发懒加载
  await page.evaluate(() => {
    window.scrollTo(0, document.body.scrollHeight);
  });
  await page.waitForTimeout(CONFIG.scrollDelay);
  
  // 滚动回顶部
  await page.evaluate(() => {
    window.scrollTo(0, 0);
  });
  await page.waitForTimeout(CONFIG.scrollDelay);
  
  // 截图
  const screenshotPath = path.join(CONFIG.outputDir, `${name}-full.png`);
  await page.screenshot({
    path: screenshotPath,
    fullPage: true,
  });
  
  console.log(`  📸 全屏截图: ${name}-full.png`);
  return screenshotPath;
}

// 截取特定区域
async function captureRegion(page, name, selector) {
  try {
    await page.waitForSelector(selector, { timeout: 5000 });
    await page.waitForTimeout(500);
    
    const screenshotPath = path.join(CONFIG.outputDir, `${name}-region.png`);
    const element = await page.$(selector);
    if (element) {
      await element.screenshot({
        path: screenshotPath,
      });
      console.log(`  📸 区域截图: ${name}-region.png`);
      return screenshotPath;
    }
  } catch (error) {
    console.log(`  ⚠️  区域截图失败: ${name}`);
  }
  return null;
}

// 生成GitHub图片链接
async function generateImageLinks() {
  console.log('\n📝 生成GitHub图片链接说明...\n');
  console.log('=' .repeat(70));
  console.log('上传图片到GitHub并获取链接的步骤：');
  console.log('=' .repeat(70));
  console.log('\n1. 访问: https://github.com/maco1979/ai-agriculture-system/issues');
  console.log('2. 点击 "New Issue"');
  console.log('3. 将截图文件拖拽到评论框中');
  console.log('4. GitHub会自动上传并生成链接（格式：https://github.com/user-attachments/assets/xxxxxx）');
  console.log('5. 复制这些链接，更新到README.md中');
  console.log('\n' + '=' .repeat(70));
  
  // 生成README模板
  const readmeTemplate = generateReadmeTemplate();
  const templatePath = path.join(CONFIG.outputDir, 'README-images-template.md');
  fs.writeFileSync(templatePath, readmeTemplate);
  console.log(`\n✅ 已生成README模板: ${templatePath}`);
  console.log('\n将此模板内容复制到主README.md的"## 🖼️ 界面预览"部分\n');
}

// 生成README模板
function generateReadmeTemplate() {
  const images = PAGES_TO_CAPTURE.map(page => {
    const imageName = `${page.name}-full.png`;
    return `### ${page.title}
${page.description}

<!-- 将下面的链接替换为GitHub生成的实际链接 -->
<img src="https://github.com/user-attachments/assets/REPLACE_WITH_ACTUAL_ID_${page.name}" 
     width="800" 
     alt="${page.title}"/>

---`;
  }).join('\n\n');

  return `## 🖼️ 界面预览

${images}

> 💡 **提示**: 将上面的图片链接替换为实际上传到GitHub的链接
`;
}

// 主函数
async function main() {
  console.log('🌾 AI农业决策系统 - 自动化截图工具');
  console.log('=' .repeat(70));
  console.log(`基础URL: ${CONFIG.baseUrl}`);
  console.log(`输出目录: ${CONFIG.outputDir}`);
  console.log('=' .repeat(70));

  // 检查依赖
  try {
    require.resolve('puppeteer');
  } catch (error) {
    console.error('❌ 未找到puppeteer依赖');
    console.log('请先安装依赖:');
    console.log('  cd scripts');
    console.log('  npm install puppeteer');
    process.exit(1);
  }

  ensureOutputDir();

  let browser;
  try {
    console.log('\n🚀 启动浏览器...');
    browser = await puppeteer.launch({
      headless: true,
      defaultViewport: CONFIG.viewport,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });

    const page = await browser.newPage();

    // 测试连接
    console.log('🔗 测试连接...');
    try {
      await page.goto(CONFIG.baseUrl, { timeout: 10000, waitUntil: 'networkidle2' });
      console.log('✅ 成功连接到前端服务');
    } catch (error) {
      console.error('❌ 无法连接到前端服务');
      console.log('请确保前端服务已启动: npm run dev');
      console.log(`访问: ${CONFIG.baseUrl}`);
      await browser.close();
      process.exit(1);
    }

    // 截图所有页面
    for (const pageConfig of PAGES_TO_CAPTURE) {
      console.log(`\n📸 截图页面: ${pageConfig.title}`);
      
      const url = `${CONFIG.baseUrl}${pageConfig.path}`;
      await page.goto(url, { 
        timeout: CONFIG.timeout, 
        waitUntil: 'networkidle2' 
      });
      
      // 截图全屏
      await captureFullPage(page, pageConfig.name);
      
      // 特定页面的特殊截图
      if (pageConfig.name === 'dashboard') {
        await captureRegion(page, 'dashboard-stats', '.grid.grid-cols-2.md\\:grid-cols-4');
      }
      if (pageConfig.name === 'community') {
        await captureRegion(page, 'community-posts', '.space-y-4');
      }
    }

    await browser.close();
    
    console.log('\n✅ 所有截图完成！');
    
    // 生成图片链接说明
    await generateImageLinks();

  } catch (error) {
    console.error('\n❌ 截图过程中出错:', error);
    if (browser) {
      await browser.close();
    }
    process.exit(1);
  }
}

// 运行
if (require.main === module) {
  main();
}

module.exports = { main, CONFIG, PAGES_TO_CAPTURE };
