import { NavLink, useNavigate } from "react-router-dom";
import Marca from "./Marca";

export default function BarraTopo() {
  const navigate = useNavigate();

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
      <button className="btn btn-outline-secondary btn-sm" onClick={sair}>Sair</button>
    </nav>
  );
}
