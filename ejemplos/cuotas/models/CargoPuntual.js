// Interfaz del modelo CargoPuntual (en el backend real es un modelo Mongoose).
// Cargo manual: { clubId, socioId, etiquetaId, estado, montoEsperadoSnapshot, montoPagadoSnapshot, active }.
// Los services solo usan los métodos de abajo; en los tests se reemplaza
// con vi.mock(), así que este ejemplo no necesita Mongo ni Mongoose.
const noImplementado = (metodo) => () => {
  throw new Error(`CargoPuntual.${metodo}: interfaz sin implementación; mockeala en el test.`);
};

export default {
  find: noImplementado('find'),
};
