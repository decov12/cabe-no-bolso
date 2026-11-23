# Cabe no bolso?

Site de viagens que responde uma pergunta: **a minha viagem cabe no meu orçamento?**
A pessoa informa origem, destino, datas, orçamento e interesses. O site busca preços reais de passagem e hotel, estima o resto com IA e diz se **cabe**, **cabe com ajustes** ou **não cabe**, com alternativas para caber (outro mês, menos noites, hotel mais simples).

Projeto 3 de Tecnologias Web (Insper, 2026/2). Integrantes: André, Felipe e Henrique.

| | |
| --- | --- |
| Deploy | https://cabe-no-bolso-site.onrender.com |
| Quadro de tarefas | [GitHub Projects](https://github.com/users/decov12/projects/1) |
| Fluxo de telas | [docs/fluxo-de-telas.md](docs/fluxo-de-telas.md) |
| API do backend | [docs/api.md](docs/api.md) |
| Como publicar (Render) | [docs/deploy.md](docs/deploy.md) |
| Uso de IA no desenvolvimento | [docs/uso-de-ia-no-desenvolvimento.md](docs/uso-de-ia-no-desenvolvimento.md) |

> O servidor gratuito do Render "dorme" depois de 15 minutos sem uso. A primeira chamada pode levar cerca de 1 minuto para acordar.

## Como funciona

- Passagem, hotel e calendário de preços vêm do Google, pela SerpApi.
- A IA (Gemini) estima só comida, passeios e transporte.
- **O código soma tudo e decide o veredito**, não a IA. Todo valor é uma estimativa.
- Buscas e estimativas ficam 24 horas em cache, e cada pessoa faz até 5 simulações por dia, para não estourar a cota das APIs.

Tecnologias: React (Vite) + Bootstrap, Django REST Framework, PostgreSQL, SerpApi, Gemini, Render.

## Fluxo de telas

![Fluxo de telas](docs/fluxo-de-telas-desktop.png)

## Cronograma

**Sprint 1 (10/11 a 13/11): experiência principal**
- [x] Proposta validada, fluxo de telas e quadro de tarefas
- [x] Repositório criado, com a professora (BarbaraTieko) como colaboradora
- [x] Projeto Django com DRF
- [x] Cadastro e login na API
- [x] Projeto React com Bootstrap e rotas das 7 telas
- [x] Telas de login e cadastro
- [x] Busca de voos, hotéis e calendário (SerpApi)
- [x] Estimativa de gastos (Gemini) e regra do veredito
- [x] Formulário de simulação e tela de resultado

**Sprint 2 (16/11 a 19/11): histórico, alternativas e deploy**
- [x] Histórico de simulações e alternativas automáticas
- [x] Cache de 24 horas e limite diário por usuário
- [x] Deploy público
- [ ] Acabamento visual
- [x] Testes do veredito
- [x] Validação com a ferramenta de custo de viagem da Nomad (teste de precisão)
- [x] Comparação de versões do prompt

**Apresentação (24/11, commits até as 09:30)**
- [x] Resultados no README e exemplo de uso de IA no desenvolvimento

Tarefas detalhadas, com responsável, tamanho e datas, no quadro do GitHub Projects.

## Resultados

### Validação com a ferramenta da Nomad (teste de precisão)

Validamos o site com a ferramenta de custo de viagem da Nomad, o simulador [Quanto custa viajar](https://www.nomadglobal.com/viagens/quanto-custa-viajar), que estima voo, hospedagem, alimentação e passeios por destino e estilo de viagem. Comparamos o nosso total com o dela em 5 destinos (Lisboa, Buenos Aires, Santiago, Paris e Orlando), viagem de 7 dias para 1 pessoa saindo de São Paulo, nos perfis econômico e confortável da referência. Rodado em 23/11/2026, com o prompt v1.

| Perfil da referência | Erro médio do total | Melhor e pior destino |
| --- | --- | --- |
| Econômico (com passagem) | **9,0%** | Lisboa 1,3% · Paris 24,9% |
| Confortável (sem passagem) | **53,6%** | Paris 25,3% · Buenos Aires 70,8% |

| Categoria | Erro médio (10 viagens) |
| --- | --- |
| Passagem (só perfil econômico) | 43,8% |
| Hotel | 45,5% |
| Comida | 27,2% |
| Passeios | 44,4% |

- **O total do perfil econômico fica perto da referência (9%)**, que é o perfil que o site simula: voo mais barato e hotel acessível.
- No perfil confortável o site fica bem abaixo, como esperado, porque ele não tem a opção de viagem confortável.
- Por categoria o erro é maior que no total, porque os erros se compensam: a passagem saiu mais cara que a referência nos 5 destinos e o hotel saiu mais barato em 4 deles.
- A referência não separa transporte local, então essa categoria não entra. Os preços da Nomad são de outubro de 2025, e os nossos são de maio de 2027 (a SerpApi só busca datas futuras).

Detalhes, método e tabela viagem a viagem: [comparacao-com-guias.md](docs/teste-de-precisao/comparacao-com-guias.md) e [resultado.md](docs/teste-de-precisao/resultado.md).

### Comparação de versões do prompt

Rodamos as duas versões do prompt do Gemini nas mesmas 10 viagens de referência. Só comida e passeios têm valor na referência.

| Categoria | Erro v1 | Erro v2 |
| --- | --- | --- |
| Comida | **27,2%** | 29,6% |
| Passeios | 44,4% | **40,7%** |
| Média | 35,8% | **35,2%** |

A v2 erra um pouco menos na média, mas a diferença (0,6 ponto) é pequena demais para separar do acaso, já que o Gemini varia de uma chamada para outra. A v1 é melhor em comida e a v2 é melhor em passeios. Mantivemos a **v1** como padrão: ela é mais simples e, no perfil econômico, o que o site simula, errou bem menos em comida (4,3% contra 21,0%). Tabela completa: [comparacao-prompts.md](docs/teste-de-precisao/comparacao-prompts.md).

## Como rodar

Precisa de Python 3.12+, Node.js 22+ e chaves gratuitas da SerpApi e do Gemini.

**Backend**
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env         # Linux/Mac: cp .env.example .env (e preencha as chaves)
python manage.py migrate
python manage.py runserver
```

**Frontend**
```bash
cd frontend
npm install
copy .env.example .env         # opcional: sem ele, o site usa http://localhost:8000
npm run dev
```

No `.env` do backend, `GEMINI_MODEL` é opcional (vazio usa `gemini-3.5-flash-lite`).

O site abre em `http://localhost:5173` e a API em `http://localhost:8000`. Os testes (`python manage.py test`, dentro de `backend/`) usam as respostas salvas em `fixtures/`, sem gastar a cota da SerpApi nem do Gemini. Como usar os serviços de preço e IA: [docs/servicos-ia.md](docs/servicos-ia.md).

## Deploy

O site, a API e o banco PostgreSQL ficam no Render, descritos no arquivo `render.yaml`. O passo a passo, as variáveis de ambiente e os cuidados (servidor que dorme, banco gratuito que expira) estão em [docs/deploy.md](docs/deploy.md).
