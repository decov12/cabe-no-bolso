import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api from "../api";
import { VEREDITOS, formatarReais, mensagemDeErro } from "../formatar";
import { formularioDaSimulacao } from "../formulario";

// Os tipos que o backend calcula (api/servicos/alternativas.py).
const TITULOS = {
  outro_mes: "Ir em outro mês",
  menos_noites: "Ficar menos noites",
  hotel_mais_simples: "Trocar por um hotel mais simples",
};

// Tela 6: o que mudar para a viagem caber, a partir do campo "alternativas" da simulação salva.
// Nada aqui gasta busca: as alternativas já vieram calculadas no POST da simulação.
export default function Alternativas() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [carga, setCarga] = useState({ id: null, dados: null, erro: "" });

  useEffect(() => {
    let ativo = true;
    api.get(`/api/simulacoes/${id}/`)
      .then((resposta) => ativo && setCarga({ id, dados: resposta.data, erro: "" }))
      .catch((e) => ativo && setCarga({
        id,
        dados: null,
        erro: e.response?.status === 404 ? "Simulação não encontrada." : mensagemDeErro(e),
      }));
    return () => {
      ativo = false;
    };
  }, [id]);

  if (carga.id !== id) {
    return (
      <div className="text-center py-5">
        <span className="spinner-border text-primary" role="status" aria-label="Carregando" />
      </div>
    );
  }

  if (carga.erro) {
    return (
      <div className="text-center py-5">
        <h1 className="h3">{carga.erro}</h1>
        <Link to="/historico" className="btn btn-sinal mt-3">Ver o histórico</Link>
      </div>
    );
  }

  const s = carga.dados;
  const cidade = s.cidade_destino || s.destino;
  const orcamento = Number(s.orcamento);
  const totalAtual = Number(s.total_estimado);
  // As alternativas só baixam o total, então a simulação original é a maior barra possível.
  const escala = Math.max(totalAtual, orcamento);
  const alternativas = [...(s.alternativas ?? [])].sort((a, b) => Number(b.economia) - Number(a.economia));

  function simularDeNovo() {
    navigate("/nova", { state: { formulario: formularioDaSimulacao(s) } });
  }

  return (
    <>
      <div className="d-flex flex-wrap justify-content-between align-items-end gap-3 mb-4">
        <div>
          <h1 className="mb-1">Como fazer {cidade} caber em {formatarReais(orcamento)}</h1>
          <p className="text-secondary mb-0">
            Hoje a viagem sai por {formatarReais(totalAtual)}.
            {alternativas.length > 0 && " Opções calculadas a partir da sua simulação, da que mais economiza para a que menos economiza."}
          </p>
        </div>
        <Link to={`/resultado/${s.id}`} className="fw-semibold text-decoration-none">Voltar ao resultado</Link>
      </div>

      {alternativas.length === 0 ? (
        <div className="card border-0 shadow-sm mb-4">
          <div className="card-body p-5 text-center">
            {s.veredito === "cabe" ? (
              <>
                <h2 className="h4">A viagem já cabe no orçamento</h2>
                <p className="text-secondary mb-0">Por isso não há alternativas: nada precisa mudar.</p>
              </>
            ) : (
              <>
                <h2 className="h4">Nenhuma mudança deixou a viagem mais barata</h2>
                <p className="text-secondary mb-0">
                  Com os preços desta busca, outro mês, menos noites ou um hotel mais simples não reduziram o total.
                  Tente outras datas ou outro orçamento.
                </p>
              </>
            )}
          </div>
        </div>
      ) : (
        <>
          {alternativas.map((alt) => {
            const veredito = VEREDITOS[alt.novo_veredito] ?? { texto: alt.novo_veredito, cor: "secondary" };
            const novoTotal = Number(alt.novo_total);
            const sobra = orcamento - novoTotal;
            return (
              <div key={alt.tipo} className="card border-0 shadow-sm mb-3">
                <div className="card-body p-4">
                  <div className="row g-3 align-items-center">
                    <div className="col-lg-6">
                      <h2 className="h5 mb-1">{TITULOS[alt.tipo] ?? alt.tipo}</h2>
                      <p className="text-secondary small mb-0">{alt.descricao}</p>
                    </div>

                    <div className="col-md-7 col-lg-3">
                      {/* Barra do novo total; a linha tracejada vermelha é o orçamento, como no Resultado. */}
                      <div className="position-relative">
                        <div className="progress" role="progressbar" aria-label="Novo total" style={{ height: 12 }}
                          aria-valuenow={novoTotal} aria-valuemin="0" aria-valuemax={escala}>
                          <div className={`progress-bar bg-${veredito.cor}`} style={{ width: `${(novoTotal / escala) * 100}%` }} />
                        </div>
                        <div className="position-absolute border-start border-2 border-danger"
                          style={{ left: `${(orcamento / escala) * 100}%`, top: -5, bottom: -5, borderLeftStyle: "dashed" }} />
                      </div>
                      <div className="small mt-2">
                        Total <strong>{formatarReais(novoTotal)}</strong>
                        <span className="text-secondary">, economia de {formatarReais(alt.economia)}</span>
                      </div>
                    </div>

                    <div className="col-md-5 col-lg-3 text-md-end">
                      <span className={`badge rounded-pill text-bg-${veredito.cor} mb-1`}>{veredito.texto}</span>
                      <div className="small fw-semibold">
                        {sobra >= 0 ? `Sobram ${formatarReais(sobra)}` : `Ainda faltam ${formatarReais(-sobra)}`}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
          <p className="small text-secondary mb-4">
            A linha tracejada marca o seu orçamento. As contas são feitas pelo sistema com os mesmos preços da
            simulação, não pela IA. Os preços podem mudar quando você simular de novo.
          </p>
        </>
      )}

      <div className="d-flex flex-wrap gap-2">
        <button type="button" className="btn btn-sinal btn-lg" onClick={simularDeNovo}>Simular de novo com outros dados</button>
        <Link to={`/resultado/${s.id}`} className="btn btn-outline-dark btn-lg fw-bold">Voltar ao resultado</Link>
      </div>
    </>
  );
}
