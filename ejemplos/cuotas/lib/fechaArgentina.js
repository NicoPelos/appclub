// Recorte de src/services/fechaArgentina.js del backend: solo lo que usan los
// services de cuotas. Argentina no tiene horario de verano (siempre UTC-3) y
// el servidor corre en UTC, así que el período "del mes en curso" se calcula
// explícitamente en hora argentina.

export const ARG_OFFSET_MS = -3 * 60 * 60 * 1000;

// 'YYYY-MM' de la fecha, en huso horario argentino.
export const periodoDeFecha = (fecha) => {
  const local = new Date(fecha.getTime() + ARG_OFFSET_MS);
  return `${local.getUTCFullYear()}-${String(local.getUTCMonth() + 1).padStart(2, '0')}`;
};

// Instante en que arranca el período 'YYYY-MM': el 1° del mes a las 00:00
// hora argentina (03:00 UTC). Es la fecha de referencia para buscar el precio
// que regía en ese mes.
export const inicioDePeriodoArgentino = (periodo) => {
  const [year, month] = periodo.split('-').map(Number);
  return new Date(Date.UTC(year, month - 1, 1) - ARG_OFFSET_MS);
};
