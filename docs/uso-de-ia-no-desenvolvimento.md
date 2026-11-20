# Uso de IA no desenvolvimento (rascunho da tarefa #34)

> RASCUNHO para o grupo escolher **um** caso para a apresentação. Tudo aqui aconteceu de verdade
> durante a implementação dos serviços de preço e IA (13/11/2026), feita com um assistente de código (Claude Code).

## Caso 1: a documentação do Gemini tinha mudado (sugerido)

**O que pedimos:** antes de escrever o código do Gemini, o assistente devia conferir na documentação oficial o modelo gratuito atual e a forma de pedir JSON, sem confiar na memória.

**O que aconteceu:**
- O endereço `ai.google.dev` agora redireciona para `aistudio.google.com/docs`.
- O exemplo oficial usa uma API nova (`client.interactions.create` com `response_format`), e não mais `generate_content`.
- Modelos antigos como o `gemini-2.5-flash` estão marcados para desativação em 01/12/2026.

**Como conferimos:** o assistente leu a página e depois abriu o código do SDK instalado (`google-genai` 3.3.0) para ver se os parâmetros existiam mesmo. No fim, uma única chamada real (com autorização, gastando 3 buscas) confirmou que tudo funcionava.

**Lição:** o que a IA "lembra" pode estar desatualizado. Pedir a fonte oficial e testar com uma chamada controlada evitou código quebrado.

## Caso 2: preços extremos nos voos

As respostas reais da SerpApi tinham passagens de R$ 1.930 e de R$ 6.777 para a mesma rota. Em vez de usar a média, que seria puxada pelo extremo, a regra ficou assim: menor preço de `best_flights`; se essa lista vier vazia, mediana de `other_flights`. As fixtures reais guiaram a decisão, e os testes provam o comportamento.

## Caso 3: a IA estima, o código decide

O Gemini só devolve valores por pessoa por dia (comida, passeios e transporte) num JSON com schema. O código:

- valida faixas plausíveis (comida não pode custar R$ 50.000 por dia);
- tenta de novo uma vez se a resposta for inválida;
- multiplica pelos dias e pelas pessoas;
- soma tudo e decide o veredito.

Os 85 testes dos serviços nunca chamam as APIs de verdade e têm uma "trava" que falha se alguém esquecer um mock.

## Caso 4: a IA também erra (bom para mostrar senso crítico)

Durante a sessão, o assistente rodou um comando a partir da pasta errada: o arquivo de dependências e duas pastas foram criados dentro do `venv/`. Ele percebeu pelo resultado, conferiu que tudo tinha sido criado naquele momento, apagou só o que criou e refez no lugar certo. Revisar o que a IA fez (`git status`, testes) continua sendo trabalho nosso.

## Caso 5: duas IAs fizeram a mesma tela (coordenação)

**O que aconteceu:** na noite de 13/11, o André pediu à IA dele as telas de início e de login. Ao mesmo tempo, a IA do Henrique, que cuidava do backend, também escreveu essas telas e mais três (nova simulação, buscando e resultado). Na hora de juntar (`git pull`), deu conflito nos arquivos de tela.

**Como resolvemos:** em vez de escolher no escuro, comparamos as duas versões. A do Henrique estava mais completa (mensagens de erro por campo, abas por endereço, tratamento de token vencido), então ficamos com ela e descartamos a nossa. Depois conferimos que o projeto compilava e passava no lint.

**Lição:** com IA, duas pessoas produzem código em minutos e sem perceber que estão fazendo o mesmo trabalho. O que evita isso é combinar quem faz o quê, antes de pedir. Desde então, cada IA recebe o texto da divisão de tarefas.

## Roteiro curto para a demonstração (#35)

1. Mostrar `docs/servicos-ia.md` (o que entra e o que sai de `simular()`).
2. Rodar `python manage.py test` (96 testes, sem gastar cota).
3. Mostrar o resultado real GRU→LIS: não cabe, faltam R$ 5.032, com as alternativas.
4. Contar o caso escolhido acima em 1 minuto.
