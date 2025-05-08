import tkinter as tk
from tkinter import messagebox, font
from PIL import Image, ImageTk, ImageFont
import cv2
import numpy as np
import os
from ultralytics import YOLO
from rembg import remove

from random_detail import go_to_country_info_screen



class BlockGameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Block Game")

        # Initial setup
        self.current_screen = "main"
        self.blocknumber = None
        self.sample_image_path = None
        self.last_frame = None
        self.frame_count = 0
        self.captured_images = {"Japan": None, "Sweden": None, "Estonia": None, "Holland": None, "Germany": None, "Denmark": None}  # Store captured images for house and cars
        self.capture = cv2.VideoCapture(1)

        if not self.capture.isOpened():
            messagebox.showerror("Error", "Cannot access the camera")
            root.destroy()

        # Load YOLO model
        self.model = YOLO('best.pt')

        # Output directory for processed images
        self.output_dir = "output_images"
        os.makedirs(self.output_dir, exist_ok=True)

        # Main canvas
        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack()

        # Load background image
        try:
            self.bg_image = Image.open("image/background.jpg")
            self.bg_image = self.bg_image.resize((800, 600))
            self.bg_tk = ImageTk.PhotoImage(self.bg_image)
        except Exception as e:
            print(f"Background image error: {e}")
            self.bg_tk = None

        # Draw the initial screen
        self.draw_main_screen()

        # Mouse click event
        self.canvas.bind("<Button-1>", self.mouse_event)

        # Frame update
        self.update_frame()

    def update_background_image(self):
    
        if self.captured_images["Japan"] and self.captured_images["Sweden"] and self.captured_images["Italy"] and self.captured_images["Russia"] and self.captured_images["Germany"] and self.captured_images["Denmark"]:
            background_path = "image/house_car_less.jpg"
        elif self.captured_images["Japan"]:
            background_path = "image/Japan_less.jpg"
        elif self.captured_images["Sweden"]:
            background_path = "image/Sweden_less.jpg"
        elif self.captured_images["Estonia"]:
            background_path = "image/Estonia_less.jpg"
        elif self.captured_images["Holland"]:
            background_path = "image/Holland_less.jpg"
        elif self.captured_images["Germany"]:
            background_path = "image/Germany_less.jpg"
        elif self.captured_images["Denmark"]:
            background_path = "image/Denmark_less.jpg"
        else:
            background_path = "image/background.jpg"  # 初期背景

        try:
            new_bg_image = Image.open(background_path)
            new_bg_image = new_bg_image.resize((800, 600))
            self.bg_tk = ImageTk.PhotoImage(new_bg_image)
        except Exception as e:
            print(f"Error updating background image: {e}")
            self.bg_tk = None


    def draw_main_screen(self):
        # 基準情報
        self.update_background_image()
        self.canvas.delete("all")
        self.current_screen = "main"

        # Draw background image
        if self.bg_tk:
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_tk)

        # Text
        self.canvas.create_text(400, 30, text="Legoooooo", font=("Helvetica", 24), fill="black")
        self.canvas.create_text(420, 70, text="こっきをつくろう！", font=font_subject, fill="black")
        self.canvas.create_text(420, 110, text="つくりたいくにをクリックしてね！", font=font_subject, fill="black")

        # Buttons and images
        # Japan button
        if self.captured_images["Japan"]:
            # Display captured house image
            Japan_image = Image.open(self.captured_images["Japan"])
            Japan_image = Japan_image.resize((300, 350))  # Match button size
            Japan_tk = ImageTk.PhotoImage(Japan_image)
            self.canvas.create_image(100, 100, anchor=tk.CENTER, image=Japan_tk)
            self.Japan_image_tk = Japan_tk  # Keep reference

            # Transparent button overlay
            self.canvas.create_rectangle(10, top_position1, 250, top_position2, fill="", outline="", tags="Japan")

        else:
            # Draw house button (visible if no image yet)
            self.canvas.create_rectangle(10, top_position1, 250, top_position2, fill="#90EE90", outline="black", stipple="gray50", tags="Japan")
            self.canvas.create_text(130, 220, text="にほん", font=font_title2, fill="black")

        # ロシア button 
        if self.captured_images["Sweden"]:
            # Display captured car image
            Sweden_image = Image.open(self.captured_images["Sweden"])
            Sweden_image = Sweden_image.resize((260, 120))  # Match button size
            Sweden_tk = ImageTk.PhotoImage(Sweden_image)
            self.canvas.create_image(370, 520, anchor=tk.CENTER, image=Sweden_tk)
            self.Sweden_image_tk = Sweden_tk  # Keep reference

            # Transparent button overlay
            self.canvas.create_rectangle(260, top_position1, 510, top_position2  , fill="", outline="", tags="Sweden")

        else:
            # Draw car button (visible if no image yet)
            self.canvas.create_rectangle( 260, top_position1, 510, top_position2 , fill="#90EE90", outline="black", stipple="gray50", tags="Sweden")
            self.canvas.create_text(385, 220, text="スウェーデン", font=font_title2, fill="black")

         # スウェーデン button
        if self.captured_images["Estonia"]:
            # Display captured car image
            Estonia_image = Image.open(self.captured_images["Estonia"])
            Estonia_image = Estonia_image.resize((260, 120))  # Match button size
            Estonia_tk = ImageTk.PhotoImage(Estonia_image)
            self.canvas.create_image(370, 520, anchor=tk.CENTER, image=Estonia_tk)
            self.Estonia_image_tk = Estonia_tk  # Keep reference

            # Transparent button overlay
            self.canvas.create_rectangle(520, top_position1, 770, top_position2, fill="", outline="", tags="Estonia")

        else:
            # Draw car button (visible if no image yet)
            self.canvas.create_rectangle(520, top_position1, 770, top_position2 , fill="#90EE90", outline="black", stipple="gray50", tags="Estonia")
            self.canvas.create_text(645, 220, text="エストニア", font=font_title2, fill="black")

         # イタリア button
        if self.captured_images["Holland"]:
            # Display captured car image
            Holland_image = Image.open(self.captured_images["Holland"])
            Holland_image = Holland_image.resize((260, 120))  # Match button size
            Holland_tk = ImageTk.PhotoImage(Holland_image)
            self.canvas.create_image(370, 520, anchor=tk.CENTER, image=Holland_tk)
            self.Holland_image_tk = Holland_tk  # Keep reference

            # Transparent button overlay
            self.canvas.create_rectangle(10, bottom_position1, 250, bottom_position2 , fill="", outline="", tags="Holland")

        else:
            # Draw car button (visible if no image yet)
            self.canvas.create_rectangle(10,
            bottom_position1, 250, bottom_position2 , fill="#90EE90", outline="black", stipple="gray50", tags="Holland")
            self.canvas.create_text(130, 380, text="オランダ", font=font_title2, fill="black")

         # ドイツ button
        if self.captured_images["Germany"]:
            # Display captured car image
            Germany_image = Image.open(self.captured_images["Germany"])
            Germany_image = Germany_image.resize((260, 120))  # Match button size
            Germany_tk = ImageTk.PhotoImage(Germany_image)
            self.canvas.create_image(370, 520, anchor=tk.CENTER, image=Germany_tk)
            self.Germany_image_tk = Germany_tk  # Keep reference

            # Transparent button overlay
            self.canvas.create_rectangle(260, bottom_position1, 510, bottom_position2, fill="", outline="", tags="Germany")

        else:
            # Draw car button (visible if no image yet)
            self.canvas.create_rectangle(260, bottom_position1, 510, bottom_position2, fill="#90EE90", outline="black", stipple="gray50", tags="Germany")
            self.canvas.create_text(385, 380, text="ドイツ", font=font_title2, fill="black")

         #  デンマークbutton
        if self.captured_images["Denmark"]:
            # Display captured car image
            Denmark_image = Image.open(self.captured_images["Denmark"])
            Denmark_image = Denmark_image.resize((260, 120))  # Match button size
            Denmark_tk = ImageTk.PhotoImage(Denmark_image)
            self.canvas.create_image(520, 770, anchor=tk.CENTER, image=Denmark_tk)
            self.Denmark_image_tk = Denmark_tk  # Keep reference

            # Transparent button overlay
            self.canvas.create_rectangle(520, bottom_position1, 770, bottom_position2 , fill="", outline="", tags="Denmark")

        else:
            # Draw car button (visible if no image yet)
            self.canvas.create_rectangle(520, bottom_position1, 770, bottom_position2 , fill="#90EE90", outline="black", stipple="gray50", tags="Denmark")
            self.canvas.create_text(645, 380, text="デンマーク", font=font_title2, fill="black")


    def draw_next_screen(self):
        self.canvas.delete("all")
        self.current_screen = "next"

        # 背景画像として Sam.jpg を表示
        try:
            bg_image = Image.open("sample.jpg")
            bg_image = bg_image.resize((800, 600))  # キャンバスサイズに合わせてリサイズ
            bg_tk = ImageTk.PhotoImage(bg_image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=bg_tk)
            self.bg_next_screen_tk = bg_tk  # 参照を保持
        except Exception as e:
            print(f"Error loading Sam.jpg: {e}")
        self.canvas.create_text(400, 30, text="ひだりのおてほんとおなじものをつくってね", font=font_subject, fill="black")
        if self.blocknumber == 0:
            self.canvas.create_text(240, 80, text="まえからとってね！", font=font_subject, fill="black")
        elif self.blocknumber == 1:
            self.canvas.create_text(240, 80, text="よこむきにとってね！", font=font_subject, fill="black")

        # Display camera feed on the right
        if self.last_frame is not None:
            frame_rgb = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2RGB)
            frame_image = Image.fromarray(frame_rgb)
            frame_image = frame_image.resize((300, 300))
            frame_tk = ImageTk.PhotoImage(image=frame_image)
            self.canvas.create_image(550, 200, anchor=tk.CENTER, image=frame_tk)
            self.image_tk = frame_tk  # Keep reference

        # Sample image
        if self.blocknumber == 0:
            self.sample_image_path = "image/Japan.png"
            imageSizeX = 300 
            imageSizeY = 300

        elif self.blocknumber == 1:
            self.sample_image_path = "image/Sweden.png"
            imageSizeX = 300 
            imageSizeY = 300

        elif self.blocknumber == 2:
            self.sample_image_path = "image/Estonia.png"
            imageSizeX = 300 
            imageSizeY = 300
        
        elif self.blocknumber == 3:
            self.sample_image_path = "image/Holland.png"
            imageSizeX = 300 
            imageSizeY = 300

        elif self.blocknumber == 4:
            self.sample_image_path = "image/Germany.png"
            imageSizeX = 300 
            imageSizeY = 300

        elif self.blocknumber == 5:
            self.sample_image_path = "image/Denmark.png"
            imageSizeX = 300 
            imageSizeY = 300


        try:
            sample_image = Image.open(self.sample_image_path)
            sample_image.thumbnail((imageSizeX,imageSizeY))

            # Create frame around the sample image
            x1, y1, x2, y2 = 150, 100, 350, 300
            # self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="black", width=4)

            # Place the sample image within the frame
            sample_tk = ImageTk.PhotoImage(sample_image)
            self.canvas.create_image((x1 + x2) // 2, (y1 + y2) // 2, anchor=tk.CENTER, image=sample_tk)
            self.sample_image_tk = sample_tk  # Keep reference

        except Exception as e:
            print(f"Sample image error: {e}")

        # Shutter button
        self.canvas.create_rectangle(300, 400, 500, 450, fill="red", outline="black", tags="shutter")
        self.canvas.create_text(400, 425, text="しゃしん", font=font_subject, fill="white")

        # Back to main button (left bottom)
        self.canvas.create_rectangle(10, 500, 250, 550, fill="blue", outline="black", tags="back_to_main")
        self.canvas.create_text(125, 525, text="さいしょにもどる", font=font_subject, fill="white")

        # Message area
        self.message_id = self.canvas.create_text(400, 500, text="", font=("Helvetica", 14), fill="red")



    def mouse_event(self, event):
        x, y = event.x, event.y

        if self.current_screen == "main":
            if 10 <= x <= 250 and  top_position1 <= y <= top_position2:
                self.blocknumber = 0#日本選択
                self.draw_next_screen()
            elif 260 <= x <= 510 and top_position1 <= y <= top_position2:
                self.blocknumber = 1#スウェーデン選択
                self.draw_next_screen()
            elif 520 <= x <= 770 and top_position1 <= y <= top_position2:
                self.blocknumber = 2#エストニア選択
                self.draw_next_screen()
            elif 10 <= x <= 250 and bottom_position1 <= y <= bottom_position2:
                self.blocknumber = 3#オランダ選択
                self.draw_next_screen()
            elif 260 <= x <= 510 and bottom_position1 <= y <= bottom_position2:
                self.blocknumber = 4#ドイツ選択
                self.draw_next_screen()
            elif 520 <= x <= 770 and bottom_position1 <= y <= bottom_position2:
                self.blocknumber = 5#デンマーク選択
                self.draw_next_screen()


        elif self.current_screen == "next":
            if 300 <= x <= 500 and 400 <= y <= 450:
                self.capture_shutter()
            elif 50 <= x <= 200 and 500 <= y <= 550:
                self.draw_main_screen()  # メインページに戻る

    def capture_shutter(self):
        global tome_home, tome_car
        if self.last_frame is not None:
            filename = f"captured_image_{self.blocknumber}.jpg"
            cv2.imwrite(filename, self.last_frame)
            print(f"Image saved: {filename}")

            # YOLOモデルの適用
            results = self.model(filename)

            # 信頼値のしきい値
            confidence_threshold = 0.3  # ここでしきい値を設定

            if results and len(results[0].boxes) > 0:
                detected = False  # 検出結果の確認用
                self.canvas.itemconfig(self.message_id, text="すこしまってね")

                for i, box in enumerate(results[0].boxes.xyxy):
                    confidence = results[0].boxes.conf[i]  # 信頼値を取得
                    if confidence < confidence_threshold:
                        continue  # 信頼値がしきい値以下の場合はスキップ

                    x1, y1, x2, y2 = map(int, box.tolist())
                    label_index = int(results[0].boxes.cls[i])  # クラスIDを取得
                    object_type = self.model.names[label_index]  # クラス名を取得
                    print(f"Detected object: {object_type} with confidence: {confidence}")

                    # ブロックナンバーに対応するオブジェクトかどうかを確認
                    if (self.blocknumber == 0 and object_type != "house") or \
                    (self.blocknumber == 1 and object_type != "cars"):
                        continue  # 対応しない場合はスキップ

                    #ボタンの透過度を変更
                    if (self.blocknumber == 0 and object_type == "house"):
                        tome_home ="gray25"

                    if (self.blocknumber == 1 and object_type == "car"):
                        tome_car ="gray25"

                    detected = True  # 検出成功
                    self.current_screen == "detail"
                    

                    # 検出されたオブジェクトを切り抜き
                    
                    cropped = Image.open(filename).crop((x1, y1, x2, y2))

                    # 背景を削除
                    temp_path = os.path.join(self.output_dir, f"temp_{object_type}_{i}.jpg")
                    cropped.save(temp_path, "JPEG")
                    with open(temp_path, "rb") as input_file:
                        output_data = remove(input_file.read())
                    output_path = os.path.join(self.output_dir, f"result_{object_type}_{i}.png")
                    with open(output_path, "wb") as output_file:
                        output_file.write(output_data)

                    trimmed_output_path = os.path.join(self.output_dir, f"trimmed_{object_type}_{i}.png")

                    # 透過部分をトリミング
                    if self.trim_transparent_area(output_path, trimmed_output_path):
                        # トリミング後の画像パスを保存    
                        self.captured_images[object_type] = output_path
                    # トリミング後の画像パスを保存
                        self.captured_images[object_type] = trimmed_output_path
                        
                        self.go_to_country_info_screen(self.blocknumber)
                        
                    else:
                        print(f"Trimming failed for {output_path}")

                if detected:
                    self.draw_main_screen()
                else:#物体は検知されているが、対象の物体がないor精度が低すぎる
                    self.canvas.itemconfig(self.message_id, text="あとちょっと！")
            else:#そもそも物体がない
                self.canvas.itemconfig(self.message_id, text="みつからないよ～")

    def trim_transparent_area(self, input_path, output_path):
        """
        PNG画像の透過部分をトリミングし、物体ができるだけ大きくなるように画像の端に配置します。
        
        Args:
            input_path (str): トリミング対象の画像パス。
            output_path (str): トリミング後の画像を保存するパス。
            
        Returns:
            bool: トリミングが成功した場合はTrue、失敗した場合はFalse。
        """
        try:
            # 入力画像を開く
            img = Image.open(input_path).convert("RGBA")
            
            # アルファチャンネルを使って非透過部分の範囲を取得
            bbox = img.getbbox()

            if bbox:
                # 物体部分が画像の端に触れるように画像を拡大
                img_cropped = img.crop(bbox)
                
                # 新しい画像サイズを設定（物体が画像端に触れるように）
                img_width, img_height = img_cropped.size
                new_img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))

                # 物体を新しい画像内で最適に配置
                new_img.paste(img_cropped, (0,0), img_cropped)  # 物体を画像の左上に配置
                
                # 保存
                new_img.save(output_path, "PNG")
                print(f"Trimmed and enlarged image saved: {output_path}")
                return True
            else:
                print("No non-transparent pixels found in the image.")
                return False

        except Exception as e:
            print(f"Error trimming transparent image: {e}")
            return False

    def update_frame(self):
        if self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                self.frame_count += 1
                if self.frame_count % 5 == 0:  # Update every 5 frames
                    self.last_frame = frame

                    if self.current_screen == "next":
                        frame_rgb = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2RGB)
                        frame_image = Image.fromarray(frame_rgb)
                        frame_image = frame_image.resize((300, 300))
                        frame_tk = ImageTk.PhotoImage(image=frame_image)
                        self.canvas.create_image(550, 200, anchor=tk.CENTER, image=frame_tk)
                        self.image_tk = frame_tk  # Keep reference

        self.root.after(10, self.update_frame)

    def on_close(self):
        # リソース解放
        self.capture.release()

        # captured_image_0.jpg と captured_image_1.jpg を削除
        for i in range(2):
            filename = f"captured_image_{i}.jpg"
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                    print(f"Deleted: {filename}")
                except Exception as e:
                    print(f"Error deleting {filename}: {e}")

        self.root.destroy()
# Main loop
root = tk.Tk()

# tkinter用のフォントを指定
font_title = font.Font(family="ＭＳ ゴシック", size=50)
font_title2 = font.Font(family="ＭＳ ゴシック", size=30)
font_subject = font.Font(family="ＭＳ ゴシック", size=20)
tome_home ="gray75"
tome_car ="gray75"
sample_images = {}
top_position1 = 150
top_position2 = 300
bottom_position1 = 310
bottom_position2 = 460
app = BlockGameApp(root)
root.protocol("WM_DELETE_WINDOW", app.on_close)
root.mainloop()
