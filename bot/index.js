const { default: makeWASocket, DisconnectReason, useMultiFileAuthState, Browsers } = require('@whiskeysockets/baileys');
require('dotenv').config();

async function startBot() {
  const { state, saveCreds } = await useMultiFileAuthState('auth');
  const sock = makeWASocket({
    auth: state,
    browser: Browsers.ubuntu('Chrome'),
    connectTimeoutMs: 120000,
    keepAliveIntervalMs: 10000
  });
  sock.ev.on('creds.update', saveCreds);
  sock.ev.on('connection.update', async ({ connection, lastDisconnect }) => {
    if (connection === 'open') {
      console.log('Bourgelat connected!');
    }
    if (connection === 'close') {
      console.log('Disconnected:', lastDisconnect?.error?.message);
    }
  });
  await new Promise(r => setTimeout(r, 3000));
  const registered = sock.authState.creds.registered;
  if (!registered) {
    try {
      const code = await sock.requestPairingCode('2348067875847');
      console.log('PAIRING CODE: ' + code);
    } catch(e) {
      console.log('Pairing error:', e.message);
    }
  }
}

startBot().catch(console.error);
