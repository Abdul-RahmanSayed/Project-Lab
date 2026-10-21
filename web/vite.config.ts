import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { apiOrigin } from './src/apiOrigin.ts';

const target = process.env.FDA_API_TARGET ?? 'http://127.0.0.1:8765';
const proxy = Object.fromEntries(['/api', '/readyz', '/healthz'].map(path => [path, { target }]));

export default defineConfig(({ mode }) => {
  const origin = apiOrigin(loadEnv(mode, process.cwd(), 'VITE_').VITE_FDA_API_ORIGIN);
  if (mode === 'deployment' && !origin) throw new Error('Deployment builds require VITE_FDA_API_ORIGIN.');
  return {
    plugins: [react()],
    base: './',
    server: { host: '127.0.0.1', port: 5173, strictPort: true, proxy },
    preview: { host: '127.0.0.1', port: 4173, strictPort: true, proxy },
    build: { sourcemap: false },
  };
});
