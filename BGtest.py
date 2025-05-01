import torch
import numpy as np
import cv2
from segment_anything import sam_model_registry, SamPredictor

# モデルのパスとタイプ
MODEL_PATH = "../sam_vit_l_0b3195.pth"  # ダウンロードしたモデルファイル
MODEL_TYPE = "vit_l"          # モデルの種類: vit_b, vit_l, vit_h

# 入力画像と出力画像のパス
INPUT_IMAGE_PATH = "car_0024.jpg"
OUTPUT_IMAGE_PATH = "output_image.png"

# モデルをロード
device = "cuda" if torch.cuda.is_available() else "cpu"
sam = sam_model_registry[MODEL_TYPE](checkpoint=MODEL_PATH)
sam.to(device)

# 画像をロード
image = cv2.imread(INPUT_IMAGE_PATH)
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # OpenCVはBGRなのでRGBに変換

# SAMのPredictorを初期化
predictor = SamPredictor(sam)
predictor.set_image(image)

# 中央付近のポイントを選択 (例: 中心の手動選択)
image_height, image_width, _ = image.shape
input_point = np.array([[image_width // 2, image_height // 2]])  # 画像中心
input_label = np.array([1])  # 前景ラベル

# マスクを予測
masks, _, _ = predictor.predict(point_coords=input_point, point_labels=input_label, multimask_output=False)

# 最初のマスクを使用
mask = masks[0]

# 背景を透明にする
output_image = np.zeros_like(image, dtype=np.uint8)
output_image[mask] = image[mask]  # マスクされた部分のみ保持

# 保存 (背景を透明化したPNGとして保存)
output_image = cv2.cvtColor(output_image, cv2.COLOR_RGB2BGRA)  # RGBA形式に変換
output_image[:, :, 3] = mask.astype(np.uint8) * 255  # アルファチャネル設定
cv2.imwrite(OUTPUT_IMAGE_PATH, output_image)

print(f"背景削除完了: {OUTPUT_IMAGE_PATH}")
