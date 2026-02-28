"""
Ball Crash Visualizer
---------------------
Reads 3-axis accelerometer data from a Nordic sensor via a local Node server
(GET http://127.0.0.1:3000/api/nordic) and drives a ball around a 3-D box.

Expected sensor payload (JSON):
    { "value": [ax, ay, az] }          <-- 3-element list, raw 0-1023 each axis
    { "value": ax }                    <-- single value  (only X used)

Crash detection: when the magnitude of the acceleration vector crosses a
configurable threshold a bright red flash + "CRASH!" label is triggered.

Camera: orbit with Q/E, zoom +/-, height Up/Down arrow keys.
"""

from vpython import (
    sphere, box, vector, rate, scene, keysdown,
    label, cylinder, color, mag, norm
)
import numpy as np
import requests

# ── Configuration ──────────────────────────────────────────────────────────────
NODE_URL          = "http://127.0.0.1:3000/api/nordic"
FETCH_TIMEOUT     = 0.08          # seconds

RAW_MIN, RAW_MAX  = 0, 1023       # raw ADC range from sensor
ACCEL_SCALE       = 2.0           # ±g full-scale (adjust to match your IMU)

CRASH_G_THRESHOLD = 2.5           # g   — spike above this fires crash
CRASH_LINGER      = 60            # frames crash overlay stays visible

BOX_HALF          = 2.0           # half-size of the bounding box (metres)
BALL_RADIUS       = 0.18
DAMPING           = 0.85          # velocity multiplied on bounce
GRAVITY           = vector(0, -0.04, 0)   # small gravity to keep it grounded-ish

FPS               = 60
CAMERA_SPEED      = 0.05
ZOOM_SPEED        = 0.1
# ───────────────────────────────────────────────────────────────────────────────


def get_accel():
    """Return (ax, ay, az) in g, or None on failure."""
    try:
        resp = requests.get(NODE_URL, timeout=FETCH_TIMEOUT)
        val  = resp.json().get("value", None)
    except Exception:
        return None

    def raw_to_g(raw):
        """Map 0-1023 → -ACCEL_SCALE .. +ACCEL_SCALE."""
        return (float(raw) / RAW_MAX * 2 - 1.0) * ACCEL_SCALE

    if isinstance(val, list) and len(val) >= 3:
        return raw_to_g(val[0]), raw_to_g(val[1]), raw_to_g(val[2])
    elif isinstance(val, (int, float)):
        return raw_to_g(val), 0.0, 0.0
    return None


# ── Scene ──────────────────────────────────────────────────────────────────────
scene.title      = "Ball Crash Visualizer"
scene.width      = 1280
scene.height     = 720
scene.background = vector(0.05, 0.05, 0.08)
scene.center     = vector(0, 0, 0)
scene.camera.pos = vector(4, 3, 6)

# Transparent bounding box (wireframe via 12 edges)
B = BOX_HALF
EDGE_R  = 0.025
EDGE_COL = vector(0.3, 0.6, 1.0)

def make_edges():
    corners = [vector(sx*B, sy*B, sz*B)
               for sx in (-1,1) for sy in (-1,1) for sz in (-1,1)]
    edges_drawn = set()
    for i, a in enumerate(corners):
        for j, b in enumerate(corners):
            diff = [abs(a.x-b.x)>0, abs(a.y-b.y)>0, abs(a.z-b.z)>0]
            if sum(diff) == 1 and (j,i) not in edges_drawn:
                edges_drawn.add((i,j))
                axis = b - a
                cylinder(pos=a, axis=axis, radius=EDGE_R, color=EDGE_COL)

make_edges()

# Ball
ball = sphere(
    pos=vector(0, 0, 0),
    radius=BALL_RADIUS,
    color=vector(0.2, 0.8, 1.0),
    emissive=True
)

# Crash overlay label (hidden initially)
crash_label = label(
    pos=vector(0, 0, 0),
    text="",
    height=40,
    color=color.red,
    opacity=0,
    box=False,
    line=False
)

# HUD: live G reading
g_label = label(
    pos=vector(-BOX_HALF, BOX_HALF + 0.4, 0),
    text="G: 0.00",
    height=14,
    color=vector(0.6, 1.0, 0.6),
    opacity=0,
    box=False,
    line=False,
    align="left"
)

sensor_status = label(
    pos=vector(-BOX_HALF, BOX_HALF + 0.8, 0),
    text="NO SENSOR — sine fallback",
    height=12,
    color=vector(1, 0.6, 0.2),
    opacity=0,
    box=False,
    line=False,
    align="left"
)

# ── Physics state ──────────────────────────────────────────────────────────────
velocity      = vector(0.04, 0.07, 0.05)   # initial nudge
crash_counter = 0                           # frames remaining for crash overlay
t             = 0.0                         # time for fallback sine

# ── Main loop ──────────────────────────────────────────────────────────────────
while True:
    rate(FPS)
    t += 1.0 / FPS

    # ── Sensor read ────────────────────────────────────────────────────────────
    accel = get_accel()

    if accel is not None:
        ax, ay, az = accel
        sensor_status.text = "SENSOR LIVE"
        sensor_status.color = vector(0.2, 1.0, 0.4)
        g_mag = np.sqrt(ax**2 + ay**2 + az**2)
    else:
        # Sine-wave fallback — simulates gentle motion + one crash every 8 s
        freq  = 0.4
        ax    = ACCEL_SCALE * 0.3 * np.sin(2 * np.pi * freq * t)
        ay    = ACCEL_SCALE * 0.2 * np.cos(2 * np.pi * freq * 1.3 * t)
        az    = ACCEL_SCALE * 0.25 * np.sin(2 * np.pi * freq * 0.7 * t + 1)
        # Inject a spike every 8 s for demo
        spike = 4.0 if int(t) % 8 == 0 and t % 1 < 0.08 else 0
        ax   += spike
        g_mag = np.sqrt(ax**2 + ay**2 + az**2)
        sensor_status.text = "NO SENSOR — sine fallback"
        sensor_status.color = vector(1, 0.6, 0.2)

    g_label.text = f"G: {g_mag:.2f}"

    # ── Crash detection ────────────────────────────────────────────────────────
    if g_mag >= CRASH_G_THRESHOLD:
        crash_counter = CRASH_LINGER
        # Flash the ball red
        ball.color = color.red
        # Make ball jump proportional to the spike
        impulse_scale = min(g_mag / CRASH_G_THRESHOLD, 5.0) * 0.12
        velocity += vector(ax, ay, az) * impulse_scale

    if crash_counter > 0:
        crash_counter -= 1
        alpha = crash_counter / CRASH_LINGER
        crash_label.text    = f"CRASH!  {g_mag:.1f} G"
        crash_label.opacity = alpha
        crash_label.height  = int(30 + 20 * alpha)
        if crash_counter == 0:
            crash_label.text = ""
            ball.color       = vector(0.2, 0.8, 1.0)
    else:
        # Tint ball by current G level (blue → orange)
        t_col = min(g_mag / CRASH_G_THRESHOLD, 1.0)
        ball.color = vector(0.2 + 0.8*t_col, 0.8 - 0.5*t_col, 1.0 - 0.8*t_col)

    # ── Physics: apply acceleration + gravity ──────────────────────────────────
    dt           = 1.0 / FPS
    force        = vector(ax, ay, az) * 0.004   # scale to scene units
    velocity    += force + GRAVITY * dt

    ball.pos    += velocity

    # Bounce off box walls
    for attr, vattr in [("x","x"), ("y","y"), ("z","z")]:
        p = getattr(ball.pos, attr)
        v = getattr(velocity,  vattr)
        lim = BOX_HALF - BALL_RADIUS
        if p >  lim:
            setattr(ball.pos, attr,  lim)
            setattr(velocity,  vattr, -abs(v) * DAMPING)
        elif p < -lim:
            setattr(ball.pos, attr, -lim)
            setattr(velocity,  vattr,  abs(v) * DAMPING)

    # ── Camera controls ────────────────────────────────────────────────────────
    keys = keysdown()
    cam_dir = scene.camera.pos - scene.center
    dist = mag(cam_dir)

    if 'w' in keys:
        scene.camera.pos -= cam_dir * CAMERA_SPEED
    if 's' in keys:
        scene.camera.pos += cam_dir * CAMERA_SPEED
    if 'up' in keys:
        scene.camera.pos += vector(0, CAMERA_SPEED * dist, 0)
    if 'down' in keys:
        scene.camera.pos -= vector(0, CAMERA_SPEED * dist, 0)
    if '+' in keys or '=' in keys:
        scene.camera.pos -= cam_dir * ZOOM_SPEED
    if '-' in keys or '_' in keys:
        scene.camera.pos += cam_dir * ZOOM_SPEED

    for key, delta_theta in [('q', 0.05), ('e', -0.05)]:
        if key in keys:
            cd = scene.camera.pos - scene.center
            d2 = np.sqrt(cd.x**2 + cd.z**2)   # horizontal distance
            theta = np.arctan2(cd.z, cd.x) + delta_theta
            phi   = np.arctan2(cd.y, d2)
            r     = dist
            scene.camera.pos = scene.center + vector(
                r * np.cos(phi) * np.cos(theta),
                r * np.sin(phi),
                r * np.cos(phi) * np.sin(theta)
            )
