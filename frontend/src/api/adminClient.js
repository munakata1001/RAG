import axios from "axios";

const baseURL = import.meta.env.VITE_ADMIN_API_BASE ?? "http://localhost:8000/admin";

export const adminApi = axios.create({
  baseURL,
  timeout: 60000,
});


