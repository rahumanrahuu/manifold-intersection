import json
import math
import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import expm
from matplotlib.colors import LinearSegmentedColormap
import os

# Physical Constants
G = 6.67430e-11 
C = 299792458   
MASA_5D = 2e12      # 2 Billion Metric Tons
RADIUS_5D = 6.0     # Hyper-radius in meters

def get_so5_rotation(t):
    """Generates a 5D rotation matrix using SO(5) Lie Algebra."""
    A = np.zeros((5, 5))
    A[0, 1] = 0.5 * t; A[1, 0] = -0.5 * t # XY Plane
    A[0, 4] = 0.3 * t; A[4, 0] = -0.3 * t # XV Plane
    A[2, 3] = 0.7 * t; A[3, 2] = -0.7 * t # ZW Plane
    return expm(A)

def run_simulation():
    os.makedirs('results', exist_ok=True)
    plt.style.use('dark_background')
    
    steps = 150
    duration = 30.0
    dt_vals = np.linspace(0, duration, steps)
    
    # Lab Sensor Grid (3x3)
    detailed_sensors = [
        (-2, 2), (0, 2), (2, 2),
        (-2, 0), (0, 0), (2, 0),
        (-2, -2), (0, -2), (2, -2)
    ]
    
    # Path Model (Lissajous + W-Dive + V-Oscillation)
    path = np.zeros((steps, 5))
    path[:, 0] = 6 * np.sin(0.4 * dt_vals)  # X
    path[:, 1] = 6 * np.cos(0.3 * dt_vals)  # Y
    path[:, 2] = 2 * np.sin(0.2 * dt_vals)  # Z
    path[:, 3] = 10 - 0.7 * dt_vals         # W-Dive
    path[:, 4] = 4 * np.sin(0.5 * dt_vals)  # V
    
    json_output = []
    max_pressures = []
    lensing_peaks = []
    
    # High-Resolution Sensor Grid for Heatmaps (25x25)
    grid_size = 25
    x_range = np.linspace(-8, 8, grid_size)
    y_range = np.linspace(-8, 8, grid_size)
    X, Y = np.meshgrid(x_range, y_range)
    cmap_pressure = LinearSegmentedColormap.from_list("hyper", ["#000022", "#0000FF", "#00FFFF", "#FFFFFF"])

    print("Initiating Unified 5D Simulation...")
    
    for i in range(steps):
        t, pos_5d = dt_vals[i], path[i]
        
        # 1. Physics: Lensing
        dist_5d = np.linalg.norm(pos_5d)
        deflection = ((4 * G * MASA_5D) / (C**2 * max(0.5, dist_5d))) * 206265
        lensing_peaks.append(deflection)
        
        # 2. Physics: Intersection
        slice_sq = RADIUS_5D**2 - (pos_5d[3]**2 + pos_5d[4]**2)
        slice_r = math.sqrt(slice_sq) if slice_sq > 0 else 0
        
        # 3. High-Res Grid Sensors (For Heatmap)
        dist_grid = np.sqrt((X - pos_5d[0])**2 + (Y - pos_5d[1])**2)
        grid_p = np.maximum(0, (slice_r - dist_grid) * 1000)
        max_pressures.append(np.max(grid_p))
        
        # 4. Lab Grid Sensors (3x3 for JSON)
        frame_sensors = []
        for sx, sy in detailed_sensors:
            dist_3d = math.sqrt((sx - pos_5d[0])**2 + (sy - pos_5d[1])**2)
            p = (slice_r - dist_3d) * 1000 if slice_r > dist_3d else 0
            frame_sensors.append({"id": f"{sx},{sy}", "pa": round(p, 2)})

        json_output.append({
            "t": round(t, 2),
            "coords": {"3d": pos_5d[:3].tolist(), "hyper": pos_5d[3:].tolist()},
            "physics": {"lensing": round(deflection, 10), "slice_r": round(slice_r, 2)},
            "sensors": frame_sensors
        })
        
        # Capture Heatmap at midpoint
        if i == steps // 2:
            plt.figure(figsize=(10, 8))
            plt.pcolormesh(X, Y, grid_p, cmap=cmap_pressure, shading='gouraud')
            plt.colorbar(label='Pressure (Pa)')
            plt.title(f"5D Slice Intersection Heatmap (T={t:.1f}s)")
            plt.savefig('results/heatmap_peak_intersection.png', dpi=150)
            plt.close()

    # Save outputs.json
    os.makedirs('output_json', exist_ok=True)
    with open("output_json/outputs.json", "w") as f:
        json.dump({"experiment": "Unified 5D Simulation", "data": json_output}, f, indent=2)

    # Generate Plots
    print("Generating Visual Reports...")
    
    # Trajectory
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    sc = ax.scatter(path[:, 0], path[:, 1], path[:, 3], c=dt_vals, cmap='plasma', s=10, alpha=0.6)
    ax.set_title("5D Trajectory Projection (X-Y-W)")
    plt.savefig('results/trajectory_dive.png', dpi=200)
    plt.close()

    # Physics Correlation
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()
    ax1.plot(dt_vals, lensing_peaks, color='#FFD700', label='Lensing Deflection')
    ax2.fill_between(dt_vals, max_pressures, color='#00FFFF', alpha=0.3, label='Pressure')
    plt.title("5D Physical Signature Correlation")
    plt.savefig('results/physics_correlation.png', dpi=200)
    plt.close()

    print("Success. Results saved to results/ and output_json/outputs.json")

if __name__ == "__main__":
    run_simulation()