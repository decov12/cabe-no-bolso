import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import api from "../api";
import Marca from "./Marca";

export default function BarraTopo() {
  const navigate = useNavigate();
  const [usuario, setUsuario] = useState(null);

  // Quem está logado, para mostrar ao lado do "Sair". Se falhar, a barra fica como antes.
  useEffect(() => {
    api.get("/api/auth/eu/")
      .then((resposta) => setUsuario(resposta.data))
      .catch(() => {});
  }, []);

  function sair() {
    localStorage.removeItem("token");
    navigate("/");
  }

  return (
    <nav className="navbar bg-white border-bottom px-4" style={{ height: 72 }}>
      <div className="d-flex align-items-center gap-4">
        <Marca para="/nova" />
        <NavLink to="/nova" className="nav-link fw-semibold">Nova simulação</NavLink>
        <NavLink to="/historico" className="nav-link fw-semibold">Histórico</NavLink>
      </div>
      <div className="d-flex align-items-center gap-3">
        {usuario && <span className="fw-semibold">{usuario.nome || usuario.email}</span>}
        <button className="btn btn-outline-secondary btn-sm" onClick={sair}>Sair</button>
      </div>
    </nav>
  );
}
