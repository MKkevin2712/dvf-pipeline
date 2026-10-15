import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// En développement, les appels à /api sont redirigés vers l'API FastAPI (uvicorn, port 8000)
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
})
