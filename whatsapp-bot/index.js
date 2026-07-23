require('dotenv').config();

/**
 * WhatsApp automation service using BAILEYS (NOT whatsapp-web.js, NOT Twilio).
 * Connects over WebSocket directly - no browser/Puppeteer involved, so the
 * "database error occurred on your browser. Please relink your device"
 * issue from whatsapp-web.js cannot happen here.
 *
 * Same HTTP API as before: GET /health, POST /send, POST /send-bulk
 * so reminder_scheduler.py and the dashboard's "send now" button need
 * ZERO changes.
 */

const express = require('express');
const qrcode = require('qrcode-terminal');
const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
} = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');

const PORT = process.env.WA_BOT_PORT || 4000;
const API_KEY = process.env.WA_BOT_API_KEY || 'change-this-secret';
const AUTH_DIR = './auth_info_baileys';

console.log('[whatsapp-bot] Loaded API key from .env:', API_KEY ? '(set)' : '(NOT SET)');
console.log('[whatsapp-bot] Loaded port from .env:', PORT);

const app = express();
app.use(express.json());

let sock = null;
let isReady = false;

async function startSock() {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
  const { version } = await fetchLatestBaileysVersion();

  sock = makeWASocket({
    version,
    auth: state,
    printQRInTerminal: false, // we handle QR printing ourselves below
  });

  sock.ev.on('creds.update', saveCreds);

  sock.ev.on('connection.update', (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      isReady = false;
      console.log('\n=== SCAN THIS QR CODE WITH WHATSAPP (Linked Devices) ===\n');
      qrcode.generate(qr, { small: true });
    }

    if (connection === 'open') {
      isReady = true;
      console.log('[whatsapp-bot] WhatsApp connection OPEN. Logged in and listening.');
    }

    if (connection === 'close') {
      isReady = false;
      const statusCode = new Boom(lastDisconnect?.error)?.output?.statusCode;
      const loggedOut = statusCode === DisconnectReason.loggedOut;
      console.log('[whatsapp-bot] Connection closed. Reason code:', statusCode, '- reconnecting:', !loggedOut);

      if (!loggedOut) {
        // transient disconnect -> just reconnect with same saved session
        startSock();
      } else {
        console.log('[whatsapp-bot] Logged out. Delete the auth_info_baileys folder and restart to re-link.');
      }
    }
  });
}

startSock().catch(err => {
  console.error('[whatsapp-bot] Failed to start:', err);
});

function toJid(rawNumber) {
  if (!rawNumber) return null;
  let n = String(rawNumber).replace(/[^\d]/g, '');
  if (!n) return null;
  if (n.length === 10) n = '91' + n;
  return `${n}@s.whatsapp.net`;
}

function checkApiKey(req, res, next) {
  const key = req.headers['x-api-key'];
  if (key !== API_KEY) {
    return res.status(401).json({ ok: false, error: 'invalid api key' });
  }
  next();
}

app.get('/health', (req, res) => {
  res.json({ ok: true, ready: isReady });
});

app.post('/send', checkApiKey, async (req, res) => {
  if (!isReady || !sock) {
    return res.status(503).json({ ok: false, error: 'WhatsApp client not ready yet (scan QR / wait for startup)' });
  }
  const { to, message } = req.body || {};
  const jid = toJid(to);
  if (!jid || !message) {
    return res.status(400).json({ ok: false, error: 'to and message are required' });
  }
  try {
    const [result] = await sock.onWhatsApp(jid);
    if (!result || !result.exists) {
      return res.status(404).json({ ok: false, error: `${to} is not on WhatsApp` });
    }
    await sock.sendMessage(jid, { text: message });
    console.log(`[whatsapp-bot] Sent to ${jid}`);
    return res.json({ ok: true, to: jid });
  } catch (err) {
    console.error('[whatsapp-bot] send failed:', err);
    return res.status(500).json({ ok: false, error: String(err) });
  }
});

app.post('/send-bulk', checkApiKey, async (req, res) => {
  if (!isReady || !sock) {
    return res.status(503).json({ ok: false, error: 'WhatsApp client not ready yet' });
  }
  const { messages } = req.body || {};
  if (!Array.isArray(messages)) {
    return res.status(400).json({ ok: false, error: 'messages must be an array of {to, message}' });
  }

  const results = [];
  for (const item of messages) {
    const jid = toJid(item.to);
    if (!jid || !item.message) {
      results.push({ to: item.to, ok: false, error: 'missing to/message' });
      continue;
    }
    try {
      const [result] = await sock.onWhatsApp(jid);
      if (!result || !result.exists) {
        results.push({ to: item.to, ok: false, error: 'not on WhatsApp' });
        continue;
      }
      await sock.sendMessage(jid, { text: item.message });
      results.push({ to: item.to, ok: true });
    } catch (err) {
      results.push({ to: item.to, ok: false, error: String(err) });
    }
    await new Promise((r) => setTimeout(r, 1500));
  }
  res.json({ ok: true, results });
});

app.listen(PORT, () => {
  console.log(`[whatsapp-bot] HTTP API listening on http://localhost:${PORT}`);
  console.log('[whatsapp-bot] Waiting for WhatsApp to initialize (QR will print if needed)...');
});
