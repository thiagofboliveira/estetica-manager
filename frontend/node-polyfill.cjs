const crypto = require('node:crypto');
if (!global.crypto) {
  global.crypto = crypto.webcrypto || crypto;
}
if (!globalThis.crypto) {
  globalThis.crypto = crypto.webcrypto || crypto;
}
