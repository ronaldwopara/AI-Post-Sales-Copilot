import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Send all requests starting with /api ot root to the backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      
      
    }
  }
})