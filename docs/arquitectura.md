# Arquitectura

appCARC tiene una sola API (Node 20, Express 5, Mongoose sobre MongoDB) y tres clientes: la app móvil de socios y staff (Expo / React Native, también como PWA), el panel web del staff (React) y el panel del superadministrador (React). Los tres comparten el mismo login (JWT) y los mismos permisos.

Cada recurso del backend vive en su carpeta, con la misma estructura:

```
src/resources/<recurso>/
  models/     esquemas Mongoose
  handlers/   un archivo por endpoint
  services/   lógica de negocio reutilizable (registrarCobro, calcularDeuda, …)
  routes.js   método + path → middleware de permisos → handler
  tests/      unit (con mocks) e integration (contra Mongo real)
```

## Pagos

### Cobro de secretaría

Un cobro registra en una sola operación lo que pagó un socio: cuotas de uno o más meses, cargos puntuales (viajes, inscripciones, indumentaria), saldos de eventos y visitas de Muro Libre. Todo pasa por un service único, `registrarCobro`, que:

1. Valida cada ítem contra la deuda real del socio (ver la [especificación de `calcularDeuda`](specs/cuotas-calcularDeuda.md)).
2. Resuelve el importe. Si el staff no escribe uno, toma el precio vigente; si no hay precio, responde con el contrato [`PRECIO_NO_VIGENTE`](contrato-precio-no-vigente.md).
3. Dentro de una **transacción de MongoDB** crea el cobro, marca las cuotas o visitas como pagadas, actualiza el saldo de los cargos y genera el movimiento de caja correspondiente.

Por eso la base corre como replica set: las transacciones no funcionan en un `mongod` standalone.

El importe por defecto es el **precio de hoy** para todos los meses adeudados. Cobrar cada mes al precio que regía entonces es una opción aparte, con permiso propio y motivo obligatorio, y queda registrada en el cobro.

### Pago online con Mercado Pago

Cada club configura su propia cuenta de Mercado Pago. Las credenciales se guardan por club, nunca en el código.

```
Staff o socio            Backend                          Mercado Pago
     │  pide un link        │                                   │
     ├─────────────────────►│ crea PagoOnlineIntent (pendiente) │
     │                      │ con los ítems ya resueltos        │
     │                      ├── crea preferencia ──────────────►│
     │◄──── link ───────────┤   (external_reference = intent)   │
     │                                                          │
     │  paga en Checkout Pro ──────────────────────────────────►│
     │                      │◄── webhook (firma HMAC por club) ─┤
     │                      │── consulta el pago con la API ───►│
     │                      │   procesarPagoMercadoPago:        │
     │                      │   intent → aprobado → registrarCobro
```

- **Intent:** al generar el link se guardan los ítems exactos que se van a cobrar (meses, visitas puntuales, cargos) y el total. Al confirmarse el pago se llama a `registrarCobro` con esos mismos ítems, sin volver a calcular precios.
- **Webhook:** es público, porque lo llama Mercado Pago. Se valida la firma HMAC-SHA256 del header `x-signature` con el secreto del club, en tiempo constante. Aun con firma válida, el backend no confía en el cuerpo de la notificación: consulta el pago a la API de Mercado Pago con las credenciales del club.
- **Idempotencia:** el intent pasa de estado con una actualización condicional (`pendiente` o `rechazado` → `aprobado`). Si el webhook llega dos veces, o el webhook y la conciliación llegan juntos, solo uno registra el cobro; el otro recibe "duplicado".
- **Monto:** si el pago aprobado no coincide con el total del intent, se marca rechazado con motivo `monto_no_coincide` y no se registra ningún cobro.
- **Link de un solo uso:** Checkout Pro permite pagar dos veces el mismo link. Por eso, en cuanto se confirma un pago, el backend vence la preferencia.

### Conciliación

Hay dos niveles:

1. **Pagos online sin confirmar.** Si no llega el webhook, un job cada 30 minutos (y un botón "revisar ahora" en la app) busca en Mercado Pago, por `external_reference`, los intents pendientes de los últimos 7 días y los procesa con la misma función que el webhook. Cada intent se aísla: un error en uno no frena la revisión de los demás, y las respuestas de error de la API quedan en el log.
2. **Movimientos contra pagos.** Cada movimiento de caja puede vincularse a uno o más pagos de Mercado Pago (id de pago, monto, fecha). Los cobros que nacen de un link propio se vinculan solos. Los demás, como transferencias o pagos importados de un extracto, se concilian a mano desde el panel, y se detectan los casos de "un pago, varios movimientos".

## Varios clubes

El sistema es multi-club. En producción hoy corren el Club Andino Río Cuarto y un club de demostración que se restablece todas las noches.

### Aislamiento por `clubId`

- Casi todos los documentos tienen `clubId`.
- El `clubId` sale del token del usuario (`req.user.clubId`), nunca del cuerpo de la petición.
- **Toda consulta que lee o escribe datos de un club filtra por `clubId`.** También las búsquedas por `_id` que llega en la URL: un id válido de otro club se responde como inexistente. Una consulta sin ese filtro se trata como una fuga de datos entre clubes, no como un detalle de estilo.
- Un club dado de baja deja de aceptar tokens de sus usuarios en la siguiente petición.
- Los procesos programados (morosidad, recordatorios, conciliación, avisos de precios) trabajan club por club, cada uno con sus propios datos y credenciales. Un candado en la base evita que dos ejecuciones del mismo job se superpongan.

### Permisos `recurso:accion`

Los permisos son strings con la forma `recurso:accion`: `socios:read`, `socios:create`, `cobros:write`, `inventario:write`, `cobros:precio-historico`. Son más de 50, definidos en un único módulo de constantes.

- **Roles por club:** cada club tiene sus roles (admin, secretaría, profesor, colaborador, socio…) y cada rol es una lista de permisos. El superadministrador los edita desde su panel.
- **Chequeo declarativo:** las rutas usan middleware (`authorize(PERMISOS.COBROS_WRITE)`); los handlers no chequean permisos a mano. Hay una variante para "el propio socio o quien tenga permiso", por ejemplo para que un socio vea su deuda.
- **Caché:** los permisos de cada club se guardan en memoria del proceso durante 5 minutos. Editar un rol desde la API invalida la caché de ese club al momento.
- **Superadministrador:** es un rol fuera de los clubes. Gestiona clubes, roles y usuarios, y pasa todos los chequeos.
- **Clientes:** los tres reciben los permisos del usuario y ocultan lo que no puede usar. La autorización real ocurre siempre en el backend.

## Operación

### Despliegue

Todo corre en una **Raspberry Pi 5 con SSD**. Un único `docker-compose.yml` levanta:

| Servicio | Rol |
|---|---|
| `app` | API (Node 20). |
| `mongo` | MongoDB 6 como replica set de un nodo (necesario para transacciones), con los datos en el SSD. |
| `mongo-init` | Inicializa el replica set en el primer arranque. |
| `mongo-express` | Interfaz web de administración de la base, de uso interno. |
| `staff`, `superadmin` | Paneles web compilados, servidos por nginx. |
| `gateway` | nginx que enruta `/`, `/staff/`, `/admin/` y `/api/` al servicio que corresponde. |
| `cloudflared` | Túnel de salida hacia Cloudflare: publica el gateway con dominio propio y HTTPS sin abrir puertos en el router. |

El gateway tiene un listener para cada camino de entrada. Solo el que está detrás del túnel confía en el header de IP del cliente que agrega el proxy. El otro lo ignora, así nadie puede falsificarlo desde afuera.

**Actualizar el backend:** `git pull`, `docker compose build app` y `docker compose up -d app`. El build del backend es liviano (`npm ci --omit=dev`) y se hace en la Raspberry. Los frontends **se compilan en una PC** y a la Raspberry llega el resultado: compilar Vite dentro de la Pi la dejó sin responder más de una vez.

Todos los secretos (JWT, credenciales de Mercado Pago por club, token del túnel, cuenta de servicio de Google) van en un `.env` que no se versiona.

### Backups

- **Diario, por cron en el host** (no dentro de un contenedor): `mongodump` comprimido de la base, subido a Google Drive con una cuenta de servicio.
- **Retención:** se conservan los últimos 30 backups; los más viejos se borran solos después de cada subida.
- Queda además una copia local en el SSD.

### Integración continua

Cada pull request y cada push a `main` corre tres jobs en GitHub Actions (ver [`ejemplos/ci/ci.yml`](../ejemplos/ci/ci.yml)):

| Job | Qué hace |
|---|---|
| `unit` | Tests unitarios con vitest. Los modelos están mockeados y no hace falta base. Hoy son más de 1500 tests. |
| `integration` | Levanta MongoDB 6 como replica set dentro del runner y corre los tests de integración (supertest sobre la app completa, con transacciones reales). No usa secretos: el setup de tests define los suyos y apaga las integraciones externas. |
| `nginx-gateway` | Prueba la configuración del gateway: qué IP de cliente le llega al backend por cada listener. |

Además:
- Cada uno de los cuatro repositorios tiene su propio CI (lint, typecheck, build).
- **Mutation testing:** se corre a mano con Stryker sobre los services de cuotas; hoy elimina el 94,9 % de los mutantes. Ver [`ejemplos/cuotas/`](../ejemplos/cuotas/).
- **Revisión nocturna automatizada** del código y del manual de usuario.
