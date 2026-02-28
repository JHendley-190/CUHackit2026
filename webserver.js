const http = require('http');
const os = require('os');
const fs = require('fs'); // New! Used to read files
const path = require('path');

let latestNordicData = null; // store last value from Nordic device
let previousNordicData = null; // track previous reading for delta calculation
let eventLog = []; // log of threshold-exceeded events
const THRESHOLD = 50; // change threshold per axis
const THRESHOLD_LOG_FILE = path.join(__dirname, 'threshold-events.log');

// Function to log threshold event to file
function logThresholdEvent(event) {
  const logEntry = JSON.stringify(event) + '\n';
  fs.appendFile(THRESHOLD_LOG_FILE, logEntry, (err) => {
    if (err) console.error('Failed to write threshold event log:', err);
  });
}

// Helper function to calculate magnitude of change (accelerometer only - first 3 values)
function calculateDelta(current, previous) {
  if (!current || !previous) {
    return null;
  }
  // Only use accelerometer data (first 3 values: AX, AY, AZ)
  const accelCurrent = current.slice(0, 3);
  const accelPrevious = previous.slice(0, 3);
  
  if (accelCurrent.length !== accelPrevious.length) {
    return null;
  }
  const deltas = accelCurrent.map((val, i) => Math.abs(val - accelPrevious[i]));
  const maxDelta = Math.max(...deltas);
  return { deltas, maxDelta };
}

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
          const newValue = data.value;
          
          // Calculate delta if we have previous data
          if (previousNordicData && Array.isArray(newValue) && Array.isArray(previousNordicData)) {
            const deltaInfo = calculateDelta(newValue, previousNordicData);
            if (deltaInfo && deltaInfo.maxDelta > THRESHOLD) {
              const event = {
                timestamp: new Date().toISOString(),
                previousValue: previousNordicData,
                currentValue: newValue,
                deltas: deltaInfo.deltas,
                maxDelta: deltaInfo.maxDelta
              };
              eventLog.push(event);
              // Keep only last 100 events in memory
              if (eventLog.length > 100) eventLog.shift();
              // Also log to file for persistent record
              logThresholdEvent(event);
            }
          }
          
          previousNordicData = newValue;
          latestNordicData = newValue;
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

  // ROUTE 1c: Event log and current data
  if (req.url === '/api/imu-data') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({
      latestReading: latestNordicData,
      threshold: THRESHOLD,
      eventLog: eventLog
    }));
  }

  // ROUTE 1d: Threshold events log file
  if (req.url === '/api/threshold-events') {
    fs.readFile(THRESHOLD_LOG_FILE, 'utf8', (err, data) => {
      if (err) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ events: [] }));
      }
      const lines = data.trim().split('\n').filter(line => line.length > 0);
      const events = lines.map(line => {
        try {
          return JSON.parse(line);
        } catch (e) {
          return null;
        }
      }).filter(e => e !== null);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ events: events }));
    });
    return;
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