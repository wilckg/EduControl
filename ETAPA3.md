# EduControl v1.0 — Etapa 3: importação em lote e migrações

## O que foi adicionado

- **Alunos > Importar planilha** (somente administrador e Secretaria).
- CSV UTF-8 (vírgula, ponto e vírgula ou tab) e XLSX, até **3 MB e 2.000 linhas**.
- Mapeamento das colunas Nome, Matrícula, E-mail, Colégio e Turma.
- Turma indicada por código na planilha ou escolhida como padrão na interface.
- Prévia **sem gravação**, com identificação de novos alunos, matrículas adicionais, registros já existentes e linhas inválidas.
- Confirmação com leitura e validação do arquivo **novamente**, dentro de uma transação.
- Registro de auditoria `students.bulk_import` e testes pytest básicos.
- Alembic inicial: `backend/alembic.ini`, `backend/migrations/versions/0001_baseline.py`.

## Atualizar banco existente

**Faça backup antes de atualizar**. Suba os serviços e execute:

```powershell
docker compose down
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
```

A revisão baseline identifica as tabelas existentes e não apaga cadastros ou fotos. As versões anteriores podem continuar usando `flask --app app init-db`, mas nas próximas evoluções utilize `alembic upgrade head`.

## Testar

```powershell
docker compose exec backend python -m pytest -q
```

Abra `http://localhost:5173`, faça login como administrador ou Secretaria, entre em **Alunos > Importar planilha** e escolha um arquivo de exemplo.

Exemplo CSV UTF-8:

```csv
Nome;Matrícula;Colégio;Turma
Ana Souza;EDU9001;Escola Municipal Exemplo;WEB-2026-A
Bruno Lima;EDU9002;Escola Estadual Exemplo;WEB-2026-A
```

O código da turma deve existir no EduControl. Caso os códigos do sistema de origem sejam diferentes, utilize a seleção de turma padrão ou prepare o mapeamento de códigos.

## Regras e limites

- Uma matrícula existente **na mesma turma** não é criada novamente.
- Aluno existente com **mesmo número de matrícula** e nome compatível pode receber matrícula em outra turma.
- Matrícula repetida na planilha, turma desconhecida ou registro existente com mesmo número de matrícula e nome diferente bloqueiam a confirmação.
- Registros existentes não têm nome, e-mail ou colégio sobrescritos automaticamente.
- A importação é **tudo ou nada** quando há erros de validação, para evitar cadastros parciais.
- A confirmação não faz transferência automática: se o aluno já está em outra turma, a nova matrícula é adicional. Use o módulo Transferências quando for uma movimentação de fato.
- Fotografias continuam sendo gerenciadas individualmente; não são importadas pela planilha nesta etapa.
- Adequar retenção, autorização, privacidade e proteção de dados antes de usar informações reais de menores.

## Próxima etapa

Histórico de contatos do aluno, auditoria detalhada, exportação de chamada adaptada à automação e logos institucionais oficiais (quando fornecidas).
