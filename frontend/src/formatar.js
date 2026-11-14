// Funções de formatação e de leitura de erros usadas pelas telas.

const reais = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

// A API manda dinheiro como string ("9000.00"); Number() só para formatar.
export function formatarReais(valor) {
  return reais.format(Number(valor));
}

// "2027-03-10" -> Date local (sem o deslocamento de fuso que new Date("2027-03-10") causaria).
function lerData(iso) {
  const [ano, mes, dia] = iso.split("-").map(Number);
  return new Date(ano, mes - 1, dia);
}

export function formatarData(iso) {
  return lerData(iso).toLocaleDateString("pt-BR");
}

// "10 a 17 de março de 2027" ou "28 de março a 4 de abril de 2027"
export function formatarPeriodo(ida, volta) {
  const a = lerData(ida);
  const b = lerData(volta);
  const mesAno = (d) => d.toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
  const diaMes = (d) => d.toLocaleDateString("pt-BR", { day: "numeric", month: "long" });
  if (a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth()) {
    return `${a.getDate()} a ${b.getDate()} de ${mesAno(b)}`;
  }
  if (a.getFullYear() === b.getFullYear()) {
    return `${diaMes(a)} a ${diaMes(b)} de ${b.getFullYear()}`;
  }
  return `${formatarData(ida)} a ${formatarData(volta)}`;
}

// "2027-03" -> "mar/2027"
export function formatarMes(anoMes) {
  const [ano, mes] = anoMes.split("-").map(Number);
  const nome = new Date(ano, mes - 1, 1).toLocaleDateString("pt-BR", { month: "short" });
  return `${nome.replace(".", "")}/${ano}`;
}

export const VEREDITOS = {
  cabe: { texto: "Cabe", placa: "CABE", cor: "success" },
  cabe_com_ajustes: { texto: "Cabe com ajustes", placa: "CABE COM AJUSTES", cor: "warning" },
  nao_cabe: { texto: "Não cabe", placa: "NÃO CABE", cor: "danger" },
};

// Mensagem principal de um erro do axios.
// A API responde {"erro": "..."} (regra da viagem, 503) ou {campo: [mensagens]} (formato).
export function mensagemDeErro(erro) {
  const dados = erro?.response?.data;
  if (!erro?.response) return "Não foi possível falar com o servidor. Confira sua conexão e tente de novo.";
  if (dados?.erro) return dados.erro;
  if (dados?.detail) return dados.detail;
  if (dados && typeof dados === "object") {
    const primeira = Object.values(dados).flat()[0];
    if (typeof primeira === "string") return primeira;
  }
  return "Algo deu errado. Tente de novo em instantes.";
}
