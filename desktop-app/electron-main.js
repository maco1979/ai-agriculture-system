// Electron 主进程文件
const { app, BrowserWindow, ipcMain, Menu, protocol } = require('electron');
const path = require('path');
const url = require('url');
const { performance } = require('perf_hooks');

// 导入内存监控
const { memoryMonitor } = require('./src/services/memory/MemoryMonitor');

// 全局窗口引用
global.mainWindow = null;

// 启动时间监控
const startTime = performance.now();

// 窗口对象引用由全局变量管理

// 配置项
const config = {
  window: {
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600
  },
  preload: {
    enabled: true,
    scripts: []
  },
  devTools: process.env.ELECTRON_START_URL ? true : false
};

// 优化应用启动
app.commandLine.appendSwitch('disable-gpu-sandbox');
app.commandLine.appendSwitch('disable-features', 'OutOfBlinkCors');
app.commandLine.appendSwitch('disable-background-timer-throttling');

// 禁用硬件加速（如果需要）
// app.disableHardwareAcceleration();

// 注册文件协议以提高加载速度
function registerFileProtocol() {
  protocol.registerFileProtocol('app', (request, callback) => {
    const url = request.url.replace('app://', '');
    const pathName = path.join(__dirname, url);
    callback({ path: pathName });
  });
}

// 创建窗口函数
function createWindow() {
  const createWindowStart = performance.now();
  
  // 创建浏览器窗口
  global.mainWindow = new BrowserWindow({
    ...config.window,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true,
      // 预加载脚本
      preload: path.join(__dirname, 'src', 'preload.js'),
      // 禁用web安全（开发模式）
      webSecurity: !config.devTools,
      // 启用图像硬件加速
      backgroundThrottling: false
    },
    title: 'AI决策系统',
    icon: path.join(__dirname, 'src', 'assets', 'icon.ico'),
    // 隐藏窗口，等加载完成后再显示
    show: false,
    // 禁用默认菜单
    frame: true
  });

  // 加载应用
  const startUrl = process.env.ELECTRON_START_URL || url.format({
    pathname: path.join(__dirname, 'dist-vite', 'index.html'),
    protocol: 'file:',
    slashes: true
  });

  // 监听页面加载完成事件
  global.mainWindow.webContents.on('did-finish-load', () => {
    const loadFinishTime = performance.now();
    console.log(`窗口创建和加载时间: ${(loadFinishTime - createWindowStart).toFixed(2)}ms`);
    console.log(`总启动时间: ${(loadFinishTime - startTime).toFixed(2)}ms`);
    
    // 显示窗口
    global.mainWindow.show();
    
    // 打开开发者工具（开发模式）
    if (config.devTools) {
      global.mainWindow.webContents.openDevTools();
    }
    
    // 启动内存监控
    memoryMonitor.startMonitoring();
    console.log('内存监控已启动');
  });

  // 加载URL
  global.mainWindow.loadURL(startUrl);

  // 窗口关闭时触发
  global.mainWindow.on('closed', function () {
    // 取消引用窗口对象
    global.mainWindow = null;
  });

  // 创建应用菜单
  createMenu();
}

// 创建应用菜单
function createMenu() {
  const template = [
    {
      label: '文件',
      submenu: [
        {
          label: '退出',
          accelerator: process.platform === 'darwin' ? 'Command+Q' : 'Ctrl+Q',
          click() { app.quit(); }
        }
      ]
    },
    {
      label: '编辑',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectall' }
      ]
    },
    {
      label: '视图',
      submenu: [
        { role: 'reload' },
        { role: 'forcereload' },
        { role: 'toggledevtools' },
        { type: 'separator' },
        { role: 'resetzoom' },
        { role: 'zoomin' },
        { role: 'zoomout' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: '帮助',
      submenu: [
        {
          label: '关于',
          click() {
            // 可以添加关于对话框
            console.log('关于应用');
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// 预加载脚本
function createPreloadScript() {
  const preloadPath = path.join(__dirname, 'src', 'preload.js');
  const fs = require('fs');
  
  if (!fs.existsSync(preloadPath)) {
    const preloadContent = `
// 预加载脚本
const { contextBridge, ipcRenderer } = require('electron');

// 暴露API给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 系统信息
  getSystemInfo: () => {
    return {
      electronVersion: process.versions.electron,
      nodeVersion: process.versions.node,
      chromiumVersion: process.versions.chrome
    };
  },
  // 消息通信
  sendMessage: (message) => {
    ipcRenderer.send('message', message);
  },
  onMessage: (callback) => {
    ipcRenderer.on('reply', (event, arg) => callback(arg));
  },
  // 更新检查
  checkUpdate: () => {
    ipcRenderer.send('check-update');
  },
  onUpdateStatus: (callback) => {
    ipcRenderer.on('update-status', (event, arg) => callback(arg));
  }
});

// 预加载完成通知
console.log('Preload script loaded');
`;
    
    fs.writeFileSync(preloadPath, preloadContent);
  }
}

// Electron 完成初始化并准备创建浏览器窗口时触发
app.on('ready', () => {
  const readyTime = performance.now();
  console.log(`App ready time: ${(readyTime - startTime).toFixed(2)}ms`);
  
  // 注册文件协议
  registerFileProtocol();
  
  // 创建预加载脚本
  createPreloadScript();
  
  // 创建窗口
  createWindow();
});

// 关闭所有窗口时退出应用（Windows & Linux）
app.on('window-all-closed', function () {
  // 在 macOS 上，应用程序和菜单栏通常保持活动状态，直到用户使用 Cmd + Q 显式退出
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', function () {
  // 在 macOS 上，当单击 Dock 图标且没有其他窗口打开时，通常会重新创建一个窗口
  if (global.mainWindow === null) {
    createWindow();
  }
});

// 处理来自渲染进程的消息
ipcMain.on('message', (event, arg) => {
  console.log(arg);
  event.reply('reply', '消息已收到');
});

// 处理应用更新检查
ipcMain.on('check-update', (event) => {
  // 这里可以添加更新检查逻辑
  event.reply('update-status', { available: false, version: app.getVersion() });
});

// 处理性能监控
ipcMain.on('performance-monitor', (event, data) => {
  console.log('Performance data:', data);
});

// 处理内存监控相关的IPC消息
ipcMain.on('get-memory-info', (event) => {
  const memoryInfo = memoryMonitor.getMemoryInfo();
  const processMemoryInfo = memoryMonitor.getProcessMemoryInfo();
  event.reply('memory-info', { system: memoryInfo, process: processMemoryInfo });
});

// 停止内存监控
ipcMain.on('stop-memory-monitoring', () => {
  memoryMonitor.stopMonitoring();
  console.log('内存监控已停止');
});

// 启动内存监控
ipcMain.on('start-memory-monitoring', (event, interval) => {
  memoryMonitor.startMonitoring(interval);
  console.log(`内存监控已启动，间隔: ${interval}ms`);
});

// 启动完成
app.on('will-finish-launching', () => {
  const launchTime = performance.now();
  console.log(`Launching time: ${(launchTime - startTime).toFixed(2)}ms`);
});

// 应用退出时停止内存监控
app.on('before-quit', () => {
  memoryMonitor.stopMonitoring();
  console.log('内存监控已停止');
});
