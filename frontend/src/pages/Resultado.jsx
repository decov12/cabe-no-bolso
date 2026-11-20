import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api from "../api";
import Plaquinhas from "../components/Plaquinhas";
import { VEREDITOS, formatarMes, formatarPeriodo, formatarReais, mensagemDeErro } from "../formatar";
import { formularioDaSimulacao } from "../formulario";

const CATEGORIAS = {
  passagem: { nome: "Passagem", cor: "bg-dark" },
  hotel: { nome: "Hotel", cor: "bg-primary" },
  comida: { nome: "Comida", cor: "bg-info" },
  passeios: { nome: "Passeios", cor: "bg-secondary" },
  transporte: { nome: "Transporte", cor: "bg-warning" },
};

const plural = (n, um, varios) => `${n} ${n === 1 ? um : varios}`;

// Tela 5: veredito, gasto por categoria, passagem e hotel sugeridos.
export default function Resultado() {
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
        <Link to="/nova" className="btn btn-sinal mt-3">Nova simulação</Link>
      </div>
    );
  }

  const s = carga.dados;
  const veredito = VEREDITOS[s.veredito] ?? { texto: s.veredito, placa: s.veredito, cor: "secondary" };
  const total = Number(s.total_estimado);
  const orcamento = Number(s.orcamento);
  const diferenca = Number(s.diferenca);
  const escala = Math.max(total, orcamento);
  // [["comida", "Café da manhã simples..."], ...]; vazio nas simulações feitas antes do campo existir.
  const justificativas = Object.entries(s.estimativa_ia?.justificativas ?? {});

  function mudarDados() {
    navigate("/nova", { state: { formulario: formularioDaSimulacao(s) } });
  }

  return (
    <div className="row g-4">
      <div className="col-lg-8">
        <h1 className="mb-1">
          {/* Nas simulações antigas cidade_destino vem vazio: aí fica só o código. */}
          {s.origem} → {s.cidade_destino ? `${s.cidade_destino} (${s.destino})` : s.destino}, {formatarPeriodo(s.data_ida, s.data_volta)}
        </h1>
        <p className="text-secondary mb-4">
          {plural(s.pessoas, "pessoa", "pessoas")}, {plural(s.noites, "noite", "noites")}
        </p>

        {/* Veredito */}
        <div className={`card border-0 shadow-sm text-bg-${veredito.cor} mb-4`}>
          <div className="card-body p-4">
            <Plaquinhas texto={veredito.placa} tamanho="md" className="mb-3" />
            <p className="fs-5 mb-0">
              A viagem completa sai por cerca de <strong>{formatarReais(total)}</strong>.{" "}
              {diferenca >= 0 ? (
                <>Sobram <strong>{formatarReais(diferenca)}</strong> do seu orçamento de {formatarReais(orcamento)}.</>
              ) : (
                <>Faltam <strong>{formatarReais(-diferenca)}</strong> para caber nos seus {formatarReais(orcamento)}.</>
              )}
            </p>
          </div>
        </div>

        {/* Gasto por categoria */}
        <div className="card border-0 shadow-sm mb-4">
          <div className="card-body p-4">
            <h2 className="h5 mb-4">Para onde vai o dinheiro</h2>
            <div className="position-relative pt-4 mb-4">
              <div
                className="position-absolute top-0 bottom-0 border-start border-2 border-danger"
                style={{ left: `${(orcamento / escala) * 100}%`, borderLeftStyle: "dashed" }}
              >
                <span className="position-absolute top-0 end-0 me-1 small fw-semibold text-danger text-nowrap">
                  Seu orçamento
                </span>
              </div>
              <div className="progress-stacked" style={{ height: 40 }}>
                {s.gastos.map((gasto) => (
                  <div key={gasto.categoria} className="progress" role="progressbar"
                    aria-label={CATEGORIAS[gasto.categoria]?.nome ?? gasto.categoria}
                    aria-valuenow={Number(gasto.valor)} aria-valuemin="0" aria-valuemax={escala}
                    style={{ width: `${(Number(gasto.valor) / escala) * 100}%`, height: 40 }}>
                    <div className={`progress-bar ${CATEGORIAS[gasto.categoria]?.cor ?? "bg-secondary"}`} />
                  </div>
                ))}
              </div>
            </div>

            <div className="row g-3">
              {s.gastos.map((gasto) => {
                const categoria = CATEGORIAS[gasto.categoria] ?? { nome: gasto.categoria, cor: "bg-secondary" };
                return (
                  <div key={gasto.categoria} className="col-6 col-md">
                    <div className="small text-secondary d-flex align-items-center gap-1">
                      <span className={`d-inline-block rounded-1 ${categoria.cor}`} style={{ width: 10, height: 10 }} />
                      {categoria.nome}
                      {gasto.categoria === "hotel" && `, ${plural(s.noites, "noite", "noites")}`}
                      {gasto.estimativa_ia && (
                        <span className="badge text-bg-light border" title="Estimativa da IA (Gemini)">IA</span>
                      )}
                    </div>
                    <div className="fw-bold fs-5">{formatarReais(gasto.valor)}</div>
                  </div>
                );
              })}
            </div>

            {justificativas.length > 0 && (
              // <details> abre e fecha sozinho, sem JavaScript; começa fechado para não pesar a tela.
              <details className="mt-4 small">
                <summary className="fw-semibold text-secondary">Como a IA estimou comida, passeios e transporte</summary>
                <ul className="list-unstyled mt-2 mb-0">
                  {justificativas.map(([categoria, texto]) => (
                    <li key={categoria} className="mb-2">
                      <strong>{CATEGORIAS[categoria]?.nome ?? categoria}</strong>
                      {s.estimativa_ia.por_pessoa_dia?.[categoria] &&
                        ` (${formatarReais(s.estimativa_ia.por_pessoa_dia[categoria])} por pessoa por dia)`}
                      : <span className="text-secondary">{texto}</span>
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        </div>

        {/* Passagem mês a mês */}
        {s.precos_por_mes?.length > 0 && <PrecosPorMes precos={s.precos_por_mes} mesEscolhido={s.data_ida.slice(0, 7)} />}
      </div>

      <div className="col-lg-4">
        <div className="card border-0 shadow-sm mb-3">
          <div className="card-body p-4">
            <div className="small fw-semibold text-secondary">Passagem ida e volta</div>
            <div className="fs-3 fw-bold">{formatarReais(s.passagem.preco_total)}</div>
            <p className="text-secondary mb-2">
              {formatarReais(s.passagem.preco_por_pessoa)} por pessoa
              {s.passagem.companhia && `, ${s.passagem.companhia}`}. {s.origem} para {s.destino}.
            </p>
            {s.passagem.link_google_voos && (
              <a href={s.passagem.link_google_voos} target="_blank" rel="noopener noreferrer" className="fw-semibold">
                Ver no Google Voos
              </a>
            )}
          </div>
        </div>

        <div className="card border-0 shadow-sm mb-3">
          <div className="card-body p-4">
            <div className="small fw-semibold text-secondary">Hotel sugerido</div>
            <div className="fs-3 fw-bold">
              {formatarReais(s.hotel.preco_noite)} <span className="fs-6 fw-semibold text-secondary">por noite</span>
            </div>
            <p className="text-secondary mb-2">
              {s.hotel.nome}
              {s.hotel.estrelas ? `, ${s.hotel.estrelas} estrelas` : ""}
              {s.hotel.nota ? `, nota ${s.hotel.nota.toLocaleString("pt-BR")}` : ""}.
              {" "}Total de {formatarReais(s.hotel.preco_total)}.
            </p>
            {s.hotel.link && (
              <a href={s.hotel.link} target="_blank" rel="noopener noreferrer" className="fw-semibold">
                Ver o hotel
              </a>
            )}
          </div>
        </div>

        {s.alternativas?.length > 0 && (
          <div className="card border-0 shadow-sm mb-3">
            <div className="card-body p-4">
              <h2 className="h5">Como fazer caber</h2>
              <ul className="list-group list-group-flush">
                {s.alternativas.map((alt) => (
                  <li key={alt.tipo} className="list-group-item px-0">
                    <p className="mb-1">{alt.descricao}</p>
                    <div className="d-flex justify-content-between align-items-center small">
                      <span>
                        Novo total <strong>{formatarReais(alt.novo_total)}</strong> (economia de {formatarReais(alt.economia)})
                      </span>
                      <span className={`badge rounded-pill text-bg-${VEREDITOS[alt.novo_veredito]?.cor ?? "secondary"}`}>
                        {VEREDITOS[alt.novo_veredito]?.texto ?? alt.novo_veredito}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        <div className="d-grid gap-2 mb-3">
          {s.veredito !== "cabe" && (
            <Link to={`/alternativas/${s.id}`} className="btn btn-tinta btn-lg">Ver como fazer caber</Link>
          )}
          <button type="button" className="btn btn-outline-dark btn-lg fw-bold" onClick={mudarDados}>Mudar dados</button>
          <Link to="/nova" className="btn btn-sinal btn-lg">Nova simulação</Link>
        </div>

        <div className="alert alert-warning small mb-0" role="note">
          <strong>Todos os valores são estimativas.</strong> Passagem e hotel vêm de preços do Google no momento
          da busca e podem mudar. Os itens marcados com <span className="badge text-bg-light border">IA</span>{" "}
          são estimativas do Gemini.
        </div>
      </div>
    </div>
  );
}

// Menor preço de passagem (ida e volta, por pessoa) em cada mês, em barras horizontais.
function PrecosPorMes({ precos, mesEscolhido }) {
  const valores = precos.map((p) => Number(p.menor_preco));
  const maior = Math.max(...valores);
  const menor = Math.min(...valores);

  return (
    <div className="card border-0 shadow-sm">
      <div className="card-body p-4">
        <h2 className="h5 mb-1">Passagem mês a mês</h2>
        <p className="small text-secondary mb-3">
          Menor preço de ida e volta por pessoa em cada mês (viagens de 7 noites).{" "}
          <span className="text-dark fw-semibold">Escuro</span>: o mês escolhido.{" "}
          <span className="text-success fw-semibold">Verde</span>: o mais barato.
        </p>
        {precos.map((p) => {
          const valor = Number(p.menor_preco);
          const cor = p.mes === mesEscolhido ? "bg-dark" : valor === menor ? "bg-success" : "bg-info";
          return (
            <div key={p.mes} className="d-flex align-items-center gap-3 mb-2">
              <span className="small text-secondary" style={{ width: 70 }}>{formatarMes(p.mes)}</span>
              <div className="progress flex-grow-1" role="progressbar" aria-label={formatarMes(p.mes)}
                aria-valuenow={valor} aria-valuemin="0" aria-valuemax={maior} style={{ height: 18 }}>
                <div className={`progress-bar ${cor}`} style={{ width: `${(valor / maior) * 100}%` }} />
              </div>
              <span className="small fw-semibold text-end" style={{ width: 100 }}>{formatarReais(p.menor_preco)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
