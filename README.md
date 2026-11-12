# Cabe no bolso?

Site de viagens que responde uma pergunta: **a minha viagem cabe no meu orçamento?**
A pessoa informa origem, destino, datas, orçamento e interesses. O site busca preços reais de passagem e hotel, estima o resto com IA e diz se **cabe**, **cabe com ajustes** ou **não cabe**, com alternativas para caber (outro mês, menos noites, hotel mais simples).

Projeto 3 de Tecnologias Web (Insper, 2026/2). Integrantes: André, Felipe e Henrique.

| | |
| --- | --- |
| Deploy | a definir (Sprint 2) |
| Quadro de tarefas | [GitHub Projects](https://github.com/users/decov12/projects/1) |
| Fluxo de telas | [docs/fluxo-de-telas.md](docs/fluxo-de-telas.md) |

## Como funciona

- Passagem, hotel e calendário de preços vêm do Google, pela SerpApi.
- A IA (Gemini) estima só comida, passeios e transporte.
- **O código soma tudo e decide o veredito**, não a IA. Todo valor é uma estimativa.

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
- [ ] Telas de login e cadastro
- [ ] Busca de voos, hotéis e calendário (SerpApi)
- [ ] Estimativa de gastos (Gemini) e regra do veredito
- [ ] Formulário de simulação e tela de resultado

**Sprint 2 (16/11 a 19/11): histórico, alternativas e deploy**
- [ ] Histórico de simulações e alternativas automáticas
- [ ] Cache de 24 horas e limite diário por usuário
- [ ] Acabamento visual e deploy público
- [ ] Testes do veredito, teste de precisão com viagens reais e feedback de 10 pessoas

**Apresentação (24/11, commits até as 09:30)**
- [ ] Resultados no README e exemplo de uso de IA no desenvolvimento

Tarefas detalhadas, com responsável, tamanho e datas, no quadro do GitHub Projects.

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

O site abre em `http://localhost:5173` e a API em `http://localhost:8000`. Os testes usam as respostas salvas em `fixtures/serpapi/`, sem gastar a cota da SerpApi.
