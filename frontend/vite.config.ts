/// <reference types="vitest/config" />
import { fileURLToPath, URL } from 'node:url';

import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  // Em desenvolvimento, /api é encaminhado ao FastAPI: o navegador vê uma única origem,
  // igual à produção (onde o FastAPI serve o build do React).
  const apiTarget = env.VITE_DEV_API_PROXY ?? 'http://localhost:8000';

  return {
    plugins: [react()],
    resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
    server: {
      host: true,
      port: 5173,
      proxy: { '/api': { target: apiTarget, changeOrigin: true } },
    },
    build: { outDir: 'dist', sourcemap: false },
    test: {
      environment: 'jsdom',
      setupFiles: ['./src/test/setup.ts'],
      globals: true,
    },
  };
});
