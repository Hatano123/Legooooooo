import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk
import random

def go_to_country_info_screen(country):
    root = tk.Tk()

    # フォント設定
    font_title = font.Font(family="ＭＳ ゴシック", size=50)
    font_subject = font.Font(family="ＭＳ ゴシック", size=20)

    canvas = tk.Canvas(root, width=900, height=600, bg="white")

    # 国のデータ（画像ファイル・説明文）
    countries = {
        "Japan":[
            {
                "name": "にほん",
                "image": "image/sushi.jpg",
                "text": "お寿司（すし）やおにぎりが大好きな、ごはんの国だよ。"
            },
            {
                "name": "にほん（富士山）",
                "image": "image/fuji.jpg",
                "text": "富士山（ふじさん）という大きな山がぽっこりそびえているよ。"
            },
            {
                "name": "にほん（春）",
                "image": "image/Japan_town.jpg",
                "text": "春には桜（さくら）がたくさん咲（さ）いて、\nピンクの景色（けしき）だよ。"
            },
        ],
        # 他の国を追加したければここに辞書を追加！
        "Sweden":[
            {
                "name": "スウェーデン",
                "image": "image/オーロラ.jpg",
                "text": "オーロラが見（み）られる、星空（ほしぞら）がきれいな国だよ。"
            },
            {
                "name": "スウェーデン（動物）",
                "image": "image/鹿.jpg",
                "text": "森（もり）でクマやトナカイに会（あ）えるかもしれないよ。"
            },
            {
                "name": "スウェーデン（イケア）",
                "image": "image/IKEA.jpg",
                "text": "イケア（IKEA）の家具（かぐ）をつくる、デザインの国だよ。"
            },
        ],
        "Estonia":[
            {
                "name": "エストニア",
                "image": "image/森.jpg",
                "text": "森（もり）と湖（みずうみ）がたくさんある、\n自然（しぜん）あふれる国だよ。"
            },
            {
                "name": "エストニア（お菓子）",
                "image": "image/カレフ.jpg",
                "text": "かわいいお菓子（おかし）「カレフ」を楽しめるよ。"
            },
            {
                "name": "エストニア（教育）",
                "image": "image/図書館.jpg",
                "text": "デジタル大国（たいこく）で、\n学校の宿題（しゅくだい）もインターネットでできるよ。"
            },
        ],
        "Holland":[
            {
                "name": "オランダ",
                "image": "image/チューリップ.jpg",
                "text": "風車とチューリップがいっぱいの、カラフルなお花の国だよ。"
            },
            {
                "name": "オランダ（自転車）",
                "image": "image/自転車.jpg",
                "text": "自転車に乗る人が多くて、どこへでもペダルでおさんぽできるよ。"
            },
            {
                "name": "オランダ（運河）",
                "image": "image/街並み.jpg",
                "text": "運河（うんが）に小舟（こぶね）を浮かべて、水の上をわたれるよ。"
            },
        ],
        "Germany":[
            {
                "name": "ドイツ",
                "image": "image/城.jpg",
                "text": "お城（しろ）が山（やま）や川（かわ）のそばにたくさんあるよ。"
            },
            {
                "name": "ドイツ（食べ物）",
                "image": "image/ソーセージ.jpg",
                "text": "ソーセージやプレッツェルをもぐもぐおいしく食（た）べられるよ。"
            },
            {
                "name": "ドイツ（街）",
                "image": "image/ド街並み.jpg",
                "text": "森の中を走る汽車（きしゃ）や、\n大きなクリスマスマーケットがあるよ。"
            },
        ],
        "Denmark":[
            {
                "name": "デンマーク",
                "image": "image/人魚.jpg",
                "text": "おとぎ話（ばなし）の人魚姫（ひめ）や\nお城（しろ）がある、メルヘンの国だよ。"
            },
            {
                "name": "デンマーク（自転車）",
                "image": "image/お城.jpg",
                "text": "自転車（じてんしゃ）で町（まち）を走（はし）るのが\nとっても上手（じょうず）だよ。"
            },
            {
                "name": "デンマーク（レゴ）",
                "image": "image/レゴ.jpg",
                "text": "レゴの本社（ほんしゃ）があって、\nブロックで遊（あそ）ぶのが大好きだよ。"
            },
        ]
    }



    # 画像の参照保持用リスト
    image_refs = []

    def draw_country_group(flag):
        canvas.delete("all")  # 前の表示を消す
        image_refs.clear()

        selected_info = random.choice(countries[flag])

        title_text = countries[flag][0]["name"]+"について"
        canvas.create_text(450, 50, text=title_text, font=font_title, fill="black")

        img = Image.open(selected_info["image"]).resize((350,350))
        img_tk = ImageTk.PhotoImage(img)
        image_refs.append(img_tk)

        canvas.create_image(450, 300, image=img_tk, anchor=tk.CENTER)
        canvas.create_text(450, 530, text=selected_info["text"], font=font_subject, fill="black")


    canvas.pack()

    current_flag = "Japan"
# 初期表示
    draw_country_group(current_flag)

# ボタンで切り替え（お好みで）
    btn_japan = tk.Button(root, text="日本", command=lambda: draw_country_group("Japan"))
    btn_sweden = tk.Button(root, text="スウェーデン", command=lambda: draw_country_group("Sweden"))
    btn_estonia = tk.Button(root, text="エストニア", command=lambda: draw_country_group("Estonia"))
    btn_holland = tk.Button(root, text="オランダ", command=lambda: draw_country_group("Holland"))
    btn_germany = tk.Button(root, text="ドイツ", command=lambda: draw_country_group("Germany"))
    btn_denmark = tk.Button(root, text="デンマーク", command=lambda: draw_country_group("Denmark"))
    btn_japan.pack(side=tk.LEFT, padx=20)
    btn_sweden.pack(side=tk.LEFT, padx=20)
    btn_estonia.pack(side=tk.LEFT, padx=20)
    btn_holland.pack(side=tk.LEFT, padx=20)
    btn_germany.pack(side=tk.LEFT, padx=20)
    btn_denmark.pack(side=tk.LEFT, padx=20)


    root.mainloop()

go_to_country_info_screen("Japan")
