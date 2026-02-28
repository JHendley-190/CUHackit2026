import numpy as np
import re
import matplotlib.pyplot as plt

# =========================
# IMU PARSER
# =========================

def parse_imu_log(text):
    """
    Parse IMU log lines like:
    IMU: -919 -169 -39 -6213 -1076 68
    Returns numpy array Nx6: ax ay az gx gy gz
    """
    pattern = r"IMU:\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)"
    matches = re.findall(pattern, text)
    data = np.array(matches, dtype=float)

    # Convert to SI units
    # Your accel appears raw ±2048 or ±4096 LSB/g → assume 16384 LSB = 1g (MPU6050)
    accel_scale = 1/16384.0 * 9.81
    gyro_scale  = 1/131.0 * np.pi/180.0

    data[:, 0:3] *= accel_scale     # ax ay az  → m/s²
    data[:, 3:6] *= gyro_scale      # gx gy gz  → rad/s
    return data


# =========================
# COMPLEMENTARY FILTER
# =========================

def complementary_filter(accel, gyro, dt, alpha=0.98):
    """
    accel: Nx3 accelerometer (m/s²)
    gyro : Nx3 gyro (rad/s)
    dt   : timestep
    """
    N = accel.shape[0]
    roll = np.zeros(N)
    pitch = np.zeros(N)

    # initial orientation from accel
    ax, ay, az = accel[0]
    roll[0]  = np.arctan2(ay, az)
    pitch[0] = np.arctan2(-ax, np.sqrt(ay**2 + az**2))

    for i in range(1, N):
        gx, gy, gz = gyro[i]

        # integrate gyro
        roll_gyro  = roll[i-1]  + gx * dt
        pitch_gyro = pitch[i-1] + gy * dt

        # accel estimate
        ax, ay, az = accel[i]
        roll_accel  = np.arctan2(ay, az)
        pitch_accel = np.arctan2(-ax, np.sqrt(ay**2 + az**2))

        # complementary filter
        roll[i]  = alpha*roll_gyro  + (1-alpha)*roll_accel
        pitch[i] = alpha*pitch_gyro + (1-alpha)*pitch_accel

    return roll, pitch


# =========================
# IMPACT / INJURY ESTIMATION
# =========================

def detect_events(accel, gyro):
    """
    Detect:
    - impacts (>20 m/s²)
    - torsional knee load (> 200 deg/s)
    - abrupt valgus/varus patterns
    """
    impacts = np.where(np.linalg.norm(accel, axis=1) > 20)[0]

    # knee torsion load ~ rotation around shin axis → z-axis gyro
    torsion = np.where(np.abs(gyro[:,2]) > np.deg2rad(200))[0]

    # lateral acceleration → side load on knee
    lateral = np.where(np.abs(accel[:,1]) > 8)[0]  # y-axis over 8 m/s²

    return impacts, torsion, lateral


# =========================
# PLOT
# =========================

def plot_results(roll, pitch, impacts, torsion, lateral):
    t = np.arange(len(roll))

    plt.figure(figsize=(12,6))
    plt.plot(t, np.rad2deg(roll), label="Roll (deg)")
    plt.plot(t, np.rad2deg(pitch), label="Pitch (deg)")

    plt.scatter(impacts, np.zeros(len(impacts)), color='red', label="Impacts (>20 m/s²)")
    plt.scatter(torsion, np.zeros(len(torsion)), color='purple', label="High Knee Torsion")
    plt.scatter(lateral, np.zeros(len(lateral)), color='green', label="Lateral Knee Load")

    plt.legend()
    plt.xlabel("Time step")
    plt.ylabel("Degrees")
    plt.title("Snowboarder Leg IMU Orientation & Stress Markers")
    plt.grid()
    plt.show()


# =========================
# MAIN PIPELINE
# =========================

def run_simulation(raw_imu_text):
    imu = parse_imu_log(raw_imu_text)
    accel = imu[:,0:3]
    gyro  = imu[:,3:6]

    dt = 1/100.0  # assume 100 Hz

    roll, pitch = complementary_filter(accel, gyro, dt)

    impacts, torsion, lateral = detect_events(accel, gyro)

    plot_results(roll, pitch, impacts, torsion, lateral)

    print("\n=== EVENT SUMMARY ===")
    print(f"Impacts detected: {len(impacts)}")
    print(f"Knee torsion events: {len(torsion)}")
    print(f"Lateral knee load events: {len(lateral)}")

    return {
        "roll": roll,
        "pitch": pitch,
        "impacts": impacts,
        "torsion": torsion,
        "lateral": lateral
    }
