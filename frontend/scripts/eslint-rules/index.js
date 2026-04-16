/**
 * STORY-4.3 (TD-FE-004) — Local ESLint plugin entrypoint.
 *
 * Exposes the single rule `no-hardcoded-hex` via the
 * `eslint-plugin-local-rules` convention. Registered in
 * `frontend/.eslintrc.json` under `plugins: ["local-rules"]`.
 */

'use strict';

const noHardcodedHex = require('./no-hardcoded-hex');
const noInlineStyles = require('./no-inline-styles');

module.exports = {
  rules: {
    'no-hardcoded-hex': noHardcodedHex,
    'no-inline-styles': noInlineStyles,
  },
};
