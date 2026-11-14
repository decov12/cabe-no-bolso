import { Link, Navigate } from "react-router-dom";
import Marca from "../components/Marca";
import Placa from "../components/Placa";
import { estaLogado } from "../api";

// Exemplos só para ilustrar a página inicial (não vêm do servidor).
const EXEMPLOS = [
  { destino: "Lisboa", detalhe: "7 noites, R$ 8.000", veredito: "AJUSTAR" },
  { destino: "Salvador", detalhe: "5 noites, R$ 3.500", veredito: "CABE" },
  { destino: "Buenos Aires", detalhe: "5 noites, R$ 3.000", veredito: "NÃO CABE" },
  { destino: "Santiago", detalhe: "7 noites, R$ 6.000", veredito: "CABE" },
];

export default function Inicio() {
  // Quem já está logado vai direto para a simulação.
  if (estaLogado()) return <Navigate to="/nova" replace />;

  return (
    <div className="tela-dividida">
      <section className="lado-claro">
        <Marca />

        <div className="miolo">
          <h1 className="titulo-grande">Sua viagem cabe no seu orçamento?</h1>
          <p className="texto-apoio">
            Diga para onde quer ir, quando e quanto pode gastar. A gente busca passagem e hotel
            com preços reais e responde em segundos.
          </p>
          <div className="d-flex gap-3 flex-wrap">
            <Link to="/entrar?aba=criar" className="btn btn-sinal btn-lg">
              Criar conta grátis
            </Link>
            <Link to="/entrar" className="btn btn-outline-dark btn-lg">
              Entrar
            </Link>
          </div>
        </div>

        <p className="rodape-lado mb-0">Projeto 3 de Tecnologias Web, Insper</p>
      </section>

      <section className="lado-escuro">
        <div className="miolo">
          <h2 className="rotulo-painel">Simulações de hoje</h2>
          <ul className="lista-painel">
            {EXEMPLOS.map((e) => (
              <li key={e.destino}>
                <div>
                  <strong>{e.destino}</strong>
                  <small>{e.detalhe}</small>
                </div>
                <Placa texto={e.veredito} tamanho="sm" />
              </li>
            ))}
          </ul>
          <p className="nota-painel mb-0">
            Valores estimados a partir de preços do Google Voos e Google Hotéis.
          </p>
        </div>
      </section>
    </div>
  );
}
