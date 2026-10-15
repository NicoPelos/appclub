# Ejemplo: services de cuotas

Los services que calculan la deuda de un socio y resuelven la vigencia de precios, con sus tests unitarios y la configuración de mutation testing. Es una copia del backend de appCARC, aislada para que corra sola.

| Carpeta | Contenido |
|---|---|
| `services/` | `calcularDeuda`, `findPrecioVigente`, `resolverPreciosPorPeriodo`, `resolverVigenciaPrecio` y `estaExentoEnPeriodo`, iguales al backend salvo las rutas de import y algunos comentarios. |
| `models/` | **Interfaces**, no modelos Mongoose: objetos con los métodos que usan los services, que tiran error si se llaman sin mockear. Los tests los reemplazan con `vi.mock()`. |
| `lib/fechaArgentina.js` | Solo las dos funciones de fechas en hora argentina que usan estos services. |
| `tests/` | Tests unitarios. Incluyen los de caracterización (`C1`…`C22`, `D1`…`D7`) que fijan cada regla de la [especificación](../../docs/specs/cuotas-calcularDeuda.md). |

## Correr

```bash
npm install
npx vitest run        # 99 tests
npx stryker run       # mutation testing, unos 30 segundos
```

## Mutation testing

Stryker modifica el código de los services (cambia operadores, condiciones, constantes) y verifica que algún test falle con cada cambio. Resultado sobre esta carpeta:

| Service | Mutantes eliminados |
|---|---|
| `calcularDeuda` | 95,5 % |
| `exencion` | 100 % |
| `findPrecioVigente` | 100 % |
| `resolverPreciosPorPeriodo` | 86,4 % |
| `resolverVigenciaPrecio` | 96,0 % |
| **Total** | **94,9 %** (371 eliminados, 1 por timeout, 19 sobrevivientes, 1 sin cobertura) |

`resolverPreciosPorPeriodo` queda más bajo porque en el backend su regla se prueba sobre todo con tests de integración contra MongoDB, que no están incluidos acá.
