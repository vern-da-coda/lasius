import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import fs from 'fs';
import path from 'path';
import crypto from 'node:crypto';

// Polyfill crypto.hash for Node.js < 20.19.0 (introduced in Node 21.7 / 20.19)
if (typeof (crypto as any).hash !== 'function') {
  (crypto as any).hash = (algorithm: string, data: crypto.BinaryLike, outputEncoding?: crypto.BinaryToTextEncoding) => {
    return crypto.createHash(algorithm).update(data).digest(outputEncoding as any);
  };
}

const urdfMeshesDir = path.resolve(__dirname, '../../hardware/mechanics/export/urdf/meshes');

export default defineConfig({
  plugins: [
    vue(),
    {
      name: 'serve-and-bundle-freecad-v2-urdf-meshes',
      configureServer(server) {
        server.middlewares.use('/meshes', (req, res, next) => {
          const cleanUrl = (req.url || '').split('?')[0].replace(/^\/+/, '');
          const safeName = path.basename(cleanUrl);
          if (!safeName.endsWith('.stl')) {
            return next();
          }
          const filePath = path.join(urdfMeshesDir, safeName);
          if (fs.existsSync(filePath)) {
            res.setHeader('Content-Type', 'model/stl');
            res.setHeader('Cache-Control', 'public, max-age=3600');
            fs.createReadStream(filePath).pipe(res);
            return;
          }
          next();
        });
      },
      closeBundle() {
        const outMeshesDir = path.resolve(__dirname, 'dist/meshes');
        if (!fs.existsSync(urdfMeshesDir)) return;
        fs.mkdirSync(outMeshesDir, { recursive: true });
        for (const entry of fs.readdirSync(urdfMeshesDir)) {
          if (entry.endsWith('.stl')) {
            fs.copyFileSync(
              path.join(urdfMeshesDir, entry),
              path.join(outMeshesDir, entry)
            );
          }
        }
      },
    },
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  base: './',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:8765',
        ws: true,
      },
    },
  },
});
