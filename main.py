from vpython import sphere, cylinder, vector, rate
import numpy as np

class Joint:
    def __init__(self, name, position, parent=None):
        self.name = name
        self.position = np.array(position, dtype=float)
        self.parent = parent
        self.children = []
        if parent:
            parent.children.append(self)
        # VPython graphics
        self.sphere = sphere(pos=vector(*self.position), radius=0.1, color=vector(0.2,0.5,1))
        self.cylinder = None
        if parent:
            self.cylinder = cylinder(pos=vector(*parent.position), axis=vector(* (self.position - parent.position)),
                                     radius=0.05, color=vector(0.8,0.2,0.2))
    
    def update_graphics(self):
        self.sphere.pos = vector(*self.position)
        if self.parent and self.cylinder:
            self.cylinder.pos = vector(*self.parent.position)
            self.cylinder.axis = vector(* (self.position - self.parent.position))

class Skeleton:
    def __init__(self):
        self.joints = {}
    
    def add_joint(self, name, position, parent_name=None):
        parent = self.joints.get(parent_name)
        joint = Joint(name, position, parent)
        self.joints[name] = joint
    
    def apply_ai_control(self, ai_output):
        """
        ai_output: dict {joint_name: [dx, dy, dz]}  small position deltas
        """
        for joint_name, delta in ai_output.items():
            if joint_name in self.joints:
                self.joints[joint_name].position += np.array(delta)
    
    def update_graphics(self):
        for joint in self.joints.values():
            joint.update_graphics()

# --- Create Skeleton ---
skeleton = Skeleton()
skeleton.add_joint("root", [0,0,0])
skeleton.add_joint("spine", [0,1,0], "root")
skeleton.add_joint("head", [0,2,0], "spine")
skeleton.add_joint("left_arm", [-1,1.5,0], "spine")
skeleton.add_joint("right_arm", [1,1.5,0], "spine")

# --- Simulation Loop ---
t = 0
while True:
    rate(50)  # 50 FPS
    
    # Example AI control: simple waving motion
    ai_output = {
        "left_arm": [0, 0.05*np.sin(t), 0],
        "right_arm": [0, -0.05*np.sin(t), 0]
    }
    
    skeleton.apply_ai_control(ai_output)
    skeleton.update_graphics()
    t += 0.1