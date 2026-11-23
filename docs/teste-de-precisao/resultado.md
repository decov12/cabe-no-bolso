# Resultado do teste de precisão

Gerado por `python manage.py teste_precisao` em 23/11/2026 20:34. Prompt do Gemini: v1 (gemini-3.5-flash-lite).

Erro percentual = |estimado − real| ÷ real × 100. Gastos reais e estimados são do grupo, na viagem toda. Todo valor do site é uma estimativa.

> 10 viagem(ns) já aconteceram e foram simuladas no mesmo período de um ano futuro (a SerpApi só busca datas futuras). Preços de outro ano podem explicar parte do erro.

> 10 viagem(ns) não têm valor real em todas as categorias. Nelas, o total soma só as categorias com valor real, dos dois lados, para comparar a mesma coisa.

## Erro médio por categoria

| Categoria | Erro médio | Viagens com valor real |
| --- | --- | --- |
| passagem | 43,8% | 5 |
| hotel | 45,5% | 10 |
| comida | 27,2% | 10 |
| passeios | 44,4% | 10 |
| transporte | – | 0 |
| **Total** | 31,3% | 10 |

**Erro médio geral (média das categorias com valor real): 40,2%**

## Viagem a viagem

| # | Rota | Datas simuladas | Pessoas | Total estimado (R$) | Total real (R$) | Passagem | Hotel | Comida | Passeios | Transporte | Total | Veredito |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | GRU→LIS | 06/05/2027 a 13/05/2027 | 1 | 8.565,00 | 8.455,00 | 30,5% | 27,2% | 11,3% | 24,6% | – | 1,3% | cabe_com_ajustes |
| 2 | GRU→EZE | 06/05/2027 a 13/05/2027 | 1 | 4.126,00 | 4.640,00 | 42,5% | 53,1% | 0,0% | 37,8% | – | 11,1% | cabe |
| 3 | GRU→SCL | 06/05/2027 a 13/05/2027 | 1 | 5.198,00 | 5.496,00 | 46,8% | 32,9% | 6,7% | 8,9% | – | 5,4% | cabe |
| 4 | GRU→CDG | 06/05/2027 a 13/05/2027 | 1 | 12.810,00 | 10.259,00 | 32,5% | 20,9% | 0,6% | 83,1% | – | 24,9% | nao_cabe |
| 5 | GRU→MCO | 06/05/2027 a 13/05/2027 | 1 | 11.018,00 | 10.770,00 | 66,6% | 45,9% | 3,0% | 13,5% | – | 2,3% | cabe_com_ajustes |
| 6 | GRU→LIS | 06/05/2027 a 13/05/2027 | 1 | 3.647,00 | 10.121,00 | – | 68,6% | 52,3% | 64,5% | – | 64,0% | cabe |
| 7 | GRU→EZE | 06/05/2027 a 13/05/2027 | 1 | 1.988,00 | 6.800,00 | – | 75,2% | 60,0% | 76,7% | – | 70,8% | cabe |
| 8 | GRU→SCL | 06/05/2027 a 13/05/2027 | 1 | 3.199,00 | 7.109,00 | – | 57,6% | 44,0% | 59,2% | – | 55,0% | cabe |
| 9 | GRU→CDG | 06/05/2027 a 13/05/2027 | 1 | 7.035,00 | 9.413,00 | – | 5,0% | 53,1% | 37,8% | – | 25,3% | cabe |
| 10 | GRU→MCO | 06/05/2027 a 13/05/2027 | 1 | 6.853,00 | 14.485,00 | – | 68,2% | 41,1% | 37,9% | – | 52,7% | cabe |
