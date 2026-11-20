import { Link } from "react-router-dom";
import Marca from "../components/Marca";

// Qualquer endereço que não existe cai aqui (por exemplo /resultado/abc ou um link antigo).
export default function NaoEncontrada() {
  const logado = Boolean(localStorage.getItem("token"));

  return (
    <div className="container py-5" style={{ maxWidth: 560 }}>
      <Marca para={logado ? "/nova" : "/"} />
      <h1 className="display-5 mt-5 mb-3">Essa página não existe</h1>
      <p className="fs-5 text-secondary mb-4">
        O endereço pode ter sido digitado errado ou a página foi removida.
      </p>
      <Link to={logado ? "/nova" : "/"} className="btn btn-sinal btn-lg px-4">
        {logado ? "Fazer uma simulação" : "Ir para o início"}
      </Link>
    </div>
  );
}
