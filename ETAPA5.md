# EduControl v1.0 — Etapa 5

## Entregas
- Rodapé compartilhado no login e nas telas autenticadas com a ordem Fábrica de Programadores → Prefeitura Municipal de Santana de Parnaíba → SENAI-SP. **Logos não incluídas**: insira os PNGs oficiais em `frontend/public/institutions/` conforme o README dessa pasta. Até lá, aparecem iniciais neutras.
- Em **Relatórios → Exportar chamadas**, selecione turma, intervalo opcional, formato, clique **Pré-visualizar** e só então **Baixar**.
- CSV UTF-8 com BOM e cabeçalhos fixos: `turma, curso, matricula, aluno, data_aula, horas_aula, conteudo, presenca, horas_presentes, horas_falta`.
- Excel com abas `Registros`, `Matriz` (datas identificadas por `AAAA-MM-DD#ID` para distinguir aulas do mesmo dia) e `Legenda`.
- A exportação inclui somente chamadas com registros salvos (P, F, J). **J conta como horas de falta**, conforme regra da POC. Não preencher dados ausentes como faltas.
- Administração, Secretaria e Coordenação podem exportar. Professor não possui acesso ao módulo de relatórios.
- Não há comunicação automática com sistema externo, importação de planilha no sistema de destino ou escolha de layout customizado ainda. Envie um modelo real para a adaptação futura.

## Atualizar
Faça backup do PostgreSQL e fotografias; preserve `.env` e volumes. Na raiz:

```powershell
docker compose down
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend python -m pytest -q
```

Não há novas tabelas ou migrações nesta etapa. **Não execute** `docker compose down -v`.

## Verificação manual
1. Abrir login e confirmar rodapé com placeholders.
2. Entrar como Secretaria e confirmar rodapé e aba Exportar chamadas.
3. Exportar uma turma com chamadas (CSV e XLSX), conferir P/F/J e que as horas são coerentes.
4. Entrar como Professor e conferir que Relatórios não aparece e que a API retorna 403.
5. Instalar logos autorizadas e reconstruir o frontend.
