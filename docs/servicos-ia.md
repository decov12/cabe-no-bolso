# Serviços de busca e IA

Como chamar a parte de preços e IA do backend. O código fica em `backend/api/servicos/`:

| Arquivo | O que faz |
| --- | --- |
| `simulacao.py` | `simular(...)`: junta tudo e devolve o resultado da simulação |
| `serpapi.py` | `buscar(engine, params)` e as buscas de lugares, voos, hotéis e calendário |
| `gemini.py` | Estimativa de comida, passeios e transporte, com os prompts versionados |
| `veredito.py` | Soma dos gastos e regra do veredito (margem de 15%) |
| `alternativas.py` | Outro mês, menos noites e hotel mais simples |
| `erros.py` | `ErroEntrada` e `ErroServicoExterno` |
| `precisao.py` | Leitura do CSV do teste de precisão (comandos das tarefas #29 e #30) |

**Regra central:** quem soma os custos e decide o veredito é o código. O Gemini só estima comida, passeios e transporte, por pessoa por dia, e o código multiplica e soma.

## `simular()` (para o `POST /api/simulacoes/`)

```python
from api.servicos.simulacao import simular
from api.servicos.erros import ErroEntrada, ErroServicoExterno

try:
    resultado = simular(
        origem="GRU",                    # código do aeroporto (str)
        destino="LIS",
        data_ida=date(2027, 3, 10),      # datetime.date
        data_volta=date(2027, 3, 17),
        orcamento=Decimal("9000"),       # total do grupo
        pessoas=2,                       # int, de 1 a 9
        interesses=["museus", "gastronomia"],  # list[str], até 10
    )
except ErroEntrada as erro:
    return Response({"erro": erro.mensagem}, status=400)
except ErroServicoExterno as erro:
    return Response({"erro": erro.mensagem}, status=503)
```

Há um parâmetro opcional `versao_prompt="v1"` (ou `"v2"`) usado nos testes de prompt. O endpoint não precisa dele.

### Saída

Valores em dinheiro são `Decimal` com 2 casas. No DRF, use `DecimalField` ou converta com `str()` antes de salvar em JSON.

```python
{
  "cidade_destino": "Lisboa",
  "veredito": "cabe_com_ajustes",          # "cabe" | "cabe_com_ajustes" | "nao_cabe"
  "orcamento": Decimal("9000.00"),
  "total_estimado": Decimal("10104.00"),
  "diferenca": Decimal("-1104.00"),        # orçamento − total; negativo = falta dinheiro
  "noites": 7,
  "gastos": [
    {"categoria": "passagem",   "valor": Decimal("3860.00"), "estimativa_ia": False},
    {"categoria": "hotel",      "valor": Decimal("2674.00"), "estimativa_ia": False},
    {"categoria": "comida",     "valor": Decimal("2240.00"), "estimativa_ia": True},
    {"categoria": "passeios",   "valor": Decimal("980.00"),  "estimativa_ia": True},
    {"categoria": "transporte", "valor": Decimal("350.00"),  "estimativa_ia": True},
  ],
  "passagem": {"companhia": "LATAM", "preco_por_pessoa": Decimal("1930.00"),
               "preco_total": Decimal("3860.00"), "link_google_voos": "https://www.google.com/travel/flights?..."},
  "hotel": {"nome": "R & Freud B&B", "estrelas": 3, "nota": 4.5, "preco_noite": Decimal("382.00"),
            "preco_total": Decimal("2674.00"), "link": None},
  "precos_por_mes": [{"mes": "2027-01", "menor_preco": Decimal("...")}, ...],
  "alternativas": [
    {"tipo": "menos_noites", "descricao": "Ficar 5 noites em vez de 7 (voltar em 15/03/2027)...",
     "novo_total": Decimal("8320.00"), "novo_veredito": "cabe", "economia": Decimal("1784.00")},
    {"tipo": "hotel_mais_simples", "descricao": "Ficar no Ibis Lisboa Jose Malhoa Hotel (2 estrelas, nota 4.2)...",
     "novo_total": Decimal("9824.00"), "novo_veredito": "cabe_com_ajustes", "economia": Decimal("280.00")},
  ],
  "estimativa_ia": {"por_pessoa_dia": {"comida": Decimal("160.00"), ...}, "justificativas": {"comida": "...", ...}},
  "buscas_serpapi": 3,
  "versao_prompt": "v1",
}
```

A rota `POST /api/simulacoes/` salva esse resultado e o devolve em JSON, com o dinheiro como texto ("9000.00"). O contrato da API para o frontend está em [api.md](api.md).

Estes são os números de verdade do teste de ponta a ponta, feito com as fixtures. Detalhes:

- **Veredito:** "cabe" se total ≤ orçamento; "cabe_com_ajustes" se total ≤ orçamento × 1,15; "nao_cabe" acima disso. A margem fica em `veredito.MARGEM_AJUSTE`.
- **Passagem:** preço por pessoa (ida e volta) × pessoas. Usa o menor preço de `best_flights`. Se essa lista vier vazia, usa a mediana de `other_flights`, porque há preços extremos.
- **Hotel:** preço por noite × noites × quartos. O preço do Google é de 1 quarto para 2 adultos, então quartos = teto(pessoas ÷ 2). O hotel escolhido é o mais barato com 3 estrelas ou mais e nota 4 ou mais. `hotel["link"]` e `hotel["estrelas"]` podem ser `None`.
- **Comida, passeios e transporte:** valor do Gemini por pessoa por dia × noites × pessoas.
- **`precos_por_mes`:** menor preço de passagem por pessoa em cada mês, numa janela de 6 meses que começa 2 meses antes da ida. O Google calcula esse calendário com viagens de **7 noites**.
- **`alternativas`:** só aparecem quando o veredito não é "cabe", e só as que reduzem o total. Nenhuma gasta busca extra. Pode vir vazia.
  - `outro_mes`: o mês mais barato do calendário. Troca só a passagem.
  - `menos_noites`: tira 1 noite por vez até caber, com mínimo de 2.
  - `hotel_mais_simples`: o hotel mais barato da mesma busca com nota ≥ 3,5.

### Exceções

| Exceção | Quando | Sugestão de status |
| --- | --- | --- |
| `ErroEntrada` | Volta antes da ida ou no mesmo dia, ida no passado, mais de 30 noites, orçamento ≤ 0, pessoas fora de 1 a 9, código de aeroporto inválido, origem igual ao destino. Também quando não há voo ou hotel para a rota e as datas. | 400 |
| `ErroServicoExterno` | A SerpApi ou o Gemini falharam duas vezes (a 1ª tentativa e mais 1), não há chave configurada ou o Gemini respondeu um JSON inválido ou com valores absurdos duas vezes. | 503 |

`erro.mensagem` está em português, pronta para a tela, e nunca contém chave.

## Quantas buscas cada simulação gasta

| Chamada | Buscas da SerpApi |
| --- | --- |
| Voos | 1 |
| Hotéis | 1 |
| Calendário (6 meses) | 1 |
| Cidade do destino | 0 se o código estiver em `serpapi.CIDADES_POR_AEROPORTO` (cerca de 120 aeroportos comuns); senão 1 (autocomplete) |
| **Total** | **3**, ou **4** com destino fora do mapeamento |
| Gemini | 1 chamada (2 se a 1ª falhar) |

O Gemini é chamado **antes** da SerpApi. Assim, se ele falhar, nenhuma busca é gasta. Se a simulação levantar exceção, `buscas_serpapi` não chega à view. O limite diário (#25, `api/limites.py`) conta simulações salvas: 5 por pessoa por dia, ou seja, no máximo 20 buscas por pessoa por dia, e menos quando há cache.

A cota gratuita é de 250 buscas por mês e 50 por hora, ou seja, umas **60 a 80 simulações por mês**.

### Cache de 24 horas (#24)

Implementado em `cache.py`. Todas as buscas passam por `serpapi.buscar(engine, params)`. Ela procura a resposta no cache (chave = SHA-256 de `engine` + `params`) e só chama a SerpApi de verdade (`_buscar_na_api`, com timeout de 30 s e 1 nova tentativa) se não achar. Respostas com falha não ficam guardadas. A estimativa do Gemini também fica no cache, com chave = modelo + texto do prompt, então a mesma viagem dá os mesmos números durante 24 horas.

O cache é o do Django (`settings.CACHES`), guardado na tabela `cache_respostas` do banco. Essa tabela é criada pela migração `api/0003`. Nos testes, `CACHES` usa `DummyCache`, que não guarda nada. Se o cache falhar, a busca é feita normalmente e só não fica guardada.

`buscas_serpapi` continua contando as buscas da simulação, venham elas do cache ou não.

## `buscar_lugares()` (para o `GET /api/lugares/?q=`)

```python
from api.servicos.serpapi import buscar_lugares

buscar_lugares("Lisboa")   # 1 busca; texto com menos de 2 letras devolve [] sem gastar busca
```

```python
[
  {"tipo": "cidade",    "nome": "Lisboa", "codigo": "LIS", "pais": "Portugal", "descricao": "Capital de Portugal"},
  {"tipo": "aeroporto", "nome": "Aeroporto Humberto Delgado", "codigo": "LIS", "pais": "Portugal",
   "cidade": "Lisboa", "distancia": "5 km"},
  {"tipo": "cidade",    "nome": "Santo Antônio de Lisboa", "codigo": "FLN", "pais": None, "descricao": "Florianópolis"},
  {"tipo": "aeroporto", "nome": "Aeroporto Internacional de Florianópolis - Hercílio Luz", "codigo": "FLN", ...},
  ...
]
```

Cada cidade vem seguida dos seus aeroportos, na ordem do Google. O autocomplete traz sugestões irrelevantes, como "Santo Antônio de Lisboa" para "Lisboa", por isso a escolha fica com a tela. O `codigo` de uma cidade é o do seu primeiro aeroporto, que é o que vai para `simular()`. A rota pode levantar `ErroServicoExterno`. Vale usar o cache aqui também, porque cada letra digitada gastaria uma busca: chame só depois de uma pausa na digitação (debounce) ou com o botão "buscar".

## Gemini

- Modelo: `GEMINI_MODEL` no `.env`. Vazio usa `gemini-3.5-flash-lite`, que é estável e está no nível gratuito. Isso foi conferido na documentação oficial em 13/11/2026.
- Chamada: `client.interactions.create(...)` com `response_format` em JSON e schema (SDK `google-genai`).
- Prompts versionados em `gemini.PROMPTS`. A **v1** é o pedido direto. A **v2** pede para considerar a estação do ano, o custo de vida local e faixas de preço.
- O código valida a resposta: números, faixas plausíveis e justificativa presente. Se algo falhar, faz 1 nova tentativa e depois levanta `ErroServicoExterno`.

## Verificação real (13/11/2026)

Uma simulação de verdade, GRU→LIS de 10/03 a 17/03/2027, 2 pessoas, orçamento de R$ 9.000, gastou **3 buscas** e 1 chamada ao Gemini. Ela confirmou que:

- a chamada `interactions.create` com schema JSON e o modelo `gemini-3.5-flash-lite` funcionam;
- o calendário aceita a janela de 6 meses inteiros (01/01 a 30/06) e devolveu os 6 meses;
- os parsers leem as respostas atuais sem erro.

Resultado: passagem R$ 4.356 por pessoa (LATAM), hotel Green View Home a R$ 200 por noite, comida R$ 180, passeios R$ 65 e transporte R$ 35 por pessoa por dia. Total de R$ 14.032, veredito "nao_cabe" e 3 alternativas.

## Testes e comandos

```bash
cd backend
python manage.py test                  # nenhum teste chama as APIs de verdade
python manage.py teste_precisao        # #29: roda as viagens de docs/teste-de-precisao/viagens.csv (GASTA COTA, pede confirmação)
python manage.py comparar_prompts      # #30: só o Gemini, v1 × v2 (pede confirmação)
```

Formato do CSV: datas em AAAA-MM-DD, interesses separados por `;` e gastos reais do **grupo** na viagem toda. Linhas com `fonte` começando por "EXEMPLO" são ignoradas. As viagens que já aconteceram são simuladas no mesmo período de um ano futuro, porque a SerpApi só busca datas futuras. Use `--limite N` para dividir em lotes e não passar de 50 buscas por hora.
