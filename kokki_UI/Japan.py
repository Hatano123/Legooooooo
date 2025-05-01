import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk  # Pillow ライブラリが必要

root = tk.Tk()

font_title = font.Font(family="ＭＳ ゴシック", size=50)
font_subject = font.Font(family="ＭＳ ゴシック", size=20)

canvas = tk.Canvas(root, width=800, height=600, bg="white")

# 画像の読み込み（PILでJPEGを読み込んでPhotoImageに変換）
sushi_img = ImageTk.PhotoImage(Image.open("image/sushi.jpg").resize((200,200)))
fuji_img = ImageTk.PhotoImage(Image.open("image/fuji.jpg").resize((200,200)))
town_img = ImageTk.PhotoImage(Image.open("image/Japan_town.jpg").resize((200,200)))


canvas.create_text(400, 70, text="にほんについて", font=font_title, fill="black")
canvas.create_text(150, 430, text="お寿司（すし）\nやおにぎりが\n大好きな、\nごはんの国だよ。", font=font_subject, fill="black")
canvas.create_image(150,250,image=sushi_img,anchor=tk.CENTER)
canvas.create_text(400, 430, text="富士山（ふじさん）\nという大きな山が\nぽっこり\nそびえているよ。", font=font_subject, fill="black")
canvas.create_image(400,250,image=fuji_img,anchor=tk.CENTER)
canvas.create_text(650, 430, text="春には桜（さくら）\nがたくさん咲（さ）\nいて、ピンクの景色\n（けしき）だよ。", font=font_subject, fill="black")
canvas.create_image(650,250,image=town_img,anchor=tk.CENTER)
canvas.pack()

# 画像が消えないように参照を保持
canvas.image_sushi = sushi_img
canvas.image_fuji = fuji_img
canvas.image_town = town_img

root.mainloop()