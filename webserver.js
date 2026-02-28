const http = require('http');
const os = require('os');
const fs = require('fs'); // New! Used to read files
const path = require('path');

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