import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,              // exposes to all interfaces
    port: 5173,              // fixed port for Replit dev
    strictPort: true,        // ensures consistency
    watch: {
      usePolling: true       // helps hot-reload on cloud envs like Replit
    },
    allowedHosts: "all",    // allows *.replit.dev to access
    proxy: {
      '/api': 'http://localhost:5000' // proxy API calls to Flask backend
    }
  }
})
