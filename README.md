# Cabe no bolso?

Site de viagens que responde uma pergunta: **a minha viagem cabe no meu orçamento?**
A pessoa informa origem, destino, datas, orçamento e interesses. O site busca preços reais de passagem e hotel, estima o resto com IA e diz se **cabe**, **cabe com ajustes** ou **não cabe**, com alternativas para caber (outro mês, menos noites, hotel mais simples).

Projeto 3 de Tecnologias Web (Insper, 2026/2). Integrantes: André, Felipe e Henrique.

| | |
| --- | --- |
| Deploy | a definir (Sprint 2) |
| Quadro de tarefas | [GitHub Projects](https://github.com/users/decov12/projects/1) |
| Fluxo de telas | [docs/fluxo-de-telas.md](docs/fluxo-de-telas.md) |
| API do backend | [docs/api.md](docs/api.md) |

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
- [ ] Acabamento visual e deploy público
- [ ] Testes do veredito, teste de precisão com viagens reais e feedback de 10 pessoas

**Apresentação (24/11, commits até as 09:30)**
- [ ] Resultados no README e exemplo de uso de IA no desenvolvimento

Tarefas detalhadas, com responsável, tamanho e datas, no quadro do GitHub Projects.

## Resultados

- **Teste de precisão** (15 a 20 viagens reais, total estimado contra gasto real): [resultado](docs/teste-de-precisao/resultado.md)
- **Comparação com guias de custo** (complemento, não é precisão; estimativas publicadas, não gasto real): [como foi feito](docs/teste-de-precisao/comparacao-com-guias.md)
- **Comparação de versões do prompt** (v1 e v2, qual erra menos): mesmo arquivo de resultado.
- **Feedback de 10 pessoas** (roteiro e resumo das respostas): [docs/feedback-usuarios.md](docs/feedback-usuarios.md)

Os números entram aqui até 23/11, antes da apresentação.

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

**Frontend** (entra na Sprint 1)
```bash
cd frontend
npm install
npm run dev
```

No `.env`, `GEMINI_MODEL` é opcional (vazio usa `gemini-3.5-flash-lite`).

O site abre em `http://localhost:5173` e a API em `http://localhost:8000`. Os testes (`python manage.py test`, dentro de `backend/`) usam as respostas salvas em `fixtures/`, sem gastar a cota da SerpApi nem do Gemini. Como usar os serviços de preço e IA: [docs/servicos-ia.md](docs/servicos-ia.md).
