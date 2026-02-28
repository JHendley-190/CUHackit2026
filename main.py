from vpython import sphere, cylinder, vector, rate, box, scene, keysdown
import numpy as np
import requests   # used to fetch the nordic sensor value from the node server


def get_nordic_value():
    """Return the most recent numeric value pushed from the browser or None on failure."""
    try:
        resp = requests.get('http://127.0.0.1:3000/api/nordic', timeout=0.05)
        return resp.json().get('value', None)
    except Exception:
        return None


class Joint:
    def __init__(self, name, position, parent=None, radius=0.08, color=None, size=None):
        self.name = name
        self.position = np.array(position, dtype=float)
        self.parent = parent
        self.children = []
        self.original_position = np.array(position, dtype=float)
        if parent:
            parent.children.append(self)
        
        # Default colors for different bone types
        if color is None:
            color = vector(0.8, 0.7, 0.5)  # Bone color
        
        # VPython graphics
        self.sphere = sphere(pos=vector(*self.position), radius=radius, color=color)
        self.cylinder = None
        self.cylinder_color = vector(0.75, 0.65, 0.4)  # Slightly darker bone
        if parent:
            self._create_cylinder()
    
    def _create_cylinder(self):
        if self.parent:
            direction = self.position - self.parent.position
            length = np.linalg.norm(direction)
            if length > 0:
                self.cylinder = cylinder(
                    pos=vector(*self.parent.position),
                    axis=vector(*direction),
                    radius=0.06,
                    color=self.cylinder_color
                )
    
    def update_graphics(self):
        self.sphere.pos = vector(*self.position)
        if self.parent and self.cylinder:
            direction = self.position - self.parent.position
            self.cylinder.pos = vector(*self.parent.position)
            self.cylinder.axis = vector(*direction)

class Skeleton:
    def __init__(self):
        self.joints = {}
        self.children_by_parent = {}
    
    def add_joint(self, name, position, parent_name=None, radius=0.08, color=None):
        parent = self.joints.get(parent_name)
        joint = Joint(name, position, parent, radius=radius, color=color)
        self.joints[name] = joint
        
        if parent_name not in self.children_by_parent:
            self.children_by_parent[parent_name] = []
        self.children_by_parent[parent_name] = self.children_by_parent.get(parent_name, []) + [name]
    
    def rotate_joint(self, joint_name, axis, angle):
        """Rotate a joint and its children around an axis"""
        if joint_name not in self.joints:
            return
        
        joint = self.joints[joint_name]
        if not joint.parent:
            return
        
        # Get rotation matrix
        axis = np.array(axis)
        axis = axis / np.linalg.norm(axis)
        
        # Rodrigues rotation formula
        K = np.array([
            [0, -axis[2], axis[1]],
            [axis[2], 0, -axis[0]],
            [-axis[1], axis[0], 0]
        ])
        R = np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * (K @ K)
        
        # Rotate position relative to parent
        relative_pos = joint.original_position - joint.parent.original_position
        rotated_pos = joint.parent.position + R @ relative_pos
        joint.position = rotated_pos
        
        # Rotate children recursively
        for child_name in self.children_by_parent.get(joint_name, []):
            self._rotate_children(child_name, joint, R, joint.original_position)
    
    def _rotate_children(self, joint_name, parent_joint, rotation_matrix, pivot_point):
        """Recursively rotate children around a pivot point"""
        if joint_name not in self.joints:
            return
        
        child = self.joints[joint_name]
        relative_pos = child.original_position - pivot_point
        rotated_offset = rotation_matrix @ relative_pos
        child.position = parent_joint.position + rotated_offset
        
        for grandchild_name in self.children_by_parent.get(joint_name, []):
            self._rotate_children(grandchild_name, child, rotation_matrix, pivot_point)
    
    def update_graphics(self):
        for joint in self.joints.values():
            joint.update_graphics()

# --- Create a Detailed Knee Structure ---
skeleton = Skeleton()

# Femur (thighbone)
skeleton.add_joint("femur_top", [0, 3.5, 0], radius=0.12, color=vector(0.9, 0.8, 0.6))
skeleton.add_joint("femur_mid", [0, 2.8, 0], "femur_top", radius=0.11, color=vector(0.9, 0.8, 0.6))
skeleton.add_joint("knee_center", [0, 2.0, 0], "femur_mid", radius=0.13, color=vector(0.85, 0.75, 0.5))

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
knee_angle = 0
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
    
    # ----------------------------------------------------------------------------------
    # obtain latest sensor reading and convert to an angle
    sensor_val = get_nordic_value()
    if sensor_val is not None:
        # assume sensor provides 0..1023, map to roughly -0.8..0.8 radians
        knee_angle = (sensor_val / 1023.0) * 1.6 - 0.8
    else:
        # fallback to automatic sine motion when no data is available
        knee_angle = 0.8 * np.sin(t)
    
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