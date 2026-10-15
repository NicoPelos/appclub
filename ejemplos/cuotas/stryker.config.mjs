// Mutation testing de los services de cuotas. Se corre a mano, no en CI:
//   npx stryker run                       → todos los services con los tests unitarios
//   npx stryker run -m <archivo>          → un solo service
// En el backend completo dio 94,9 % de mutantes eliminados.
/** @type {import('@stryker-mutator/api/core').PartialStrykerOptions} */
export default {
  testRunner: 'vitest',
  vitest: { configFile: 'vitest.config.js' },
  mutate: ['services/*.service.js'],
  coverageAnalysis: 'perTest',
  reporters: ['clear-text', 'progress', 'html'],
  htmlReporter: { fileName: 'reports/mutation/unit.html' },
  tempDirName: '.stryker-tmp',
  concurrency: 4,
};
