from vpython import *
import math

# -------------------------------------------------------
#                  IMU DATA PARSER
# -------------------------------------------------------
def parse_imu_line(line):
    """
    Parse lines of the format:
    IMU: ax ay az gx gy gz
    Returns floats.
    """
    try:
        parts = line.strip().split()
        ax = float(parts[1])
        ay = float(parts[2])
        az = float(parts[3])
        gx = float(parts[4])
        gy = float(parts[5])
        gz = float(parts[6])
        return ax, ay, az, gx, gy, gz
    except:
        return None


# -------------------------------------------------------
#     COMPLEMENTARY FILTER ORIENTATION ESTIMATOR
# -------------------------------------------------------
def complementary_filter(ax, ay, az, gx, gy, gz, dt,
                         prev_roll, prev_pitch, alpha=0.98):
    # Gyroscope integration
    roll_gyro  = prev_roll  + gx * dt
    pitch_gyro = prev_pitch + gy * dt

    # Accelerometer tilt estimate
    roll_acc  = math.atan2(ay, az)
    pitch_acc = math.atan2(-ax, math.sqrt(ay**2 + az**2))

    # Complementary filter
    roll  = alpha*roll_gyro  + (1-alpha)*roll_acc
    pitch = alpha*pitch_gyro + (1-alpha)*pitch_acc

    return roll, pitch


# -------------------------------------------------------
#        VPYTHON SCENE + SNOWBOARDER OBJECTS
# -------------------------------------------------------
scene = canvas(title="Snowboarder IMU Simulation",
               width=1000, height=700,
               center=vector(0,1,0), background=color.cyan)

ground = box(pos=vector(0,-0.1,0), size=vector(20,0.1,20), color=color.white)

# The snowboard
board = box(pos=vector(0,0,0), size=vector(2.0,0.05,0.4), color=color.red)

# The rider
rider = cylinder(pos=vector(0,0.5,0), axis=vector(0,1,0),
                 radius=0.15, color=color.blue)


# -------------------------------------------------------
#                SIMULATION LOOP
# -------------------------------------------------------
roll = 0.0
pitch = 0.0
yaw = 0.0

# Fake IMU file (YOU WILL REPLACE THIS WITH YOUR DATA)
imu_lines = []
with open("imu_data.txt", "r") as f:
    imu_lines = f.readlines()

dt = 0.01  # time step

for line in imu_lines:
    rate(dt)

    imu = parse_imu_line(line)
    if imu is None:
        continue

    ax, ay, az, gx, gy, gz = imu

    # Convert gyro raw units → rad/s (assuming deg/s)
    gx = math.radians(gx)
    gy = math.radians(gy)
    gz = math.radians(gz)

    # Update roll & pitch
    roll, pitch = complementary_filter(ax, ay, az, gx, gy, gz, dt,
                                       roll, pitch)

    # Integrate yaw separately
    yaw += gz * dt

    # ----------------------------
    # Apply to the snowboard
    # ----------------------------
    # Create a rotation matrix from roll, pitch, yaw
    c1 = math.cos(yaw)
    s1 = math.sin(yaw)
    c2 = math.cos(pitch)
    s2 = math.sin(pitch)
    c3 = math.cos(roll)
    s3 = math.sin(roll)

    # Direction vectors
    forward = vector(c1*c2, s2, s1*c2)
    right    = vector(c1*s2*s3 - s1*c3, -c2*s3, s1*s2*s3 + c1*c3)
    up       = vector(c1*s2*c3 + s1*s3, -c2*c3, s1*s2*c3 - c1*s3)

    # Update object's orientation
    board.axis = forward
    board.up = up

    rider.pos = board.pos + vector(0,0.5,0)
    rider.axis = up
