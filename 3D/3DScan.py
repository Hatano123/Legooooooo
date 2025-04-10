import cv2
import numpy as np
import open3d as o3d
import os

# === 1. カメラから画像取得 ===
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("カメラが開けませんでした")
    exit()

ret, frame = cap.read()
cap.release()

if not ret:
    print("画像取得に失敗しました")
    exit()

cv2.imwrite("capture.png", frame)
print("画像を保存しました: capture.png")

# === 2. グレースケール画像から深度マップっぽいデータを生成（超簡易）===
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
gray = cv2.GaussianBlur(gray, (5, 5), 0)
depth = gray.astype(np.float32)

# === 3. 疑似点群生成 ===
h, w = depth.shape
fx, fy = 500, 500
cx, cy = w // 2, h // 2

points = []
for v in range(h):
    for u in range(w):
        z = depth[v, u] / 255.0  # 正規化
        x = (u - cx) * z / fx
        y = (v - cy) * z / fy
        points.append([x, y, z])

pcd = o3d.geometry.PointCloud()

if pcd.is_empty():
    print("⚠️ 点群が空です！")
    
pcd.points = o3d.utility.Vector3dVector(np.array(points))

# === 4. 点群からメッシュ化 ===
pcd = pcd.voxel_down_sample(voxel_size=0.005)
pcd.estimate_normals()
mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=8)

# === 5. STLとして保存 ===
o3d.io.write_triangle_mesh("output.stl", mesh)
print("STLファイルを書き出しました: output.stl")
