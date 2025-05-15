import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk

root = tk.Tk()

# フォント設定
font_title = font.Font(family="ＭＳ ゴシック", size=50)
font_subject = font.Font(family="ＭＳ ゴシック", size=18)

canvas = tk.Canvas(root, width=900, height=600, bg="white")

# 国のデータ（画像ファイル・説明文）
countries = {
    "Japan":[
        {
            "name": "にほん",
            "image": "image/sushi.jpg",
            "text": "お寿司（すし）\nやおにぎりが\n大好きな、\nごはんの国だよ。"
        },
        {
            "name": "にほん（富士山）",
            "image": "image/fuji.jpg",
            "text": "富士山（ふじさん）\nという大きな山が\nぽっこり\nそびえているよ。"
        },
        {
            "name": "にほん（春）",
            "image": "image/Japan_town.jpg",
            "text": "春には桜（さくら）\nがたくさん咲（さ）\nいて、ピンクの景色\n（けしき）だよ。"
        },
    ],
    # 他の国を追加したければここに辞書を追加！
    "Sweden":[
        {
            "name": "スウェーデン",
            "image": "image/オーロラ.jpg",
            "text": "オーロラが\n見（み）られる、\n星空（ほしぞら）が\nきれいな国だよ。"
        },
        {
            "name": "スウェーデン（動物）",
            "image": "image/鹿.jpg",
            "text": "森（もり）で\nクマやトナカイに\n会（あ）えるかも\nしれないよ。"
        },
        {
            "name": "スウェーデン（イケア）",
            "image": "image/IKEA.jpg",
            "text": "イケア（IKEA）の\n家具（かぐ）を\nつくる、デザインの国だよ。"
        },
    ],
    "Estonia":[
        {
            "name": "エストニア",
            "image": "image/森.jpg",
            "text": "森（もり）と\n湖（みずうみ）が\nたくさんある、\n自然（しぜん）あふれる\n国だよ。"
        },
        {
            "name": "エストニア（お菓子）",
            "image": "image/カレフ.jpg",
            "text": "かわいい\nお菓子（おかし）\n「カレフ」を楽しめるよ。"
        },
        {
            "name": "エストニア（教育）",
            "image": "image/図書館.jpg",
            "text": "デジタル大国（たいこく）\nで、学校の宿題（しゅくだい）\nもインターネットでできるよ。"
        },
    ],
    "Holland":[
        {
            "name": "オランダ",
            "image": "image/チューリップ.jpg",
            "text": "風車とチューリップ\nがいっぱいの、\nカラフルなお花の国だよ。"
        },
        {
            "name": "オランダ（自転車）",
            "image": "image/自転車.jpg",
            "text": "自転車に乗る人が\n多くて、どこへでも\nペダルでおさんぽできるよ。"
        },
        {
            "name": "オランダ（運河）",
            "image": "image/街並み.jpg",
            "text": "運河（うんが）に\n小舟（こぶね）を浮かべて、\n水の上をわたれるよ。"
        },
    ],
    "Germany":[
        {
            "name": "ドイツ",
            "image": "image/城.jpg",
            "text": "お城（しろ）が\n山（やま）や川（かわ）\nのそばにたくさんあるよ。"
        },
        {
            "name": "ドイツ（食べ物）",
            "image": "image/ソーセージ.jpg",
            "text": "ソーセージや\nプレッツェルを\nもぐもぐおいしく\n食（た）べられるよ。"
        },
        {
            "name": "ドイツ（街）",
            "image": "image/ド街並み.jpg",
            "text": "森の中を走る\n汽車（きしゃ）や、\n大きなクリスマスマーケット\nがあるよ。"
        },
    ],
    "Denmark":[
        {
            "name": "デンマーク",
            "image": "image/人魚.jpg",
            "text": "おとぎ話（ばなし）\nの人魚姫（ひめ）や\nお城（しろ）がある、\nメルヘンの国だよ。"
        },
        {
            "name": "デンマーク（自転車）",
            "image": "image/お城.jpg",
            "text": "自転車（じてんしゃ）\nで町（まち）\nを走（はし）る\nのがとっても\n上手（じょうず）だよ。"
        },
        {
            "name": "デンマーク（レゴ）",
            "image": "image/レゴ.jpg",
            "text": "レゴの本社（ほんしゃ）\nがあって、ブロックで\n遊（あそ）ぶのが大好きだよ。"
        },
    ]
}



# 画像の参照保持用リスト
image_refs = []

def draw_country_group(flag):
    canvas.delete("all")  # 前の表示を消す
    image_refs.clear()


     # 国のデータ（略）

    flag_bg_path = f"image/{flag}.png"

    try:
        flag_bg_img = Image.open(flag_bg_path).resize((800,600)).convert("RGBA")
        alpha = flag_bg_img.split()[3].point(lambda p: p * 0.4)
        flag_bg_img.putalpha(alpha)
        flag_bg_tk = ImageTk.PhotoImage(flag_bg_img)
        image_refs.append(flag_bg_tk)
        print("読み込んだ")

        # キャンバスに背景として描画（←削除の後に描画されるのでOK）
        canvas.create_image(400, 300, image=flag_bg_tk, anchor=tk.CENTER)
    except Exception as e:
        print(f"国旗画像の読み込み失敗: {e}")

    title_text = countries[flag][0]["name"]+"について"
    canvas.create_text(450, 50, text=title_text, font=font_title, fill="black")

    countriy_list = countries[flag]
    
    start_x = 150
    space_x = 300
    image_y = 250
    text_y = 430

    for i, country in enumerate(countriy_list):
        x = start_x + i * space_x
        img = ImageTk.PhotoImage(Image.open(country["image"]).resize((200, 200)))
        image_refs.append(img)
        canvas.create_image(x, image_y, image=img, anchor=tk.CENTER)
        canvas.create_text(x, text_y, text=country["text"], font=font_subject, fill="black")

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
