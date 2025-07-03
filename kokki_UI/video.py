import tkinter as tk
from tkvideo import tkvideo

root = tk.Tk()
root.title("Tkinter Video Player")

root.geometry("800x600")

# ここで tk.Label() を使って label ウィジェットを作成します
label = tk.Label(root)
label.pack(expand=True, fill="both") # ウィンドウに配置

video_path = "video_test.mp4" # 動画ファイルのパス

# tkvideo オブジェクトを作成し、作成した label を渡します
player = tkvideo(video_path, label, loop = 1) # loop=1でループ再生、hz=25でフレームレートを指定

# 再生を開始
player.play()

root.mainloop()