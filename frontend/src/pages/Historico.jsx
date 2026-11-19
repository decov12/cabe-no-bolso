import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api";
import { VEREDITOS, formatarPeriodo, formatarReais, mensagemDeErro } from "../formatar";

// Nas simulações antigas cidade_destino vem vazio: aí vale o código (LIS).
const destinoDe = (s) => s.cidade_destino || s.destino;

// criado_em -> "hoje", "ontem", "08/11" ou "08/11/2025" (de outro ano).
function simuladoEm(iso) {
  const data = new Date(iso);
  const hoje = new Date();
  const ontem = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate() - 1);
  if (data.toDateString() === hoje.toDateString()) return "hoje";
  if (data.toDateString() === ontem.toDateString()) return "ontem";
  if (data.getFullYear() === hoje.getFullYear()) {
    return data.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
  }
  return data.toLocaleDateString("pt-BR");
}

// Tela 7: lista as simulações salvas (a API já manda da mais recente para a mais antiga).
export default function Historico() {
  const navigate = useNavigate();
  // Cada "Tentar de novo" soma 1 em tentativa, e o efeito busca a lista de novo.
  const [tentativa, setTentativa] = useState(0);
  const [carga, setCarga] = useState({ tentativa: null, lista: [], erro: "" });
  const [excluindo, setExcluindo] = useState(null);
  const [erroAoExcluir, setErroAoExcluir] = useState("");

  useEffect(() => {
    let ativo = true;
    api.get("/api/simulacoes/")
      .then((resposta) => ativo && setCarga({ tentativa, lista: resposta.data, erro: "" }))
      .catch((e) => ativo && setCarga({ tentativa, lista: [], erro: mensagemDeErro(e) }));
    return () => {
      ativo = false;
    };
  }, [tentativa]);

  function tirarDaLista(id) {
    setCarga((atual) => ({ ...atual, lista: atual.lista.filter((s) => s.id !== id) }));
  }

  async function excluir(s) {
    const pergunta = `Excluir a simulação para ${destinoDe(s)} (${formatarPeriodo(s.data_ida, s.data_volta)})? Não dá para desfazer.`;
    if (!window.confirm(pergunta)) return;
    setExcluindo(s.id);
    setErroAoExcluir("");
    try {
      await api.delete(`/api/simulacoes/${s.id}/`);
      tirarDaLista(s.id);
    } catch (e) {
      // 404: já tinha sido apagada (em outra aba, por exemplo). Some da lista do mesmo jeito.
      if (e.response?.status === 404) tirarDaLista(s.id);
      else setErroAoExcluir(mensagemDeErro(e));
    } finally {
      setExcluindo(null);
    }
  }

  const cabecalho = (
    <div className="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-4">
      <div>
        <h1 className="mb-1">Suas simulações</h1>
        <p className="text-secondary mb-0">Abra uma simulação para ver o resultado e as alternativas de novo.</p>
      </div>
      <Link to="/nova" className="btn btn-sinal btn-lg px-4">Nova simulação</Link>
    </div>
  );

  if (carga.tentativa !== tentativa) {
    return (
      <>
        {cabecalho}
        <div className="text-center py-5">
          <span className="spinner-border text-primary" role="status" aria-label="Carregando" />
        </div>
      </>
    );
  }

  if (carga.erro) {
    return (
      <>
        {cabecalho}
        <div className="alert alert-danger" role="alert">
          <p className="mb-3">Não deu para carregar o histórico. {carga.erro}</p>
          <button type="button" className="btn btn-tinta" onClick={() => setTentativa((t) => t + 1)}>
            Tentar de novo
          </button>
        </div>
      </>
    );
  }

  const lista = carga.lista;

  if (lista.length === 0) {
    return (
      <>
        {cabecalho}
        <div className="card border-0 shadow-sm">
          <div className="card-body p-5 text-center">
            <h2 className="h4">Você ainda não fez nenhuma simulação</h2>
            <p className="text-secondary">Diga para onde quer ir e quanto pode gastar. A gente diz se cabe no bolso.</p>
            <Link to="/nova" className="btn btn-sinal btn-lg">Fazer a primeira simulação</Link>
          </div>
        </div>
      </>
    );
  }

  const numeros = [
    { valor: lista.length, texto: lista.length === 1 ? "simulação" : "simulações" },
    { valor: lista.filter((s) => s.veredito === "cabe").length, texto: "cabem no orçamento" },
    { valor: new Set(lista.map((s) => s.destino)).size, texto: "destinos diferentes" },
  ];

  return (
    <>
      {cabecalho}

      <div className="d-flex flex-wrap gap-3 mb-4">
        {numeros.map((n) => (
          <div key={n.texto} className="card border-0 shadow-sm" style={{ minWidth: 180 }}>
            <div className="card-body">
              <div className="fs-3 fw-bold">{n.valor}</div>
              <div className="small text-secondary">{n.texto}</div>
            </div>
          </div>
        ))}
      </div>

      {erroAoExcluir && (
        <div className="alert alert-danger alert-dismissible" role="alert">
          Não deu para excluir. {erroAoExcluir}
          <button type="button" className="btn-close" aria-label="Fechar" onClick={() => setErroAoExcluir("")} />
        </div>
      )}

      <div className="card border-0 shadow-sm">
        <div className="table-responsive">
          <table className="table table-hover align-middle mb-0">
            <thead className="table-light small">
              <tr>
                <th scope="col" className="ps-4">Viagem</th>
                <th scope="col">Datas</th>
                <th scope="col">Orçamento</th>
                <th scope="col">Total estimado</th>
                <th scope="col">Resultado</th>
                <th scope="col">Simulado em</th>
                <th scope="col"><span className="visually-hidden">Ações</span></th>
              </tr>
            </thead>
            <tbody>
              {lista.map((s) => {
                const veredito = VEREDITOS[s.veredito] ?? { texto: s.veredito, cor: "secondary" };
                return (
                  // A linha inteira abre o resultado; "Abrir" é o mesmo atalho para quem usa o teclado.
                  <tr key={s.id} onClick={() => navigate(`/resultado/${s.id}`)} style={{ cursor: "pointer" }}>
                    <td className="ps-4 text-nowrap">
                      <span className="small text-secondary">{s.origem} → </span>
                      <span className="fw-bold">{destinoDe(s)}</span>
                    </td>
                    <td className="text-nowrap">{formatarPeriodo(s.data_ida, s.data_volta)}</td>
                    <td className="text-nowrap">{formatarReais(s.orcamento)}</td>
                    <td className="text-nowrap">{formatarReais(s.total_estimado)}</td>
                    <td>
                      <span className={`badge rounded-pill text-bg-${veredito.cor}`}>{veredito.texto}</span>
                    </td>
                    <td className="small text-secondary text-nowrap">{simuladoEm(s.criado_em)}</td>
                    <td className="text-end pe-4 text-nowrap" onClick={(e) => e.stopPropagation()}>
                      <Link to={`/resultado/${s.id}`} className="btn btn-sm btn-link fw-semibold">Abrir</Link>
                      <button type="button" className="btn btn-sm btn-outline-danger ms-2"
                        disabled={excluindo === s.id} onClick={() => excluir(s)}>
                        {excluindo === s.id ? "Excluindo..." : "Excluir"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
