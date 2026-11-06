# EduControl v1.0 — Etapa 2: serviços e relatórios

Esta entrega parte da **v1.0 etapa 1**, mantendo o banco e endpoints da POC. Não executar `docker compose down -v`.

## Estrutura principal

```
backend/app/
  extensions.py             # configuração do Flask / SQLAlchemy
  models.py                 # entidades relacionais
  security.py               # autenticação/autorização/validação
  serializers.py            # JSON dos modelos
  services/frequency.py     # frequência por matrícula
  services/reports.py       # regras, filtros, progresso de carga horária
  routes/reports.py         # relatório JSON e Excel
  core.py                   # ponte para imports legados; será removida gradualmente
frontend/src/
  Reports.tsx               # filtros, métricas, tabela e exportação
```

## Endpoints novos

- `GET /api/reports/attendance` — filtros opcionais `course_id`, `class_id`, `student_id`, `date_from`, `date_to` (AAAA-MM-DD).
- `GET /api/reports/attendance/export` — mesmos filtros, retorna XLSX com abas **Frequência** e **Critérios**.
- Perfis: `admin`, `secretaria`, `coordenador`. `professor` recebe 403. As permissões do frontend são apenas auxiliares.

## Regras de cálculo

- Frequência da matrícula no período = horas presentes / (horas presentes + horas ausentes) x 100. Faltas justificadas (`J`) contam como horas ausentes na POC.
- Sem horas registradas no período, frequência = **não disponível**, não 100%.
- Progresso da turma = total de horas em `Lesson` até a data final / carga horária do curso. Exibe no máximo 100%, sem esconder horas excedentes na coluna de horas ministradas.
- Risco de faltas = ausências acumuladas da matrícula até a data final em comparação ao limite definido no curso. `warning` até 8h restantes, `critical` até 4h, `exceeded` abaixo de zero.
- Matrículas de origem e destino de transferências permanecem separadas até haver regra institucional de aproveitamento.
- O filtro de data inicial afeta horas presentes e de falta da tabela; não redefine o acumulado para risco e progresso. A data final limita todos os cálculos.

## Atualização no Windows/WSL2

1. Faça backup da pasta e banco da etapa anterior. Preserve `.env` e fotos.
2. Extraia esta versão e execute no diretório do `docker-compose.yml`:

```powershell
docker compose down
docker compose up -d --build
```

3. Acesse `http://localhost:5173` e faça login com `admin@educontrol.local` / senha configurada em `DEMO_PASSWORD` (padrão da demo: `Demo@12345`).
4. Acesse o item **Relatórios**, aplique filtros e clique em **Exportar Excel**.
5. Para validar a API:

```powershell
docker compose exec backend python -m pytest -q
```

Os testes usam **SQLite isolado**, nunca o PostgreSQL da POC. Esta etapa **não altera o esquema do banco**. Em uma próxima etapa serão adicionadas migrações versionadas, importação CSV/XLSX e rastreabilidade ampliada.

**Aviso:** código demonstrativo. Não utilizar dados reais de menores nem disponibilizar publicamente sem revisão de autenticação, LGPD, logs e políticas de retenção.
