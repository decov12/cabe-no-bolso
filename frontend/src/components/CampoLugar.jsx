import { useEffect, useState } from "react";
import api from "../api";
import { mensagemDeErro } from "../formatar";

const PAUSA_MS = 500; // espera a pessoa parar de digitar antes de buscar
const MINIMO_LETRAS = 2;

// Respostas já recebidas nesta aba: repetir o mesmo texto não gasta outra busca da SerpApi.
const cache = new Map();

// Campo de cidade/aeroporto com sugestões de /api/lugares/.
// `valor` é o lugar escolhido ({codigo, rotulo, nome}) ou null enquanto a pessoa digita.
export default function CampoLugar({ id, rotulo, valor, onChange, erro }) {
  const [texto, setTexto] = useState(valor?.rotulo ?? "");
  const [sugestoes, setSugestoes] = useState([]);
  const [aberto, setAberto] = useState(false);
  const [carregando, setCarregando] = useState(false);
  const [erroBusca, setErroBusca] = useState("");

  useEffect(() => {
    const busca = texto.trim();
    if (valor || busca.length < MINIMO_LETRAS) return;

    let cancelado = false;
    const timer = setTimeout(async () => {
      setCarregando(true);
      try {
        if (!cache.has(busca)) {
          const resposta = await api.get("/api/lugares/", { params: { q: busca } });
          cache.set(busca, resposta.data);
        }
        if (!cancelado) {
          setSugestoes(cache.get(busca));
          setAberto(true);
        }
      } catch (e) {
        if (!cancelado) setErroBusca(mensagemDeErro(e));
      } finally {
        setCarregando(false);
      }
    }, PAUSA_MS);

    return () => {
      cancelado = true;
      clearTimeout(timer);
    };
  }, [texto, valor]);

  function digitar(evento) {
    const novo = evento.target.value;
    setTexto(novo);
    setErroBusca("");
    if (valor) onChange(null); // mudou o texto: a escolha anterior deixa de valer
    if (novo.trim().length < MINIMO_LETRAS) {
      setSugestoes([]);
      setAberto(false);
    }
  }

  function escolher(lugar) {
    const nome = lugar.tipo === "aeroporto" ? lugar.cidade || lugar.nome : lugar.nome;
    const rotulo = `${lugar.nome} (${lugar.codigo})`;
    setTexto(rotulo);
    setAberto(false);
    onChange({ codigo: lugar.codigo, rotulo, nome });
  }

  return (
    <div className="position-relative">
      <label htmlFor={id} className="form-label fw-semibold small">{rotulo}</label>
      <div className="position-relative">
        <input
          id={id}
          className={`form-control form-control-lg ${erro ? "is-invalid" : ""}`}
          value={texto}
          onChange={digitar}
          onFocus={() => sugestoes.length && !valor && setAberto(true)}
          onBlur={() => setAberto(false)}
          placeholder="Digite a cidade"
          autoComplete="off"
          role="combobox"
          aria-expanded={aberto}
          aria-controls={`${id}-lista`}
        />
        {carregando && (
          <span className="spinner-border spinner-border-sm text-secondary position-absolute top-50 end-0 translate-middle" aria-label="Buscando" />
        )}
        {erro && <div className="invalid-feedback">{erro}</div>}
      </div>
      {erroBusca && <div className="small text-danger mt-1">{erroBusca}</div>}

      {aberto && (
        <ul id={`${id}-lista`} className="list-group position-absolute w-100 shadow mt-1 z-3 overflow-auto" style={{ maxHeight: 320 }} role="listbox">
          {sugestoes.length === 0 && (
            <li className="list-group-item text-secondary">Nenhum lugar encontrado.</li>
          )}
          {sugestoes.map((lugar, i) => (
            <li key={i} className="list-group-item list-group-item-action p-0" role="option" aria-selected="false">
              <button
                type="button"
                className={`btn w-100 text-start d-flex justify-content-between align-items-center gap-2 py-2 ${lugar.tipo === "aeroporto" ? "ps-4" : ""}`}
                // onMouseDown em vez de onClick: escolhe antes de o campo perder o foco e fechar a lista
                onMouseDown={(e) => {
                  e.preventDefault();
                  escolher(lugar);
                }}
              >
                <span>
                  {lugar.tipo === "aeroporto" ? (
                    <span className="small">✈ {lugar.nome}</span>
                  ) : (
                    <span className="fw-semibold">{lugar.nome}{lugar.pais ? `, ${lugar.pais}` : ""}</span>
                  )}
                  {lugar.descricao && <span className="d-block small text-secondary">{lugar.descricao}</span>}
                </span>
                <span className="badge text-bg-light border">{lugar.codigo}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
