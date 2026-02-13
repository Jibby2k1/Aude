const http = require('http');
const fs = require('fs');
const path = require('path');
const net = require('net');
const { WebSocketServer } = require('ws');

const HTTP_PORT = 8080;
const TRACK_PORT = 9000;
const POT_PORT = 9001;

// ─── HTTP Server (serves the UI) ────────────────────────────────────
const httpServer = http.createServer((req, res) => {
  let filePath = req.url === '/' ? '/index.html' : req.url;
  filePath = path.join(__dirname, 'public', filePath);

  const ext = path.extname(filePath);
  const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css' };

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404);
      res.end('Not found');
      return;
    }
    res.writeHead(200, { 'Content-Type': types[ext] || 'text/plain' });
    res.end(data);
  });
});

// ─── WebSocket Server (pushes data to browser) ─────────────────────
const wss = new WebSocketServer({ server: httpServer });
const wsClients = new Set();

wss.on('connection', (ws) => {
  console.log('[WS] Browser connected');
  wsClients.add(ws);
  ws.on('close', () => {
    wsClients.delete(ws);
    console.log('[WS] Browser disconnected');
  });
});

function broadcast(type, data) {
  const msg = JSON.stringify({ type, data });
  for (const ws of wsClients) {
    if (ws.readyState === 1) ws.send(msg);
  }
}

// ─── ODAS JSON Stream Parser ────────────────────────────────────────
function createOdasParser(label, onFrame) {
  let remaining = '';

  return function onData(d) {
    const stream = remaining + d.toString('utf8');
    const parts = stream.split('}\n{');

    if (parts.length < 2) {
      remaining = stream;
      return;
    }

    for (let i = 0; i < parts.length; i++) {
      if (i === parts.length - 1) {
        remaining = parts[i];
        break;
      }

      let str = parts[i];
      if (str.charAt(0) !== '{') str = '{' + str;
      // Add closing brace if needed
      str = str.trimEnd();
      if (!str.endsWith('}')) str += '}';

      try {
        const frame = JSON.parse(str);
        onFrame(frame);
      } catch (e) {
        // skip malformed frame
      }
    }
  };
}

// ─── TCP Server for Tracking (SST) ─────────────────────────────────
const trackServer = net.createServer((conn) => {
  const addr = conn.remoteAddress + ':' + conn.remotePort;
  console.log(`[TRACK] Connected: ${addr}`);
  broadcast('status', { tracking: true });

  conn.on('data', createOdasParser('TRACK', (frame) => {
    broadcast('tracking', frame);
  }));

  conn.on('close', () => {
    console.log(`[TRACK] Disconnected: ${addr}`);
    broadcast('status', { tracking: false });
  });

  conn.on('error', (err) => console.log(`[TRACK] Error: ${err.message}`));
});

// ─── TCP Server for Potential Sources (SSL) ─────────────────────────
const potServer = net.createServer((conn) => {
  const addr = conn.remoteAddress + ':' + conn.remotePort;
  console.log(`[POT] Connected: ${addr}`);
  broadcast('status', { potential: true });

  conn.on('data', createOdasParser('POT', (frame) => {
    broadcast('potential', frame);
  }));

  conn.on('close', () => {
    console.log(`[POT] Disconnected: ${addr}`);
    broadcast('status', { potential: false });
  });

  conn.on('error', (err) => console.log(`[POT] Error: ${err.message}`));
});

// ─── Start everything ───────────────────────────────────────────────
trackServer.listen(TRACK_PORT, () => console.log(`[TRACK] Listening on port ${TRACK_PORT}`));
potServer.listen(POT_PORT, () => console.log(`[POT]   Listening on port ${POT_PORT}`));
httpServer.listen(HTTP_PORT, () => {
  console.log(`\n  ODAS Visualizer running at http://localhost:${HTTP_PORT}\n`);
  console.log(`  Waiting for ODAS to connect...`);
  console.log(`    - Tracking (SST) on port ${TRACK_PORT}`);
  console.log(`    - Potential (SSL) on port ${POT_PORT}\n`);
});
