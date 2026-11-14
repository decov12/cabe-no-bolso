import axios from "axios";

// Um único "cliente" para falar com o backend (Django).
// O endereço vem do arquivo .env (VITE_API_URL); se não tiver, usa o local.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

// Antes de cada pedido, anexa o token de login (se existir).
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Token ${token}`;
  return config;
});

// Se o backend disser "token inválido" (401), a sessão acabou: volta para o login.
api.interceptors.response.use(
  (resposta) => resposta,
  (erro) => {
    if (erro.response?.status === 401 && localStorage.getItem("token")) {
      sair();
      window.location.href = "/entrar";
    }
    return Promise.reject(erro);
  }
);

// --- Sessão (token guardado no navegador) ---

export function guardarSessao({ token, usuario }) {
  localStorage.setItem("token", token);
  localStorage.setItem("usuario", JSON.stringify(usuario));
}

export function sair() {
  localStorage.removeItem("token");
  localStorage.removeItem("usuario");
}

export function estaLogado() {
  return Boolean(localStorage.getItem("token"));
}

// --- Mensagem de erro em português para mostrar na tela ---
// O backend responde de jeitos diferentes: {"erro": "..."}, {"email": ["..."]},
// {"non_field_errors": ["..."]}. Esta função junta tudo em um texto só.
export function mensagemDeErro(erro) {
  if (!erro.response) {
    return "Não consegui falar com o servidor. Confira sua internet e tente de novo.";
  }
  const dados = erro.response.data;
  if (typeof dados === "string") return "Algo deu errado no servidor. Tente de novo em instantes.";
  if (dados?.erro) return dados.erro;
  if (dados?.detail) return dados.detail;

  const mensagens = Object.values(dados || {})
    .flat()
    .filter((m) => typeof m === "string");
  return mensagens.length > 0 ? mensagens.join(" ") : "Algo deu errado. Tente de novo.";
}

export default api;
