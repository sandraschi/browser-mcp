import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 10781,
    proxy: {
      '/health': {
        target: 'http://127.0.0.1:10780',
        changeOrigin: true,
      },
      '/mcp': {
        target: 'http://127.0.0.1:10780',
        changeOrigin: true,
      },
    },
  },
});
