# Legooooooo

car_game.pyがメインのプログラム　スマホの画像とかでテストして

家の方が認識しやすい

物体が検出できると、初期画面のボタンの横に透過した画像が出る

### **実行環境セッティング**

python v3.10.11（まあこれならとりあえず動いたよバージョン）

python -m venv .venv #仮想環境の用意
.venv\Scripts\activate      # Windowsでの仮想環境の起動（ファイルパス要チェック）、実行するとターミナルの様子が変わるはず
pip install pillow opencv-python numpy ultralytics rembg onnxruntime#必須ライブラリ、依存環境のインストール

pyglet　　　も増えました

ffmpegが必要なので少し古めのバージョンを取ってきてください

ffmpeg version 6.0-full_build-www.gyan.dev Copyright (c) 2000-2023 the FFmpeg developers
これなら動きました

# 現状AIinブランチで動かします
