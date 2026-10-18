import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// One origin in production: FastAPI serves `dist/` and a catch-all returns
// index.html (`SW-ADR-020`), so there is no CORS and the session cookie is
// first-party. In development Vite runs on its own port, so `/api` is PROXIED
// rather than fetched cross-origin — a cross-origin fetch would need
// credentials:'include' plus CORS plus SameSite=None, three things production
// does not have, and the dev setup would stop resembling the deployed one.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: false },
    },
  },
  build: {
    outDir: 'dist',
    // The API serves these from `/assets/`; the default hashed names are what
    // makes a long cache header safe on them and no-store correct on index.html.
    assetsDir: 'assets',
    // No source maps in the shipped bundle (F-S2): they republish the readable
    // client source — component names, comments, structure — to anyone who
    // opens devtools on the public site. Build them locally when debugging.
    sourcemap: false,
  },
})
