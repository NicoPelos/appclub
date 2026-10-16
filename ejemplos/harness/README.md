# El harness de appClub

Las piezas que rodean al asistente de IA (Claude Code) para que el trabajo sea confiable. Son copias de los archivos reales; se explican en [`docs/como-trabajo-con-ia.md`](../../docs/como-trabajo-con-ia.md).

| Archivo | Qué es |
|---|---|
| [`CLAUDE.backend.md`](CLAUDE.backend.md) | Reglas del repositorio del backend: estructura, regla de multi-club, permisos, comandos, qué verificar antes de borrar, convención de nombres. El asistente lo lee al empezar cada sesión. Los otros tres repositorios (app, panel de staff, panel de superadmin) tienen el suyo, más un mapa general de los cuatro. |
| [`AGENTS.mobile.md`](AGENTS.mobile.md) | Instrucción para agentes en el repositorio de la app: leer la documentación exacta de la versión de Expo antes de programar, porque cambió mucho. |
| [`hooks/block-dangerous.sh`](hooks/block-dangerous.sh) | Hook `PreToolUse`: corre antes de cada comando o edición del asistente y puede bloquearla o pedir confirmación. |
| [`hooks/test-block-dangerous.sh`](hooks/test-block-dangerous.sh) | Pruebas del hook: 49 casos que deben bloquearse, pedir confirmación o pasar. Se corre con `bash hooks/test-block-dangerous.sh` (requiere `jq`). |
| [`settings.ejemplo.json`](settings.ejemplo.json) | Cómo se conecta el hook y qué se permite o se bloquea sobre la base de producción: lectura sí, escritura no. |
| [`workflows/claude-nightly-review.yml`](workflows/claude-nightly-review.yml) | Revisión semanal automática del código con Claude en GitHub Actions: un módulo por vez, solo lectura, y abre un issue por cada hallazgo sin duplicar los existentes. |

## Qué bloquea el hook

- Editar o borrar un archivo `.env` (tiene secretos).
- `git push --force` a `main`, `master` o `production`; con `--force-with-lease` pide confirmación.
- Compilar los frontends o la APK en la Raspberry Pi, o instalar todas las dependencias ahí. Dos veces la dejó sin responder.
- Escribir en la base de producción por `ssh` y `docker exec`: pide confirmación. Leer, no.
