# Deploy no Render

O site fica no ar com três peças no Render, todas descritas no arquivo [`render.yaml`](../render.yaml) (Blueprint):

| Peça | Tipo no Render | Pasta |
| --- | --- | --- |
| `cabe-no-bolso-db` | PostgreSQL (gratuito) | — |
| `cabe-no-bolso-api` | Web Service Python (gratuito) | `backend/` |
| `cabe-no-bolso-site` | Static Site | `frontend/` |

## Passo a passo no painel

1. Entre em [dashboard.render.com](https://dashboard.render.com) com a conta do GitHub que tem acesso ao repositório.
2. Clique em **New → Blueprint** e escolha o repositório `cabe-no-bolso`, branch `main`. O Render lê o `render.yaml` e mostra as três peças.
3. Preencha as variáveis marcadas como "sync: false" (lista abaixo). Ainda não sabemos os endereços finais, então na primeira vez:
   - `ALLOWED_HOSTS`: pode deixar vazio. O backend aceita sozinho o próprio domínio `.onrender.com`, que o Render informa em `RENDER_EXTERNAL_HOSTNAME`.
   - `CORS_ALLOWED_ORIGINS` e `VITE_API_URL`: coloque qualquer valor provisório e corrija no passo 5.
4. Clique em **Apply** e espere o banco, a API e o site ficarem com status **Live**. O build da API roda o `backend/build.sh`: instala as dependências, faz o `collectstatic` e aplica as migrações.
5. Com os endereços em mãos (aparecem no topo da página de cada serviço):
   - na **API** (`cabe-no-bolso-api` → Environment), ponha em `CORS_ALLOWED_ORIGINS` o endereço do site, com `https://` e sem barra no final;
   - no **site** (`cabe-no-bolso-site` → Environment), ponha em `VITE_API_URL` o endereço da API, com `https://` e sem barra no final.
   - Salve. A API reinicia sozinha. O site precisa de um novo build (**Manual Deploy → Deploy latest commit**), porque o Vite grava o `VITE_API_URL` dentro dos arquivos no momento do build.
6. Teste: abra o site, crie uma conta e faça **uma** simulação (gasta de 3 a 4 buscas da SerpApi).
7. Coloque o link do site no README.

Para criar um usuário do admin (`/admin/`), abra **Shell** na página da API e rode `python manage.py createsuperuser`. (O Shell pode não estar disponível no plano gratuito; nesse caso, o admin não é necessário para o site funcionar.)

Na primeira vez, confira no painel: se o site mostrar "Not Found" ao recarregar uma página como `/nova`, a regra de rewrite não foi criada. Crie em `cabe-no-bolso-site` → **Redirects/Rewrites**: Source `/*`, Destination `/index.html`, Action **Rewrite**.

## Variáveis de ambiente

Os valores ficam só no painel do Render (ou no `.env` local), nunca no Git.

**API (`cabe-no-bolso-api`)**

| Variável | De onde vem |
| --- | --- |
| `DATABASE_URL` | Automática, do banco `cabe-no-bolso-db` |
| `SECRET_KEY` | Gerada pelo Render |
| `DEBUG` | Já vem como `False` no `render.yaml` |
| `PYTHON_VERSION` | Já vem no `render.yaml` (a mesma versão usada nos testes) |
| `ALLOWED_HOSTS` | Preencher (opcional: domínios extras, separados por vírgula) |
| `CORS_ALLOWED_ORIGINS` | Preencher: endereço do site |
| `SERPAPI_KEY` | Preencher: chave da SerpApi |
| `GEMINI_API_KEY` | Preencher: chave do Gemini |
| `GEMINI_MODEL` | Opcional. Vazio usa o padrão do código |

**Site (`cabe-no-bolso-site`)**

| Variável | De onde vem |
| --- | --- |
| `NODE_VERSION` | Já vem no `render.yaml` |
| `VITE_API_URL` | Preencher: endereço da API |

## Limitações do plano gratuito

- **A API "dorme".** Depois de 15 minutos sem receber nenhuma requisição, o Render desliga o backend. A primeira chamada seguinte o acorda e **demora cerca de 1 minuto**. Antes de uma demonstração, abra o site (ou o endereço da API) um ou dois minutos antes. As chamadas seguintes voltam a ser rápidas.
- **O banco expira.** O PostgreSQL gratuito expira **30 dias depois de criado**. Depois disso há 14 dias para passar para um plano pago; passado esse prazo, o Render apaga o banco com todos os dados (usuários e simulações). Para a apresentação de 24/11 isso não é problema, mas o banco não serve para guardar dados por muito tempo. Também não há backup, e só é permitido um banco gratuito por conta.
- Arquivos gravados no disco do servidor somem a cada deploy ou quando a API dorme. Por isso tudo o que precisa durar (usuários, simulações, cache) fica no banco.
