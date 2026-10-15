# Contrato `PRECIO_NO_VIGENTE`

Qué responde la API cuando una operación necesita un precio y la etiqueta no tiene uno vigente para ese período. También describe los avisos al staff antes de que un precio venza.

## Por qué existe

Los precios de cada concepto (cuota social, escuelita, Muro Libre, remeras…) se cargan con fecha de inicio y, opcionalmente, de fin. Si un precio vence y nadie carga el siguiente, cualquier cobro que dependa de él falla. Antes la API respondía con un mensaje genérico ("No hay un precio vigente configurado para esta cuota"), sin decir qué etiqueta ni qué mes faltaban. El cliente no podía ofrecer un acceso directo a la pantalla de precios sin interpretar el texto.

El contrato fija:
- un **código estable** (`code`) para que los clientes reconozcan el caso sin leer el mensaje;
- **qué falta**: la etiqueta y el período;
- un mensaje distinto para el staff, que puede cargar precios, y para el socio que paga online, que no puede.

## Respuesta

```json
{
  "message": "No hay precio vigente para «Remeras» en diciembre 2026. Cargalo o actualizalo en Etiquetas → Precios para completar la operación.",
  "code": "PRECIO_NO_VIGENTE",
  "etiquetaId": "665f0c…",
  "etiquetaNombre": "Remeras",
  "periodo": "2026-12"
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `message` | string | Texto listo para mostrar. Si no se conoce la etiqueta dice «esta cuota»; si no se conoce el período, lo omite. |
| `code` | `"PRECIO_NO_VIGENTE"` | Constante. Es lo que tienen que comparar los clientes. |
| `etiquetaId` | string \| null | Id de la etiqueta sin precio. |
| `etiquetaNombre` | string \| null | Nombre de la etiqueta. |
| `periodo` | `"YYYY-MM"` \| null | Mes para el que falta el precio, en hora argentina. |

### Status HTTP

| Operación | Status |
|---|---|
| Registrar un cobro de secretaría (suscripción, precio de cada mes o Muro Libre pendiente) | **400** |
| Crear un cargo puntual sin monto | **400** |
| Registrar una visita de Muro Libre como pagada sin monto | **400** |
| Pago online del socio (link de Mercado Pago) | **400**, con el mensaje para el socio |
| `GET /api/muro-libre/precio-diario` | **200** con `monto: null` y los campos del contrato. Sigue siendo 200 porque los clientes ya esperaban `monto: null` cuando no hay precio. |

El período que se informa depende de la operación:
- en una suscripción, el mes de la fecha del cobro;
- con precio de cada mes, el primer mes sin precio;
- en una visita de Muro Libre, el mes de la visita.

Si el staff escribe el importe a mano, la operación funciona igual que antes y este error no aparece.

### Mensaje para el socio

Cuando paga online, el socio no puede cargar precios ni escribir un monto, así que el mensaje cambia y no menciona la pantalla de precios:

> Todavía no está cargado el precio de «Remeras» para diciembre 2026, así que por ahora no se puede pagar online. Le avisamos al club para que lo cargue.

El `code` y los demás campos son los mismos.

Además se avisa al staff con permiso `precios:read` (notificación push y campanita de la app y del panel web):
- Como mucho **una vez por etiqueta y por día**, aunque varios socios lo intenten. El límite se apoya en el historial de notificaciones, sin estado aparte; dos intentos simultáneos pueden generar dos avisos, y se acepta.
- El aviso se dispara sin esperarlo: no demora ni rompe la respuesta al socio.

## Muro Libre: un ítem por visita

Al generar el link de pago de visitas de Muro Libre pendientes:

- Cada visita vale **su** precio guardado. Si se registró sin precio (no había uno vigente ese día), toma el vigente **en la fecha de la visita**, igual que el cobro de secretaría. Así, cargar el precio después alcanza para poder cobrarla.
- Si tampoco hay precio para esa fecha, responde `PRECIO_NO_VIGENTE` con el mes de la visita.
- El link guarda **un ítem por visita**, con `asistenciaIds: [id]` y su importe, en vez de "N visitas al precio promedio". Al confirmarse el pago se marcan pagadas exactamente las visitas elegidas, cada una con su importe, aunque el staff haya cobrado otra en el medio.
- Los links generados con el formato anterior se siguen procesando como antes.

Esto corrigió un error: una visita sin precio sumaba 0 al link, el socio pagaba de menos y la visita quedaba igual como pagada.

```json
{
  "items": [
    { "socioId": "…", "asistenciaIds": ["a1"], "amount": 2000, "description": "Muro Libre — visita pendiente" },
    { "socioId": "…", "asistenciaIds": ["a2"], "amount": 2500, "description": "Muro Libre — visita pendiente" }
  ]
}
```

## Aviso anticipado de vencimiento

Un job diario busca precios con `vigenteHasta` en los próximos 30 días **sin un precio que los reemplace**, y avisa al staff con permiso de precios.

- **Escalones:** 30, 14, 7 y 1 día antes del vencimiento. Se avisa **una vez por escalón**, no todos los días. Según los días que faltan, corresponde el escalón más cercano: 20 → 30, 10 → 14, 3 → 7, 0 → 1.
- **Registro:** el precio guarda `avisoVencimiento: { vigenteHasta, diasAntes }` con el último escalón avisado. Solo lo escribe el job; los endpoints no lo tocan.
- **Si cambia `vigenteHasta`**, el registro ya no coincide y los avisos arrancan de nuevo.
- **Si el job no corrió un día**, avisa al siguiente con el escalón que corresponda.
- **Si el envío falla**, no marca nada y reintenta en la próxima corrida.
- **Texto:** "vence hoy", "vence mañana" o "vence el 28 de agosto (faltan N días)".
- **Datos de la notificación:** `{ tipo: 'precio_por_vencer', precioId, diasRestantes }`.
- **Canal:** las notificaciones quedan también en la campanita de la app y del panel web, así que llegan aunque el usuario no tenga push.

## Implementación de referencia

```js
// Helper compartido por todos los caminos (cobro, cargo puntual, Muro Libre, pago online).
export const PRECIO_NO_VIGENTE = 'PRECIO_NO_VIGENTE';

export const mensajePrecioNoVigente = ({ etiquetaNombre, periodo }) => {
  const cuota = etiquetaNombre ? `«${etiquetaNombre}»` : 'esta cuota';
  const cuando = periodo ? ` en ${nombrePeriodo(periodo)}` : '';
  return `No hay precio vigente para ${cuota}${cuando}. Cargalo o actualizalo en Etiquetas → Precios para completar la operación.`;
};

// Campos que acompañan a `message` en el cuerpo de la respuesta.
export const detallePrecioNoVigente = ({ etiqueta, periodo }) => ({
  code: PRECIO_NO_VIGENTE,
  etiquetaId: etiqueta?._id ? String(etiqueta._id) : null,
  etiquetaNombre: etiqueta?.nombre ?? null,
  periodo: periodo ?? null,
});
```

## Para los clientes

- Comparar `code === 'PRECIO_NO_VIGENTE'`, nunca el texto de `message`.
- Para el staff: mostrar `message` y ofrecer un acceso a Etiquetas → Precios, filtrado por `etiquetaId` si se puede.
- Para el socio: mostrar `message` tal cual; no hay acción posible de su lado.
