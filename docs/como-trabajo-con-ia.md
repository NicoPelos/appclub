# Cómo trabajo con asistentes de IA

appClub se programa con ayuda de asistentes de IA (Claude Code). Un asistente escribe código rápido, pero eso no alcanza para que el resultado sea confiable. Lo que lo vuelve confiable es el entorno que lo rodea: reglas escritas, especificaciones, pruebas y una persona que revisa. A ese conjunto se lo suele llamar *harness* (arnés), y la práctica de diseñarlo, *harness engineering*. Acá está el mío, con dónde mirar cada pieza: sus archivos reales están copiados en [`ejemplos/harness/`](../ejemplos/harness/).

Las decisiones las tomo yo. El asistente propone y escribe; no decide qué se hace ni qué entra.

## El circuito de un cambio

1. **Un issue** dice qué se quiere lograr y por qué, antes de tocar código.
2. **Una especificación** fija el comportamiento cuando la lógica es delicada (dinero, fechas, permisos). Ejemplo: [`specs/cuotas-calcularDeuda.md`](specs/cuotas-calcularDeuda.md), escrita junto con los tests que fijan cada regla.
3. **Un contrato**, cuando cambia lo que la API le dice a las apps. Ejemplo: [`contrato-precio-no-vigente.md`](contrato-precio-no-vigente.md), escrito antes de programar.
4. **Un pull request** con el cambio. Corre el CI: tests unitarios, tests de integración contra MongoDB real y una prueba del gateway ([`ejemplos/ci/ci.yml`](../ejemplos/ci/ci.yml)).
5. **Revisión mía** antes de integrar. No integro un cambio con el CI en rojo.
6. **Las decisiones quedan escritas** en el repositorio, no en la memoria de una conversación.

## Las piezas del harness

- **Archivos de contexto** (`CLAUDE.md`, `AGENTS.md`). Cada uno de los cuatro repositorios tiene el suyo, y hay un mapa general que los conecta. Fijan estructura, reglas y comandos. Ver [`CLAUDE.backend.md`](../ejemplos/harness/CLAUDE.backend.md) y [`AGENTS.mobile.md`](../ejemplos/harness/AGENTS.mobile.md).
- **Hooks.** Un hook `PreToolUse` corre antes de cada comando o edición del asistente y puede bloquearlo o pedir confirmación: impide editar `.env`, hacer force push a `main`, compilar frontends en la Raspberry Pi y escribir en la base de producción sin confirmar. Tiene su propio script de pruebas, con 49 casos. Ver [`hooks/`](../ejemplos/harness/hooks/).
- **Permisos.** Una lista de comandos permitidos y una regla explícita sobre producción: la lectura está permitida y la escritura no. Ver [`settings.ejemplo.json`](../ejemplos/harness/settings.ejemplo.json).
- **Revisión automática con Claude en GitHub Actions.** Una vez por semana revisa un módulo del backend, en modo solo lectura, y abre un issue por cada hallazgo, sin duplicar los que ya existen. Ver [`workflows/claude-nightly-review.yml`](../ejemplos/harness/workflows/claude-nightly-review.yml).

## Reglas que el asistente lee en cada sesión

Cada repositorio tiene un archivo `CLAUDE.md` con reglas del proyecto. El asistente lo lee al empezar, así que no depende de que yo me acuerde de repetirlas. Estas son tres, copiadas del repositorio real y sin tocar su sentido:

**Un club nunca ve datos de otro.**

> Casi todo documento tiene `clubId`. Cualquier query que lea/escriba datos de un club **tiene que filtrar por `clubId`** — un query sin ese filtro es una fuga de datos entre clubes, no un detalle de estilo. Lo mismo para cualquier `findOne`/`findById` por `_id` que venga de la URL: filtrar también por `clubId` para que un id válido de otro club no sea accesible.

**Antes de borrar algo "sin uso", verificar.**

> Las herramientas de detección de código muerto (y la detección a ojo) dan falsos positivos: un `export default` + nombrado que parecen duplicados puede ser que solo se use uno de los dos caminos; un archivo bajo `scripts/` puede ser un entry point manual que nada importa. Verificar con `grep -rn` en todo el repo y mirar `git log --oneline -- <archivo>` antes de asumir que algo es código muerto.

**Lo que ya está en producción no se renombra a la ligera.**

> Campos ya persistidos o expuestos por la API: **no renombrar** sin migración versionada y confirmación. Al tocar un modelo, usar los nombres que ya tiene.

Los scripts de migración que ya corrieron contra producción tampoco se borran sin mi confirmación, porque el repositorio no tiene forma de saber por sí solo si ya cumplieron su función.

## Pruebas que miden si los tests sirven

Tener tests no dice si detectan errores. Por eso sobre la lógica de cuotas corro *mutation testing* con Stryker: modifica el código a propósito (cambia operadores, condiciones, constantes) y verifica que algún test falle con cada cambio. Hoy detectan el 94,9 % de los cambios. Los números por archivo y cómo reproducirlos están en [`ejemplos/cuotas/`](../ejemplos/cuotas/README.md).

## Qué no hago

- No dejo que el asistente decida el alcance de un cambio.
- No acepto un cambio que no entiendo.
- No uso datos reales de socios para probar: las capturas y las demos salen de un club de demostración con datos inventados.
