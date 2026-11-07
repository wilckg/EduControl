# EduControl v1.0 — Etapa 4: contatos, auditoria e importação

Esta etapa parte da **Etapa 3**, preservando os endpoints e registros anteriores.

## Novidades

- **Ficha do aluno → Contatos:** Administração e Secretaria registram contato, canal, assunto, resultado, resposta/descrição, próxima ação e data de retorno. Coordenação consulta; Professor não vê contatos administrativos.
- **Dashboard da Secretaria → alertas:** cada alerta oferece atalho **Registrar contato**, abrindo diretamente a ficha do estudante na aba de contatos.
- **Administração → Auditoria:** histórico paginado de eventos, com filtros por ação, responsável e período, exibindo a referência do registro. Os eventos já registrados pelo sistema continuam disponíveis; novos eventos de contato possuem campos estruturados, sem dados sensíveis na auditoria.
- **Alunos → Importar planilha:** assistente visual de 3 etapas: arquivo (com arrastar e soltar e modelo CSV), prévia + mapeamento de colunas, confirmação. O backend continua responsável pela validação e gravação transacional.
- **Migração `0002_contacts_audit`:** cria `student_contact` e acrescenta informações estruturadas à tabela `audit`.

## Atualização de um banco existente

1. Faça backup do PostgreSQL e das fotografias dos alunos.
2. Extraia a Etapa 4 em pasta nova, preservando configurações locais.
3. Execute na pasta principal:

```powershell
docker compose down
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
```

> **Nunca execute `docker compose down -v`** em um ambiente com dados que queira manter. Não é necessário rodar `seed` novamente para atualizar.

Para a instalação nova, depois da migração, utilize o procedimento de criação de usuários e dados de demonstração descrito no `README.md`.

## Testes

```powershell
docker compose exec backend python -m pytest -q
```

Os testes usam SQLite temporário. Antes de qualquer publicação real, valide fluxo de login, cada perfil, registro/consulta/atualização de contato, auditoria, upload de planilha e restauração de backup.

## Segurança e limitações

- Logs são acessíveis somente pelo perfil Administrador e os dados de contatos são limitados a Administração, Secretaria e Coordenação (somente leitura).
- Contatos **não podem ser apagados pela API** para preservar histórico; correções geram um evento de auditoria.
- Alterações preexistentes continuam auditadas com o formato antigo de evento/resumo. Os campos estruturados novos são preenchidos nos eventos de contato; enriquecer todas as mutações antigas exige outra etapa.
- A importação preserva o limite de 3 MB/2.000 linhas, requer prévia, valida novamente no commit e não cria transferências automaticamente.
- **Não há notificação automática ao estudante**, apenas registro administrativo; dados reais e de menores exigem revisão de LGPD, política de retenção e controles de acesso.
- A identidade institucional definitiva com as três logomarcas permanece pendente dos arquivos oficiais autorizados.
- A exportação operacional das chamadas para o sistema externo permanece pendente do arquivo de modelo acordado.
