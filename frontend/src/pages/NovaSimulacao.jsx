import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import api from "../api";
import CampoLugar from "../components/CampoLugar";
import { VEREDITOS, formatarPeriodo } from "../formatar";

const INTERESSES = [
  "Gastronomia", "História", "Museus", "Arte e cultura", "Praia", "Natureza",
  "Vida noturna", "Compras", "Esportes", "Parques de diversão", "Arquitetura", "Descanso",
];
const MAXIMO_INTERESSES = 10;

const VAZIO = {
  origem: null,
  destino: null,
  data_ida: "",
  data_volta: "",
  orcamento: "",
  pessoas: 1,
  interesses: [],
};

function hojeIso() {
  const d = new Date();
  const doisDigitos = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${doisDigitos(d.getMonth() + 1)}-${doisDigitos(d.getDate())}`;
}

// Erros que dá para pegar antes de gastar uma busca. O resto o backend confere.
function validar(f) {
  const erros = {};
  if (!f.origem) erros.origem = "Escolha a cidade de origem na lista de sugestões.";
  if (!f.destino) erros.destino = "Escolha o destino na lista de sugestões.";
  if (f.origem && f.destino && f.origem.codigo === f.destino.codigo) {
    erros.destino = "A origem e o destino precisam ser diferentes.";
  }
  if (!f.data_ida) erros.data_ida = "Informe a data de ida.";
  else if (f.data_ida < hojeIso()) erros.data_ida = "A data de ida não pode estar no passado.";
  if (!f.data_volta) erros.data_volta = "Informe a data de volta.";
  else if (f.data_ida && f.data_volta <= f.data_ida) {
    erros.data_volta = "A volta precisa ser depois da ida.";
  }
  if (!(Number(f.orcamento) > 0)) erros.orcamento = "Informe um orçamento maior que zero.";
  return erros;
}

// Tela 3: formulário da simulação. Ao enviar, a tela 4 (Buscando) faz o POST.
export default function NovaSimulacao() {
  const navigate = useNavigate();
  const location = useLocation();
  // Ao voltar da tela Buscando ou do Resultado, o formulário chega preenchido.
  const [form, setForm] = useState(location.state?.formulario ?? VAZIO);
  const [erros, setErros] = useState({});
  const [ultimas, setUltimas] = useState([]);

  useEffect(() => {
    api.get("/api/simulacoes/")
      .then((resposta) => setUltimas(resposta.data.slice(0, 3)))
      .catch(() => {}); // a lista lateral é só um atalho; sem ela o formulário funciona
  }, []);

  function mudar(nome, valor) {
    setForm((atual) => ({ ...atual, [nome]: valor }));
    setErros((atual) => ({ ...atual, [nome]: undefined }));
  }

  function alternarInteresse(interesse) {
    const escolhidos = form.interesses.includes(interesse)
      ? form.interesses.filter((i) => i !== interesse)
      : [...form.interesses, interesse];
    mudar("interesses", escolhidos);
  }

  function enviar(evento) {
    evento.preventDefault();
    const encontrados = validar(form);
    setErros(encontrados);
    if (Object.keys(encontrados).length === 0) {
      navigate("/buscando", { state: { formulario: form } });
    }
  }

  function erroDe(nome) {
    return erros[nome] && <div className="invalid-feedback d-block">{erros[nome]}</div>;
  }

  const limiteAtingido = form.interesses.length >= MAXIMO_INTERESSES;

  return (
    <div className="row g-4">
      <div className="col-lg-8">
        <h1 className="mb-1">Para onde você quer ir?</h1>
        <p className="text-secondary mb-4">Preencha o básico. O resto a gente estima.</p>

        <form className="card border-0 shadow-sm" onSubmit={enviar} noValidate>
          <div className="card-body p-4">
            <div className="row g-3">
              <div className="col-md-6">
                <CampoLugar id="origem" rotulo="Saindo de" valor={form.origem} onChange={(l) => mudar("origem", l)} erro={erros.origem} />
              </div>
              <div className="col-md-6">
                <CampoLugar id="destino" rotulo="Destino" valor={form.destino} onChange={(l) => mudar("destino", l)} erro={erros.destino} />
              </div>

              <div className="col-md-6">
                <label htmlFor="data_ida" className="form-label fw-semibold small">Ida</label>
                <input id="data_ida" type="date" min={hojeIso()} className={`form-control form-control-lg ${erros.data_ida ? "is-invalid" : ""}`}
                  value={form.data_ida} onChange={(e) => mudar("data_ida", e.target.value)} />
                {erroDe("data_ida")}
              </div>
              <div className="col-md-6">
                <label htmlFor="data_volta" className="form-label fw-semibold small">Volta</label>
                <input id="data_volta" type="date" min={form.data_ida || hojeIso()} className={`form-control form-control-lg ${erros.data_volta ? "is-invalid" : ""}`}
                  value={form.data_volta} onChange={(e) => mudar("data_volta", e.target.value)} />
                {erroDe("data_volta")}
              </div>

              <div className="col-md-6">
                <label htmlFor="orcamento" className="form-label fw-semibold small">Orçamento total</label>
                <div className={`input-group input-group-lg ${erros.orcamento ? "has-validation" : ""}`}>
                  <span className="input-group-text">R$</span>
                  <input id="orcamento" type="number" min="1" step="0.01" inputMode="decimal" placeholder="8000"
                    className={`form-control ${erros.orcamento ? "is-invalid" : ""}`}
                    value={form.orcamento} onChange={(e) => mudar("orcamento", e.target.value)} />
                </div>
                {erroDe("orcamento")}
                <div className="form-text">Tudo incluído: passagem, hotel, comida, passeios e transporte.</div>
              </div>
              <div className="col-md-6">
                <label htmlFor="pessoas" className="form-label fw-semibold small">Pessoas</label>
                <select id="pessoas" className="form-select form-select-lg" value={form.pessoas}
                  onChange={(e) => mudar("pessoas", Number(e.target.value))}>
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => (
                    <option key={n} value={n}>{n} {n === 1 ? "pessoa" : "pessoas"}</option>
                  ))}
                </select>
              </div>

              <div className="col-12">
                <span className="form-label fw-semibold small d-block mb-2">
                  Do que você gosta <span className="fw-normal text-secondary">(até {MAXIMO_INTERESSES})</span>
                </span>
                <div className="d-flex flex-wrap gap-2">
                  {INTERESSES.map((interesse) => {
                    const ativo = form.interesses.includes(interesse);
                    return (
                      <button key={interesse} type="button" aria-pressed={ativo}
                        className={`btn rounded-pill ${ativo ? "btn-tinta" : "btn-outline-secondary"}`}
                        disabled={!ativo && limiteAtingido}
                        onClick={() => alternarInteresse(interesse)}>
                        {interesse}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
          <div className="card-footer bg-white d-flex justify-content-between align-items-center p-4">
            <span className="small text-secondary">Leva de 5 a 15 segundos.</span>
            <button type="submit" className="btn btn-sinal btn-lg px-4">Simular viagem</button>
          </div>
        </form>
      </div>

      <div className="col-lg-4">
        <div className="card border-0 shadow-sm mb-4">
          <div className="card-body p-4">
            <h2 className="h5">Como a conta é feita</h2>
            <ol className="text-secondary mb-0 ps-3">
              <li>Buscamos o preço real da passagem e do hotel.</li>
              <li>A IA estima comida, passeios e transporte.</li>
              <li>Somamos tudo e comparamos com o seu orçamento.</li>
            </ol>
          </div>
        </div>

        {ultimas.length > 0 && (
          <div className="card border-0 shadow-sm">
            <div className="card-body p-4">
              <h2 className="h5">Últimas simulações</h2>
              <ul className="list-group list-group-flush">
                {ultimas.map((s) => (
                  <li key={s.id} className="list-group-item px-0 d-flex justify-content-between align-items-center">
                    <Link to={`/resultado/${s.id}`} className="text-decoration-none">
                      <span className="fw-semibold d-block">{s.origem} → {s.destino}</span>
                      <span className="small text-secondary">{formatarPeriodo(s.data_ida, s.data_volta)}</span>
                    </Link>
                    <span className={`badge rounded-pill text-bg-${VEREDITOS[s.veredito]?.cor ?? "secondary"}`}>
                      {VEREDITOS[s.veredito]?.texto ?? s.veredito}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
