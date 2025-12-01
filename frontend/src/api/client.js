import axios from "axios";

// 開発環境ではViteのプロキシを使用、本番環境では環境変数から取得
const baseURL = import.meta.env.VITE_API_BASE ?? "/api";

export const api = axios.create({
  baseURL,
  timeout: 60000,
  headers: {
    "Content-Type": "application/json",
  },
});
 