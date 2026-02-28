const http = require('http');
const os = require('os');
const fs = require('fs'); // New! Used to read files
const path = require('path');

let latestNordicData = null; // store last value from Nordic device

const server = http.createServer((req, res) => {
  
  // ROUTE 1: The API Data (Backend)
  if (req.url === '/api/stats') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    
    const totalMem = os.totalmem();
    const freeMem = os.freemem();
    const usedMem = totalMem - freeMem;
    
    // CPU Load is usually an array of [1min, 5min, 15min] averages. 
    // We'll normalize it roughly to a percentage for the graph.
    const rawLoad = os.loadavg()[0];
    const cpuCores = os.cpus().length;
    const cpuPercent = Math.min(((rawLoad / cpuCores) * 100), 100).toFixed(1);

    const stats = {
      cpuLoad: cpuPercent,
      memPercent: ((usedMem / totalMem) * 100).toFixed(1),
      uptime: os.uptime()
    };
    
    return res.end(JSON.stringify(stats));
  }

  // ROUTE 1b: Nordic data storage
  if (req.url === '/api/nordic') {
    if (req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ value: latestNordicData }));
    } else if (req.method === 'POST') {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', () => {
        try {
          const data = JSON.parse(body);
          latestNordicData = data.value;

          // forward the same payload to the IMU dashboard running on port 4000
          const forwardOptions = {
            hostname: '127.0.0.1',
            port: 4000,
            path: '/imu',
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
          };
          const dashReq = http.request(forwardOptions, dashRes => {
            // ignore response, but you can log statusCode if you want
          });
          dashReq.on('error', err => console.error('dash forward error', err));
          dashReq.write(JSON.stringify({ value: latestNordicData }));
          dashReq.end();

          res.writeHead(200);
          res.end('OK');
        } catch (e) {
          res.writeHead(400);
          res.end('Bad JSON');
        }
      });
      return;
    }
  }

  // ROUTE 2: The Web Page (Frontend)
  if (req.url === '/') {
    // We tell Node to read the index.html file and send it to the browser
    const filePath = path.join(__dirname, 'index.html');
    
    fs.readFile(filePath, (err, content) => {
      if (err) {
        res.writeHead(500);
        return res.end('Error loading index.html');
      }
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(content);
    });
    return;
  }

  res.writeHead(404);
  res.end('Not Found');
});

server.listen(3000, () => console.log('Server live: http://127.0.0.1:3000'));