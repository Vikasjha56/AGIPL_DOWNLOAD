/**
 * WhatsApp Web automation service (whatsapp-web.js based — NOT Twilio).
 *
 * How it works:
 *  - First run: a QR code prints in this terminal. Open WhatsApp on your
 *    phone -> Linked Devices -> Link a Device -> scan it.
 *  - Session is saved to ./.wwebjs_auth, so you only scan once. As long as
 *    this process keeps running (and you don't log out from your phone),
 *    it stays logged in.
 *  - Exposes a simple HTTP API on http://localhost:4000 that the Flask app
 *    calls to send messages. Flask never talks to WhatsApp directly.
 *
 * Run:
 *    cd whatsapp-bot
 *    npm install
 *    node index.js
 *
 * Keep this process running 24x7 (use pm2 / a systemd service / screen /
 * tmux in production) so the 10:30am daily job and the dashboard button
 * both work at any time.
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');

const PORT = process.env.WA_BOT_PORT || 4000;
// Simple shared-secret so random people on your network can't hit /send.
const API_KEY = process.env.WA_BOT_API_KEY || 'change-this-secret';

const app = express();
app.use(express.json());

const client = new Client({
  authStrategy: new LocalAuth({ dataPath: './.wwebjs_auth' }),
  puppeteer: {
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  },
});

let isReady = false;

client.on('qr', (qr) => {
  console.log('\n=== SCAN THIS QR CODE WITH WHATSAPP (Linked Devices) ===\n');
  qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
  isReady = true;
  console.log('[whatsapp-bot] WhatsApp client is READY. Logged in and listening.');
});

client.on('authenticated', () => {
  console.log('[whatsapp-bot] Authenticated. Session saved for next time.');
});

client.on('disconnected', (reason) => {
  isReady = false;
  console.log('[whatsapp-bot] Disconnected:', reason, '- restart this process and re-scan if needed.');
});

client.initialize();

// Turns "9198xxxxxxx" / "+9198xxxxxxx" / "919xxxxxxxxx" into WhatsApp's
// internal chat id format "9198xxxxxxx@c.us"
function toChatId(rawNumber) {
  if (!rawNumber) return null;
  let n = String(rawNumber).replace(/[^\d]/g, ''); // strip spaces, +, -, etc
  if (!n) return null;
  // If someone saved a 10-digit Indian number without country code, assume +91
  if (n.length === 10) n = '91' + n;
  return `${n}@c.us`;
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

// POST /send  { to: "9198xxxxxxx", message: "..." }
app.post('/send', checkApiKey, async (req, res) => {
  if (!isReady) {
    return res.status(503).json({ ok: false, error: 'WhatsApp client not ready yet (scan QR / wait for startup)' });
  }
  const { to, message } = req.body || {};
  const chatId = toChatId(to);
  if (!chatId || !message) {
    return res.status(400).json({ ok: false, error: 'to and message are required' });
  }
  try {
    // Confirm this number actually has WhatsApp before trying to send.
    const isRegistered = await client.isRegisteredUser(chatId);
    if (!isRegistered) {
      return res.status(404).json({ ok: false, error: `${to} is not on WhatsApp` });
    }
    await client.sendMessage(chatId, message);
    console.log(`[whatsapp-bot] Sent to ${chatId}`);
    return res.json({ ok: true, to: chatId });
  } catch (err) {
    console.error('[whatsapp-bot] send failed:', err);
    return res.status(500).json({ ok: false, error: String(err) });
  }
});

// POST /send-bulk  { messages: [{to, message}, ...] }
// Sends one by one with a small delay to avoid looking like spam/getting flagged.
app.post('/send-bulk', checkApiKey, async (req, res) => {
  if (!isReady) {
    return res.status(503).json({ ok: false, error: 'WhatsApp client not ready yet' });
  }
  const { messages } = req.body || {};
  if (!Array.isArray(messages)) {
    return res.status(400).json({ ok: false, error: 'messages must be an array of {to, message}' });
  }

  const results = [];
  for (const item of messages) {
    const chatId = toChatId(item.to);
    if (!chatId || !item.message) {
      results.push({ to: item.to, ok: false, error: 'missing to/message' });
      continue;
    }
    try {
      const isRegistered = await client.isRegisteredUser(chatId);
      if (!isRegistered) {
        results.push({ to: item.to, ok: false, error: 'not on WhatsApp' });
        continue;
      }
      await client.sendMessage(chatId, item.message);
      results.push({ to: item.to, ok: true });
    } catch (err) {
      results.push({ to: item.to, ok: false, error: String(err) });
    }
    // small delay between messages — be gentle, this is an unofficial method
    await new Promise((r) => setTimeout(r, 1500));
  }
  res.json({ ok: true, results });
});

app.listen(PORT, () => {
  console.log(`[whatsapp-bot] HTTP API listening on http://localhost:${PORT}`);
  console.log('[whatsapp-bot] Waiting for WhatsApp to initialize (QR will print if needed)...');
});
