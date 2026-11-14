import { Link } from "react-router-dom";

// Logo do projeto. Use `claro` quando estiver sobre fundo escuro.
export default function Marca({ para = "/", claro = false }) {
  return (
    <Link to={para} className="marca" style={claro ? { color: "#fff" } : undefined}>
      <span className="marca-placa">?</span>
      Cabe no bolso
    </Link>
  );
}
