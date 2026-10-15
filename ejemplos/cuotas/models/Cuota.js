// Interfaz del modelo Cuota (en el backend real es un modelo Mongoose).
// Cuota pagada de un socio: { clubId, socioId, etiquetaId, periodo: 'YYYY-MM', estado, active }.
// Los services solo usan los métodos de abajo; en los tests se reemplaza
// con vi.mock(), así que este ejemplo no necesita Mongo ni Mongoose.
const noImplementado = (metodo) => () => {
  throw new Error(`Cuota.${metodo}: interfaz sin implementación; mockeala en el test.`);
};

export default {
  find: noImplementado('find'),
  findOne: noImplementado('findOne'),
};
