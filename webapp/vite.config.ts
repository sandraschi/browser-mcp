import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    allowedHosts: ['goliath'],
    port: 10777,
    proxy: {
      '/health': { target: 'http://127.0.0.1:10776', changeOrigin: true },
      '/mcp': { target: 'http://127.0.0.1:10776', changeOrigin: true },
      '/api': { target: 'http://127.0.0.1:10776', changeOrigin: true },
    },
  },
});
