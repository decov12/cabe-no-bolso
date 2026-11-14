import { useState } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";
import api from "../api";
import Marca from "../components/Marca";
import Plaquinhas from "../components/Plaquinhas";
import { mensagemDeErro } from "../formatar";

// Tela 2: login e cadastro na mesma tela, trocando pelas abas.
// /entrar abre em "Entrar"; /entrar?modo=cadastro abre em "Criar conta".
export default function Entrar() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const modo = params.get("modo") === "cadastro" ? "cadastro" : "login";

  const [campos, setCampos] = useState({ nome: "", email: "", senha: "" });
  const [erros, setErros] = useState({});
  const [enviando, setEnviando] = useState(false);

  if (localStorage.getItem("token")) return <Navigate to="/nova" replace />;

  function trocarModo(novo) {
    setErros({});
    setParams(novo === "cadastro" ? { modo: "cadastro" } : {});
  }

  function mudar(evento) {
    const { name, value } = evento.target;
    setCampos({ ...campos, [name]: value });
    setErros({ ...erros, [name]: undefined });
  }

  async function enviar(evento) {
    evento.preventDefault();
    setEnviando(true);
    setErros({});
    const url = modo === "cadastro" ? "/api/auth/cadastro/" : "/api/auth/login/";
    const corpo = modo === "cadastro" ? campos : { email: campos.email, senha: campos.senha };
    try {
      const resposta = await api.post(url, corpo);
      localStorage.setItem("token", resposta.data.token);
      navigate("/nova");
    } catch (erro) {
      // 400 de validação: {campo: [mensagens]} e {non_field_errors: [...]}
      if (erro.response?.status === 400 && typeof erro.response.data === "object") {
        setErros(erro.response.data);
      } else {
        setErros({ non_field_errors: [mensagemDeErro(erro)] });
      }
      setEnviando(false);
    }
  }

  function campo(nome, rotulo, props = {}) {
    const mensagens = erros[nome];
    return (
      <div className="mb-3">
        <label htmlFor={nome} className="form-label fw-semibold small">{rotulo}</label>
        <input
          id={nome}
          name={nome}
          className={`form-control form-control-lg ${mensagens ? "is-invalid" : ""}`}
          value={campos[nome]}
          onChange={mudar}
          {...props}
        />
        {mensagens && <div className="invalid-feedback">{mensagens.join(" ")}</div>}
      </div>
    );
  }

  const cadastro = modo === "cadastro";

  return (
    <div className="container-fluid">
      <div className="row min-vh-100">
        <div className="col-lg-6 painel-tinta d-none d-lg-flex flex-column justify-content-center p-5">
          <Plaquinhas texto="BOA VIAGEM" tamanho="lg" className="mb-4" />
          <p className="fs-5 text-white-50 mb-0">
            Suas simulações ficam salvas na sua conta.
            <br />
            Compare destinos e volte nelas quando quiser.
          </p>
        </div>

        <div className="col-lg-6 bg-white d-flex flex-column p-4 p-md-5">
          <Marca />
          <div className="my-auto mx-auto w-100 py-5" style={{ maxWidth: 460 }}>
            <ul className="nav nav-underline mb-4 border-bottom">
              <li className="nav-item">
                <button type="button" className={`nav-link ${!cadastro ? "active" : ""}`} onClick={() => trocarModo("login")}>
                  Entrar
                </button>
              </li>
              <li className="nav-item">
                <button type="button" className={`nav-link ${cadastro ? "active" : ""}`} onClick={() => trocarModo("cadastro")}>
                  Criar conta
                </button>
              </li>
            </ul>

            <h1 className="mb-4">{cadastro ? "Crie sua conta" : "Que bom te ver de novo"}</h1>

            <form onSubmit={enviar} noValidate>
              {erros.non_field_errors && (
                <div className="alert alert-danger py-2" role="alert">
                  {erros.non_field_errors.join(" ")}
                </div>
              )}

              {cadastro && campo("nome", "Nome (opcional)", { autoComplete: "name" })}
              {campo("email", "E-mail", { type: "email", autoComplete: "email", required: true })}
              {campo("senha", "Senha", {
                type: "password",
                autoComplete: cadastro ? "new-password" : "current-password",
                required: true,
              })}
              {cadastro && <p className="form-text mt-n2 mb-3">Pelo menos 8 caracteres.</p>}

              <button type="submit" className="btn btn-tinta btn-lg w-100" disabled={enviando}>
                {enviando && <span className="spinner-border spinner-border-sm me-2" aria-hidden="true" />}
                {cadastro ? "Criar conta" : "Entrar"}
              </button>
            </form>

            <p className="text-center text-secondary mt-3 mb-0">
              {cadastro ? "Já tem conta? " : "Ainda não tem conta? "}
              <button type="button" className="btn btn-link p-0 fw-semibold align-baseline" onClick={() => trocarModo(cadastro ? "login" : "cadastro")}>
                {cadastro ? "Entrar" : "Criar conta"}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
