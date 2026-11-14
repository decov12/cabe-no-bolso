import axios from "axios";

// Cliente único para falar com o backend. O endereço vem do arquivo .env.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

// Se a pessoa estiver logada, envia o token em toda chamada.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Token ${token}`;
  return config;
});

export default api;
