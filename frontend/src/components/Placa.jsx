// Palavra escrita em "plaquinhas" de painel de aeroporto (uma letra por plaquinha).
// Uso: <Placa texto="NÃO CABE" />. Espaços viram um vão.
export default function Placa({ texto, tamanho = "md" }) {
  return (
    <span className={`placa placa-${tamanho}`} role="img" aria-label={texto}>
      {[...texto].map((letra, i) =>
        letra === " " ? (
          <span key={i} className="placa-vao" aria-hidden="true" />
        ) : (
          <span key={i} className="placa-letra" aria-hidden="true">
            {letra}
          </span>
        )
      )}
    </span>
  );
}
