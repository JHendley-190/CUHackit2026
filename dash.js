const http = require('http');

let latestIMU = null;
let latestGForce = null;
let crashLog = []; // Store crash events (timestamp only)
let crashActive = false; // Track if currently in crash state

function computeGForce(accelData) {
  if (!accelData || accelData.length < 3) return null;

  const ax = accelData[0] / 16384;
  const ay = accelData[1] / 16384;
  const az = accelData[2] / 16384;

  let gTotal = Math.sqrt(ax*ax + ay*ay + az*az);

  const baseG = 0.056;
  const step = 0.02;
  const multiplier = 2.5;

  if (gTotal <= baseG) {
    gTotal = 1;
  } else {
    const stepsAbove = (gTotal - baseG) / step;
    gTotal = Math.pow(multiplier, stepsAbove);
  }

  return gTotal;
}

const server = http.createServer((req, res) => {
  // POST IMU data
  if (req.url === '/imu' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        latestIMU = data.value;
        latestGForce = computeGForce(latestIMU);
        console.log('dash received', latestIMU, '→', latestGForce.toFixed(3));

        // Only log crash when G > 5 and not already in crash
        if (latestGForce > 5 && !crashActive) {
          const timestamp = new Date().toLocaleString();
          crashLog.push({ timestamp });
          crashActive = true;
        } else if (latestGForce <= 5) {
          crashActive = false; // Reset crash state
        }

        res.writeHead(200);
        res.end('OK');
      } catch (e) {
        res.writeHead(400);
        res.end('Bad JSON');
      }
    });
    return;
  }

  // GET IMU data including crash log
  if (req.url === '/imu' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ 
      imu: latestIMU, 
      gForce: latestGForce ? latestGForce.toFixed(3) : null,
      crashLog
    }));
  }

  // Dashboard HTML
  if (req.url === '/' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(`
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IMU Dashboard</title>
<style>
  body {
    background-color: #050b14;
    color: #f8fafc;
    font-family: 'Segoe UI', sans-serif;
    display: flex; justify-content: center; align-items: flex-start;
    min-height: 100vh; margin: 0; padding: 2rem;
  }
  .dashboard {
    background: rgba(13, 22, 37, 0.8);
    border-radius: 20px; padding: 2rem 3rem;
    text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.6);
    width: 350px;
    margin-right: 2rem;
  }
  h1 { color: #0ea5e9; margin-bottom: 1rem; }
  .imu-values { font-family: monospace; margin: 0.5rem 0; font-size: 1rem; }
  .g-force { font-size: 2rem; margin: 1rem 0; transition: color 0.3s ease; }
  .warning { color: #f87171; font-size: 1.5rem; font-weight: bold; margin-top: 1rem; animation: blink 1s infinite; }
  @keyframes blink { 0%, 50%, 100% { opacity: 1; } 25%, 75% { opacity: 0; } }
  .imu-bars { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem; margin-top: 1rem; font-family: monospace; font-size: 0.95rem; }
  .imu-bars div { background: rgba(0, 255, 150, 0.1); border-left: 5px solid #4ade80; padding: 5px 10px; border-radius: 5px; transition: all 0.2s ease; }
  .log-panel { background: rgba(0,0,0,0.6); border-radius: 15px; padding: 1rem; width: 300px; max-height: 500px; overflow-y: auto; font-family: monospace; }
  .log-panel h2 { margin-top: 0; color: #f87171; }
  .log-item { margin-bottom: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.3rem; }
  button { background: #0284c7; border: none; padding: 10px 20px; border-radius: 10px; color: #fff; cursor: pointer; transition: 0.2s; font-weight: bold; margin-top: 1rem; }
  button:hover { background: #0369a1; }
</style>
</head>
<body>
<div class="dashboard">
  <h1>IMU Dashboard</h1>
  <div class="imu-values" id="imu-values">IMU: ${latestIMU ? `[${latestIMU.join(', ')}]` : 'No Data'}</div>
  <div class="g-force" id="g-force">${latestGForce ? `${latestGForce.toFixed(3)} G` : '0.000 G'}</div>
  <div class="warning" id="warning" style="display:none;">!Crash Detected</div>
  <div class="imu-bars">
    <div>Accel X: <span id="accel-x">0</span></div>
    <div>Accel Y: <span id="accel-y">0</span></div>
    <div>Accel Z: <span id="accel-z">0</span></div>
    <div>Gyro X: <span id="gyro-x">0</span></div>
    <div>Gyro Y: <span id="gyro-y">0</span></div>
    <div>Gyro Z: <span id="gyro-z">0</span></div>
  </div>
  <button onclick="update()">Refresh</button>
</div>

<div class="log-panel">
  <h2>Crash Log</h2>
  <div id="crash-log">
    <!-- Crash events appear here -->
  </div>
</div>

<script>
async function update() {
  try {
    const res = await fetch('/imu');
    const data = await res.json();
    const imu = data.imu || [0,0,0,0,0,0];
    const gForce = parseFloat(data.gForce) || 0;
    const crashLog = data.crashLog || [];

    document.getElementById('imu-values').innerText = 'IMU: [' + imu.join(', ') + ']';
    const gEl = document.getElementById('g-force');
    gEl.innerText = gForce.toFixed(3) + ' G';

    if (gForce > 5) {
      gEl.style.color = '#f87171';
      document.getElementById('warning').style.display = 'block';
    } else {
      gEl.style.color = '#4ade80';
      document.getElementById('warning').style.display = 'none';
    }

    document.getElementById('accel-x').innerText = (imu[0]/16384).toFixed(3);
    document.getElementById('accel-y').innerText = (imu[1]/16384).toFixed(3);
    document.getElementById('accel-z').innerText = (imu[2]/16384).toFixed(3);
    document.getElementById('gyro-x').innerText = imu[3];
    document.getElementById('gyro-y').innerText = imu[4];
    document.getElementById('gyro-z').innerText = imu[5];

    const logEl = document.getElementById('crash-log');
    logEl.innerHTML = '';
    crashLog.slice(-10).reverse().forEach(item => {
      const div = document.createElement('div');
      div.className = 'log-item';
      div.innerText = item.timestamp;
      logEl.appendChild(div);
    });

  } catch(e) {
    console.error(e);
  }
}

setInterval(update, 500);
</script>
</body>
</html>
    `);
    return;
  }

  res.writeHead(404);
  res.end('Not Found');
});

server.listen(4000, () => console.log('IMU Dashboard running at http://127.0.0.1:4000'));