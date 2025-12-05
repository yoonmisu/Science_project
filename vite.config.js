import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'styled-components', 'lucide-react']
  },
  build: {
    sourcemap: true,
    minify: 'esbuild'
  }
})
