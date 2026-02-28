from vpython import sphere, vector, rate, scene
import requests
import numpy as np

# -------------------------
# Fetch accelerometer data
# -------------------------
def get_accelerometer_value():
    """Return latest accelerometer [ax, ay, az] or None."""
    try:
        resp = requests.get('http://127.0.0.1:3000/api/nordic', timeout=0.1)
        val = resp.json().get('value', None)
        if isinstance(val, list) and len(val) >= 3:
            return val[:3]
        return None
    except Exception:
        return None

# -------------------------
# Scene setup
# -------------------------
scene.width = 1000
scene.height = 600
scene.background = vector(0.2, 0.2, 0.25)
scene.center = vector(0, 0, 0)
scene.camera.pos = vector(5, 5, 5)

# Sphere representing snowboarder
ball = sphere(pos=vector(0, 0, 0), radius=0.2, color=vector(0.9, 0.2, 0.2))

# -------------------------
# Simulation variables
# -------------------------
vel = np.array([0.0, 0.0, 0.0])
pos = np.array([0.0, 0.0, 0.0])
dt = 0.05
scale = 0.2  # acceleration scaling factor

# -------------------------
# Main loop
# -------------------------
t = 0
while True:
    rate(60)

    # Get accelerometer
    accel = get_accelerometer_value()
    if accel is not None:
        ax, ay, az = accel
        a_vec = np.array([ax, ay, az]) * scale
    else:
        # fallback: small oscillation if no data
        a_vec = np.array([0.5 * np.sin(t), 0, 0])

    # Integrate acceleration to velocity, then velocity to position
    vel += a_vec * dt
    pos += vel * dt

    # Optional: simple friction / damping for realism
    vel *= 0.95

    # Update ball position
    ball.pos = vector(*pos)

    t += dt
