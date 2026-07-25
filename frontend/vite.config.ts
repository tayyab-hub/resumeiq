// defineConfig comes from `vitest/config`, not `vite`: it is the same helper
// re-exported with the `test` option typed. A triple-slash reference alone no
// longer augments it in Vitest 2.
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    port: 5173,
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    // Recharts is ~537 kB raw (155 kB gzipped) and exceeds the default 500 kB
    // warning threshold. That is expected here rather than a problem: it is
    // split into its own chunk below and loaded only by the dashboard route,
    // so it never reaches a visitor who does not sign in.
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        // Keeps the charting library out of the initial bundle, which only
        // the dashboard needs.
        manualChunks: {
          charts: ['recharts'],
        },
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './tests/setup.ts',
    css: false,
  },
});
