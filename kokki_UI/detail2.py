import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk
import os # ファイルの存在確認のために追加

class CountryDetailApp:
    def __init__(self, root):
        self.root = root
        self.root.title("国の説明")

        # --- フォントの定義 ---
        try:
            self.font_title = font.Font(family="Yu Gothic", size=30, weight="bold")
            self.font_subject = font.Font(family="Yu Gothic", size=16)
        except tk.TclError:
            # Yu Gothic がない場合のフォールバック
            try:
                self.font_title = font.Font(family="Meiryo", size=30, weight="bold")
                self.font_subject = font.Font(family="Meiryo", size=16)
            except tk.TclError:
                print("Japanese fonts (Yu Gothic/Meiryo) not found, using Tk default.")
                self.font_title = font.Font(size=30, weight="bold")
                self.font_subject = font.Font(size=16)

        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack()

        # 画像参照を保持するためのリスト (ガベージコレクション防止)
        self.image_refs = []
        self.background_flag_tk = None # 背景の国旗画像参照用

        # --- 国のデータ構造化 ---
        self.countries_data = {
            "Japan": {
                "name_jp": "日本",
                "details": [
                    {
                        "image": "image/sushi.jpg",
                        "text": "お寿司（すし）やおにぎりが大好きな、ごはんの国だよ。",
                    },
                    {
                        "image": "image/fuji.jpg",
                        "text": "富士山（ふじさん）という大きな山がぽっこりそびえているよ。",
                    },
                    {
                        "image": "image/Japan_town.jpg",
                        "text": "春には桜（さくら）がたくさん咲（さ）いて、\nピンクの景色（けしき）だよ。",
                    },
                ]
            },
            "Sweden": {
                "name_jp": "スウェーデン",
                "details": [
                    {
                        "image": "image/オーロラ.jpg",
                        "text": "オーロラが見（み）られる、星空（ほしぞら）がきれいな国だよ。",
                    },
                    {
                        "image": "image/鹿.jpg",
                        "text": "森（もり）でクマやトナカイに会（あ）えるかもしれないよ。",
                    },
                    {
                        "image": "image/IKEA.jpg",
                        "text": "イケア（IKEA）の家具（かぐ）をつくる、デザインの国だよ。",
                    },
                ]
            },
            "Estonia": {
                "name_jp": "エストニア",
                "details": [
                    {
                        "image": "image/森.jpg",
                        "text": "森（もり）と湖（みずうみ）がたくさんある、\n自然（しぜん）あふれる国だよ。",
                    },
                    {
                        "image": "image/カレフ.jpg",
                        "text": "かわいいお菓子（おかし）「カレフ」を楽しめるよ。",
                    },
                    {
                        "image": "image/図書館.jpg",
                        "text": "デジタル大国（たいこく）で、\n学校の宿題（しゅくだい）もインターネットでできるよ。",
                    },
                ]
            },
            "Oranda": {
                "name_jp": "オランダ",
                "details": [
                    {
                        "image": "image/チューリップ.jpg",
                        "text": "風車とチューリップがいっぱいの、カラフルなお花の国だよ。",
                    },
                    {
                        "image": "image/自転車.jpg",
                        "text": "自転車に乗る人が多くて、どこへでもペダルでおさんぽできるよ。",
                    },
                    {
                        "image": "image/街並み.jpg",
                        "text": "運河（うんが）に小舟（こぶね）を浮かべて、水の上をわたれるよ。",
                    },
                ]
            },
            "Germany": {
                "name_jp": "ドイツ",
                "details": [
                    {
                        "image": "image/城.jpg",
                        "text": "お城（しろ）が山（やま）や川（かわ）のそばにたくさんあるよ。",
                    },
                    {
                        "image": "image/ソーセージ.jpg",
                        "text": "ソーセージやプレッツェルをもぐもぐおいしく食（た）べられるよ。",
                    },
                    {
                        "image": "image/ド街並み.jpg",
                        "text": "森の中を走る汽車（きしゃ）や、\n大きなクリスマスマーケットがあるよ。",
                    },
                ]
            },
            "Denmark": {
                "name_jp": "デンマーク",
                "details": [
                    {
                        "image": "image/人魚.jpg",
                        "text": "おとぎ話（ばなし）の人魚姫（ひめ）や\nお城（しろ）がある、メルヘンの国だよ。",
                    },
                    {
                        "image": "image/お城.jpg",
                        "text": "自転車（じてんしゃ）で町（まち）を走（はし）るのが\nとっても上手（じょうず）だよ。",
                    },
                    {
                        "image": "image/レゴ.jpg",
                        "text": "レゴの本社（ほんしゃ）があって、\nブロックで遊（あそ）ぶのが大好きだよ。",
                    },
                ]
            },
        }

        self.current_country_key = list(self.countries_data.keys())[0] # 初期表示の国 (例: Japan)
        self.current_detail_index = 0 # 各国の説明のインデックス

        self.create_widgets()
        self.update_display()

    def create_widgets(self):
        # 背景国旗用のプレースホルダー。毎回更新されるのでIDを持たせる
        self.background_flag_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=None)
        self.canvas.lower(self.background_flag_id) # 最背面に配置

        # メインタイトル
        self.title_text_id = self.canvas.create_text(400, 50, text="", font=self.font_title, fill="black")

        # 画像表示エリア
        self.image_display_id = self.canvas.create_image(400, 250, anchor=tk.CENTER, image=None)

        # 説明テキストエリア
        self.description_text_id = self.canvas.create_text(400, 450, text="", font=self.font_subject, fill="black", justify=tk.CENTER)

        # 戻るボタン
        self.prev_button_rect_id = self.canvas.create_rectangle(100, 520, 250, 570, fill="lightblue", outline="black", tags="prev_detail")
        self.prev_button_text_id = self.canvas.create_text(175, 545, text="← もどる", font=self.font_subject, fill="black", tags="prev_detail")

        # 進むボタン
        self.next_button_rect_id = self.canvas.create_rectangle(550, 520, 700, 570, fill="lightblue", outline="black", tags="next_detail")
        self.next_button_text_id = self.canvas.create_text(625, 545, text="すすむ →", font=self.font_subject, fill="black", tags="next_detail")

        # 国選択ボタン
        x_start = 20
        y_start = 5
        button_width = 80
        button_height = 30
        padding = 10
        
        for i, country_key in enumerate(self.countries_data.keys()):
            x1 = x_start + i * (button_width + padding)
            y1 = y_start
            x2 = x1 + button_width
            y2 = y1 + button_height
            
            # 各国のボタンを配置
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="lightgreen", outline="black", tags=(f"select_{country_key}", "country_button"))
            self.canvas.create_text((x1+x2)/2, (y1+y2)/2, text=self.countries_data[country_key]["name_jp"], font=("", 10), fill="black", tags=(f"select_{country_key}", "country_button_text"))

        # イベントバインディング
        self.canvas.bind("<Button-1>", self.on_click)

    def on_click(self, event):
        x, y = event.x, event.y
        items = self.canvas.find_overlapping(x, y, x, y)
        if not items:
            return

        # クリックされたアイテムのタグを取得
        clicked_tags = self.canvas.gettags(items[-1]) # 最も手前のアイテムのタグ

        if "prev_detail" in clicked_tags:
            self.current_detail_index -= 1
            if self.current_detail_index < 0:
                self.current_detail_index = len(self.countries_data[self.current_country_key]["details"]) - 1
            self.update_display()
        elif "next_detail" in clicked_tags:
            self.current_detail_index += 1
            if self.current_detail_index >= len(self.countries_data[self.current_country_key]["details"]):
                self.current_detail_index = 0
            self.update_display()
        
        # 国選択ボタンの処理
        for country_key in self.countries_data.keys():
            if f"select_{country_key}" in clicked_tags:
                if self.current_country_key != country_key: # 同じ国を再選択しない
                    self.current_country_key = country_key
                    self.current_detail_index = 0 # 国が変わったら最初の説明に戻る
                    self.update_display()
                break # 一致するボタンが見つかったらループを抜ける

    def update_display(self):
        # 画像参照を保持するためのリストをクリア
        self.image_refs.clear() # これにより前回の画像がGCされる

        country_key = self.current_country_key
        country_data = self.countries_data[country_key]
        detail = country_data["details"][self.current_detail_index]

        # --- 背景国旗の表示 ---
        flag_bg_path = f"image/{country_key}.png" # 国旗画像パスの例。ファイル構成に合わせて変えてください。
        if not os.path.exists(flag_bg_path):
             # .jpg も試す
            flag_bg_path = f"image/{country_key}.jpg"

        if os.path.exists(flag_bg_path):
            try:
                flag_bg_img = Image.open(flag_bg_path).resize((800,600), Image.Resampling.LANCZOS).convert("RGBA")
                # 透明度を下げる（アルファ値を調整）
                alpha = flag_bg_img.split()[3].point(lambda p: p * 0.4) # 0.4は透明度調整。0=透明,1=不透明
                flag_bg_img.putalpha(alpha)

                self.background_flag_tk = ImageTk.PhotoImage(flag_bg_img)
                self.image_refs.append(self.background_flag_tk) # 参照を保持

                # 既存の背景画像アイテムを更新
                self.canvas.itemconfig(self.background_flag_id, image=self.background_flag_tk)
                self.canvas.lower(self.background_flag_id) # Canvasの一番下に移動
            except Exception as e:
                print(f"背景国旗画像の読み込みまたは加工失敗: {flag_bg_path} - {e}")
                self.canvas.itemconfig(self.background_flag_id, image=None) # エラー時は画像なし
        else:
            print(f"背景国旗画像ファイルが見つかりません: {flag_bg_path}")
            self.canvas.itemconfig(self.background_flag_id, image=None) # ファイルがない場合は画像なし
        # --- 背景国旗の表示ここまで ---

        # タイトル更新
        self.canvas.itemconfig(self.title_text_id, text=f"{country_data['name_jp']}について")

        # 画像更新
        image_path = detail["image"]
        if os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                img.thumbnail((300, 300), Image.Resampling.LANCZOS) # 画像サイズ調整
                img_tk = ImageTk.PhotoImage(img)
                self.image_refs.append(img_tk) # 新しい参照を保持
                self.canvas.itemconfig(self.image_display_id, image=img_tk)
            except Exception as e:
                print(f"画像読み込みエラー: {image_path} - {e}")
                self.canvas.itemconfig(self.image_display_id, image=None) # エラー時は画像なし
        else:
            print(f"画像ファイルが見つかりません: {image_path}")
            self.canvas.itemconfig(self.image_display_id, image=None) # ファイルがない場合は画像なし

        # 説明テキスト更新
        self.canvas.itemconfig(self.description_text_id, text=detail["text"])

        # 各要素の描画順序を調整 (背景が一番下、次に文字、画像、ボタン)
        self.canvas.tag_raise(self.title_text_id)
        self.canvas.tag_raise(self.image_display_id)
        self.canvas.tag_raise(self.description_text_id)
        self.canvas.tag_raise("prev_detail")
        self.canvas.tag_raise("next_detail")
        self.canvas.tag_raise("country_button") # 国選択ボタンも前面に
        self.canvas.tag_raise("country_button_text")


if __name__ == "__main__":
    root = tk.Tk()
    app = CountryDetailApp(root)
    root.mainloop()