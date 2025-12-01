import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default {
  plugins: [react()],
  resolve: {
    extensions: ['.js', '.jsx', '.json'],
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path, // パスをそのまま転送
      },
      '/admin': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path, // パスをそのまま転送
      },
    },
  },
};
