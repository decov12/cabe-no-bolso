# Quadro de tarefas

Lista de tarefas do projeto, no formato do quadro do GitHub Projects (Team Planning). Use esta tabela para criar os cartões. Colunas do quadro: **To Do**, **Doing**, **Done**.

Tamanhos: XS (menos de 1h), S (1 a 3h), M (meio dia), L (um dia), XL (mais de um dia).

## Sprint 1 (10/11 a 13/11)

| # | Tarefa | Descrição | Responsável | Tam. | Início | Fim | Coluna |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Escrever e validar a proposta | Documento com problema, funcionalidades, tecnologias e cronograma, aprovado pela professora | André | S | 10/11 | 10/11 | Done |
| 2 | Testar a SerpApi no Playground | Testar voos, hotéis, calendário e autocomplete e guardar as respostas | André | S | 10/11 | 10/11 | Done |
| 3 | Criar o repositório e adicionar a professora | Repositório no GitHub com BarbaraTieko como colaboradora e os 3 integrantes com acesso | André | XS | 10/11 | 10/11 | Doing |
| 4 | Desenhar o fluxo de telas | Desenho de baixa fidelidade das 7 telas, salvo em `docs/` | André | S | 10/11 | 10/11 | Doing |
| 5 | Montar o README com cronograma | Descrição, proposta de valor, cronograma com checklist e instruções para rodar | André | S | 10/11 | 11/11 | Doing |
| 6 | Criar o quadro no GitHub Projects | Quadro Team Planning com as tarefas desta tabela | André | XS | 10/11 | 10/11 | Doing |
| 7 | Guardar respostas reais da SerpApi como fixtures | Pasta `fixtures/` com JSONs usados nos testes, para não gastar cota | Felipe | XS | 10/11 | 10/11 | Done |
| 8 | Criar o projeto Django com DRF | Projeto base, CORS, variáveis de ambiente e `.env.example` | Henrique | S | 10/11 | 11/11 | To Do |
| 9 | Criar o projeto React com Bootstrap | Vite, rotas, Bootstrap e a estrutura de pastas | André | S | 10/11 | 11/11 | To Do |
| 10 | Cadastro e login na API | Cadastro, login por token e rota protegida | Henrique | M | 11/11 | 12/11 | To Do |
| 11 | Telas de cadastro e login | Telas 1 e 2 do fluxo, ligadas à API | André | M | 11/11 | 12/11 | To Do |
| 12 | Serviço SerpApi: autocomplete e voos | Achar o código do aeroporto e buscar o preço da passagem | Felipe | M | 10/11 | 12/11 | Done |
| 13 | Serviço SerpApi: hotéis e calendário | Buscar hotel por noite e o calendário de preços | Felipe | M | 11/11 | 12/11 | Done |
| 14 | Integração com o Gemini | Pedir estimativa de comida, passeios e transporte, com resposta em JSON | Felipe | L | 11/11 | 13/11 | Done |
| 15 | Regra do veredito no código | Somar os custos e decidir: cabe, cabe com ajustes ou não cabe | Felipe | M | 12/11 | 13/11 | Done |
| 16 | Endpoint de simulação | `POST /api/simulacoes/` que junta busca, IA e veredito e salva no banco | Henrique | M | 12/11 | 13/11 | To Do |
| 17 | Formulário de nova simulação | Tela 3, com sugestões de cidade e envio para a API | André | M | 12/11 | 13/11 | To Do |
| 18 | Tela de resultado (versão simples) | Telas 4 e 5: carregando, veredito e gasto por categoria | André | M | 13/11 | 13/11 | To Do |
| 19 | Responder o questionário da Sprint 1 | Cada integrante responde o questionário da equipe | André, Felipe, Henrique | XS | 13/11 | 16/11 | To Do |

## Sprint 2 (16/11 a 19/11)

| # | Tarefa | Descrição | Responsável | Tam. | Início | Fim | Coluna |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20 | Histórico na API | Listar e abrir simulações do usuário logado | Henrique | M | 16/11 | 17/11 | To Do |
| 21 | Telas de histórico | Tela 7 e reabrir o resultado | André | M | 16/11 | 17/11 | To Do |
| 22 | Alternativas automáticas | Calcular outro mês, menos noites e hotel mais barato | Felipe | L | 16/11 | 18/11 | Done |
| 23 | Tela de alternativas | Tela 6 ligada à API | André | M | 17/11 | 18/11 | To Do |
| 24 | Cache de 24 horas | Reaproveitar busca da mesma rota e das mesmas datas | Henrique | M | 16/11 | 17/11 | To Do |
| 25 | Limite diário por usuário | Bloquear excesso de simulações para não estourar a cota das APIs | Henrique | S | 17/11 | 18/11 | To Do |
| 26 | Acabamento visual | Bootstrap, estados de carregando e erro, textos claros | André | M | 17/11 | 18/11 | To Do |
| 27 | Deploy | Backend, banco PostgreSQL e site no ar, com o link no README | Henrique | L | 17/11 | 19/11 | To Do |
| 28 | Testes automatizados do veredito | Testes usando os arquivos de `fixtures/` | Felipe | M | 17/11 | 18/11 | Done |
| 29 | Teste de precisão | 15 a 20 viagens reais: comparar o total estimado com o gasto real | André, Felipe | L | 16/11 | 19/11 | Doing |
| 30 | Comparação de versões do prompt | Rodar as mesmas viagens com duas versões e ver qual erra menos | Felipe | M | 18/11 | 19/11 | Doing |
| 31 | Questionário de feedback | Formulário para pelo menos 10 pessoas testarem e responderem | André | M | 17/11 | 19/11 | To Do |
| 32 | Responder o questionário da Sprint 2 | Cada integrante responde o questionário da equipe | André, Felipe, Henrique | XS | 19/11 | 20/11 | To Do |

## Até a apresentação (24/11, commits até as 09:30)

| # | Tarefa | Descrição | Responsável | Tam. | Início | Fim | Coluna |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 33 | Resultados no README | Tabela do teste de precisão, comparação de versões e resumo do feedback | André | M | 20/11 | 23/11 | To Do |
| 34 | Exemplo de uso de IA no desenvolvimento | Escolher um caso concreto para mostrar na apresentação | André, Felipe, Henrique | S | 20/11 | 23/11 | To Do |
| 35 | Ensaio da apresentação | Passar a demonstração do início ao fim | André, Felipe, Henrique | S | 23/11 | 23/11 | To Do |

## Como criar o quadro

1. No repositório, abra a aba **Projects** e clique em **New project**.
2. Escolha o modelo **Team Planning** e dê um nome (por exemplo, "Cabe no bolso? — Tarefas").
3. Confira se existem os campos Responsável (Assignees), Tamanho (Size), Data de início e Data de fim. Se faltar algum, crie com **+** na tabela.
4. Cole os títulos das tarefas, uma por linha, em **Add item**. Depois preencha responsável, tamanho, datas e coluna.
5. Mantenha o que está em andamento em **Doing** e mova para **Done** ao terminar. Cada tarefa precisa passar pelas três colunas.
