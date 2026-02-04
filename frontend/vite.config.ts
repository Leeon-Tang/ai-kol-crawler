import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8501',
        changeOrigin: true,
        secure: false,
        // 添加错误处理，避免控制台刷屏
        configure: (proxy) => {
          proxy.on('error', () => {
            // 静默处理代理错误
          })
        },
      },
      '/ws': {
        target: 'ws://localhost:8501',
        ws: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    // 代码分割优化
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'antd-vendor': ['antd', '@ant-design/icons'],
          'chart-vendor': ['recharts'],
          'motion-vendor': ['framer-motion'],
        },
      },
    },
    // 压缩优化
    minify: 'esbuild', // 使用esbuild代替terser，更快
  },
})
