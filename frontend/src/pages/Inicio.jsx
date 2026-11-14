import { Link } from "react-router-dom";
import Marca from "../components/Marca";
import Plaquinhas from "../components/Plaquinhas";

// Exemplos ilustrativos do painel (não são simulações reais).
const EXEMPLOS = [
  { destino: "Lisboa", detalhe: "7 noites, R$ 8.000", placa: "AJUSTAR" },
  { destino: "Salvador", detalhe: "5 noites, R$ 3.500", placa: "CABE" },
  { destino: "Buenos Aires", detalhe: "5 noites, R$ 3.000", placa: "NÃO CABE" },
  { destino: "Santiago", detalhe: "7 noites, R$ 6.000", placa: "CABE" },
];

// Tela 1: apresenta a ideia e leva para criar conta ou entrar.
export default function Inicio() {
  const logado = Boolean(localStorage.getItem("token"));

  return (
    <div className="container-fluid">
      <div className="row min-vh-100">
        <div className="col-lg-5 d-flex flex-column p-4 p-md-5">
          <Marca />
          <div className="my-auto py-5">
            <h1 className="display-4 mb-4">Sua viagem cabe no seu orçamento?</h1>
            <p className="fs-5 text-secondary mb-4">
              Diga para onde quer ir, quando e quanto pode gastar. A gente busca passagem e hotel
              com preços reais e responde em segundos.
            </p>
            <div className="d-flex flex-wrap gap-3">
              {logado ? (
                <Link to="/nova" className="btn btn-sinal btn-lg px-4">Fazer uma simulação</Link>
              ) : (
                <>
                  <Link to="/entrar?modo=cadastro" className="btn btn-sinal btn-lg px-4">Criar conta</Link>
                  <Link to="/entrar" className="btn btn-outline-dark btn-lg px-4 fw-bold">Entrar</Link>
                </>
              )}
            </div>
          </div>
          <p className="text-secondary mb-0">Projeto 3 de Tecnologias Web, Insper</p>
        </div>

        <div className="col-lg-7 painel-tinta d-flex flex-column justify-content-center p-4 p-md-5">
          <p className="text-white-50 fw-semibold mb-2">Exemplos de simulação</p>
          <ul className="list-unstyled mb-4">
            {EXEMPLOS.map((exemplo) => (
              <li key={exemplo.destino} className="row align-items-center py-3 border-top border-secondary">
                <div className="col-sm-5 mb-2 mb-sm-0">
                  <div className="fs-5 fw-bold">{exemplo.destino}</div>
                  <div className="small text-white-50">{exemplo.detalhe}</div>
                </div>
                <div className="col-sm-7">
                  <Plaquinhas texto={exemplo.placa} tamanho="sm" />
                </div>
              </li>
            ))}
          </ul>
          <p className="small text-white-50 mb-0">
            Valores estimados a partir de preços do Google Voos e Google Hotéis.
          </p>
        </div>
      </div>
    </div>
  );
}
