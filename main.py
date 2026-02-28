from vpython import sphere, cylinder, vector, rate, box, scene, keysdown
import numpy as np

# --- Setup Scene & Camera ---
scene = canvas(title='<b>Realistic Dynamic Knee Simulation</b>', width=800, height=600, background=vector(0.1, 0.1, 0.15))
scene.center = vector(0, 1.95, 0) # Lock focus explicitly on the knee joint
scene.camera.pos = vector(2, 2.5, 2) # Initial isometric view
scene.camera.axis = scene.center - scene.camera.pos
scene.autoscale = False # Prevent the camera from jumping around as the leg moves

# On-screen instructions
label(pos=vector(0, 3.8, 0), text="Right-click & drag to rotate.\nScroll to zoom.", box=False, color=vector(0.8,0.8,0.8), opacity=0)

# --- Camera UI Controls ---
def set_view_front(b):
    scene.camera.pos = vector(0, 1.95, 3)
    scene.camera.axis = scene.center - scene.camera.pos

def set_view_side(b):
    scene.camera.pos = vector(3, 1.95, 0)
    scene.camera.axis = scene.center - scene.camera.pos

def set_view_iso(b):
    scene.camera.pos = vector(2, 2.5, 2)
    scene.camera.axis = scene.center - scene.camera.pos

scene.append_to_caption('\n<b>Camera Controls:</b>\n')
button(text='Front View', bind=set_view_front)
button(text='Side View', bind=set_view_side)
button(text='Isometric View', bind=set_view_iso)
scene.append_to_caption('\n\n')

# --- Helper Classes ---
class Bone:
    def __init__(self, start_pos, end_pos, radius, bone_color=vector(0.9, 0.88, 0.8)):
        self.start_pos = vector(*start_pos)
        self.end_pos = vector(*end_pos)
        self.radius = radius
        self.bone_color = bone_color
        
        self.cyl = cylinder(pos=self.start_pos, axis=self.end_pos - self.start_pos, 
                            radius=self.radius, color=self.bone_color)
        self.joint_sphere1 = sphere(pos=self.start_pos, radius=self.radius*1.1, color=self.bone_color)
        self.joint_sphere2 = sphere(pos=self.end_pos, radius=self.radius*1.1, color=self.bone_color)

    def rotate(self, angle, axis, origin):
        for obj in [self.cyl, self.joint_sphere1, self.joint_sphere2]:
            obj.rotate(angle=angle, axis=vector(*axis), origin=vector(*origin))

class DynamicLigament:
    def __init__(self, pos1_func, pos2_func, radius=0.015, color=vector(0.9, 0.9, 0.9)):
        self.pos1_func = pos1_func
        self.pos2_func = pos2_func
        self.cyl = cylinder(radius=radius, color=color, opacity=0.9)
        
    def update(self):
        p1 = self.pos1_func()
        p2 = self.pos2_func()
        self.cyl.pos = p1
        self.cyl.axis = p2 - p1

# --- Anatomy Setup ---
bone_color = vector(0.89, 0.85, 0.78)
cartilage_color = vector(0.6, 0.8, 0.9) 
ligament_color = vector(0.9, 0.9, 0.9)

# Bones
femur = Bone([0, 3.5, 0], [0, 2.0, 0], radius=0.12)
lateral_condyle = sphere(pos=vector(-0.08, 2.0, 0.04), radius=0.1, color=bone_color)
medial_condyle = sphere(pos=vector(0.08, 2.0, 0.04), radius=0.1, color=bone_color)

tibia = Bone([0, 1.95, 0], [0, 0.4, 0], radius=0.1)
fibula = Bone([0.15, 1.85, -0.05], [0.15, 0.35, -0.05], radius=0.06)
patella = sphere(pos=vector(0, 2.0, 0.18), radius=0.08, color=bone_color)

# Meniscus
lateral_meniscus = ring(pos=vector(-0.06, 1.97, 0), axis=vector(0,1,0), radius=0.06, thickness=0.02, color=cartilage_color)
medial_meniscus = ring(pos=vector(0.06, 1.97, 0), axis=vector(0,1,0), radius=0.06, thickness=0.02, color=cartilage_color)

# Kneecap (patella) - sits in front of knee
patella = sphere(pos=vector(0, 2.0, 0.15), radius=0.09, color=vector(0.95, 0.85, 0.7))

# Tibia (shinbone)
skeleton.add_joint("tibia_top", [0, 2.0, 0], "knee_center", radius=0.1, color=vector(0.88, 0.78, 0.58))
skeleton.add_joint("tibia_mid", [0, 1.2, 0], "tibia_top", radius=0.09, color=vector(0.88, 0.78, 0.58))
skeleton.add_joint("ankle", [0, 0.4, 0], "tibia_mid", radius=0.08, color=vector(0.88, 0.78, 0.58))

# Fibula (smaller leg bone, slightly to the side)
skeleton.add_joint("fibula_top", [0.15, 1.95, 0], "knee_center", radius=0.05, color=vector(0.87, 0.77, 0.57))
skeleton.add_joint("fibula_mid", [0.15, 1.1, 0], "fibula_top", radius=0.05, color=vector(0.87, 0.77, 0.57))
skeleton.add_joint("fibula_ankle", [0.15, 0.35, 0], "fibula_mid", radius=0.05, color=vector(0.87, 0.77, 0.57))

# --- Camera Setup ---
scene.width = 1200
scene.height = 800
scene.background = vector(0.2, 0.2, 0.25)
scene.center = vector(0, 1.7, 0)  # Focus on knee
scene.camera.pos = vector(2, 1.7, 2)  # Initial camera position
scene.ambient = vector(0.5, 0.5, 0.5)

# Camera movement variables
camera_speed = 0.05
zoom_speed = 0.1

# --- Simulation Loop ---
t = 0
dt = 0.03
knee_origin = vector(0, 1.95, 0)
current_angle = 0

while True:
    rate(60)  # 60 FPS
    
    # Handle camera movement with keyboard
    keys = keysdown()
    
    # WASD for camera movement in X-Z plane
    if 'w' in keys:  # Move forward (toward knee)
        scene.camera.pos -= (scene.camera.pos - scene.center) * camera_speed
    if 's' in keys:  # Move backward
        scene.camera.pos += (scene.camera.pos - scene.center) * camera_speed
    if 'a' in keys:  # Move left
        move_dir = vector(scene.camera.pos.z - scene.center.z, 0, -(scene.camera.pos.x - scene.center.x))
        scene.camera.pos -= move_dir * camera_speed
    if 'd' in keys:  # Move right
        move_dir = vector(scene.camera.pos.z - scene.center.z, 0, -(scene.camera.pos.x - scene.center.x))
        scene.camera.pos += move_dir * camera_speed
    
    # Arrow keys for camera height
    if 'up' in keys:  # Move up
        scene.camera.pos += vector(0, camera_speed, 0)
    if 'down' in keys:  # Move down
        scene.camera.pos -= vector(0, camera_speed, 0)
    
    # Zoom with +/- keys
    if '+' in keys or '=' in keys:  # Zoom in
        scene.camera.pos -= (scene.camera.pos - scene.center) * zoom_speed
    if '-' in keys or '_' in keys:  # Zoom out
        scene.camera.pos += (scene.camera.pos - scene.center) * zoom_speed
    
    # Q and E to rotate around the knee
    if 'q' in keys:  # Rotate left
        cam_dir = scene.camera.pos - scene.center
        # Calculate distance
        dist = np.sqrt(cam_dir.x**2 + cam_dir.y**2 + cam_dir.z**2)
        # Convert to spherical, rotate around Y axis
        theta = np.arctan2(cam_dir.z, cam_dir.x)
        phi = np.arccos(cam_dir.y / dist) if dist > 0 else 0
        theta += 0.05
        # Convert back
        new_x = dist * np.sin(phi) * np.cos(theta)
        new_y = dist * np.cos(phi)
        new_z = dist * np.sin(phi) * np.sin(theta)
        scene.camera.pos = scene.center + vector(new_x, new_y, new_z)
    
    if 'e' in keys:  # Rotate right
        cam_dir = scene.camera.pos - scene.center
        # Calculate distance
        dist = np.sqrt(cam_dir.x**2 + cam_dir.y**2 + cam_dir.z**2)
        # Convert to spherical, rotate around Y axis
        theta = np.arctan2(cam_dir.z, cam_dir.x)
        phi = np.arccos(cam_dir.y / dist) if dist > 0 else 0
        theta -= 0.05
        # Convert back
        new_x = dist * np.sin(phi) * np.cos(theta)
        new_y = dist * np.cos(phi)
        new_z = dist * np.sin(phi) * np.sin(theta)
        scene.camera.pos = scene.center + vector(new_x, new_y, new_z)
    
    # Realistic knee bending motion (0 to ~120 degrees flexion)
    # Use a smooth sine wave for natural motion
    knee_angle = 0.8 * np.sin(t)  # Radians (about 45 degrees max)
    
    # Reset joint positions to original
    for joint_name, joint in skeleton.joints.items():
        joint.position = np.array(joint.original_position)
    
    # Rotate tibia and fibula around the knee joint
    skeleton.rotate_joint("tibia_top", [1, 0, 0], knee_angle)  # Rotate around X-axis
    skeleton.rotate_joint("fibula_top", [1, 0, 0], knee_angle)
    
    # Update graphics
    patella.pos = vector(0, 2.0 - 0.1 * np.sin(t), 0.15)  # Kneecap moves with knee
    skeleton.update_graphics()
    
    t += 0.05