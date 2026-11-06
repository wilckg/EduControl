# Arquitetura do EduControl — reorganização inicial da v1.0

## Backend

- `backend/app/core.py`: app, configuração, modelos atuais e utilitários compartilhados.
- `backend/app/routes/auth.py`: login e contas.
- `backend/app/routes/catalog.py`: cursos e turmas.
- `backend/app/routes/students.py`: alunos e fotografias.
- `backend/app/routes/attendance.py`: matrículas, aulas, chamadas, frequência e alertas.
- `backend/app/routes/operations.py`: ocorrências, transferências e professores.
- `backend/app/routes/dashboards.py`: resumos e dashboards.
- `backend/app/commands.py`: comandos CLI.

O próximo refactor deverá separar `core.py` em models, extensions, schemas e services, e introduzir migrações versionadas sem alterar os dados existentes.

## Frontend

- `frontend/src/main.tsx`: entrada React.
- `frontend/src/App.tsx`: navegação, autenticação e composição (ainda grande).
- `frontend/src/shared.tsx`: comunicação API, constantes e utilitários compartilhados.
- `frontend/src/*Module.tsx`: módulos de cadastro e histórico.
- `frontend/src/*Profile.tsx`, `*Overview.tsx`, `*Dashboard.tsx`: views específicas.

Na próxima etapa, mover módulos para pastas `features/`, introduzir tipagem de DTOs, separar CSS em tokens, componentes e páginas, e adicionar testes. O refactor atual prioriza compatibilidade com a POC e banco preservado.

## Segurança e evolução

Ajustada a criação de cursos/turmas para Admin/Secretaria, e chamadas para Admin/Professor. A Coordenação segue consultando e pode editar dados de alunos e transferir, conforme a matriz desejada. Antes de produção, validar autorização de cada endpoint (principalmente fotos e consulta), proteção CSRF, migrações e trilha de auditoria completa.
