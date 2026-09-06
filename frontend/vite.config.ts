import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_AUTHTWIN_API_URL || `http://${env.AUTHTWIN_API_HOST || '127.0.0.1'}:${env.AUTHTWIN_API_PORT || '5000'}`


  return {
    plugins: [react()],
    server: {
      port: Number(env.AUTHTWIN_FRONTEND_PORT || '5173'),
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
        }
      }
    }
  }
})
