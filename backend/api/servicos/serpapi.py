"""Cliente da SerpApi (tarefas #12 e #13): autocomplete, voos, hotéis e calendário.

Todas as chamadas passam por buscar(engine, params), que tem o cache de
24 horas (#24, veja cache.py).

Cota gratuita: 250 buscas por mês e 50 por hora. Cada chamada bem-sucedida de
buscar() gasta 1 busca. Os testes nunca chamam a SerpApi de verdade.
"""

import statistics
import time
from collections import OrderedDict

import requests
from django.conf import settings

from . import cache
from .erros import ErroEntrada, ErroServicoExterno
from .veredito import arredondar

URL_SERPAPI = "https://serpapi.com/search.json"
TIMEOUT_SEGUNDOS = 30
PAUSA_NOVA_TENTATIVA = 1  # segundos entre a 1ª tentativa e a nova tentativa

# Idioma, país e moeda de todas as buscas de preço.
PARAMETROS_REGIONAIS = {"hl": "pt", "gl": "br", "currency": "BRL"}

# A SerpApi responde com este texto quando o Google não tem resultados. Não é
# falha do serviço: os parsers recebem a resposta e tratam a lista vazia.
TEXTO_SEM_RESULTADOS = "hasn't returned any results"

# Nome da cidade usado na busca de hotel (google_hotels precisa de texto, não
# de código). Escolha: um mapeamento simples código -> cidade para os aeroportos
# mais comuns, que não gasta busca. Se o código não estiver aqui, usamos o
# autocomplete (1 busca a mais) e pegamos a cidade que tem aquele aeroporto.
CIDADES_POR_AEROPORTO = {
    # Brasil
    "GRU": "São Paulo", "CGH": "São Paulo", "VCP": "Campinas",
    "GIG": "Rio de Janeiro", "SDU": "Rio de Janeiro", "BSB": "Brasília",
    "CNF": "Belo Horizonte", "PLU": "Belo Horizonte", "SSA": "Salvador",
    "REC": "Recife", "FOR": "Fortaleza", "NAT": "Natal", "MCZ": "Maceió",
    "AJU": "Aracaju", "JPA": "João Pessoa", "SLZ": "São Luís", "THE": "Teresina",
    "BEL": "Belém", "MAO": "Manaus", "POA": "Porto Alegre", "CWB": "Curitiba",
    "FLN": "Florianópolis", "NVT": "Navegantes", "IGU": "Foz do Iguaçu",
    "VIX": "Vitória", "GYN": "Goiânia", "CGB": "Cuiabá", "CGR": "Campo Grande",
    "BPS": "Porto Seguro", "FEN": "Fernando de Noronha",
    # América do Sul
    "EZE": "Buenos Aires", "AEP": "Buenos Aires", "BRC": "Bariloche",
    "MDZ": "Mendoza", "SCL": "Santiago", "MVD": "Montevidéu",
    "PDP": "Punta del Este", "LIM": "Lima", "CUZ": "Cusco", "BOG": "Bogotá",
    "CTG": "Cartagena", "MDE": "Medellín", "ASU": "Assunção", "UIO": "Quito",
    # América do Norte e Caribe
    "MIA": "Miami", "MCO": "Orlando", "FLL": "Fort Lauderdale",
    "JFK": "Nova York", "EWR": "Nova York", "LGA": "Nova York",
    "LAX": "Los Angeles", "SFO": "São Francisco", "LAS": "Las Vegas",
    "ORD": "Chicago", "BOS": "Boston", "IAD": "Washington", "YYZ": "Toronto",
    "YUL": "Montreal", "MEX": "Cidade do México", "CUN": "Cancún",
    "PUJ": "Punta Cana", "HAV": "Havana", "PTY": "Cidade do Panamá",
    # Europa
    "LIS": "Lisboa", "OPO": "Porto", "FAO": "Faro", "MAD": "Madri",
    "BCN": "Barcelona", "CDG": "Paris", "ORY": "Paris", "LHR": "Londres",
    "LGW": "Londres", "STN": "Londres", "FCO": "Roma", "CIA": "Roma",
    "MXP": "Milão", "LIN": "Milão", "VCE": "Veneza", "FLR": "Florença",
    "NAP": "Nápoles", "AMS": "Amsterdã", "BRU": "Bruxelas", "FRA": "Frankfurt",
    "MUC": "Munique", "BER": "Berlim", "ZRH": "Zurique", "GVA": "Genebra",
    "VIE": "Viena", "PRG": "Praga", "BUD": "Budapeste", "DUB": "Dublin",
    "EDI": "Edimburgo", "CPH": "Copenhague", "ARN": "Estocolmo", "OSL": "Oslo",
    "ATH": "Atenas", "IST": "Istambul",
    # África, Ásia e Oceania
    "CPT": "Cidade do Cabo", "JNB": "Joanesburgo", "CMN": "Casablanca",
    "CAI": "Cairo", "DXB": "Dubai", "DOH": "Doha", "TLV": "Tel Aviv",
    "NRT": "Tóquio", "HND": "Tóquio", "KIX": "Osaka", "ICN": "Seul",
    "PEK": "Pequim", "PVG": "Xangai", "HKG": "Hong Kong", "SIN": "Singapura",
    "BKK": "Bangcoc", "DPS": "Bali", "SYD": "Sydney", "MEL": "Melbourne",
    "AKL": "Auckland",
}


# ---------------------------------------------------------------------------
# Cliente único
# ---------------------------------------------------------------------------

def buscar(engine, params):
    """Faz 1 busca na SerpApi e devolve o JSON (dict).

    - Cache de 24 horas (#24): a mesma busca (engine + params) feita de novo
      nesse período devolve a resposta guardada e não gasta cota.
    - Usa timeout e faz 1 nova tentativa se a primeira falhar.
    - Levanta ErroServicoExterno se as duas tentativas falharem.
    - Respostas "sem resultados" voltam normalmente, para o parser tratar.

    As mensagens de erro nunca incluem a URL nem a chave.
    """
    if not settings.SERPAPI_KEY:
        raise ErroServicoExterno("A chave da SerpApi não está configurada (SERPAPI_KEY).")

    chave_cache = cache.montar_chave("serpapi", engine, params)
    guardado = cache.obter(chave_cache)
    if guardado is not None:
        return guardado

    dados = _buscar_na_api(engine, params)
    cache.guardar(chave_cache, dados)
    return dados


def _buscar_na_api(engine, params):
    """A busca de verdade (gasta 1 busca da cota), com 1 nova tentativa."""
    parametros = {**params, "engine": engine, "api_key": settings.SERPAPI_KEY}
    motivo = ""
    for tentativa in range(2):
        if tentativa:
            time.sleep(PAUSA_NOVA_TENTATIVA)
        try:
            resposta = requests.get(URL_SERPAPI, params=parametros, timeout=TIMEOUT_SEGUNDOS)
        except requests.Timeout:
            motivo = "tempo esgotado"
            continue
        except requests.RequestException as erro:
            # Não usamos str(erro): ela pode conter a URL com a chave.
            motivo = f"falha de conexão ({type(erro).__name__})"
            continue

        try:
            dados = resposta.json()
        except ValueError:
            motivo = f"resposta inválida (HTTP {resposta.status_code})"
            continue

        erro_api = dados.get("error") if isinstance(dados, dict) else None
        if erro_api and TEXTO_SEM_RESULTADOS in str(erro_api):
            return dados
        if resposta.status_code >= 400 or erro_api or not isinstance(dados, dict):
            motivo = f"HTTP {resposta.status_code}"
            if erro_api:
                motivo += f": {str(erro_api)[:200]}"
            continue
        return dados

    raise ErroServicoExterno(f"A busca de preços ({engine}) falhou: {motivo}.")


# ---------------------------------------------------------------------------
# Autocomplete (#12)
# ---------------------------------------------------------------------------

def _separar_cidade_pais(nome):
    """'Lisboa, Portugal' -> ('Lisboa', 'Portugal'). Sem vírgula, o país fica None."""
    if ", " in nome:
        cidade, pais = nome.rsplit(", ", 1)
        return cidade, pais
    return nome, None


def interpretar_autocomplete(dados):
    """Organiza as sugestões do google_flights_autocomplete numa lista plana.

    Cada cidade vem seguida dos seus aeroportos, na ordem do Google. O autocomplete
    traz sugestões irrelevantes (ex.: "Santo Antônio de Lisboa" para "Lisboa"),
    por isso não escolhemos nada aqui: a tela mostra a lista e a pessoa escolhe.
    O "codigo" de uma cidade é o do seu primeiro aeroporto (o mais próximo).
    """
    lugares = []
    for sugestao in dados.get("suggestions") or []:
        nome, pais = _separar_cidade_pais(sugestao.get("name", ""))
        aeroportos = sugestao.get("airports") or []
        if sugestao.get("type") == "city":
            lugares.append({
                "tipo": "cidade",
                "nome": nome,
                "codigo": aeroportos[0].get("id") if aeroportos else None,
                "pais": pais,
                "descricao": sugestao.get("description"),
            })
        elif sugestao.get("type") == "airport" and sugestao.get("id"):
            # Sugestão que já é um aeroporto, sem cidade em volta.
            lugares.append({
                "tipo": "aeroporto",
                "nome": nome,
                "codigo": sugestao.get("id"),
                "pais": pais,
                "cidade": sugestao.get("city"),
                "distancia": None,
            })
        for aeroporto in aeroportos:
            if not aeroporto.get("id"):
                continue
            lugares.append({
                "tipo": "aeroporto",
                "nome": aeroporto.get("name"),
                "codigo": aeroporto.get("id"),
                "pais": pais,
                "cidade": aeroporto.get("city"),
                "distancia": aeroporto.get("distance"),
            })
    return lugares


def buscar_lugares(texto):
    """Sugestões de cidades e aeroportos para a rota GET /api/lugares/?q=.

    Texto com menos de 2 letras devolve [] sem gastar busca.
    """
    texto = (texto or "").strip()
    if len(texto) < 2:
        return []
    dados = buscar("google_flights_autocomplete", {"q": texto, "hl": "pt", "gl": "br"})
    return interpretar_autocomplete(dados)


def cidade_do_aeroporto(codigo):
    """Nome da cidade de um aeroporto, para a busca de hotel e para o Gemini.

    Devolve (cidade, buscas_gastas): 0 buscas se o código está em
    CIDADES_POR_AEROPORTO, 1 busca se precisou do autocomplete.
    """
    codigo = codigo.upper()
    if codigo in CIDADES_POR_AEROPORTO:
        return CIDADES_POR_AEROPORTO[codigo], 0
    for lugar in buscar_lugares(codigo):
        if lugar["tipo"] == "aeroporto" and lugar["codigo"] == codigo and lugar.get("cidade"):
            return lugar["cidade"], 1
    raise ErroEntrada(f"Não encontramos a cidade do aeroporto {codigo}.")


# ---------------------------------------------------------------------------
# Voos (#12)
# ---------------------------------------------------------------------------

def _companhias(opcao):
    nomes = []
    for trecho in opcao.get("flights") or []:
        nome = trecho.get("airline")
        if nome and nome not in nomes:
            nomes.append(nome)
    return " + ".join(nomes) or None


def _opcoes_com_preco(lista):
    return [opcao for opcao in lista or [] if isinstance(opcao.get("price"), (int, float)) and opcao["price"] > 0]


def interpretar_voos(dados):
    """Escolhe o preço da passagem numa resposta do google_flights.

    O preço é por pessoa, ida e volta, em BRL. Há valores extremos (ex.: R$ 6.777
    contra R$ 1.930 na mesma rota), então a regra é:
    1. o MENOR preço de best_flights (as opções que o Google considera melhores);
    2. se best_flights vier vazio, a MEDIANA de other_flights. Usamos a mediana
       "baixa" (statistics.median_low) para o valor ser o de uma opção real,
       com companhia definida, e não a média de duas.
    Devolve None se não houver nenhuma opção com preço.
    """
    melhores = _opcoes_com_preco(dados.get("best_flights"))
    if melhores:
        escolhida = min(melhores, key=lambda opcao: opcao["price"])
        criterio = "menor_preco_best_flights"
    else:
        outras = _opcoes_com_preco(dados.get("other_flights"))
        if not outras:
            return None
        mediana = statistics.median_low([opcao["price"] for opcao in outras])
        escolhida = next(opcao for opcao in outras if opcao["price"] == mediana)
        criterio = "mediana_other_flights"

    metadados = dados.get("search_metadata") or {}
    return {
        "companhia": _companhias(escolhida),
        "preco_por_pessoa": arredondar(escolhida["price"]),
        "link_google_voos": metadados.get("google_flights_url"),
        "criterio": criterio,
    }


def buscar_voos(origem, destino, ida, volta):
    """Passagem ida e volta por pessoa (1 busca).

    origem e destino são códigos de aeroporto (ex.: GRU, LIS). Código de cidade
    como BUE volta vazio no Google Voos, por isso usamos o do aeroporto.
    """
    dados = buscar("google_flights", {
        "departure_id": origem.upper(),
        "arrival_id": destino.upper(),
        "outbound_date": ida.isoformat(),
        "return_date": volta.isoformat(),
        **PARAMETROS_REGIONAIS,
    })
    voo = interpretar_voos(dados)
    if voo is None:
        raise ErroEntrada(
            f"Não encontramos voos de {origem.upper()} para {destino.upper()} nessas datas. "
            "Confira os códigos dos aeroportos e as datas."
        )
    return voo


# ---------------------------------------------------------------------------
# Hotéis (#13)
# ---------------------------------------------------------------------------

def _numero(valor):
    return valor if isinstance(valor, (int, float)) and not isinstance(valor, bool) else None


def interpretar_hoteis(dados, noites=None):
    """Lista de hotéis de uma resposta do google_hotels, ordenada por preço.

    - Ignora "ads" (anúncios) e itens de "properties" que não são hotel
      (ex.: "vacation rental").
    - O preço é de 1 quarto para 2 adultos, por noite. Se rate_per_night faltar,
      usa total_rate dividido pelas noites.
    - Desempate por nota (maior primeiro).
    """
    hoteis = []
    for item in dados.get("properties") or []:
        if item.get("type") != "hotel":
            continue
        preco_noite = _numero((item.get("rate_per_night") or {}).get("extracted_lowest"))
        preco_total = _numero((item.get("total_rate") or {}).get("extracted_lowest"))
        if not preco_noite and preco_total and noites:
            preco_noite = preco_total / noites
        if not preco_noite or preco_noite <= 0:
            continue
        nota = _numero(item.get("overall_rating"))
        hoteis.append({
            "nome": item.get("name"),
            "estrelas": item.get("extracted_hotel_class"),
            "nota": round(nota, 1) if nota is not None else None,
            "preco_noite": arredondar(preco_noite),
            "link": item.get("link"),
        })
    hoteis.sort(key=lambda hotel: (hotel["preco_noite"], -(hotel["nota"] or 0)))
    return hoteis


def buscar_hoteis(destino_texto, entrada, saida):
    """Hotéis na cidade (1 busca), já filtrados e ordenados por preço por noite.

    destino_texto é o nome da cidade (veja cidade_do_aeroporto). A busca é
    sempre de 1 quarto para 2 adultos; quem multiplica pelos quartos é simular().
    """
    dados = buscar("google_hotels", {
        "q": destino_texto,
        "check_in_date": entrada.isoformat(),
        "check_out_date": saida.isoformat(),
        "adults": 2,
        **PARAMETROS_REGIONAIS,
    })
    return interpretar_hoteis(dados, noites=(saida - entrada).days)


# ---------------------------------------------------------------------------
# Calendário de preços (#13)
# ---------------------------------------------------------------------------

def interpretar_calendario(dados):
    """Menor preço de passagem por mês, a partir da lista "prices".

    Não usamos o campo low_price: ele não é confiável. Cada item de "prices" é
    uma viagem de 7 noites (estadia fixa da busca de calendário), por pessoa,
    ida e volta. Devolve [{"mes": "AAAA-MM", "menor_preco": Decimal}] em ordem.
    """
    por_mes = OrderedDict()
    for item in sorted(dados.get("prices") or [], key=lambda item: item.get("outbound_date", "")):
        preco = _numero(item.get("price"))
        data = item.get("outbound_date") or ""
        if not preco or preco <= 0 or len(data) < 7:
            continue
        mes = data[:7]
        if mes not in por_mes or preco < por_mes[mes]:
            por_mes[mes] = preco
    return [{"mes": mes, "menor_preco": arredondar(preco)} for mes, preco in por_mes.items()]


def buscar_calendario(origem, destino, inicio, fim):
    """Menor preço por mês entre inicio e fim (1 busca, mesmo para 6 meses)."""
    dados = buscar("google_flights_calendar", {
        "departure_id": origem.upper(),
        "arrival_id": destino.upper(),
        "date_range_start": inicio.isoformat(),
        "date_range_end": fim.isoformat(),
        **PARAMETROS_REGIONAIS,
    })
    return interpretar_calendario(dados)
