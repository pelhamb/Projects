
"""
sungraph.py
----------------
Visualizes the arc of the sun using 3D graphics.

Modules and Libraries:
- numpy: For numerical operations and generating the sun's path.
- vispy.app: Manages the application event loop and timer for animation.
- vispy.scene: Provides the 3D scene graph, canvas, and visual objects (Plane, Line, Sphere, Camera).
- vispy.color: Used for color definitions (e.g., yellow for the sun).
- vispy.visuals.transforms: Handles object transformations (translation, scaling, etc.).

How it works:
1. Sets up a 3D window using vispy's SceneCanvas.
2. Adds a ground plane and a camera for 3D navigation.
3. Generates a fake sun path using numpy (a half-ellipse in the sky).
4. Draws the sun's path as a line and the sun as a moving sphere.
5. Animates the sun along the path using a timer and transformation updates.

Run this script to see a 3D animation of the sun's arc.
"""

import numpy as np
from vispy import app, scene, color
from vispy.visuals import transforms

# --- setup window and view ---
canvas = scene.SceneCanvas(
    title='Sun Arc Viewer',
    keys='interactive',
    bgcolor='black',
    size=(1200, 800),
    show=True
)

view = canvas.central_widget.add_view()
view.camera = scene.cameras.TurntableCamera(
    fov=90, azimuth=90, elevation=0, distance=5
)
view.camera.up = '+y'  # ensure Y is "up"

# --- horizon plane ---
plane = scene.visuals.Plane(width=10, height=10, color='midnightblue')
plane.transform = transforms.STTransform(translate=(0, -1, 0))
view.add(plane)

# --- full sun path (ellipse) ---
t = np.linspace(0, 2 * np.pi, 400)
x = np.cos(t) * 3
y = np.sin(t) * 2
z = np.zeros_like(t)

# make dotted line by taking every few points separated by NaNs
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


# draw line of path
#sun_path = scene.visuals.Line(pos=np.c_[x, y, z], color='orange', width=3)
#view.add(sun_path)

# sun sphere (yellow ball)
sun = scene.visuals.Sphere(radius=0.15, color=color.Color('orange'), shading='smooth')
view.add(sun)

# --- animation ---
idx = [0]  # mutable index counter

def update(event):
    i = idx[0]
    sun.transform = transforms.STTransform(translate=(x[i], y[i], z[i]))
    idx[0] = (i + 1) % len(t)

timer = app.Timer(interval=0.02, connect=update, start=True)

if __name__ == '__main__':
    app.run()
