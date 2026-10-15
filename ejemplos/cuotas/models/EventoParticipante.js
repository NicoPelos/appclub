// Interfaz del modelo EventoParticipante (en el backend real es un modelo Mongoose).
// Participante de un evento: { clubId, socioId, eventoId, estado, montoEsperadoSnapshot, montoPagadoSnapshot, active }.
// Los services solo usan los métodos de abajo; en los tests se reemplaza
// con vi.mock(), así que este ejemplo no necesita Mongo ni Mongoose.
const noImplementado = (metodo) => () => {
  throw new Error(`EventoParticipante.${metodo}: interfaz sin implementación; mockeala en el test.`);
};

export default {
  find: noImplementado('find'),
};
