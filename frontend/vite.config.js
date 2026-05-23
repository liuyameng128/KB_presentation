import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      // 设置 @ 指向 src 目录，方便以后改代码
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    // 如果你希望局域网也能访问，可以加上 host: '0.0.0.0'
  }
})