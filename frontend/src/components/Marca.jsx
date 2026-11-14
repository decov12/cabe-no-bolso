import { Link } from "react-router-dom";

export default function Marca({ para = "/" }) {
  return (
    <Link to={para} className="marca">
      <span className="marca-placa">?</span>
      Cabe no bolso
    </Link>
  );
}
