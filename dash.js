const http = require('http');

let latestIMU = null;
let latestGForce = null;

function computeGForce(accelData) {
  if (!accelData || accelData.length < 3) return null;
  const ax = accelData[0] / 16384;
  const ay = accelData[1] / 16384;
  const az = accelData[2] / 16384;
  const gTotal = Math.sqrt(ax * ax + ay * ay + az * az);
  return gTotal.toFixed(3);
}

const server = http.createServer((req, res) => {
  if (req.url === '/imu' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        latestIMU = data.value;
        latestGForce = computeGForce(latestIMU);
        res.writeHead(200);
        res.end('OK');
      } catch (e) {
        res.writeHead(400);
        res.end('Bad JSON');
      }
    });
    return;
  }

  if (req.url === '/' || req.url === '/imu' && req.method === 'GET') {
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
            display: flex; justify-content: center; align-items: center;
            min-height: 100vh; margin: 0;
          }
          .dashboard {
            background: rgba(13, 22, 37, 0.8);
            border-radius: 20px; padding: 2rem 3rem;
            text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.6);
          }
          h1 { color: #0ea5e9; margin-bottom: 1rem; }
          .imu-values { font-family: monospace; margin: 1rem 0; font-size: 1rem; }
          .g-force { font-size: 2rem; color: #4ade80; margin: 1rem 0; }
          button {
            background: #0284c7; border: none; padding: 10px 20px;
            border-radius: 10px; color: #fff; cursor: pointer;
            transition: 0.2s; font-weight: bold;
          }
          button:hover { background: #0369a1; }
        </style>
      </head>
      <body>
        <div class="dashboard">
          <h1>IMU Dashboard</h1>
          <div class="imu-values" id="imu-values">IMU: ${latestIMU ? `[${latestIMU.join(', ')}]` : 'No Data'}</div>
          <div class="g-force" id="g-force">${latestGForce ? `${latestGForce} G` : '0.000 G'}</div>
          <button onclick="update()">Refresh</button>
        </div>
        <script>
          async function update() {
            try {
              const res = await fetch('/imu');
              const data = await res.json();
              document.getElementById('imu-values').innerText = 'IMU: ' + (data.imu ? '[' + data.imu.join(', ') + ']' : 'No Data');
              document.getElementById('g-force').innerText = data.gForce ? data.gForce + ' G' : '0.000 G';
            } catch(e) {
              console.error(e);
            }
          }

          // auto-refresh every 500ms
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
