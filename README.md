# appCARC

Sistema de gestión para clubes: socios, cuotas y cobros, pagos online, actividades (escuelita, muro de escalada, eventos), caja e inventario. Está en uso en el **Club Andino Río Cuarto** (Córdoba, Argentina), donde lo usan la secretaría, los profesores y los socios.

**Demo:** https://app.appclub.net.ar/demo/. Manual por rol con usuarios de prueba; los datos son ficticios y se restablecen todas las noches.

Este repositorio es una presentación del proyecto: documentación de arquitectura, un contrato de la API, una especificación y una parte del código con sus tests. El código completo está en repositorios privados.

## Componentes

| Componente | Qué es | Stack |
|---|---|---|
| Backend | API única para todos los clientes | Node.js 20, Express 5, MongoDB 6 (replica set) con Mongoose, JWT, vitest |
| App móvil | App de socios y staff, también como PWA | Expo, React Native, TypeScript |
| Panel web | Panel del staff para pantalla grande | React 19, TypeScript, Vite, Tailwind |
| Panel de superadministración | Gestión de clubes, roles, usuarios y auditoría | React, Vite, Tailwind |

Infraestructura: Docker Compose sobre una Raspberry Pi 5 con SSD, publicada con un túnel de Cloudflare. CI en GitHub Actions. Integraciones: Mercado Pago, Google (OAuth, Sheets, Drive para backups) y notificaciones push de Expo.

## Contenido

| Ruta | Qué hay |
|---|---|
| [`docs/arquitectura.md`](docs/arquitectura.md) | Visión general en tres secciones: [Pagos](docs/arquitectura.md#pagos) (cobro y conciliación con Mercado Pago), [Varios clubes](docs/arquitectura.md#varios-clubes) (aislamiento por `clubId` y permisos `recurso:accion`) y [Operación](docs/arquitectura.md#operación) (despliegue, backups, CI). |
| [`docs/contrato-precio-no-vigente.md`](docs/contrato-precio-no-vigente.md) | Contrato de error `PRECIO_NO_VIGENTE`: qué responde la API cuando falta un precio, avisos escalonados de vencimiento y pago de Muro Libre por visita. |
| [`docs/specs/cuotas-calcularDeuda.md`](docs/specs/cuotas-calcularDeuda.md) | Especificación del cálculo de deuda de un socio: entradas, salidas, reglas, casos concretos y casos borde. |
| [`ejemplos/cuotas/`](ejemplos/cuotas/) | Los services de cuotas con sus 99 tests unitarios y la configuración de mutation testing (Stryker, 94,9 % de mutantes eliminados). Corre de forma independiente: `npm install && npx vitest run`. |
| [`ejemplos/ci/ci.yml`](ejemplos/ci/ci.yml) | Workflow de CI del backend: tests unitarios, tests de integración contra MongoDB con replica set y prueba del gateway nginx. |

## Algunos datos

- Multi-club desde el diseño: cada consulta filtra por club, y los roles y permisos se configuran por club.
- Los cobros se registran en transacciones de MongoDB: o se guarda todo (cobro, cuotas, saldo, caja) o nada.
- Los períodos de cuota se calculan en hora argentina, aunque el servidor corre en UTC.
- El backend tiene más de 1500 tests unitarios y una suite de integración contra una base real. Las dos corren en cada pull request.
