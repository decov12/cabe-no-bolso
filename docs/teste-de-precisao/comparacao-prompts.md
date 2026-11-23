# Comparação de versões do prompt

Gerado por `python manage.py comparar_prompts` em 23/11/2026 20:32, com 10 viagem(ns) e o modelo gemini-3.5-flash-lite. Só o Gemini foi chamado; passagem e hotel não entram.

Erro percentual = |estimado − real| ÷ real × 100, sobre o gasto do grupo na viagem toda.

## Qual versão erra menos

| Categoria | Erro v1 | Erro v2 | Erra menos |
| --- | --- | --- | --- |
| comida | 27,2% | 29,6% | v1 |
| passeios | 44,4% | 40,7% | v2 |
| transporte | – | – | empate / sem dados |
| **Média geral** | 35,8% | 35,2% | v2 |

## Viagem a viagem

| # | Destino | Versão | Comida | Passeios | Transporte |
| --- | --- | --- | --- | --- | --- |
| 1 | Lisboa (LIS) | v1 | 11,3% | 24,6% | – |
| 1 | Lisboa (LIS) | v2 | 10,8% | 9,5% | – |
| 2 | Buenos Aires (EZE) | v1 | 0,0% | 37,8% | – |
| 2 | Buenos Aires (EZE) | v2 | 50,0% | 8,9% | – |
| 3 | Santiago (SCL) | v1 | 6,7% | 8,9% | – |
| 3 | Santiago (SCL) | v2 | 36,1% | 40,0% | – |
| 4 | Paris (CDG) | v1 | 0,6% | 83,1% | – |
| 4 | Paris (CDG) | v2 | 2,9% | 83,1% | – |
| 5 | Orlando (MCO) | v1 | 3,0% | 13,5% | – |
| 5 | Orlando (MCO) | v2 | 5,4% | 11,7% | – |
| 6 | Lisboa (LIS) | v1 | 52,3% | 64,5% | – |
| 6 | Lisboa (LIS) | v2 | 40,3% | 57,4% | – |
| 7 | Buenos Aires (EZE) | v1 | 60,0% | 76,7% | – |
| 7 | Buenos Aires (EZE) | v2 | 40,0% | 59,2% | – |
| 8 | Santiago (SCL) | v1 | 44,0% | 59,2% | – |
| 8 | Santiago (SCL) | v2 | 18,3% | 47,5% | – |
| 9 | Paris (CDG) | v1 | 53,1% | 37,8% | – |
| 9 | Paris (CDG) | v2 | 52,0% | 37,8% | – |
| 10 | Orlando (MCO) | v1 | 41,1% | 37,9% | – |
| 10 | Orlando (MCO) | v2 | 39,8% | 51,7% | – |

## As versões

- **v1:** pedido direto, viajante de orçamento médio.
- **v2:** pede para considerar a estação do ano, o custo de vida local e faixas de preço (econômica, média, confortável) antes de escolher o valor.

O texto completo dos prompts está em `backend/api/servicos/gemini.py` (PROMPTS).
