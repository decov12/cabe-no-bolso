import "./Plaquinhas.css";

// Texto em plaquinhas, como no painel de partidas dos aeroportos (identidade visual do projeto).
export default function Plaquinhas({ texto, tamanho = "md", className = "" }) {
  return (
    <div className={`plaquinhas plaquinhas-${tamanho} ${className}`} aria-label={texto} role="img">
      {texto.split(" ").map((palavra, i) => (
        <span key={i} className="plaquinhas-palavra">
          {[...palavra].map((letra, j) => (
            <span key={j} className="plaquinha">{letra}</span>
          ))}
        </span>
      ))}
    </div>
  );
}
