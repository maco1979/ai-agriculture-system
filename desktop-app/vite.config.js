// Vite 配置文件
const { defineConfig } = require('vite');
const react = require('@vitejs/plugin-react');
const path = require('path');
const { createHash } = require('crypto');

// 生成内容哈希
function generateHash(content) {
  return createHash('md5').update(content).digest('hex').substring(0, 8);
}

// https://vitejs.dev/config/
module.exports = defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    open: false,
    // 启用 gzip 压缩
    compress: true,
    // 优化开发服务器响应
    hmr: {
      timeout: 30000,
    },
  },
  build: {
    outDir: 'dist-vite',
    emptyOutDir: true,
    minify: 'terser',
    sourcemap: false,
    // 优化构建输出
    rollupOptions: {
      output: {
        // 启用代码分割
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          ui: ['framer-motion'],
          utils: ['axios'],
        },
        // 配置资源缓存策略
        assetFileNames: 'assets/[name]-[hash].[ext]',
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
      },
    },
    // 优化 Terser 压缩
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        passes: 2,
      },
      mangle: {
        toplevel: true,
      },
    },
    // 配置缓存目录
    cacheDir: path.resolve(__dirname, '.vite-cache'),
  },
  // 优化依赖预构建
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'framer-motion', 'axios'],
    exclude: [],
    // 强制预构建所有依赖
    force: true,
  },
  // 静态资源处理
  assetsInclude: ['**/*.ico', '**/*.svg', '**/*.png', '**/*.jpg', '**/*.jpeg'],
  // 配置全局变量
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
  },
});
