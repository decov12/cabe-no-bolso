# API do backend

Endereço base: `http://localhost:8000/api/` em desenvolvimento, ou o endereço do Render em produção (variável `VITE_API_URL` do frontend).

Todas as rotas, menos cadastro e login, exigem o cabeçalho `Authorization: Token <token>`. O `frontend/src/api.js` já envia esse cabeçalho. Sem token, a resposta é **401**.

Dinheiro vem como **texto com 2 casas** (`"9000.00"`). Use `formatarReais()` de `frontend/src/formatar.js`. Datas vêm como `AAAA-MM-DD`.

| Método | Rota | Para quê | Tela |
| --- | --- | --- | --- |
| POST | `/api/auth/cadastro/` | Criar conta (devolve token) | 2 |
| POST | `/api/auth/login/` | Entrar (devolve token) | 2 |
| GET | `/api/auth/eu/` | Dados do usuário logado | barra do topo |
| GET | `/api/lugares/?q=Lisb` | Sugestões de cidade e aeroporto | 3 |
| POST | `/api/simulacoes/` | Simular e salvar no histórico | 3 → 4 → 5 |
| GET | `/api/simulacoes/` | Histórico, da mais recente para a mais antiga | 7 e "Últimas simulações" da 3 |
| GET | `/api/simulacoes/<id>/` | Reabrir uma simulação | 5 e 6 |
| DELETE | `/api/simulacoes/<id>/` | Apagar do histórico (responde 204) | 7 |
| GET | `/api/simulacoes/limite/` | Quantas simulações ainda dá para fazer hoje | 3 |

## Erros

| Status | Formato | Quando |
| --- | --- | --- |
| 400 | `{"campo": ["mensagem"]}` | Campo faltando ou em formato errado |
| 400 | `{"erro": "mensagem"}` | Regra da viagem: volta antes da ida, sem voo ou hotel para as datas... |
| 404 | `{"detail": "..."}` | Simulação não existe ou é de outra pessoa |
| 429 | `{"erro": "mensagem", "limite_diario": {...}}` | Passou do limite diário (simulações ou buscas de lugar) |
| 503 | `{"erro": "mensagem"}` | SerpApi ou Gemini fora do ar |

O `mensagemDeErro()` de `formatar.js` já lê todos esses formatos. As mensagens estão em português.

## Simulação (POST e GET `/api/simulacoes/<id>/`)

O formato da resposta está em [servicos-ia.md](servicos-ia.md#saída). Ela tem tudo o que `simular()` devolve, com o dinheiro como texto, mais `id`, `criado_em`, `origem`, `destino`, `cidade_destino`, `data_ida`, `data_volta`, `pessoas` e `interesses`. Dois campos ajudam a explicar a conta na tela:

- `cidade_destino`: nome da cidade (`"Lisboa"`), para mostrar no lugar do código `LIS`.
- `estimativa_ia`: `{"por_pessoa_dia": {"comida": "160.00", ...}, "justificativas": {"comida": "Café da manhã simples, ...", ...}}`.

## Histórico (`GET /api/simulacoes/`)

É uma lista. Cada item tem `id`, `origem`, `destino`, `cidade_destino`, `data_ida`, `data_volta`, `orcamento`, `veredito`, `total_estimado` e `criado_em`. Os cartões da tela 7 (simulações, quantas cabem, destinos diferentes) saem da própria lista. Nas simulações feitas antes do campo existir, `cidade_destino` vem vazio, e aí vale mostrar o `destino`.

## Limite diário (`GET /api/simulacoes/limite/`)

```json
{"limite": 5, "usadas_hoje": 2, "restantes": 3}
```

- Cada pessoa faz até 5 simulações por dia (`LIMITE_SIMULACOES_DIA`). O dia vira à meia-noite de Brasília.
- Simulações com erro não contam.
- Reabrir uma simulação do histórico não gasta nada.
- Contas da equipe (`is_staff`) recebem `limite` e `restantes` iguais a `null`, ou seja, sem limite.
- As sugestões de lugar têm um limite próprio de 60 buscas por dia (`LIMITE_LUGARES_DIA`).

## Cache de 24 horas

Toda busca na SerpApi e toda estimativa do Gemini ficam guardadas por 24 horas na tabela `cache_respostas` do banco. Se a mesma rota for buscada de novo com as mesmas datas, a resposta vem do cache: não gasta cota, e a estimativa da IA não muda. Mesmo assim, a simulação repetida conta no limite diário.
