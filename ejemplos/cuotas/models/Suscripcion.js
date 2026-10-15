// Interfaz del modelo Suscripcion (en el backend real es un modelo Mongoose).
// Tramo de suscripción: { clubId, socioId, etiquetaId, fechaDesde: 'YYYY-MM', fechaHasta: 'YYYY-MM'|null, exento, active }.
// Los services solo usan los métodos de abajo; en los tests se reemplaza
// con vi.mock(), así que este ejemplo no necesita Mongo ni Mongoose.
const noImplementado = (metodo) => () => {
  throw new Error(`Suscripcion.${metodo}: interfaz sin implementación; mockeala en el test.`);
};

export default {
  find: noImplementado('find'),
  exists: noImplementado('exists'),
};
