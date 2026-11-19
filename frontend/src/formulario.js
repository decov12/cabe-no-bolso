// Monta o formulário da tela 3 a partir de uma simulação salva, para refazer a
// conta com os mesmos dados: "Mudar dados" (Resultado) e "Simular de novo" (Alternativas).
// O formato é o mesmo que o CampoLugar devolve: {codigo, rotulo, nome}.
export function formularioDaSimulacao(s) {
  const lugar = (codigo, nome) => ({
    codigo,
    rotulo: nome ? `${nome} (${codigo})` : codigo,
    nome: nome || codigo,
  });
  return {
    origem: lugar(s.origem),
    destino: lugar(s.destino, s.cidade_destino),
    data_ida: s.data_ida,
    data_volta: s.data_volta,
    orcamento: String(Number(s.orcamento)),
    pessoas: s.pessoas,
    interesses: s.interesses,
  };
}
