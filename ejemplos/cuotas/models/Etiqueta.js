// Interfaz del modelo Etiqueta (en el backend real es un modelo Mongoose).
// Concepto cobrable (Cuota Social, Escuelita, Muro Libre…): { clubId, nombre, unidad, uso_sistema }.
// Los services solo usan los métodos de abajo; en los tests se reemplaza
// con vi.mock(), así que este ejemplo no necesita Mongo ni Mongoose.
const noImplementado = (metodo) => () => {
  throw new Error(`Etiqueta.${metodo}: interfaz sin implementación; mockeala en el test.`);
};

export default {
  findById: noImplementado('findById'),
  findOne: noImplementado('findOne'),
};
