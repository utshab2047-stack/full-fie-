import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server:  {
    proxy:  {
      '/api': {
        target: 'http://127.0.0.1:8001',  // Change to 8000 (run FastAPI on 8000)
        changeOrigin: true,
        secure: false,
      }
    }
  }
})