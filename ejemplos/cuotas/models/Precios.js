// Interfaz del modelo Precios (en el backend real es un modelo Mongoose).
// Precio de una etiqueta: { clubId, etiquetaId, monto, vigenteDesde: Date, vigenteHasta: Date|null, active }.
// Los services solo usan los métodos de abajo; en los tests se reemplaza
// con vi.mock(), así que este ejemplo no necesita Mongo ni Mongoose.
const noImplementado = (metodo) => () => {
  throw new Error(`Precios.${metodo}: interfaz sin implementación; mockeala en el test.`);
};

export default {
  find: noImplementado('find'),
  findOne: noImplementado('findOne'),
};
