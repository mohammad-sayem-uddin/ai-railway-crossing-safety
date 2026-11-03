import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

# Create output figures directory
output_dir = "/Users/sayemuddin/Desktop/Train_automation/results/figures"
os.makedirs(output_dir, exist_ok=True)

# Set global matplotlib parameters for publication quality
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 1.0
plt.rcParams['figure.autolayout'] = False

print("Generating Figure 1: End-to-End Multimodal System Architecture...")

# -------------------------------------------------------------
# FIGURE 1: Overall Multimodal System Architecture
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(15, 9.5), dpi=300)
ax.set_xlim(0, 15)
ax.set_ylim(0, 9.5)
ax.axis('off')

# Background canvas style
bg_rect = FancyBboxPatch((0.2, 0.2), 14.6, 9.1, boxstyle="round,pad=0.2,rounding_size=0.3",
                         facecolor='#F8FAFC', edgecolor='#CBD5E1', linewidth=1.5)
ax.add_patch(bg_rect)

# Title Block
ax.text(7.5, 9.0, "END-TO-END MULTIMODAL RAILWAY LEVEL-CROSSING SAFETY ARCHITECTURE",
        ha='center', va='center', fontsize=15, fontweight='bold', color='#0F172A')
ax.text(7.5, 8.65, "Dual-Camera Computer Vision, Acoustic Horn Detection (Under Development), & State-Aware Decision Policy",
        ha='center', va='center', fontsize=10, style='italic', color='#475569')

# Layer 1: Sensor Ingestion (Left Column)
# Box 1: Approach Camera
p1 = FancyBboxPatch((0.6, 6.3), 3.0, 1.8, boxstyle="round,pad=0.1,rounding_size=0.15",
                    facecolor='#EFF6FF', edgecolor='#3B82F6', linewidth=2)
ax.add_patch(p1)
ax.text(2.1, 7.7, "[CAM 1] Camera 1 (Approach)", ha='center', va='center', fontsize=11, fontweight='bold', color='#1E40AF')
ax.text(2.1, 7.25, "• Upstream Track FoV\n• Real-Time Video Stream\n• Leading Locomotive Zone", 
        ha='center', va='center', fontsize=8.5, color='#1E293B')
ax.text(2.1, 6.55, "Captures: Front & Side", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#2563EB')

# Box 2: Departure Camera
p2 = FancyBboxPatch((0.6, 3.8), 3.0, 1.8, boxstyle="round,pad=0.1,rounding_size=0.15",
                    facecolor='#EFF6FF', edgecolor='#3B82F6', linewidth=2)
ax.add_patch(p2)
ax.text(2.1, 5.2, "[CAM 2] Camera 2 (Departure)", ha='center', va='center', fontsize=11, fontweight='bold', color='#1E40AF')
ax.text(2.1, 4.75, "• Downstream Crossing FoV\n• Crossing Zone Occupancy\n• Departure Trailing Zone", 
        ha='center', va='center', fontsize=8.5, color='#1E293B')
ax.text(2.1, 4.05, "Captures: Side & Rear", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#2563EB')

# Box 3: Audio Sensor (In Development)
p3 = FancyBboxPatch((0.6, 1.3), 3.0, 1.8, boxstyle="round,pad=0.1,rounding_size=0.15",
                    facecolor='#FEF3C7', edgecolor='#D97706', linewidth=2, linestyle='--')
ax.add_patch(p3)
ax.text(2.1, 2.7, "[MIC] Audio Subsystem", ha='center', va='center', fontsize=11, fontweight='bold', color='#92400E')
ax.text(2.1, 2.25, "• High-Gain Mic / Array\n• 16 kHz Continuous Stream\n• Bangladesh Horn Profile", 
        ha='center', va='center', fontsize=8.5, color='#1E293B')
ax.text(2.1, 1.55, "[ In Active Development ]", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#D97706')

# Layer 2: Perception Models (Middle-Left Column)
# Vision Model Box
p4 = FancyBboxPatch((4.3, 4.2), 3.2, 3.9, boxstyle="round,pad=0.15,rounding_size=0.2",
                    facecolor='#F0FDF4', edgecolor='#16A34A', linewidth=2)
ax.add_patch(p4)
ax.text(5.9, 7.7, "PERCEPTION: VISION", ha='center', va='center', fontsize=11.5, fontweight='bold', color='#15803D')
ax.text(5.9, 7.3, "YOLOv8 nano Multi-Class", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#0F172A')
ax.plot([4.6, 7.2], [7.05, 7.05], color='#CBD5E1', lw=1)

ax.text(5.9, 6.6, "Viewpoint Classification:", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#334155')
# 3 classes badge
ax.text(5.9, 6.15, "• FRONT (Locomotive / Nose)\n• SIDE (Carriages / Coaches)\n• REAR (Last Coach End)",
        ha='center', va='center', fontsize=8.5, color='#0F172A')

ax.plot([4.6, 7.2], [5.55, 5.55], color='#CBD5E1', lw=1)
ax.text(5.9, 5.15, "Benchmark Results Achieved:\n• mAP@50: 99.46%\n• Front AP: 98.99% | Recall: 94.7%\n• Rear AP: 99.84% | Recall: 100%\n• Side AP: 99.55% | Recall: 98.5%",
        ha='center', va='center', fontsize=8, color='#14532D')

# Audio Model Box (In Dev)
p5 = FancyBboxPatch((4.3, 1.3), 3.2, 2.3, boxstyle="round,pad=0.15,rounding_size=0.2",
                    facecolor='#FFFBEB', edgecolor='#F59E0B', linewidth=2, linestyle='--')
ax.add_patch(p5)
ax.text(5.9, 3.25, "PERCEPTION: AUDIO", ha='center', va='center', fontsize=11.5, fontweight='bold', color='#B45309')
ax.text(5.9, 2.9, "Mel-Spectrogram + CNN", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#0F172A')
ax.plot([4.6, 7.2], [2.65, 2.65], color='#CBD5E1', lw=1)
ax.text(5.9, 2.2, "• Binary: Horn vs Non-Horn\n• STFT & Mel Filterbanks\n• Noise Robustness (SNR -5 to +10dB)\n• Status: Architecture in Progress",
        ha='center', va='center', fontsize=8, color='#78350F')
ax.text(5.9, 1.5, "[ Training & Tuning Active ]", ha='center', va='center', fontsize=8, fontweight='bold', color='#D97706')

# Layer 3: Temporal Smoothing & Fusion (Middle-Right Column)
p6 = FancyBboxPatch((8.1, 2.8), 2.9, 4.5, boxstyle="round,pad=0.15,rounding_size=0.2",
                    facecolor='#FAF5FF', edgecolor='#9333EA', linewidth=2)
ax.add_patch(p6)
ax.text(9.55, 6.9, "TEMPORAL FUSION &", ha='center', va='center', fontsize=11, fontweight='bold', color='#7E22CE')
ax.text(9.55, 6.55, "EVIDENCE ENGINE", ha='center', va='center', fontsize=11, fontweight='bold', color='#7E22CE')
ax.plot([8.3, 10.8], [6.3, 6.3], color='#CBD5E1', lw=1)

ax.text(9.55, 5.8, "Multi-Sensor Aggregation:", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#334155')
ax.text(9.55, 5.0, "• Temporal Debouncing\n• Windowed Evidence (N frames)\n• Spatial Viewpoint Matching\n• Audio Early-Warning Boost\n• Confidence Thresholding\n• Stale/Drop Frame Handling",
        ha='center', va='center', fontsize=8, color='#1E293B')
ax.plot([8.3, 10.8], [4.0, 4.0], color='#CBD5E1', lw=1)
ax.text(9.55, 3.4, "Outputs Calibrated Evidence:\n[E_front, E_side, E_rear, E_horn]", 
        ha='center', va='center', fontsize=8, fontweight='bold', color='#6B21A8')

# Layer 4: State Machine & Safety Decision Engine (Right Column)
p7 = FancyBboxPatch((11.5, 3.5), 3.0, 4.6, boxstyle="round,pad=0.15,rounding_size=0.2",
                    facecolor='#FEF2F2', edgecolor='#DC2626', linewidth=2)
ax.add_patch(p7)
ax.text(13.0, 7.7, "SAFETY DECISION", ha='center', va='center', fontsize=11.5, fontweight='bold', color='#B91C1C')
ax.text(13.0, 7.35, "ENGINE & STATE MACHINE", ha='center', va='center', fontsize=10, fontweight='bold', color='#B91C1C')
ax.plot([11.8, 14.2], [7.1, 7.1], color='#CBD5E1', lw=1)

ax.text(13.0, 6.6, "10-State Safety Policy:", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#334155')
ax.text(13.0, 5.8, "• IDLE (Gate Open)\n• TRAIN_APPROACHING\n• WARNING / CLOSING\n• CROSSING_OCCUPIED\n• TRAIN_DEPARTING\n• REAR_CONFIRMED\n• GATE_OPENING\n• FAULT / FAIL-SAFE",
        ha='center', va='center', fontsize=8, color='#1E293B')
ax.plot([11.8, 14.2], [4.65, 4.65], color='#CBD5E1', lw=1)
ax.text(13.0, 4.1, "Core Safety Invariants:\n1. Fast Close on Approach\n2. REAR Confirmed to Open\n3. Zero Opening on Loss-of-Signal",
        ha='center', va='center', fontsize=8, fontweight='bold', color='#991B1B')

# Layer 5: Actuator Output Box (Bottom Right)
p8 = FancyBboxPatch((11.5, 1.0), 3.0, 1.9, boxstyle="round,pad=0.1,rounding_size=0.15",
                    facecolor='#F1F5F9', edgecolor='#475569', linewidth=2)
ax.add_patch(p8)
ax.text(13.0, 2.5, "GATE ACTUATION & ALARM", ha='center', va='center', fontsize=10.5, fontweight='bold', color='#1E293B')
ax.text(13.0, 1.75, "• Barrier Motor (Close/Open)\n• Acoustic Siren & Strobe\n• Fail-Safe Gravity Drop\n• Event Telemetry Logger",
        ha='center', va='center', fontsize=8, color='#334155')

# Connecting Arrows
arrow_kw = dict(arrowstyle="-|>", color="#334155", lw=1.8, mutation_scale=15)
arrow_dash_kw = dict(arrowstyle="-|>", color="#D97706", lw=1.8, mutation_scale=15, linestyle="--")

# Cam 1 -> Vision
ax.annotate("", xy=(4.3, 6.8), xytext=(3.6, 7.2), arrowprops=arrow_kw)
# Cam 2 -> Vision
ax.annotate("", xy=(4.3, 5.2), xytext=(3.6, 4.7), arrowprops=arrow_kw)
# Mic -> Audio Model
ax.annotate("", xy=(4.3, 2.45), xytext=(3.6, 2.2), arrowprops=arrow_dash_kw)

# Vision -> Fusion
ax.annotate("", xy=(8.1, 5.8), xytext=(7.5, 5.8), arrowprops=arrow_kw)
# Audio -> Fusion
ax.annotate("", xy=(8.1, 3.8), xytext=(7.5, 2.45), arrowprops=arrow_dash_kw)

# Fusion -> Decision Engine
ax.annotate("", xy=(11.5, 5.5), xytext=(11.0, 5.5), arrowprops=arrow_kw)

# Decision Engine -> Actuation
ax.annotate("", xy=(13.0, 2.9), xytext=(13.0, 3.5), arrowprops=arrow_kw)

# Add Legend / Watermark at bottom left
ax.text(0.6, 0.5, "Status Legend: ── [Implemented & Benchmarked]   - - [Under Active Development]", 
        ha='left', va='center', fontsize=9, fontweight='bold', color='#475569')

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "fig1_overall_architecture.png"), dpi=300)
plt.close(fig)
print("Saved fig1_overall_architecture.png")

# -------------------------------------------------------------
# FIGURE 2: Spatial Deployment Diagram at Level Crossing
# -------------------------------------------------------------
print("Generating Figure 2: Spatial Deployment Diagram...")
fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
ax.set_xlim(0, 14)
ax.set_ylim(0, 8)
ax.axis('off')

# Background
bg_rect = FancyBboxPatch((0.2, 0.2), 13.6, 7.6, boxstyle="round,pad=0.2,rounding_size=0.3",
                         facecolor='#F8FAFC', edgecolor='#CBD5E1', linewidth=1.5)
ax.add_patch(bg_rect)

# Title
ax.text(7.0, 7.4, "PHYSICAL SPATIAL DEPLOYMENT AT BANGLADESH LEVEL-CROSSING",
        ha='center', va='center', fontsize=14, fontweight='bold', color='#0F172A')

# Railway Track (Horizontal across middle)
track_bg = patches.Rectangle((0.5, 3.4), 13.0, 1.2, facecolor='#E2E8F0', edgecolor='none')
ax.add_patch(track_bg)

# Rails
ax.plot([0.5, 13.5], [4.4, 4.4], color='#475569', lw=4)
ax.plot([0.5, 13.5], [3.6, 3.6], color='#475569', lw=4)

# Sleepers (Ties)
for x in np.arange(0.7, 13.5, 0.4):
    ax.plot([x, x], [3.4, 4.6], color='#94A3B8', lw=2)

# Roadway Crossing (Vertical across track)
road_bg = patches.Rectangle((6.0, 0.5), 2.0, 7.0, facecolor='#CBD5E1', edgecolor='none')
ax.add_patch(road_bg)
# Road divider
for y in np.arange(0.7, 7.5, 0.6):
    if y < 3.2 or y > 4.8:
        ax.plot([7.0, 7.0], [y, y+0.3], color='#FFFFFF', lw=2)

# Level Crossing Reference Zone Box (Yellow hatched)
zone_box = patches.Rectangle((5.8, 3.3), 2.4, 1.4, facecolor='#FEF08A', alpha=0.4,
                             edgecolor='#EAB308', lw=2, linestyle='--')
ax.add_patch(zone_box)
ax.text(7.0, 4.0, "CROSSING DANGER ZONE", ha='center', va='center', fontsize=9, fontweight='bold', color='#854D0E')

# Gates
# Gate 1 (Top Road)
ax.plot([5.8, 8.2], [5.0, 5.0], color='#DC2626', lw=4, solid_capstyle='round')
ax.plot([5.8, 8.2], [5.0, 5.0], color='#FFFFFF', lw=2, linestyle=':', solid_capstyle='round')
ax.scatter([5.7], [5.0], color='#B91C1C', s=100, zorder=5)
ax.text(5.4, 5.3, "Gate Barrier 1", fontsize=8.5, fontweight='bold', color='#991B1B')

# Gate 2 (Bottom Road)
ax.plot([5.8, 8.2], [3.0, 3.0], color='#DC2626', lw=4, solid_capstyle='round')
ax.plot([5.8, 8.2], [3.0, 3.0], color='#FFFFFF', lw=2, linestyle=':', solid_capstyle='round')
ax.scatter([8.3], [3.0], color='#B91C1C', s=100, zorder=5)
ax.text(8.5, 2.7, "Gate Barrier 2", fontsize=8.5, fontweight='bold', color='#991B1B')

# Camera 1 (Approach Side - Left Upstream)
cam1_x, cam1_y = 3.2, 5.8
ax.scatter([cam1_x], [cam1_y], marker='s', color='#2563EB', s=160, zorder=5)
ax.text(cam1_x, cam1_y + 0.35, "[CAM 1] Approach View", ha='center', fontsize=9.5, fontweight='bold', color='#1D4ED8')
# FoV Cone for Camera 1 (Angled towards upstream track & crossing)
fov1 = patches.Polygon([[cam1_x, cam1_y], [0.8, 4.8], [6.2, 3.5]], closed=True, 
                       facecolor='#60A5FA', alpha=0.25, edgecolor='#2563EB', linestyle=':')
ax.add_patch(fov1)
ax.text(2.0, 5.0, "Approach FoV\n(Front & Early Side)", fontsize=8, color='#1E40AF', ha='center')

# Camera 2 (Departure Side - Right Downstream)
cam2_x, cam2_y = 10.8, 2.2
ax.scatter([cam2_x], [cam2_y], marker='s', color='#16A34A', s=160, zorder=5)
ax.text(cam2_x, cam2_y - 0.35, "[CAM 2] Departure View", ha='center', fontsize=9.5, fontweight='bold', color='#15803D')
# FoV Cone for Camera 2 (Angled towards crossing zone & departure track)
fov2 = patches.Polygon([[cam2_x, cam2_y], [5.8, 4.5], [13.2, 3.3]], closed=True, 
                       facecolor='#4ADE80', alpha=0.25, edgecolor='#16A34A', linestyle=':')
ax.add_patch(fov2)
ax.text(11.0, 3.0, "Departure FoV\n(Crossing Side & Rear)", fontsize=8, color='#14532D', ha='center')

# Acoustic Sensor Unit (Microphone) near crossing pole
mic_x, mic_y = 5.3, 5.8
ax.scatter([mic_x], [mic_y], marker='o', color='#D97706', s=140, zorder=5)
ax.text(mic_x, mic_y + 0.35, "[MIC] Audio Sensor Unit\n(In Active Development)", ha='center', fontsize=8.5, fontweight='bold', color='#B45309')
# Acoustic Omni rings
circle1 = plt.Circle((mic_x, mic_y), 0.8, color='#F59E0B', fill=False, linestyle='--', lw=1.2)
circle2 = plt.Circle((mic_x, mic_y), 1.5, color='#F59E0B', fill=False, linestyle=':', lw=1.0)
ax.add_patch(circle1)
ax.add_patch(circle2)

# Approaching Train Graphic / Vector
train_box = FancyBboxPatch((1.0, 3.7), 2.2, 0.6, boxstyle="round,pad=0.05,rounding_size=0.1",
                           facecolor='#0284C7', edgecolor='#0369A1', lw=2)
ax.add_patch(train_box)
ax.text(2.1, 4.0, "TRAIN (Approaching ->)", ha='center', va='center', fontsize=8, fontweight='bold', color='#FFFFFF')

# Train Movement Direction Arrow
ax.annotate("", xy=(12.5, 4.0), xytext=(0.8, 4.0), 
            arrowprops=dict(arrowstyle="-|>", color="#0284C7", lw=2.5, mutation_scale=20))
ax.text(7.0, 1.2, "Road Traffic Direction (Vehicles, Pedestrians, Rickshaws)", ha='center', fontsize=8.5, color='#475569')

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "fig2_spatial_deployment.png"), dpi=300)
plt.close(fig)
print("Saved fig2_spatial_deployment.png")

# -------------------------------------------------------------
# FIGURE 3: Safety State Machine Flowchart
# -------------------------------------------------------------
print("Generating Figure 3: Safety State Machine...")
fig, ax = plt.subplots(figsize=(15, 8.5), dpi=300)
ax.set_xlim(0, 15)
ax.set_ylim(0, 8.5)
ax.axis('off')

# Background
bg_rect = FancyBboxPatch((0.2, 0.2), 14.6, 8.1, boxstyle="round,pad=0.2,rounding_size=0.3",
                         facecolor='#F8FAFC', edgecolor='#CBD5E1', linewidth=1.5)
ax.add_patch(bg_rect)

ax.text(7.5, 8.0, "SAFETY-ORIENTED STATE MACHINE & DECISION TRANSITION GRAPH",
        ha='center', va='center', fontsize=14, fontweight='bold', color='#0F172A')

# States Layout
states = [
    {"name": "1. IDLE\n(Gate Fully Open)", "x": 1.6, "y": 5.5, "bg": "#ECFDF5", "border": "#10B981", "tc": "#065F46"},
    {"name": "2. TRAIN_APPROACHING\n(Front / Horn Evid.)", "x": 4.5, "y": 5.5, "bg": "#FEF3C7", "border": "#F59E0B", "tc": "#92400E"},
    {"name": "3. WARNING_ACTIVE\n(Siren & Strobe ON)", "x": 7.5, "y": 5.5, "bg": "#FFEDD5", "border": "#F97316", "tc": "#9A3412"},
    {"name": "4. GATE_CLOSING\n(Barrier Lowering)", "x": 10.5, "y": 5.5, "bg": "#FEE2E2", "border": "#EF4444", "tc": "#991B1B"},
    {"name": "5. CROSSING_OCCUPIED\n(Gate Locked Closed)", "x": 13.2, "y": 5.5, "bg": "#FEE2E2", "border": "#DC2626", "tc": "#7F1D1D"},
    
    {"name": "6. TRAIN_DEPARTING\n(Side / Tail Leaving)", "x": 13.2, "y": 2.2, "bg": "#EDE9FE", "border": "#8B5CF6", "tc": "#5B21B6"},
    {"name": "7. REAR_CONFIRMED\n(Positive Tail Seen)", "x": 9.5, "y": 2.2, "bg": "#DBEAFE", "border": "#3B82F6", "tc": "#1E40AF"},
    {"name": "8. CROSSING_CLEAR\n(Debounce Window OK)", "x": 5.8, "y": 2.2, "bg": "#E0E7FF", "border": "#6366F1", "tc": "#3730A3"},
    {"name": "9. GATE_OPENING\n(Barrier Raising)", "x": 2.2, "y": 2.2, "bg": "#D1FAE5", "border": "#10B981", "tc": "#065F46"},
    
    {"name": "[!] FAULT / FAIL-SAFE\n(Sensor Loss / Default Closed)", "x": 7.5, "y": 0.8, "bg": "#F1F5F9", "border": "#475569", "tc": "#0F172A"}
]

box_w, box_h = 2.4, 1.2

for st in states:
    p = FancyBboxPatch((st["x"] - box_w/2, st["y"] - box_h/2), box_w, box_h,
                       boxstyle="round,pad=0.1,rounding_size=0.15",
                       facecolor=st["bg"], edgecolor=st["border"], linewidth=2)
    ax.add_patch(p)
    ax.text(st["x"], st["y"], st["name"], ha='center', va='center', fontsize=8.5, fontweight='bold', color=st["tc"])

# Transitions
trans_arrow = dict(arrowstyle="-|>", color="#334155", lw=2, mutation_scale=16)

# 1 -> 2
ax.annotate("", xy=(3.3, 5.5), xytext=(2.8, 5.5), arrowprops=trans_arrow)
ax.text(3.05, 5.8, "Front Seen\nor Horn", fontsize=7.5, ha='center', color='#B45309', fontweight='bold')

# 2 -> 3
ax.annotate("", xy=(6.3, 5.5), xytext=(5.7, 5.5), arrowprops=trans_arrow)
ax.text(6.0, 5.8, "Conf > Thr", fontsize=7.5, ha='center', color='#C2410C', fontweight='bold')

# 3 -> 4
ax.annotate("", xy=(9.3, 5.5), xytext=(8.7, 5.5), arrowprops=trans_arrow)
ax.text(9.0, 5.8, "T_warn Exp.", fontsize=7.5, ha='center', color='#DC2626', fontweight='bold')

# 4 -> 5
ax.annotate("", xy=(12.0, 5.5), xytext=(11.7, 5.5), arrowprops=trans_arrow)
ax.text(11.85, 5.8, "Barrier Down", fontsize=7.5, ha='center', color='#991B1B', fontweight='bold')

# 5 -> 6
ax.annotate("", xy=(13.2, 2.8), xytext=(13.2, 4.9), arrowprops=trans_arrow)
ax.text(13.85, 3.85, "Side Passing\n-> Exit Zone", fontsize=7.5, ha='center', color='#6D28D9', fontweight='bold')

# 6 -> 7
ax.annotate("", xy=(10.7, 2.2), xytext=(12.0, 2.2), arrowprops=trans_arrow)
ax.text(11.35, 2.5, "REAR View\nConfirmed", fontsize=7.5, ha='center', color='#1D4ED8', fontweight='bold')

# 7 -> 8
ax.annotate("", xy=(7.0, 2.2), xytext=(8.3, 2.2), arrowprops=trans_arrow)
ax.text(7.65, 2.5, "Zone Clear\nPersists", fontsize=7.5, ha='center', color='#4338CA', fontweight='bold')

# 8 -> 9
ax.annotate("", xy=(3.4, 2.2), xytext=(4.6, 2.2), arrowprops=trans_arrow)
ax.text(4.0, 2.5, "Safety Timer\nPassed", fontsize=7.5, ha='center', color='#047857', fontweight='bold')

# 9 -> 1
ax.annotate("", xy=(1.6, 4.9), xytext=(1.6, 2.8), arrowprops=trans_arrow)
ax.text(0.9, 3.85, "Fully Open\nNormal", fontsize=7.5, ha='center', color='#065F46', fontweight='bold')

# Fail Safe transitions
fail_arrow = dict(arrowstyle="-|>", color="#DC2626", lw=1.2, linestyle="--", mutation_scale=12)
ax.annotate("", xy=(7.5, 1.4), xytext=(7.5, 4.9), arrowprops=fail_arrow)
ax.annotate("", xy=(8.7, 1.4), xytext=(13.2, 1.6), arrowprops=fail_arrow)
ax.text(7.5, 3.5, "On Discrepancy / Camera Blackout / Timeout -> Trigger FAIL-SAFE (Gate Closed)", 
        fontsize=8, ha='center', color='#DC2626', fontweight='bold', backgroundcolor='#FEF2F2')

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "fig3_state_machine_flow.png"), dpi=300)
plt.close(fig)
print("Saved fig3_state_machine_flow.png")

# -------------------------------------------------------------
# FIGURE 4: Audio Subsystem Architecture (In Development)
# -------------------------------------------------------------
print("Generating Figure 4: Audio Subsystem Architecture...")
fig, ax = plt.subplots(figsize=(14, 7), dpi=300)
ax.set_xlim(0, 14)
ax.set_ylim(0, 7)
ax.axis('off')

# Background
bg_rect = FancyBboxPatch((0.2, 0.2), 13.6, 6.6, boxstyle="round,pad=0.2,rounding_size=0.3",
                         facecolor='#FFFDF5', edgecolor='#FBBF24', linewidth=1.5)
ax.add_patch(bg_rect)

ax.text(7.0, 6.4, "ACOUSTIC TRAIN HORN DETECTION SUBSYSTEM [CURRENTLY IN ACTIVE DEVELOPMENT]",
        ha='center', va='center', fontsize=13, fontweight='bold', color='#92400E')
ax.text(7.0, 6.05, "Signal Conditioning, Mel-Spectrogram Feature Extraction, CNN Classification, & Noise Stress Protocol",
        ha='center', va='center', fontsize=9.5, style='italic', color='#78350F')

# Step 1: Ingestion
b1 = FancyBboxPatch((0.6, 2.5), 2.2, 3.0, boxstyle="round,pad=0.1,rounding_size=0.15",
                    facecolor='#EFF6FF', edgecolor='#3B82F6', lw=1.5)
ax.add_patch(b1)
ax.text(1.7, 5.1, "1. Audio Stream", ha='center', fontsize=10, fontweight='bold', color='#1E40AF')
ax.text(1.7, 4.0, "• 16 kHz Mono WAV\n• Continuous Buffer\n• Sliding Windows\n  (2.0s - 4.0s)\n• High Dynamic Range",
        ha='center', fontsize=8, color='#1E293B')

# Step 2: Signal Conditioning & Noise Mixing
b2 = FancyBboxPatch((3.2, 2.5), 2.4, 3.0, boxstyle="round,pad=0.1,rounding_size=0.15",
                    facecolor='#FEF3C7', edgecolor='#D97706', lw=1.5)
ax.add_patch(b2)
ax.text(4.4, 5.1, "2. Signal Preprocessing", ha='center', fontsize=10, fontweight='bold', color='#92400E')
ax.text(4.4, 3.9, "• RMS Normalization\n• Bandpass Filtering\n  (200 Hz - 4000 Hz)\n• Synthetic Noise Mixer\n  (SNR: -5 to +10 dB)\n• Traffic/Rain Injection",
        ha='center', fontsize=8, color='#1E293B')

# Step 3: Mel-Spectrogram
b3 = FancyBboxPatch((6.0, 2.5), 2.4, 3.0, boxstyle="round,pad=0.1,rounding_size=0.15",
                    facecolor='#FAF5FF', edgecolor='#9333EA', lw=1.5)
ax.add_patch(b3)
ax.text(7.2, 5.1, "3. Feature Extraction", ha='center', fontsize=10, fontweight='bold', color='#7E22CE')
ax.text(7.2, 3.9, "• STFT Computation\n  (n_fft=1024, hop=512)\n• 64/128 Mel Filterbanks\n• Log-Mel Spectrogram\n• Delta & Delta-Delta\n  Coefficients",
        ha='center', fontsize=8, color='#1E293B')

# Step 4: Deep Classifier
b4 = FancyBboxPatch((8.8, 2.5), 2.2, 3.0, boxstyle="round,pad=0.1,rounding_size=0.15",
                    facecolor='#F0FDF4', edgecolor='#16A34A', lw=1.5)
ax.add_patch(b4)
ax.text(9.9, 5.1, "4. Deep CNN Model", ha='center', fontsize=10, fontweight='bold', color='#15803D')
ax.text(9.9, 3.9, "• 2D CNN / ResNet-18\n• Conv-BatchNorm-ReLU\n• MaxPool & Dropout\n• Sigmoid Activation\n• Horn Probability\n  P(Horn | Audio)",
        ha='center', fontsize=8, color='#1E293B')

# Step 5: Output Evidence
b5 = FancyBboxPatch((11.4, 2.5), 2.0, 3.0, boxstyle="round,pad=0.1,rounding_size=0.15",
                    facecolor='#FEE2E2', edgecolor='#EF4444', lw=1.5)
ax.add_patch(b5)
ax.text(12.4, 5.1, "5. Fusion Evidence", ha='center', fontsize=10, fontweight='bold', color='#991B1B')
ax.text(12.4, 3.9, "• Calibrated Score\n• Debounce Window\n• Early Warning Signal\n• Robust in Dense Fog\n  & Curve Blindspots",
        ha='center', fontsize=8, color='#1E293B')

# Arrows
for x in [2.8, 5.6, 8.4, 11.0]:
    ax.annotate("", xy=(x+0.4, 4.0), xytext=(x, 4.0), 
                arrowprops=dict(arrowstyle="-|>", color="#475569", lw=2, mutation_scale=14))

# Status Box at Bottom
stat_box = FancyBboxPatch((0.6, 0.6), 12.8, 1.4, boxstyle="round,pad=0.1,rounding_size=0.15",
                          facecolor='#FFFBEB', edgecolor='#F59E0B', lw=1.5, linestyle='--')
ax.add_patch(stat_box)
ax.text(7.0, 1.5, "CURRENT ACOUSTIC DEVELOPMENT STATUS & MILESTONES:", ha='center', fontsize=9.5, fontweight='bold', color='#B45309')
ax.text(7.0, 0.95, "[x] Audio Ingestion & Preprocessor Pipeline Completed (`src/railway_detection/audio/preprocessor.py`)\n[x] Synthetic Noise Mixing Module Functional (`src/railway_detection/audio/noise_mixer.py`)\n[*] Acoustic Model Training, Mel-Spectrogram Hyperparameter Tuning, and Multi-SNR Noise Robustness Validation Ongoing",
        ha='center', fontsize=8, color='#78350F')

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "fig4_audio_pipeline.png"), dpi=300)
plt.close(fig)
print("Saved fig4_audio_pipeline.png")

# -------------------------------------------------------------
# FIGURE 5: Training & Validation Progression Curves (YOLOv8)
# -------------------------------------------------------------
print("Generating Figure 5: Training Curves from results.csv...")
results_csv_path = "/Users/sayemuddin/Desktop/Train_automation/experiments/vision/39f402dfe460/checkpoints/results.csv"
df = pd.read_csv(results_csv_path)
df.columns = [c.strip() for c in df.columns]

fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10), dpi=300)

epochs = df['epoch']

# Subplot 1: Losses
ax1.plot(epochs, df['train/box_loss'], label='Train Box Loss', color='#2563EB', lw=2)
ax1.plot(epochs, df['val/box_loss'], label='Val Box Loss', color='#3B82F6', lw=1.5, linestyle='--')
ax1.plot(epochs, df['train/cls_loss'], label='Train Class Loss', color='#DC2626', lw=2)
ax1.plot(epochs, df['val/cls_loss'], label='Val Class Loss', color='#EF4444', lw=1.5, linestyle='--')
ax1.set_title('Bounding Box & Classification Loss Convergence (100 Epochs)', fontsize=11, fontweight='bold', pad=10)
ax1.set_xlabel('Epoch', fontsize=9.5)
ax1.set_ylabel('Loss Value', fontsize=9.5)
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.legend(loc='upper right', frameon=True, fontsize=8.5)

# Subplot 2: DFL Loss
ax2.plot(epochs, df['train/dfl_loss'], label='Train DFL Loss', color='#7C3AED', lw=2)
ax2.plot(epochs, df['val/dfl_loss'], label='Val DFL Loss', color='#A855F7', lw=1.5, linestyle='--')
ax2.set_title('Distribution Focal Loss (DFL) Convergence', fontsize=11, fontweight='bold', pad=10)
ax2.set_xlabel('Epoch', fontsize=9.5)
ax2.set_ylabel('DFL Loss', fontsize=9.5)
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend(loc='upper right', frameon=True, fontsize=8.5)

# Subplot 3: Precision & Recall Progression
ax3.plot(epochs, df['metrics/precision(B)'], label='Validation Precision', color='#059669', lw=2)
ax3.plot(epochs, df['metrics/recall(B)'], label='Validation Recall', color='#0284C7', lw=2)
ax3.set_title('Validation Precision & Recall vs. Epochs', fontsize=11, fontweight='bold', pad=10)
ax3.set_xlabel('Epoch', fontsize=9.5)
ax3.set_ylabel('Metric Score (0 - 1.0)', fontsize=9.5)
ax3.set_ylim(0.5, 1.02)
ax3.grid(True, linestyle=':', alpha=0.6)
ax3.legend(loc='lower right', frameon=True, fontsize=8.5)

# Subplot 4: mAP50 & mAP50-95 Progression
ax4.plot(epochs, df['metrics/mAP50(B)'], label='mAP@50 (Peak: 0.976)', color='#D97706', lw=2.5)
ax4.plot(epochs, df['metrics/mAP50-95(B)'], label='mAP@50:95 (Peak: 0.768)', color='#EA580C', lw=2)
ax4.axhline(0.9946, color='#15803D', linestyle=':', lw=1.5, label='Final Test Set mAP@50 (0.9946)')
ax4.set_title('Validation Mean Average Precision (mAP@50 & mAP@50:95)', fontsize=11, fontweight='bold', pad=10)
ax4.set_xlabel('Epoch', fontsize=9.5)
ax4.set_ylabel('mAP Value', fontsize=9.5)
ax4.set_ylim(0.3, 1.02)
ax4.grid(True, linestyle=':', alpha=0.6)
ax4.legend(loc='lower right', frameon=True, fontsize=8.5)

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "fig5_training_curves.png"), dpi=300)
plt.close(fig)
print("Saved fig5_training_curves.png")

# -------------------------------------------------------------
# FIGURE 6: Styled Confusion Matrix Heatmap
# -------------------------------------------------------------
print("Generating Figure 6: Styled Confusion Matrix Heatmap...")
fig, ax = plt.subplots(figsize=(8, 7), dpi=300)

classes = ['Front', 'Rear', 'Side', 'Background']
cm_matrix = np.array([
    [258, 0, 0, 7],     # True Front: 258 front, 7 bg (missed)
    [0, 88, 0, 0],      # True Rear: 88 rear, 0 error
    [0, 0, 134, 0],     # True Side: 134 side, 0 error
    [29, 17, 48, 0]     # True Background: 29 FP front, 17 FP rear, 48 FP side
])

im = ax.imshow(cm_matrix, cmap='Blues', interpolation='nearest')

# Add values to cells
for i in range(4):
    for j in range(4):
        val = cm_matrix[i, j]
        color = 'white' if val > 100 else 'black'
        fontweight = 'bold' if val > 0 else 'normal'
        ax.text(j, i, f"{val}", ha='center', va='center', color=color, fontsize=12, fontweight=fontweight)

ax.set_xticks(range(4))
ax.set_yticks(range(4))
ax.set_xticklabels(['Pred Front', 'Pred Rear', 'Pred Side', 'Background'], fontsize=10, fontweight='bold')
ax.set_yticklabels(['True Front', 'True Rear', 'True Side', 'Background'], fontsize=10, fontweight='bold')
ax.set_title('Test Set Confusion Matrix (Benchmark: 487 Ground Truth Objects)', fontsize=12, fontweight='bold', pad=15)
ax.set_xlabel('Predicted Class / Detection Status', fontsize=10.5, labelpad=10)
ax.set_ylabel('Ground Truth Class', fontsize=10.5, labelpad=10)

cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label('Target Count', fontsize=10)

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "fig6_confusion_matrix_styled.png"), dpi=300)
plt.close(fig)
print("Saved fig6_confusion_matrix_styled.png")

# -------------------------------------------------------------
# FIGURE 7: Class-wise Performance Breakdown & Failure Modes
# -------------------------------------------------------------
print("Generating Figure 7: Class Performance & Failure Modes...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=300)

# Left: Bar chart of metrics
class_names = ['Front View', 'Rear View', 'Side View', 'Overall / Mean']
ap50_vals = [98.99, 99.84, 99.55, 99.46]
prec_vals = [98.43, 100.00, 95.65, 98.03]
rec_vals = [94.72, 100.00, 98.51, 97.74]
f1_vals = [96.54, 100.00, 97.06, 97.87]

x = np.arange(len(class_names))
width = 0.2

ax1.bar(x - 1.5*width, ap50_vals, width, label='AP@50 (%)', color='#2563EB')
ax1.bar(x - 0.5*width, prec_vals, width, label='Precision (%)', color='#16A34A')
ax1.bar(x + 0.5*width, rec_vals, width, label='Recall (%)', color='#D97706')
ax1.bar(x + 1.5*width, f1_vals, width, label='F1-Score (%)', color='#9333EA')

ax1.set_xticks(x)
ax1.set_xticklabels(class_names, fontsize=10, fontweight='bold')
ax1.set_ylim(85, 105)
ax1.set_ylabel('Performance Score (%)', fontsize=10.5, fontweight='bold')
ax1.set_title('Per-Class Vision Perception Metrics Breakdown', fontsize=12, fontweight='bold', pad=12)
ax1.grid(True, linestyle=':', alpha=0.6, axis='y')
ax1.legend(loc='lower left', fontsize=9, frameon=True)

# Add text labels on top of bars
for i in range(len(class_names)):
    ax1.text(x[i] - 1.5*width, ap50_vals[i] + 0.6, f"{ap50_vals[i]:.1f}%", ha='center', fontsize=7.5, fontweight='bold', color='#1E40AF')
    ax1.text(x[i] + 1.5*width, f1_vals[i] + 0.6, f"{f1_vals[i]:.1f}%", ha='center', fontsize=7.5, fontweight='bold', color='#6B21A8')

# Right: Failure Mode Distribution
fail_codes = ['Missed Front', 'Missed Side', 'Missed Rear', 'Front/Side Confusion', 'Rear/Side Confusion', 'False Train Detections', 'Low Confidence Detections']
fail_counts = [6, 0, 0, 1, 0, 9, 18]
colors = ['#EF4444', '#10B981', '#10B981', '#F59E0B', '#10B981', '#F97316', '#64748B']

bars = ax2.barh(fail_codes, fail_counts, color=colors, height=0.6)
ax2.set_xlabel('Observed Failure Instance Count', fontsize=10.5, fontweight='bold')
ax2.set_title('Detailed Failure Mode Analysis (Total Failures: 34)', fontsize=12, fontweight='bold', pad=12)
ax2.grid(True, linestyle=':', alpha=0.6, axis='x')

for bar in bars:
    w = bar.get_width()
    ax2.text(w + 0.4, bar.get_y() + bar.get_height()/2, f"{int(w)}", ha='left', va='center', fontsize=9.5, fontweight='bold')

ax2.set_xlim(0, 22)

plt.tight_layout()
fig.savefig(os.path.join(output_dir, "fig7_class_performance_and_failures.png"), dpi=300)
plt.close(fig)
print("Saved fig7_class_performance_and_failures.png")

print("All publication figures successfully created in results/figures/")
