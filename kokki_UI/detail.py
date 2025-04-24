import tkinter as tk
from tkinter import font

root = tk.Tk()

font_title = font.Font(family="ＭＳ ゴシック", size=50)
font_title2 = font.Font(family="ＭＳ ゴシック", size=30)
font_subject = font.Font(family="ＭＳ ゴシック", size=20)

canvas = tk.Canvas(root, width=800, height=600, bg="white")

canvas.create_text(420, 70, text="にほんについて", font=font_title, fill="black")
sushi_pass="image/sushi.jpg"
canvas.create_text(420, 70, text="お寿司（すし）やおにぎりが大好きな、ごはんの国だよ。", font=font_subject, fill="black")
canvas.create_image(10,50,image=sushi_pass,anchor=tk.CENTER)
canvas.create_text(39, 59, text="富士山（ふじさん）という大きな山がぽっこりそびえているよ。", font=font_subject, fill="black")
canvas.create_image(40, 55,  image="image/fuji.jpg",anchor=tk.CENTER)
canvas.create_text(89, 75, text="春には桜（さくら）がたくさん咲（さ）いて、ピンクの景色（けしき）だよ。", font=font_subject, fill="black")
canvas.create_image(566, 56, image="image/Japan_town.jpg",anchor=tk.CENTER)

canvas.pack()

root.mainloop()