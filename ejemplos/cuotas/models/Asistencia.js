// Interfaz del modelo Asistencia (en el backend real es un modelo Mongoose).
// Visita (check-in): { clubId, socioId, tipo, tipoPase, fecha, estadoPago, precioSugeridoSnapshot, active }.
// Los services solo usan los métodos de abajo; en los tests se reemplaza
// con vi.mock(), así que este ejemplo no necesita Mongo ni Mongoose.
const noImplementado = (metodo) => () => {
  throw new Error(`Asistencia.${metodo}: interfaz sin implementación; mockeala en el test.`);
};

export default {
  find: noImplementado('find'),
};
