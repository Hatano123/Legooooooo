import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk

def resize_image(image, max_size=(200, 200)):
    """画像を指定したサイズに収まるようにリサイズし、アスペクト比を保持します"""
    ratio = min(max_size[0] / image.size[0], max_size[1] / image.size[1])
    new_size = tuple(int(dim * ratio) for dim in image.size)
    return image.resize(new_size, Image.Resampling.LANCZOS)

root = tk.Tk()

font_title = font.Font(family="ＭＳ ゴシック", size=50)
font_subject = font.Font(family="ＭＳ ゴシック", size=15)  # フォントサイズを小さく

canvas = tk.Canvas(root, width=800, height=600, bg="white")

canvas.create_text(420, 70, text="にほんについて", font=font_title, fill="black")

# 画像と説明文の配置（左）
sushi_img = Image.open("image/sushi.jpg")
sushi_img = resize_image(sushi_img)
sushi_photo = ImageTk.PhotoImage(sushi_img)
canvas.create_image(100, 200, image=sushi_photo, anchor=tk.CENTER)
canvas.create_text(100, 320, text="お寿司（すし）やおにぎりが\n大好きな、ごはんの国だよ。", 
                  font=font_subject, fill="black", width=200, justify=tk.CENTER)

# 画像と説明文の配置（中央）
fuji_img = Image.open("image/fuji.jpg")
fuji_img = resize_image(fuji_img)
fuji_photo = ImageTk.PhotoImage(fuji_img)
canvas.create_image(400, 200, image=fuji_photo, anchor=tk.CENTER)
canvas.create_text(400, 320, text="富士山（ふじさん）という\n大きな山がぽっこり\nそびえているよ。", 
                  font=font_subject, fill="black", width=200, justify=tk.CENTER)

# 画像と説明文の配置（右）
japan_img = Image.open("image/Japan_town.jpg")
japan_img = resize_image(japan_img)
japan_photo = ImageTk.PhotoImage(japan_img)
canvas.create_image(700, 200, image=japan_photo, anchor=tk.CENTER)
canvas.create_text(700, 320, text="春には桜（さくら）がたくさん\n咲（さ）いて、ピンクの\n景色（けしき）だよ。", 
                  font=font_subject, fill="black", width=200, justify=tk.CENTER)

canvas.pack()

# 画像の参照を保持
root.sushi_photo = sushi_photo
root.fuji_photo = fuji_photo
root.japan_photo = japan_photo

root.mainloop()