// Electron Forge 配置
module.exports = {
  packagerConfig: {
    name: 'AI决策系统',
    executableName: 'ai-decision-system',
    icon: './src/assets/icon',
    arch: 'x64',
    platform: 'win32',
    asar: true
  },
  rebuildConfig: {},
  makers: [
    {
      name: '@electron-forge/maker-squirrel',
      config: {
        name: 'ai_decision_system',
        setupExe: 'AI决策系统安装.exe',
        setupIcon: './src/assets/icon.ico'
      }
    },
    {
      name: '@electron-forge/maker-zip',
      platforms: ['win32']
    }
  ],
  plugins: [
    {
      name: '@electron-forge/plugin-vite',
      config: {
        build: [],
        renderer: []
      }
    }
  ]
};
