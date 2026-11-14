import { useEffect } from "react";
import { Navigate, Outlet, useNavigate } from "react-router-dom";
import api from "../api";
import BarraTopo from "./BarraTopo";

// Moldura das telas que exigem login: barra do topo + a tela atual.
export default function LayoutLogado() {
  const navigate = useNavigate();
  const token = localStorage.getItem("token");

  // Se a API responder 401 (token apagado ou inválido), volta para o login.
  useEffect(() => {
    const id = api.interceptors.response.use(
      (resposta) => resposta,
      (erro) => {
        if (erro.response?.status === 401) {
          localStorage.removeItem("token");
          navigate("/entrar", { replace: true });
        }
        return Promise.reject(erro);
      },
    );
    return () => api.interceptors.response.eject(id);
  }, [navigate]);

  if (!token) return <Navigate to="/entrar" replace />;

  return (
    <>
      <BarraTopo />
      <main className="container py-5">
        <Outlet />
      </main>
    </>
  );
}
