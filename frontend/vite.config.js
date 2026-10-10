import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // En dev, évite les soucis CORS : le front appelle /api/... et Vite
    // relaie vers Flask. En production, VITE_API_URL (voir .env.example)
    // pointe directement vers l'URL réelle de l'API.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
})
