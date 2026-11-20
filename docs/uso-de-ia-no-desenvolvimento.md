# Uso de IA no desenvolvimento

O projeto foi implementado com a ajuda de um assistente de código (Claude Code). Todos os exemplos abaixo aconteceram de verdade durante a implementação: os casos 1 a 4 nos serviços de preço e IA (13/11/2026), o caso 5 na junção do frontend (13/11/2026) e os casos do Henrique na criação do backend (12/11/2026) e no deploy (a partir de 19/11/2026). Em todos, a IA escreveu código rápido, e o trabalho do grupo foi conferir o que ela fez.

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

## Caso do Henrique: o banco "dummy" do DATABASE_URL vazio

**O que pedimos:** ao Claude Code, o projeto Django com DRF e o cadastro e login por token.

**O que a IA entregou:** o código e 11 testes, todos passando.

**O que ela percebeu e corrigiu:** com `DATABASE_URL=` vazio, como no `.env.example`, a biblioteca `dj-database-url` montava um banco "dummy" em vez de cair para o SQLite. A chamada foi trocada por `dj_database_url.parse(os.getenv("DATABASE_URL") or <endereço do SQLite>)`.

**Como verificamos:** a IA não conseguiu subir o servidor, então testamos à mão, pela API navegável do DRF, o cadastro, o login, o e-mail repetido e a senha fraca. Depois repetimos no site publicado.

**Lição:** teste automático não prova que o fluxo funciona de ponta a ponta. Testar na prática continua sendo trabalho nosso.

## Caso do Henrique: o deploy no Render

- **Nome da chave:** o pedido para montar o `render.yaml` falava em `publishPath` para a pasta do site. O Claude Code conferiu na documentação do Render e usou o nome correto, `staticPublishPath`.
- **Variáveis:** as variáveis marcadas como `sync: false` (`VITE_API_URL`, `CORS_ALLOWED_ORIGINS`, `SERPAPI_KEY`, `GEMINI_API_KEY`) não foram criadas sozinhas no painel. Antes de criá-las à mão, o navegador mostrava erro de CORS e `ERR_CONNECTION_REFUSED`. Só depois disso o site passou a falar com a API.
- **Lição:** o arquivo de configuração pode estar certo e o serviço publicado ainda não funcionar. É preciso abrir o site e testar.

## Roteiro curto para a demonstração (#35)

1. Mostrar `docs/servicos-ia.md` (o que entra e o que sai de `simular()`).
2. Rodar `python manage.py test` (124 testes, sem gastar cota).
3. Mostrar o resultado real GRU→LIS: não cabe, faltam R$ 5.032, com as alternativas.
4. Contar o caso escolhido na seção abaixo em 1 minuto.

## Qual caso vamos contar na apresentação

**Recomendação:** o caso do Henrique sobre o banco "dummy" do `DATABASE_URL` vazio. É o que melhor mostra o que a IA errou e como verificamos: o código veio com 11 testes passando e mesmo assim tinha um defeito, e o fluxo só ficou confirmado quando testamos à mão, de ponta a ponta.

**Reserva:** o caso 1, que já estava sugerido no rascunho. Mostra como conferimos a fonte oficial em vez de confiar na memória da IA.

**Escolha final do grupo:** a definir.
