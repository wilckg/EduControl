# EduControl — POC de Gestão Acadêmica

Aplicação demonstrativa com **React + TypeScript (Vite)**, **Flask + SQLAlchemy** e **PostgreSQL**. Idioma: português brasileiro. Sem integração com serviços externos.

## Funcionalidades incluídas

- Login com sessão/cookie HttpOnly e token CSRF nas ações que modificam dados.
- Quatro perfis: administrador, coordenação, professor e secretaria; backend verifica permissões e professor visualiza apenas suas turmas.
- Dashboard de turmas, alunos e indicadores de frequência.
- Cadastro de alunos, cursos, turmas e matrículas.
- Criação de aulas com carga horária e conteúdo, chamada P/F/J por aluno e cálculo de horas presentes/ausentes.
- Carômetro com avatares por iniciais, com acesso rápido a ocorrências.
- Ocorrências associadas ao aluno e à turma (disponíveis para professor/coordenador/admin).
- Transferências de alunos **entre turmas do mesmo curso**, preservando a matrícula de origem e seu histórico.
- Alertas: até 8 horas restantes (atenção), até 4 horas (crítico), limite ultrapassado (excedido). Frequência mínima editável ao cadastrar curso.
- Dados fictícios iniciais para experimentar, inclusive alunos com faltas.

**Limitações intencionais:** nesta versão, as horas cursadas na turma de origem **não são consolidadas** automaticamente na frequência da matrícula de destino; regras de aproveitamento, abono/justificativas, calendário por encontros, uploads de fotos, relatórios/exportação, recuperação de senha, CRUD completo de edição/exclusão, logs detalhados e notificações externas são evoluções futuras. Alertas são calculados ao consultar a API, sem envio de e-mail/WhatsApp. O carômetro usa iniciais (não fotos reais). Um aluno transferido após a criação de aulas no destino somente aparecerá nas novas aulas do destino. O endpoint de criação de aula marca todos os alunos ativos inicialmente como presentes: o professor deve revisar antes de salvar. Os horários das aulas e conflitos de agenda ainda não são modelados.

## Requisitos

- Docker Desktop com Compose (recomendado), **ou** Python 3.12+, Node.js compatível com Vite 6 e PostgreSQL 16.
- Portas livres: `5173` (frontend) e `5000` (backend).

## Rodando com Docker (recomendado)

Na pasta que contém este README:

```bash
# Opcional: crie .env baseado em .env.example e altere os segredos
cp .env.example .env

docker compose up --build -d
docker compose exec backend flask --app app init-db
docker compose exec backend flask --app app seed
```

No Windows PowerShell, para criar o `.env` opcional: `Copy-Item .env.example .env`.

Acesse: **http://localhost:5173**. API: **http://localhost:5000/api/auth/me** (retorna 401 sem login, comportamento esperado).

Para visualizar logs:

```bash
docker compose logs -f frontend backend
```

Para parar (mantém banco): `docker compose down`.

Para reiniciar a base fictícia do zero (APAGA TODOS OS DADOS locais):

```bash
docker compose down -v
docker compose up --build -d
docker compose exec backend flask --app app init-db
docker compose exec backend flask --app app seed
```

## Usuários de demonstração

Senha de todos: `Demo@12345`, a menos que `DEMO_PASSWORD` seja alterada **antes** do primeiro `seed`.

| Perfil | E-mail |
|---|---|
| Administrador | admin@educontrol.local |
| Coordenação | coordenador@educontrol.local |
| Professor | professor@educontrol.local |
| Secretaria | secretaria@educontrol.local |

Selecione um perfil na tela de login. O professor tem acesso apenas às suas turmas; secretaria não acessa ocorrências nem lançamento de chamadas.

## Rodando sem Docker (opcional)

1. Instale e inicie PostgreSQL 16. Crie banco e usuário, por exemplo:

```sql
CREATE USER educontrol WITH PASSWORD 'educontrol_dev';
CREATE DATABASE educontrol OWNER educontrol;
```

2. Backend (terminal 1):

```bash
cd backend
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Defina `DATABASE_URL` e `SECRET_KEY` no terminal. Exemplo **Linux/macOS**:

```bash
export DATABASE_URL='postgresql+psycopg://educontrol:educontrol_dev@localhost:5432/educontrol'
export SECRET_KEY='substitua_por_uma_string_aleatoria_longa'
flask --app app init-db
flask --app app seed
python app.py
```

No **PowerShell**, substitua as duas primeiras linhas por:

```powershell
$env:DATABASE_URL='postgresql+psycopg://educontrol:educontrol_dev@localhost:5432/educontrol'
$env:SECRET_KEY='substitua_por_uma_string_aleatoria_longa'
```

3. Frontend (terminal 2, na pasta `frontend`):

```bash
npm install
npm run dev
```

O Vite encaminha chamadas `/api` para Flask em `localhost:5000` no desenvolvimento. Se não quiser instalar PostgreSQL localmente, **apenas para experimentos**, o backend usa SQLite quando `DATABASE_URL` não está definido.

## Fluxo de demonstração

1. Entre como admin e explore o Dashboard e os dados de exemplo.
2. Entre como professor, abra **Chamadas**, selecione `WEB-2026-A`, crie uma aula e altere P/F/J; salve.
3. Abra **Alertas** e veja os resultados calculados a partir das faltas e da carga horária do curso.
4. Em **Carômetro**, clique **Registrar ocorrência** e selecione a turma correspondente.
5. Entre como secretaria e, em **Transferências**, transfira um aluno ativo de `WEB-2026-A` para `WEB-2026-B`.
6. Verifique em **Alunos** o histórico de matrículas: a origem estará como transferida e o destino como ativa.

## Arquitetura

```text
educontrol-poc/
├── backend/
│   ├── app.py               # Modelos SQLAlchemy, RBAC, API e seed
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/main.tsx         # Telas React e cliente API
│   ├── src/style.css        # Layout responsivo
│   ├── vite.config.ts       # Proxy /api
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml       # PostgreSQL + Flask + React
├── .env.example
└── README.md
```

## Regras de frequência (POC)

- Cada aula tem uma duração em horas (`Lesson.hours`).
- Para cada matrícula, P soma horas presentes; F e J somam horas ausentes.
- Frequência do período registrado: `horas_presentes / (horas_presentes + horas_ausentes) × 100`.
- Limite total de faltas: `carga_horaria_curso × (1 − frequencia_minima/100)`.
- Alertas são calculados pelo limite de faltas restantes, **não** pela porcentagem parcial do período realizado.
- Dados históricos permanecem vinculados à matrícula de origem após transferência. Para implantação real, definir regras institucionais de aproveitamento de horas antes de consolidar a frequência entre turmas.

## Segurança e antes de usar com dados reais

Este projeto é uma **POC local**, não um produto pronto para produção. Alterar credenciais e segredo; habilitar HTTPS e `COOKIE_SECURE=true`; usar autenticação mais robusta/recuperação de senha; adicionar rate limiting, validação de dados mais completa, migrações Alembic, logs e auditoria imutável, testes de autorização, política de retenção de ocorrências e consentimentos/base legal conforme LGPD. Não disponibilize esta POC na internet com as credenciais demo. Também requer política de backups, segregação de ambientes e monitoramento.


## Novidades da versão 0.2
- Gestão de usuários no menu **Usuários** apenas para administrador: criação, edição de nome/e-mail/perfil/senha, ativação e desativação.
- Chamada rápida: ao criar uma aula ela é aberta automaticamente; todos iniciam presentes, marque **Faltou?** somente para ausentes e, quando necessário, **Justificada?**. Clique em **Salvar chamada** para persistir.
- Ocorrência na própria chamada: botão **Ocorrência** ao lado de cada aluno, permitindo categoria e descrição com data e autor registrados automaticamente.
- O botão **Marcar todos presentes** altera apenas a tela até clicar em **Salvar chamada**.
- Contas demonstração e banco de dados existentes são preservados ao atualizar com `docker compose up --build -d` (não use `down -v`).

### Atualização
Substitua os arquivos pelo ZIP v0.2 e rode `docker compose up --build -d`. O modelo do banco não mudou nesta versão; não é necessário executar o seed novamente.

## Atualização v0.3 — perfis e interface

- **Secretaria:** dashboard próprio com matrículas ativas, alunos cadastrados, turmas, transferências recentes, turmas sem professor e atalhos de operação.
- **Permissões:** o menu apresenta apenas os módulos do perfil; backend mantém autorização obrigatória nas rotas.
- **Professores em turmas:** endpoint restrito `/api/teachers` para selecionar responsáveis sem expor dados pessoais de outros usuários.
- **Visual:** redesign com tipografia mais legível, cores sóbrias, foco em tabelas, ações e estados.
- **Importante:** não foi possível concluir `npm install`/build integrado no ambiente de geração. Execute `docker compose up --build -d` e confira `docker compose logs -f frontend backend` para validar localmente. Não use `docker compose down -v` se deseja preservar dados.

## Novidades v0.4
- Dashboard do professor: turmas vinculadas e acesso rápido à chamada (sem alertas de frequência).
- Dashboard da Secretaria: painel de alertas de frequência, matrículas e transferências.
- Alertas permitidos somente para administrador, coordenação e secretaria, inclusive na API.
- Menu filtrado por perfil e paleta azul, amarelo e laranja discreta, inspirada na Fábrica de Programadores.
- Atenção: a indicação de "aulas do dia" ainda depende de um módulo futuro de horários; nesta POC são exibidas as turmas atribuídas.
- Reinicie com `docker compose down` e `docker compose up --build -d` (não use `down -v`).


## v0.5 — fluxos de cadastro
- Cursos, Turmas e Alunos agora seguem **listagem filtrável → novo registro → detalhes → editar/excluir**.
- A exclusão de cursos/turmas/alunos com histórico é bloqueada no backend com HTTP 409, preservando os registros acadêmicos.
- A chamada continua permitindo duração e data variáveis por encontro, sem calendário rígido.
- Matrículas, transferências e ocorrências são eventos com histórico e continuam em seus fluxos próprios; não se deve excluir histórico acadêmico indiscriminadamente.
- Para testar, execute `docker compose up --build -d`. Não execute `docker compose down -v` sobre dados que deseja conservar.


## Novidades v0.6

- Cursos, turmas e alunos: listagem, cadastro e detalhes (v0.5).
- Usuários: listagem com filtro, cadastro, detalhes, edição e ativar/desativar.
- Ocorrências e transferências: listagem com filtro, cadastro e detalhes; sem exclusão de histórico.
- Alunos: novo campo **Colégio onde estuda** e upload de foto nos detalhes (JPG/PNG/WebP até 3 MB).
- Chamada: ao passar o mouse ou focar o nome, aparece a foto; clicar amplia (quando cadastrada).
- Carômetro: exibe fotos cadastradas, com fallback para iniciais.
- Fotos ficam no volume Docker `student_photos`, não em pasta pública.

**Migração de banco existente (necessária uma vez ao atualizar da v0.5):**
```bash
docker compose up --build -d
docker compose exec backend flask --app app init-db
```
O comando `init-db` adiciona a coluna `student.school` quando ainda não existe. Não execute `down -v`, pois remove volumes.

**Atenção:** a POC ainda necessita de testes integrados, backups e endurecimento de segurança antes de receber dados reais de alunos.
