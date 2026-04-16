/**
 * eslint-plugin-local-rules resolver.
 * Points to the rules directory at scripts/eslint-rules/.
 * Each rule exported from index.js is available as local-rules/<name>.
 */
module.exports = require('./scripts/eslint-rules');
