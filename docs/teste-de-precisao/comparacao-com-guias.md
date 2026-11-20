# Teste de precisão: comparação com uma ferramenta de referência

Comparamos o total que o sistema estima com o de uma ferramenta de custos já conhecida e usada por outras pessoas, a Nomad. Para cada destino, rodamos a mesma viagem no nosso sistema e medimos o erro percentual em cada categoria e no total.

## Referência e método

- Fonte: páginas "Quanto custa" da Nomad (nomadglobal.com/viagens/quanto-custa/...), para Lisboa, Buenos Aires, Santiago, Paris e Orlando. Os links estão na coluna `fonte` de [referencia-guias.csv](referencia-guias.csv).
- Cada página traz o custo médio de **7 dias para 1 pessoa**, pesquisado em outubro de 2025 para 6 a 13 de maio de 2026, em três perfis. Usamos o econômico (com passagem em classe econômica) e o confortável.
- A referência separa voo, hospedagem, alimentação e passeios. Não separa transporte local, então essa categoria fica em branco.
- No perfil confortável a referência usa passagem em econômica premium. O nosso sistema busca o voo mais barato, então a passagem desse perfil ficou em branco para não comparar coisas diferentes.
- A origem não aparece nas páginas. Assumimos São Paulo (GRU).
- No caso de Paris o voo não tem valor próprio na leitura: foi calculado como o total menos as outras três linhas (a página informa que as linhas somam o total).
- O erro é |estimado − referência| / referência, calculado pelo comando `teste_precisao` do backend.

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
