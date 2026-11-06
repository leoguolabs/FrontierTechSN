import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  build: mode === 'archive' ? { rolldownOptions: { input: 'archive.html' } } : undefined,
  server: {
    proxy: {
      '/api': 'http://localhost:8101',
      '/outputs': 'http://localhost:8101',
    },
  },
}))
