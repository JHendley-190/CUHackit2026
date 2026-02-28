# CUHackit2026
Repository for Clemson University Hackathon 2026
Team: Jack Hendley, Michael Rosol, Gabriel Attar, Sara Castello

JoinTrack is a product that uses a gyroscope and accelrometer to determine any knee injury and strain

---

## Running the servers

Two Node servers are used:

* `webserver.js` – serves the frontend on port **3000** and proxies Nordic POSTs
* `logger.js` – collects IMU data and serves `/api/imu-data` (default port **3001**)

If you need to run the logger on a different port (to avoid conflicts or run multiple
instances), set the `LOGGER_PORT` environment variable before starting both
servers. The proxy in `webserver.js` will automatically use the same port. (The
logger server file is now `logger.js`.)

### Examples (Windows PowerShell)

```powershell
# run logger on 3002 and webserver normally
$env:LOGGER_PORT=3002; node .\logger.js
node .\webserver.js
```

Or using `cmd.exe`:

```bat
set LOGGER_PORT=3002
node logger.js
node webserver.js
```

The frontend (`index.html`/`logger.html`) doesn’t need any changes – it only talks
to the webserver on port 3000.

---