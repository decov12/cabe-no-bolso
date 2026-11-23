# Validação com a ferramenta de custo de viagem da Nomad

Validamos o site comparando o total que ele estima com o da ferramenta de custo de viagem da Nomad, o simulador [Quanto custa viajar](https://www.nomadglobal.com/viagens/quanto-custa-viajar). Para cada destino, rodamos a mesma viagem no nosso sistema e medimos o erro percentual em cada categoria e no total.

## Referência e método

- Ferramenta: o simulador da Nomad, em que a pessoa escolhe o destino, o estilo de viagem (econômica, confortável ou luxuosa), os dias e as pessoas, e recebe o custo de voo, hospedagem, alimentação e passeios. Usamos Lisboa, Buenos Aires, Santiago, Paris e Orlando. Os links de cada destino estão na coluna `fonte` de [referencia-guias.csv](referencia-guias.csv). Os valores foram conferidos de novo na ferramenta em 23/11/2026 e não mudaram.
- A base da ferramenta é **7 dias para 1 pessoa**, pesquisada em outubro de 2025 para 6 a 13 de maio de 2026. Usamos os estilos econômico (com passagem em classe econômica) e confortável.
- A referência separa voo, hospedagem, alimentação e passeios. Não separa transporte local, então essa categoria fica em branco.
- No perfil confortável a referência usa passagem em econômica premium. O nosso sistema busca o voo mais barato, então a passagem desse perfil ficou em branco para não comparar coisas diferentes.
- A ferramenta não pede a cidade de origem. Assumimos São Paulo (GRU).
- O erro é |estimado − referência| / referência, calculado pelo comando `teste_precisao` do backend.
- O total compara só as categorias que a referência tem, somando as mesmas dos dois lados: passagem, hotel, comida e passeios no perfil econômico, e hotel, comida e passeios no confortável.

## Resultado (23/11/2026, prompt v1)

| Perfil | Lisboa | Buenos Aires | Santiago | Paris | Orlando | Média |
| --- | --- | --- | --- | --- | --- | --- |
| Econômico: erro do total | 1,3% | 11,1% | 5,4% | 24,9% | 2,3% | **9,0%** |
| Confortável: erro do total | 64,0% | 70,8% | 55,0% | 25,3% | 52,7% | **53,6%** |

- No perfil econômico, que é o que o site simula (voo mais barato e hotel acessível), o total fica a 9% da referência, em média.
- No confortável o site fica abaixo em todos os destinos, porque não tem essa opção de viagem.
- Por categoria o erro é maior (passagem 43,8%, hotel 45,5%, comida 27,2%, passeios 44,4%), mas os erros se compensam no total. A passagem saiu mais cara que a referência nos 5 destinos, em parte porque os preços são de outro ano. O hotel saiu mais barato em 4 de 5 destinos.
- Paris é o pior caso do perfil econômico: passagem, hotel e passeios saíram todos acima da referência.

Tabela completa, viagem a viagem: [resultado.md](resultado.md). Comparação dos prompts v1 e v2: [comparacao-prompts.md](comparacao-prompts.md).

## Limites

- A referência é uma estimativa publicada, não o gasto de uma viagem específica. Os resultados mostram o quanto o nosso sistema se aproxima dela.
- Os preços da referência são de outubro de 2025. O comando desloca as datas para o futuro e busca preços atuais, então parte da diferença vem do tempo.
- São 5 destinos e 1 pessoa, uma amostra pequena.

## Como rodar (gasta cota da SerpApi)

São 10 viagens, cerca de 30 buscas (cota: 50 por hora e 250 por mês). Combine com o Felipe para não rodar junto com outros testes. No `backend/`, com o ambiente ativo:

```
python manage.py teste_precisao --csv ../docs/teste-de-precisao/referencia-guias.csv --limite 10
```

O comando pede confirmação antes de gastar a cota e grava o resultado em `docs/teste-de-precisao/resultado.md`. Depois é só colocar o resumo na seção Resultados do README.

## Comparação de versões do prompt

Para ver qual versão do prompt do Gemini erra menos (v1 ou v2), rode nas mesmas viagens. Esse comando não usa a SerpApi, só chama o Gemini:

```
python manage.py comparar_prompts --csv ../docs/teste-de-precisao/referencia-guias.csv
```

O resultado fica em `docs/teste-de-precisao/comparacao-prompts.md`.
