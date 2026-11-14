import { useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import Marca from "../components/Marca";
import Placa from "../components/Placa";
import api, { estaLogado, guardarSessao, mensagemDeErro } from "../api";

export default function Entrar() {
  const navigate = useNavigate();
  // A aba vem do endereço: /entrar (login) ou /entrar?aba=criar (cadastro).
  const [params, setParams] = useSearchParams();
  const criando = params.get("aba") === "criar";

  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);

  if (estaLogado()) return <Navigate to="/nova" replace />;

  function trocarAba(cadastro) {
    setErro("");
    setParams(cadastro ? { aba: "criar" } : {});
  }

  async function enviar(evento) {
    evento.preventDefault();
    setErro("");
    setEnviando(true);
    try {
      const rota = criando ? "/api/auth/cadastro/" : "/api/auth/login/";
      const corpo = criando ? { nome, email, senha } : { email, senha };
      const { data } = await api.post(rota, corpo);
      guardarSessao(data); // guarda o token e o usuário no navegador
      navigate("/nova");
    } catch (e) {
      setErro(mensagemDeErro(e));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="tela-dividida tela-entrar">
      <section className="lado-escuro">
        <Marca claro />
        <div className="miolo">
          <Placa texto="BOA VIAGEM" tamanho="lg" />
          <p className="texto-apoio-escuro">
            Suas simulações ficam salvas na sua conta. Compare destinos e volte nelas quando quiser.
          </p>
        </div>
        <span />
      </section>

      <section className="lado-branco">
        <div className="caixa-form">
          <div className="abas" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={!criando}
              className={!criando ? "ativa" : ""}
              onClick={() => trocarAba(false)}
            >
              Entrar
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={criando}
              className={criando ? "ativa" : ""}
              onClick={() => trocarAba(true)}
            >
              Criar conta
            </button>
          </div>

          <h1 className="h2 mb-4">{criando ? "Crie sua conta" : "Que bom te ver de novo"}</h1>

          <form onSubmit={enviar} noValidate>
            {criando && (
              <div className="mb-3">
                <label htmlFor="nome" className="form-label fw-bold small">
                  Nome (opcional)
                </label>
                <input
                  id="nome"
                  className="form-control form-control-lg"
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  autoComplete="name"
                />
              </div>
            )}

            <div className="mb-3">
              <label htmlFor="email" className="form-label fw-bold small">E-mail</label>
              <input
                id="email"
                type="email"
                className="form-control form-control-lg"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>

            <div className="mb-3">
              <label htmlFor="senha" className="form-label fw-bold small">Senha</label>
              <input
                id="senha"
                type="password"
                className="form-control form-control-lg"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                autoComplete={criando ? "new-password" : "current-password"}
                required
              />
              {criando && <div className="form-text">Pelo menos 8 caracteres.</div>}
            </div>

            {erro && (
              <div className="caixa-erro" role="alert">
                {erro}
              </div>
            )}

            <button type="submit" className="btn btn-tinta btn-lg w-100" disabled={enviando}>
              {enviando ? "Um momento..." : criando ? "Criar conta" : "Entrar"}
            </button>
          </form>

          <p className="text-center text-secondary mt-4 mb-0">
            {criando ? "Já tem conta? " : "Ainda não tem conta? "}
            <a
              href="#"
              className="fw-bold"
              onClick={(e) => {
                e.preventDefault();
                trocarAba(!criando);
              }}
            >
              {criando ? "Entrar" : "Criar conta"}
            </a>
          </p>
          <p className="text-center mt-3 mb-0 small">
            <Link to="/">Voltar para o início</Link>
          </p>
        </div>
      </section>
    </div>
  );
}
