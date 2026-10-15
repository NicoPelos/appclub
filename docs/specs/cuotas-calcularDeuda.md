# Especificación: `calcularDeuda`

Calcula cuánto debe un socio: cuotas de sus suscripciones y otros cargos pendientes. Lo usan la pantalla de deuda del socio (`GET /api/socios/:id/deuda`), los avisos de morosidad, el recordatorio de cuotas y la exportación a planillas.

El código y sus tests están en [`ejemplos/cuotas/`](../../ejemplos/cuotas/): `services/calcularDeuda.service.js` y `tests/calcularDeuda.test.js`. Los tests de caracterización llevan en el nombre el código de la regla o caso que fijan (`C2:`, `D3:`, …).

## Tipos

- `Suscripcion.fechaDesde` y `fechaHasta`: strings `'YYYY-MM'`. `fechaHasta: null` significa tramo abierto.
- `Cuota.periodo`: string `'YYYY-MM'`. Una cuota pertenece a (socio, etiqueta, período).
- `Precios.vigenteDesde` y `vigenteHasta`: `Date` (instantes). `vigenteHasta` puede ser `null`.
- Montos: `Number`, sin moneda ni redondeo.
- Todo se filtra por `clubId` (ver [Varios clubes](../arquitectura.md#varios-clubes)).

## Entrada

```
calcularDeuda({ socioId, clubId, incluirPrecioHistorico = false })
```

| Parámetro | Descripción |
|---|---|
| `socioId` | Socio cuya deuda se calcula. |
| `clubId` | Club del usuario que pide la deuda. |
| `incluirPrecioHistorico` | Opcional. Agrega el desglose a precio de cada mes (regla R4c). Cuesta una consulta extra por etiqueta adeudada, así que los procesos que recorren muchos socios no lo piden, y el endpoint solo lo pide para usuarios con el permiso `cobros:precio-historico`. |

## Salida

```
{ suscripciones: Deuda[], otrosCargos: OtroCargo[] }
```

Los dos bloques se calculan en paralelo y no dependen uno del otro.

### `Deuda` (una por suscripción activa)

| Campo | Descripción |
|---|---|
| `suscripcionId`, `etiqueta`, `planId`, `fechaDesde`, `fechaHasta` | Datos del tramo. `etiqueta` viene con `nombre`, `unidad` y `uso_sistema`. |
| `vigente` | `true` si el tramo sigue en curso (ver abajo). |
| `periodoActual` | Mes en curso en hora argentina (`'YYYY-MM'`). |
| `periodos` | Meses adeudados, en orden cronológico. |
| `mesesDeuda` | `periodos.length`. |
| `periodosPagados` | Todos los períodos pagados de esa etiqueta en la historia del socio. |
| `ultimoPeriodoPagado` | Último período pagado hasta el mes en curso, o `null`. |
| `precioUnitario` | Precio vigente hoy, o `null` si no hay. |
| `totalDeuda` | `mesesDeuda × precioUnitario`, o `null` si no hay precio. |
| `exento` | Solo presente (y `true`) en tramos exentos. |
| `desglosePrecioHistorico`, `totalDeudaPrecioHistorico` | Solo con `incluirPrecioHistorico` (R4c). |

### El campo `vigente`

`vigente` se calcula en cada respuesta; no está guardado en la base:

```
vigente = fechaHasta == null || fechaHasta >= mesEnCurso
```

Se calcula igual en las tres ramas (exento, a futuro y normal). Los clientes lo usan para separar los planes en curso del historial. Antes lo deducían de `fechaHasta && mesesDeuda === 0`, y eso marcaba como cerrado un tramo al día con `fechaHasta` futura. Como depende del mes en curso, el mismo tramo puede venir `vigente: true` un mes y `false` al siguiente sin que cambie ningún dato.

### `OtroCargo`

`otrosCargos = [muroLibre?, ...cargosPuntuales, ...eventos]`, en ese orden.

| Tipo | Forma |
|---|---|
| `muro_libre` | Un solo objeto con `cantidadPendiente`, `unidadPendiente: 'visita'`, `fechas[]` (se mantiene por compatibilidad con clientes viejos), `visitas[{ asistenciaId, fecha, monto }]` y `totalDeuda`. Solo aparece si hay al menos una visita pendiente. |
| `cargo_puntual` | Uno por cargo: `cargoPuntualId`, `nombre`, `descripcion`, `totalDeuda`, `estado`, `montoPagado`. |
| `evento` | Uno por participación: `eventoId`, `participanteId`, `nombre`, `descripcion`, `totalDeuda`, `estado`, `montoPagado`. |

## Reglas

`hoy` es el mes en curso en **hora argentina** (`periodoDeFecha(new Date())`). El servidor corre en UTC, y con la hora del proceso el último día de cada mes desde las 21:00 ya contaba el mes siguiente.

### Suscripciones

Se buscan **todas** las suscripciones activas del socio en el club, sin filtrar por fecha: un tramo cerrado puede seguir debiendo meses de su propio rango.

**R1. Períodos pagados.** Antes de cualquier rama, `periodosPagados` son los períodos de todas las cuotas pagadas y activas de (socio, club, etiqueta). Abarcan toda la historia, no solo el tramo. La grilla de edición de meses los necesita incluso en tramos exentos.

**R2. Exenta** (`exento: true`): `mesesDeuda 0`, `periodos []`, `totalDeuda 0`, `precioUnitario null`, `ultimoPeriodoPagado null`, `exento: true`. No consulta precio.

**R3. A futuro** (`fechaDesde > hoy`): no debe nada, pero trae `precioUnitario` = precio vigente **hoy**, para que la pantalla de cobro pueda sugerir el monto de un adelanto.

**R4. Normal.**
- `hasta = min(fechaHasta ?? hoy, hoy)`: la deuda llega como máximo al mes en curso. Se pueden adelantar cuotas, pero no se cobran meses que todavía no llegaron.
- Candidatos: todos los meses de `fechaDesde` a `hasta`, inclusive en los dos extremos.
- `periodos` = candidatos menos los meses con cuota pagada de (socio, club, **etiqueta**). Se busca por etiqueta y no por suscripción: al editar los meses de un plan, el tramo viejo se puede reemplazar por uno nuevo con otro id, y las cuotas ya pagadas siguen colgando del viejo.
- `ultimoPeriodoPagado`: el mayor período pagado de esa etiqueta con `periodo <= hoy`. Los adelantos no cuentan.
- `precioUnitario`: precio vigente hoy. **Todos los meses adeudados se valúan a ese precio.**
- `totalDeuda = precioUnitario !== null ? mesesDeuda × precioUnitario : null`.

**R4b. Tramos superpuestos.** Si dos tramos activos no exentos de la misma etiqueta cubren el mismo mes, ese mes se debe una sola vez: queda en el tramo que arrancó primero y se descuenta de los demás (`periodos`, `mesesDeuda` y `totalDeuda`). El orden de `suscripciones` no cambia.

**R4c. Precio de cada mes** (solo con `incluirPrecioHistorico`). Después de R4b, cada deuda trae:
- `desglosePrecioHistorico = [{ periodo, monto }]`, con el precio que regía en cada mes adeudado. La fecha de referencia es el 1° del mes a las 00:00 hora argentina. Si un mes no tiene precio, `monto` es `null`.
- `totalDeudaPrecioHistorico`: la suma, o `null` si algún mes no tiene precio. No se adivina un precio.
- Se resuelve con **una consulta por etiqueta**, no una por mes.
- `totalDeuda` no cambia: el precio de hoy sigue siendo el default, y cobrar a precio de cada mes es una opción con permiso propio y motivo obligatorio.

### Otros cargos

**R5. Muro Libre.** Visitas con pase diario, pago pendiente y activas, ordenadas por fecha, agregadas en un solo objeto. `totalDeuda = Σ(precioSugeridoSnapshot ?? 0)`, y cada visita trae `monto: precioSugeridoSnapshot ?? null`. Los pases mensuales no entran acá porque los cubre la suscripción.

**R6. Cargos puntuales.** Uno por cada cargo con estado `pendiente` o `parcial`, ordenados por fecha de creación. `totalDeuda = montoEsperado − (montoPagado || 0)`: si ya se cobró una seña, se muestra el saldo. Si el cargo no tiene etiqueta, `nombre` es `'Cargo puntual'`.

**R7. Eventos.** Igual que R6, a partir de las participaciones en eventos. Si el evento no tiene nombre, `nombre` es `'Evento'`. Incluye `participanteId`, que hace falta para cobrarlo.

## Casos

Supuesto común: hoy = 2026-10-11, etiqueta "Cuota Social", precio vigente $15.000, salvo que se diga otra cosa.

| # | Dado | Resultado |
|---|---|---|
| C1 | Sin suscripciones ni cargos | `{ suscripciones: [], otrosCargos: [] }` |
| C2 | Desde `2026-07`, abierta; pagó `07` y `08` | `periodos ['2026-09','2026-10']`, `totalDeuda 30000`, `ultimoPeriodoPagado '2026-08'` |
| C3 | Igual que C2, sin precio cargado | `mesesDeuda 2`, `precioUnitario null`, `totalDeuda null` |
| C4 | Tramo cerrado `2026-02..2026-05`; pagó `02` a `04` | `periodos ['2026-05']`, `totalDeuda 15000` |
| C5 | Desde `2025-11`, sin pagos, hoy = `2026-01` | 3 meses (cruza el año), `totalDeuda 45000` |
| C6 | Desde `2026-08`; precio $12.000 hasta septiembre y $18.000 hoy | 3 × 18.000 = `54000` (todo al precio de hoy) |
| C7 | La cuota de `08` está pagada en un tramo anterior de la misma etiqueta | `08` no se cobra |
| C8 | Pagó adelantado `2026-12`; debe `09` y `10`; el último pago anterior fue `08` | `ultimoPeriodoPagado '2026-08'` |
| C9 | Tramo `2026-09..2026-12` (fin futuro), sin pagos | `periodos ['2026-09','2026-10']`, `vigente: true` |
| C10 | Exenta; pagó `2026-01` y `2026-02` antes de pasar a exento | `totalDeuda 0`, `periodosPagados ['2026-01','2026-02']`, `exento: true` |
| C11 | Desde `2026-11` (a futuro) | `totalDeuda 0`, `precioUnitario 15000` |
| C12 | Visitas de Muro Libre de $2.000, $2.500 y una sin precio | `cantidadPendiente 3`, `totalDeuda 4500`, la tercera con `monto null` |
| C13 | Cargo de $30.000 con seña de $15.000 | `totalDeuda 15000`, `montoPagado 15000` |
| C20 | Hoy = 2026-10-15; precio $10.000 hasta junio, $12.000 desde julio, $15.000 desde septiembre; debe de marzo a octubre | `totalDeuda 120000` (8 × 15.000), `totalDeudaPrecioHistorico 94000` |
| C21 | Igual que C20, pero el primer precio arranca en marzo y debe desde febrero | febrero con `monto null`, `totalDeudaPrecioHistorico null`, `totalDeuda` sin cambios |
| C22 | C20 sin `incluirPrecioHistorico` | `totalDeuda 120000`, sin los campos de R4c y sin la consulta extra de precios |

## Casos borde

- **Fin de mes en hora argentina.** El 31/08 a las 23:30 (02:30 UTC del 01/09) el mes en curso sigue siendo agosto; el 01/09 a las 00:30 ya es septiembre. Lo mismo vale para `vigente`.
- **`fechaDesde` igual al mes en curso** no es "a futuro": debe ese mes.
- **`fechaHasta` igual al mes en curso** cuenta ese mes y deja el tramo `vigente`.
- **Precio en 0** no es "sin precio": `totalDeuda 0`, no `null`.
- **Saldo negativo.** En cargos puntuales y eventos, si se pagó de más y el estado sigue en `parcial`, `totalDeuda` sale negativo. No tiene piso en 0.
- **Duplicados.** `periodosPagados` puede repetir un período si hay dos cuotas pagadas del mismo mes.
- **Tope de seguridad.** La expansión de meses corta en 601 períodos.
- **Tramo exento superpuesto con uno no exento.** `calcularDeuda` no anula el no exento; el check-in, en cambio, considera exento al socio. Pendiente de decisión de negocio.
- **Hueco al cerrar un precio.** Al cargar un precio nuevo, el anterior se cierra en `desde − 24 h`. Como las vigencias se comparan como instantes, durante unas horas antes del inicio del nuevo ningún precio rige, y en ese lapso `totalDeuda` es `null`. El precio de cada mes (R4c) no tiene este problema porque toma el 1° a las 00:00 hora argentina.

## Services relacionados

| Service | Regla |
|---|---|
| `findPrecioVigente` | Precio activo del club y la etiqueta con `vigenteDesde <= fecha` y (`vigenteHasta` null o `>= fecha`). Si hay varios, gana el de `vigenteDesde` más reciente. |
| `resolverPreciosPorPeriodo` | Lo mismo para muchos meses con una sola consulta; elige en memoria con la misma regla. |
| `estaExentoEnPeriodo` | `true` si hay un tramo activo y exento de esa etiqueta que contiene el período. Sin `socioId` o `etiquetaId` devuelve `false` sin consultar la base. |
| `resolverVigenciaPrecio` | Al crear o editar un precio: rechaza fechas invertidas (400), dos precios que arrancan el mismo día o uno que pisa a otro ya programado (409), y pide confirmación (409 con el cierre propuesto) antes de cerrar el precio anterior. |
