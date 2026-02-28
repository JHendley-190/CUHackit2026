const http = require('http');
const os = require('os');
const fs = require('fs');
const path = require('path');

let latestNordicData = null;
let previousNordicData = null;
let eventLog = [];
const THRESHOLD = 50;
const THRESHOLD_LOG_FILE = path.join(__dirname, 'threshold-events.log');

function logThresholdEvent(event) {
  const logEntry = JSON.stringify(event) + '\n';
  fs.appendFile(THRESHOLD_LOG_FILE, logEntry, (err) => {
    if (err) console.error('Failed to write threshold event log:', err);
  });
}

function calculateDelta(current, previous) {
  if (!current || !previous) return null;
  const accelCurrent = current.slice(0, 3);
  const accelPrevious = previous.slice(0, 3);
  if (accelCurrent.length !== accelPrevious.length) return null;
  const deltas = accelCurrent.map((val, i) => Math.abs(val - accelPrevious[i]));
  const maxDelta = Math.max(...deltas);
  return { deltas, maxDelta };
}

const server = http.createServer((req, res) => {
  
  // Nordic data storage
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
              if (eventLog.length > 100) eventLog.shift();
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

  // Event log and current data
  if (req.url === '/api/imu-data') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({
      latestReading: latestNordicData,
      threshold: THRESHOLD,
      eventLog: eventLog
    }));
  }

  // Threshold events log file
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

  // Serve logger.html
  if (req.url === '/') {
    const filePath = path.join(__dirname, 'logger.html');
    fs.readFile(filePath, (err, content) => {
      if (err) {
        res.writeHead(500);
        return res.end('Error loading logger.html');
      }
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(content);
    });
    return;
  }

  res.writeHead(404);
  res.end('Not Found');
});

server.listen(3001, () => console.log('Logger Server live: http://127.0.0.1:3001'));
