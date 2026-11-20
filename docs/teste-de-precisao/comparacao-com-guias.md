# Comparação com guias de custo (complemento ao teste de precisão)

**Isto NÃO é o teste de precisão.** O teste de precisão compara o sistema com gastos reais de viagens ([viagens.csv](viagens.csv)). Aqui comparamos o sistema com **estimativas publicadas** por um guia de custos. Serve para ver se os nossos totais estão na mesma ordem de grandeza do mercado, e não para medir erro contra a realidade.

## Fonte e método

- Fonte: páginas "Quanto custa" da Nomad (nomadglobal.com/viagens/quanto-custa/...), para Lisboa, Buenos Aires, Santiago, Paris e Orlando. Os links estão na coluna `fonte` de [referencia-guias.csv](referencia-guias.csv).
- Cada página traz o custo médio de **7 dias para 1 pessoa**, pesquisado em outubro de 2025 para 6 a 13 de maio de 2026, em três perfis. Usamos o econômico (com passagem em classe econômica) e o confortável.
- O guia separa voo, hospedagem, alimentação e passeios. Não separa transporte local, então essa categoria fica em branco.
- No perfil confortável o guia usa passagem em econômica premium. O nosso sistema busca o voo mais barato, então a passagem desse perfil ficou em branco para não comparar coisas diferentes.
- A origem não aparece nas páginas. Assumimos São Paulo (GRU).
- No guia de Paris o voo não aparece com valor próprio nesta leitura: foi calculado como o total menos as outras três linhas (a página informa que as linhas somam o total).

## Limites

- São médias do guia, não gastos de uma viagem real. Concordar com o guia não prova que o sistema está certo, e discordar não prova que está errado.
- Os preços do guia são de outubro de 2025. O comando desloca as datas para o futuro e busca preços atuais, então parte da diferença é o tempo.
- São 5 destinos e 1 pessoa, uma amostra pequena.

## Como rodar (gasta cota da SerpApi)

São 10 viagens, cerca de 30 buscas (cota: 50 por hora e 250 por mês). Combine com o Felipe para não rodar junto com outros testes. No `backend/`, com o ambiente ativo:

```
python manage.py teste_precisao --csv ../docs/teste-de-precisao/referencia-guias.csv --saida ../docs/teste-de-precisao/resultado-guias.md --limite 10
```

O comando pede confirmação antes de gastar a cota. O resultado fica em `resultado-guias.md`; depois é só colocar o resumo no README.
