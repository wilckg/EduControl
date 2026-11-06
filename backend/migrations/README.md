# Migrações versionadas (Alembic)

Dentro de `backend/` ou no container backend:

```bash
alembic upgrade head
alembic current
```

A revisão `0001_baseline` cria tabelas que não existirem e adiciona colunas legadas
quando necessário, sem apagar dados anteriores. Não execute `alembic downgrade`
em bases com dados reais. Para criar futuras migrações, revise manualmente o
script antes de aplicar; por exemplo `alembic revision --autogenerate -m "descricao"`.

Faça backup do PostgreSQL antes de aplicar migrações em banco existente.
