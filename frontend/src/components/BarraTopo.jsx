import { NavLink, useNavigate } from "react-router-dom";
import Marca from "./Marca";
import { sair } from "../api";

export default function BarraTopo() {
  const navigate = useNavigate();

  function aoSair() {
    sair();
    navigate("/");
  }

  return (
    <nav className="navbar bg-white border-bottom px-4" style={{ height: 72 }}>
      <div className="d-flex align-items-center gap-4">
        <Marca para="/nova" />
        <NavLink to="/nova" className="nav-link fw-semibold">Nova simulação</NavLink>
        <NavLink to="/historico" className="nav-link fw-semibold">Histórico</NavLink>
      </div>
      <button className="btn btn-outline-secondary btn-sm" onClick={aoSair}>Sair</button>
    </nav>
  );
}
