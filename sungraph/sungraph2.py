# sungraph.py
import numpy as np
from vispy import app, scene, color
from vispy.visuals import transforms

# --- setup window and view ---
canvas = scene.SceneCanvas(
    title='Sun Arc Viewer',
    keys='interactive',
    bgcolor='black',
    size=(1000, 800),
    show=True
)

view = canvas.central_widget.add_view()
view.camera = scene.cameras.TurntableCamera(
    fov=70, azimuth=180, elevation=25, distance=6
)
view.camera.up = '+y'

# --- ground plane ---
plane = scene.visuals.Plane(width=12, height=12, color=(0.15, 0.15, 0.15, 1))
plane.transform = transforms.STTransform(translate=(0, -1.2, 0))
view.add(plane)

# --- fake sun path ---
# east (-x) → west (+x) arc, facing south
t = np.linspace(0, np.pi, 300)
x = np.sin(t) * 4      # east to west
y = np.sin(t) * 2.2    # altitude
z = np.cos(t) * 1.5    # slight curvature toward/away

# dotted orbit under view
def make_dotted_line(x, y, z, step=6):
    X, Y, Z = [], [], []
    for i in range(0, len(x) - step, step * 2):
        X.extend(x[i:i+step])
        Y.extend(y[i:i+step])
        Z.extend(z[i:i+step])
        X.append(np.nan)
        Y.append(np.nan)
        Z.append(np.nan)
    return np.c_[X, np.array(Y) - 0.05, Z]

dotted_path = make_dotted_line(x, y, z)
sun_path = scene.visuals.Line(pos=dotted_path, color='darkorange', width=2, connect='strip')
view.add(sun_path)

# --- sun sphere ---
sun = scene.visuals.Sphere(radius=0.15, color=color.Color('yellow'), shading='smooth')
view.add(sun)

# --- animation ---
idx = [0]

def update(event):
    i = idx[0]
    sun.transform = transforms.STTransform(translate=(x[i], y[i], z[i]))
    idx[0] = (i + 1) % len(t)

timer = app.Timer(interval=0.02, connect=update, start=True)

if __name__ == '__main__':
    app.run()
