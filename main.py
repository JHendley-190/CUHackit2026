from vpython import sphere, cylinder, vector, rate, ring, canvas, button, label
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

# Ligaments
acl = DynamicLigament(
    lambda: tibia.joint_sphere1.pos + vector(0, 0.05, 0.05),
    lambda: lateral_condyle.pos + vector(0.05, 0, -0.05)
)
pcl = DynamicLigament(
    lambda: tibia.joint_sphere1.pos + vector(0, 0.05, -0.08),
    lambda: medial_condyle.pos + vector(-0.05, 0, 0.05)
)
mcl = DynamicLigament(
    lambda: medial_condyle.pos + vector(0.08, 0.1, 0),
    lambda: tibia.joint_sphere1.pos + vector(0.1, -0.15, 0)
)
lcl = DynamicLigament(
    lambda: lateral_condyle.pos + vector(-0.08, 0.1, 0),
    lambda: fibula.joint_sphere1.pos + vector(-0.02, 0, 0)
)
patellar_tendon = DynamicLigament(
    lambda: patella.pos + vector(0, -0.08, 0),
    lambda: tibia.joint_sphere1.pos + vector(0, -0.2, 0.12),
    radius=0.025
)
quad_tendon = DynamicLigament(
    lambda: femur.end_pos + vector(0, 0.3, 0.12),
    lambda: patella.pos + vector(0, 0.08, 0),
    radius=0.025
)

ligaments = [acl, pcl, mcl, lcl, patellar_tendon, quad_tendon]

# --- Simulation Loop ---
t = 0
dt = 0.03
knee_origin = vector(0, 1.95, 0)
current_angle = 0

while True:
    rate(60)
    
    target_angle = 0.95 * (np.sin(t) + 1)
    d_angle = target_angle - current_angle
    
    axis_of_rotation = [1, 0, 0]
    tibia.rotate(d_angle, axis_of_rotation, [knee_origin.x, knee_origin.y, knee_origin.z])
    fibula.rotate(d_angle, axis_of_rotation, [knee_origin.x, knee_origin.y, knee_origin.z])
    
    lateral_meniscus.rotate(angle=d_angle, axis=vector(*axis_of_rotation), origin=knee_origin)
    medial_meniscus.rotate(angle=d_angle, axis=vector(*axis_of_rotation), origin=knee_origin)
    
    patella.pos.y = 2.0 - (target_angle * 0.15)
    patella.pos.z = 0.18 - (target_angle * 0.08)
    
    for lig in ligaments:
        lig.update()
        
    current_angle = target_angle
    t += dt