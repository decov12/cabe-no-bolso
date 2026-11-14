import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import api from "../api";
import Plaquinhas from "../components/Plaquinhas";
import { formatarPeriodo, formatarReais, mensagemDeErro } from "../formatar";

const ETAPAS = [
  "Buscando passagens",
  "Buscando hotéis",
  "Montando o calendário de preços dos próximos meses",
  "Estimando comida, passeios e transporte com IA",
  "Comparando com o seu orçamento",
];

// Um POST por navegação. Cada simulação gasta de 3 a 4 buscas da SerpApi, então:
// - o React (StrictMode) monta a tela duas vezes em desenvolvimento: as duas montagens
//   reaproveitam a mesma requisição guardada aqui;
// - se a pessoa recarregar a página, o sessionStorage avisa que esse pedido já foi enviado.
const envios = new Map();

function montarPedido(f) {
  return {
    origem: f.origem.codigo,
    destino: f.destino.codigo,
    data_ida: f.data_ida,
    data_volta: f.data_volta,
    orcamento: String(f.orcamento),
    pessoas: f.pessoas,
    interesses: f.interesses,
  };
}

// Tela 4: mostra o carregando, faz o POST /api/simulacoes/ e leva ao resultado.
export default function Buscando() {
  const navigate = useNavigate();
  const location = useLocation();
  const formulario = location.state?.formulario;
  const chave = `simulacao-enviada-${location.key}`;

  const [jaEnviado] = useState(() => !envios.has(location.key) && sessionStorage.getItem(chave) !== null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    if (!formulario || jaEnviado) return;

    let promessa = envios.get(location.key);
    if (!promessa) {
      promessa = api.post("/api/simulacoes/", montarPedido(formulario));
      envios.set(location.key, promessa);
      sessionStorage.setItem(chave, "1");
    }

    let ativo = true;
    promessa
      .then((resposta) => {
        if (ativo) navigate(`/resultado/${resposta.data.id}`, { replace: true });
      })
      .catch((e) => {
        if (ativo) setErro(mensagemDeErro(e));
      });
    return () => {
      ativo = false;
    };
  }, [formulario, jaEnviado, location.key, chave, navigate]);

  if (!formulario || jaEnviado) {
    return (
      <div className="text-center py-5">
        <h1 className="h3">Nenhuma simulação em andamento</h1>
        <p className="text-secondary">
          {jaEnviado
            ? "Essa simulação já foi enviada. Para não gastar a busca de novo, comece uma nova."
            : "Preencha o formulário para simular uma viagem."}
        </p>
        <Link to="/nova" className="btn btn-sinal">Nova simulação</Link>
      </div>
    );
  }

  const destino = formulario.destino.nome || formulario.destino.codigo;

  return (
    <div className="mx-auto text-center" style={{ maxWidth: 760 }}>
      <Plaquinhas texto={destino.toUpperCase()} tamanho="lg" className="justify-content-center mb-4" />
      <h1 className="mb-1">{erro ? "Não deu para simular" : `Montando sua viagem para ${destino}`}</h1>
      <p className="text-secondary mb-4">
        {formatarPeriodo(formulario.data_ida, formulario.data_volta)}, orçamento de {formatarReais(formulario.orcamento)}
      </p>

      {erro ? (
        <div className="alert alert-danger text-start" role="alert">
          <p className="mb-3">{erro}</p>
          <button type="button" className="btn btn-tinta" onClick={() => navigate("/nova", { state: { formulario } })}>
            Voltar ao formulário
          </button>
        </div>
      ) : (
        <div className="card border-0 shadow-sm text-start">
          <div className="card-body p-4">
            <div className="d-flex align-items-center gap-3 mb-3">
              <span className="spinner-border text-primary" aria-hidden="true" />
              <span className="fw-semibold" role="status">Isso leva de 5 a 15 segundos.</span>
            </div>
            <ul className="list-group list-group-flush">
              {ETAPAS.map((etapa) => (
                <li key={etapa} className="list-group-item px-0 text-secondary">{etapa}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
