import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/search_applicant': 'http://127.0.0.1:5000',
      '/search_nearby': 'http://127.0.0.1:5000'
    }
  }
})


