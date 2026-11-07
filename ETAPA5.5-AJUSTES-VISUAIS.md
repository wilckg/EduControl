# EduControl v1.0 — Etapa 5.5

Ajustes exclusivamente visuais em `frontend/src/style.css`:

- A lista de itens do menu lateral foi compactada e alinhada ao topo, sem remover o menu fixo e a rolagem independente.
- A grade do carômetro recebeu margem inferior para separar os cartões de alunos do rodapé institucional.
- Nenhuma mudança em backend, permissões, banco ou volumes.

## Atualização

Use a pasta completa deste ZIP como base e preserve a configuração `.env` da instalação anterior. Na pasta do projeto:

```powershell
docker compose down
docker compose up --build -d
```

O build completo e a validação visual ainda precisam ser feitos no navegador local.
