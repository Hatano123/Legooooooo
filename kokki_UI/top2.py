
import tkinter as tk
from tkinter import messagebox, font
from PIL import Image, ImageTk # Removed ImageFont as it wasn't used
import cv2
import numpy as np
import os
from ultralytics import YOLO
from rembg import remove
import time
import io # Needed for processing rembg output
import shutil # For copying file in trim_transparent_area

class BlockGameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Block Game - Flag Edition")

        # --- Configuration ---
        self.flag_map = {
            0: "Japan", 1: "Sweden", 2: "Estonia",
            3: "Oranda", 4: "Germany", 5: "Denmark"
        }
        # Stores the PATH to the final processed image, or None
        self.captured_images = {flag: None for flag in self.flag_map.values()}

        # Initial setup
        self.current_screen = "main"
        self.blocknumber = None # Index (0-5) of the flag being processed
        self.last_frame = None
        self.frame_count = 0

        # Output directory for processed images
        self.output_dir = "output_images"
        os.makedirs(self.output_dir, exist_ok=True)

        # --- Camera Setup ---
        self.capture = cv2.VideoCapture(0) # Try default camera
        if not self.capture.isOpened():
            self.capture = cv2.VideoCapture(0) # Try explicitly camera 0
            if not self.capture.isOpened():
                messagebox.showerror("Error", "Cannot access the camera")
                root.destroy()
                return

        # --- YOLO Model ---
        try:
            self.model = YOLO('Rebest.pt') # Ensure this model has the correct classes
            print("Attempting to load model 'Rebest.pt'...")
            # Verify class names match self.flag_map values AFTER model loads
            model_classes_dict = self.model.names
            model_classes_set = set(model_classes_dict.values())
            expected_classes_set = set(self.flag_map.values())
            print(f"Model Classes Found: {model_classes_set}")
            print(f"Expected Classes: {expected_classes_set}")
            if not expected_classes_set.issubset(model_classes_set):
                 missing = expected_classes_set - model_classes_set
                 extra = model_classes_set - expected_classes_set
                 msg = f"Model class mismatch!\nMissing: {missing}\nUnexpected: {extra}\nCheck model and flag_map."
                 messagebox.showwarning("Model Warning", msg)
                 print(f"WARNING: {msg}") # Also print to console

        except Exception as e:
            messagebox.showerror("YOLO Error", f"Failed to load YOLO model 'Rebest.pt': {e}")
            if self.capture and self.capture.isOpened(): self.capture.release()
            root.destroy()
            return

        # --- UI Setup ---
        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack()

        self.bg_tk = None # Placeholder for main background PhotoImage
        self.bg_canvas_id = None # ID of the background image on the canvas
        self.bg_next_screen_tk = None # Placeholder for next screen background
        self.bg_result_screen_tk = None # Placeholder for result screen background
        self.result_flag_tk = None # Placeholder for result screen flag image
        self.sample_image_tk = None # Placeholder for sample image in next_screen

        self.guide_rect_id = None # <<< ガイド線のIDを保持する変数を追加

        # Store PhotoImage references for captured flags to prevent garbage collection
        self.flag_photo_references = {}

        # Draw the initial screen
        self.draw_main_screen()

        # --- Event Binding ---
        self.canvas.bind("<Button-1>", self.mouse_event)

        # Start frame update loop
        self.update_frame()

    def update_background_image(self):
        """Updates the background based on captured flags."""
        background_path = "image/background.jpg" # Default

        last_captured_flag = None
        for flag_name in self.flag_map.values():
             if self.captured_images.get(flag_name):
                 last_captured_flag = flag_name

        if last_captured_flag:
            potential_path = f"image/{last_captured_flag}.jpg"
            if os.path.exists(potential_path):
                background_path = potential_path
            else:
                print(f"Warning: Background image not found for {last_captured_flag} at {potential_path}")

        try:
            if not os.path.exists(background_path):
                print(f"ERROR: Background image file not found: {background_path}")
                self.canvas.config(bg="lightgrey")
                if self.bg_canvas_id and self.canvas.winfo_exists(): self.canvas.delete(self.bg_canvas_id)
                self.bg_tk = None
                return

            new_bg_image = Image.open(background_path)
            new_bg_image = new_bg_image.resize((800, 600), Image.Resampling.LANCZOS)
            self.bg_tk = ImageTk.PhotoImage(new_bg_image)

            if self.bg_canvas_id and self.canvas.winfo_exists():
                 try:
                    self.canvas.itemconfig(self.bg_canvas_id, image=self.bg_tk)
                 except tk.TclError:
                    print("Warning: Background canvas item not found, creating new one.")
                    self.bg_canvas_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_tk)
            else:
                 self.bg_canvas_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_tk)

            if self.bg_canvas_id: # Ensure it exists before lowering
                self.canvas.lower(self.bg_canvas_id)

        except Exception as e:
            print(f"Error updating background image from {background_path}: {e}")
            self.canvas.config(bg="lightgrey")
            if self.bg_canvas_id and self.canvas.winfo_exists(): self.canvas.delete(self.bg_canvas_id)
            self.bg_tk = None

    def draw_main_screen(self):
        self.canvas.delete("all")
        self.current_screen = "main"
        self.update_background_image() # 背景を最初に描画

        self.canvas.create_text(400, 30, text="Legoooooo Flags!", font=("Helvetica", 24, "bold"), fill="black")
        self.canvas.create_text(400, 70, text="こっきをつくろう！", font=font_subject, fill="black")
        self.canvas.create_text(400, 110, text="つくりたい くに をクリックしてね！", font=font_subject, fill="black")

        button_coords = {
            "Japan":   (10, top_position1, 250, top_position2),
            "Sweden":  (260, top_position1, 510, top_position2),
            "Estonia": (520, top_position1, 770, top_position2),
            "Oranda": (10, bottom_position1, 250, bottom_position2),
            "Germany": (260, bottom_position1, 510, bottom_position2),
            "Denmark": (520, bottom_position1, 770, bottom_position2)
        }
        button_texts = {
            "Japan": "にほん", "Sweden": "ｽｳｪｰﾃﾞﾝ", "Estonia": "ｴｽﾄﾆｱ",
            "Oranda": "オランダ", "Germany": "ドイツ", "Denmark": "ﾃﾞﾝﾏｰｸ"
        }
        text_y_offset_ratio = 0.4

        self.flag_photo_references.clear()

        for flag_name, coords in button_coords.items():
            x1, y1, x2, y2 = coords
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            btn_width = x2 - x1
            btn_height = y2 - y1
            text_y = y1 + (btn_height * text_y_offset_ratio)

            captured_image_path = self.captured_images.get(flag_name)

            if captured_image_path and os.path.exists(captured_image_path):
                try:
                    img = Image.open(captured_image_path)
                    img.thumbnail((btn_width - 10, btn_height - 10), Image.Resampling.LANCZOS)
                    img_tk = ImageTk.PhotoImage(img)
                    self.flag_photo_references[flag_name] = img_tk
                    self.canvas.create_image(center_x, center_y, anchor=tk.CENTER, image=img_tk, tags=(flag_name, "flag_display"))
                    self.canvas.create_rectangle(x1, y1, x2, y2, outline="green", width=2, tags=(flag_name, "flag_border"))
                except Exception as e:
                    print(f"Error displaying captured image {flag_name} from {captured_image_path}: {e}")
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="#FFCCCC", outline="black", stipple="gray25", tags=(flag_name, "button_fallback"))
                    self.canvas.create_text(center_x, text_y, text=f"{button_texts[flag_name]}\n(表示エラー)", font=font_subject, fill="black", tags=(flag_name, "text_fallback"))
            else:
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="#ADD8E6", outline="black", stipple="gray50", tags=(flag_name, "button_default"))
                self.canvas.create_text(center_x, text_y, text=button_texts[flag_name], font=font_title2, fill="black", tags=(flag_name, "text_default"))

        if self.bg_canvas_id and self.canvas.winfo_exists(): # 再度確認
            self.canvas.lower(self.bg_canvas_id)


    def draw_next_screen(self):
        self.canvas.delete("all")
        self.current_screen = "next"

        flag_name = self.flag_map.get(self.blocknumber)
        if not flag_name:
            messagebox.showerror("Error", f"無効な選択です ({self.blocknumber})。")
            self.draw_main_screen()
            return

        self.sample_image_path = f"image/{flag_name}.png"
        if not os.path.exists(self.sample_image_path):
            messagebox.showwarning("ファイル不足", f"サンプル画像が見つかりません:\n{self.sample_image_path}")
            self.draw_main_screen()
            return

        capture_bg_path = "image/background_capture.jpg"
        try:
            bg_image_path_to_load = capture_bg_path if os.path.exists(capture_bg_path) else "image/background.jpg"
            if not os.path.exists(bg_image_path_to_load): 
                print(f"Critical: Fallback background {bg_image_path_to_load} not found.")
                self.canvas.config(bg="lightgrey") 
            else:
                bg_image = Image.open(bg_image_path_to_load)
                bg_image = bg_image.resize((800, 600), Image.Resampling.LANCZOS)
                self.bg_next_screen_tk = ImageTk.PhotoImage(bg_image)
                self.bg_canvas_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_next_screen_tk) # 更新
                self.canvas.lower(self.bg_canvas_id) # 更新
        except Exception as e:
            print(f"Error loading capture background: {e}")
            self.canvas.config(bg="lightgrey")

        self.canvas.create_text(400, 30, text=f"{flag_name}: おてほん と おなじもの を つくってね", font=font_subject, fill="black")

        imageSizeX = 250
        imageSizeY = 200
        sample_x = 180
        sample_y = 250
        try:
            sample_image_pil = Image.open(self.sample_image_path)
            sample_image_pil.thumbnail((imageSizeX, imageSizeY), Image.Resampling.LANCZOS)
            self.sample_image_tk = ImageTk.PhotoImage(sample_image_pil) 
            self.canvas.create_image(sample_x, sample_y, anchor=tk.CENTER, image=self.sample_image_tk)
            sw, sh = sample_image_pil.size
            self.canvas.create_rectangle(sample_x - sw//2 - 5, sample_y - sh//2 - 5,
                                         sample_x + sw//2 + 5, sample_y + sh//2 + 5,
                                         outline="blue", width=2)
            self.canvas.create_text(sample_x, sample_y + sh//2 + 25, text="↑ おてほん ↑", font=font_subject, fill="black")
        except Exception as e:
            print(f"Sample image error for {self.sample_image_path}: {e}")
            self.canvas.create_text(sample_x, sample_y, text="サンプル画像\nエラー", font=font_subject, fill="red", justify=tk.CENTER)

        self.cam_x = 600
        self.cam_y = 250
        self.cam_width = 300
        self.cam_height = 300
        self.cam_feed_rect = self.canvas.create_rectangle(self.cam_x - self.cam_width//2, self.cam_y - self.cam_height//2,
                                                           self.cam_x + self.cam_width//2, self.cam_y + self.cam_height//2,
                                                           fill="black", outline="grey")
        self.cam_feed_text_id = self.canvas.create_text(self.cam_x, self.cam_y, text="カメラ準備中...", fill="white", font=font_subject)
        self.cam_feed_image_id = None
        self.image_tk = None

        # --- ガイド線描画の追加 ---
        guide_width_ratio = 0.85  # カメラフィードに対する幅の割合
        guide_height_ratio = 0.70 # カメラフィードに対する高さの割合 (国旗は横長のことが多い)

        guide_width = int(self.cam_width * guide_width_ratio)
        guide_height = int(self.cam_height * guide_height_ratio)

        guide_x1 = self.cam_x - guide_width // 2
        guide_y1 = self.cam_y - guide_height // 2
        guide_x2 = self.cam_x + guide_width // 2
        guide_y2 = self.cam_y + guide_height // 2

        # 古いガイド線があれば削除 (draw_next_screenが複数回呼ばれる可能性を考慮)
        if self.guide_rect_id and self.canvas.winfo_exists():
            try:
                if self.canvas.type(self.guide_rect_id): # アイテムが存在するか確認
                    self.canvas.delete(self.guide_rect_id)
            except tk.TclError: # アイテムが既に存在しない場合など
                pass 
            self.guide_rect_id = None


        self.guide_rect_id = self.canvas.create_rectangle(
            guide_x1, guide_y1, guide_x2, guide_y2,
            outline="yellow", # 目立つ色
            width=2,          # 線の太さ
            dash=(6, 4)       # 破線 (6ピクセル描画, 4ピクセル空白)
        )
        # --- ガイド線描画ここまで ---

        self.canvas.create_rectangle(300, 450, 500, 500, fill="red", outline="black", tags="shutter")
        self.canvas.create_text(400, 475, text="シャッター！", font=font_subject, fill="white", tags="shutter")

        self.canvas.create_rectangle(50, 530, 250, 580, fill="lightblue", outline="black", tags="back_to_main")
        self.canvas.create_text(150, 555, text="← もどる", font=font_subject, fill="black", tags="back_to_main")

        self.message_id = self.canvas.create_text(400, 555, text="", font=("Helvetica", 16), fill="red")

        if self.bg_canvas_id and self.canvas.winfo_exists(): # 再度背景を最下層に
             self.canvas.lower(self.bg_canvas_id)


    def draw_result_screen(self):
        self.canvas.delete("all")
        self.current_screen = "result"

        try:
            background_path = "image/background.jpg"
            if os.path.exists(background_path):
                bg_image = Image.open(background_path)
                bg_image = bg_image.resize((800, 600), Image.Resampling.LANCZOS)
                self.bg_result_screen_tk = ImageTk.PhotoImage(bg_image)
                self.bg_canvas_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_result_screen_tk) # 更新
                self.canvas.lower(self.bg_canvas_id) # 更新
            else:
                self.canvas.config(bg="lightyellow")
                print(f"Warning: Result screen background image not found: {background_path}")
        except Exception as e:
            print(f"Error loading background for result screen: {e}")
            self.canvas.config(bg="lightyellow")

        flag_name = self.flag_map.get(self.blocknumber, "不明な国")

        self.canvas.create_text(400, 80,
                                text=f"「{flag_name}」をゲットしたよ！",
                                font=font_title, fill="darkgreen")

        self.canvas.create_text(400, 150,
                                text=f"国旗の番号: {self.blocknumber}",
                                font=font_subject, fill="black")

        captured_image_path = self.captured_images.get(flag_name)
        if captured_image_path and os.path.exists(captured_image_path):
            try:
                img = Image.open(captured_image_path)
                img.thumbnail((250, 250), Image.Resampling.LANCZOS)
                self.result_flag_tk = ImageTk.PhotoImage(img)
                self.canvas.create_image(400, 300, anchor=tk.CENTER, image=self.result_flag_tk)
            except Exception as e:
                print(f"Error displaying captured flag image on result screen: {e}")
                self.canvas.create_text(400, 300, text="画像表示エラー", font=font_subject, fill="red")
        else:
            self.canvas.create_text(400, 300, text="キャプチャ画像なし", font=font_subject, fill="grey")

        self.canvas.create_rectangle(300, 480, 500, 530,
                                    fill="lightblue", outline="black",
                                    tags="back_to_main_from_result")
        self.canvas.create_text(400, 505, text="メインにもどる",
                                font=font_subject, fill="black",
                                tags="back_to_main_from_result")
        
        if self.bg_canvas_id and self.canvas.winfo_exists(): # 再度背景を最下層に
             self.canvas.lower(self.bg_canvas_id)

    def detail_screen(self): # Currently unused
        self.current_screen = "detail"
        self.canvas.delete("all")
        # 背景の描画 (例: main_screen と同様)
        self.update_background_image() # 既存の背景更新ロジックを使用

        flag_name = self.flag_map.get(self.blocknumber, "Unknown")
        self.canvas.create_text(400, 50, text=f"{flag_name} - 詳細", font=font_title, fill="black")
        
        # キャプチャした画像を表示 (result_screenと同様のロジック)
        captured_image_path = self.captured_images.get(flag_name)
        if captured_image_path and os.path.exists(captured_image_path):
            try:
                img = Image.open(captured_image_path)
                img.thumbnail((300, 300), Image.Resampling.LANCZOS) # 少し大きめに表示
                # この画面専用のPhotoImage参照を保持
                self.detail_flag_tk = ImageTk.PhotoImage(img) # 新しい属性が必要
                self.canvas.create_image(400, 250, anchor=tk.CENTER, image=self.detail_flag_tk)
            except Exception as e:
                print(f"Error displaying captured flag image on detail screen: {e}")
                self.canvas.create_text(400, 250, text="画像表示エラー", font=font_subject, fill="red")
        else:
            self.canvas.create_text(400, 250, text="キャプチャ画像なし", font=font_subject, fill="grey")


        self.canvas.create_rectangle(300, 500, 500, 550, fill="lightblue", outline="black", tags="back_to_main")
        self.canvas.create_text(400, 525, text="メインにもどる", font=font_subject, fill="black", tags="back_to_main")

        if self.bg_canvas_id and self.canvas.winfo_exists(): # 再度背景を最下層に
             self.canvas.lower(self.bg_canvas_id)


    def mouse_event(self, event):
        x, y = event.x, event.y
        items = self.canvas.find_overlapping(x, y, x, y)
        if not items:
            return

        tags = self.canvas.gettags(items[-1])
        if not tags:
            return

        tag = tags[0]
        print(f"Clicked on item with tags: {tags}, primary tag: {tag} on screen: {self.current_screen}")

        if self.current_screen == "main":
            for num, name in self.flag_map.items():
                if tag == name: # ボタンの主要タグが国旗名になっている想定
                    self.blocknumber = num
                    print(f"Selected flag: {name} (Block number: {self.blocknumber})")

                    if self.captured_images.get(name):
                        # 詳細画面へ（detail_screenが実装されていれば）
                        # self.detail_screen() # detail_screenを呼び出す場合
                        print(f"Flag {name} already captured. Showing detail (not implemented yet).")
                        # ここでは詳細画面の代わりにメッセージを表示するか、何もしない
                        # もし詳細画面を実装するなら self.detail_screen() を呼ぶ
                        self.draw_main_screen() # 現状はメインに戻るなど、適切な動作を
                    else:
                        self.draw_next_screen()
                    return

            print(f"Unhandled click on main screen with tag: {tag}")

        elif self.current_screen == "next":
            if tag == "shutter":
                print("Shutter button clicked")
                self.capture_shutter()
            elif tag == "back_to_main":
                print("Back to main clicked from next screen")
                if self.guide_rect_id and self.canvas.winfo_exists(): # ガイド線を削除
                    try:
                        if self.canvas.type(self.guide_rect_id): self.canvas.delete(self.guide_rect_id)
                    except tk.TclError: pass
                    self.guide_rect_id = None
                self.draw_main_screen()

        elif self.current_screen == "result":
            if tag == "back_to_main_from_result":
                print("Back to main from result screen clicked")
                self.draw_main_screen()

        elif self.current_screen == "detail": # detail_screenからの戻る処理
            if tag == "back_to_main":
                print("Back to main from detail screen clicked")
                self.draw_main_screen()


    def capture_shutter(self):
        if self.last_frame is None:
            if hasattr(self, 'message_id') and self.message_id and \
               hasattr(self, 'canvas') and self.canvas and self.canvas.winfo_exists():
                self.canvas.itemconfig(self.message_id, text="カメラの じゅんびができてないよ")
            return
        if self.blocknumber is None:
            if hasattr(self, 'message_id') and self.message_id and \
               hasattr(self, 'canvas') and self.canvas and self.canvas.winfo_exists():
                self.canvas.itemconfig(self.message_id, text="エラー: フラッグが選択されていません")
            return

        expected_flag = self.flag_map.get(self.blocknumber)
        if not expected_flag:
            if hasattr(self, 'message_id') and self.message_id and \
               hasattr(self, 'canvas') and self.canvas and self.canvas.winfo_exists():
                self.canvas.itemconfig(self.message_id, text=f"エラー: 不明なブロック番号 {self.blocknumber}")
            return

        if hasattr(self, 'message_id') and self.message_id and \
           hasattr(self, 'canvas') and self.canvas and self.canvas.winfo_exists():
            self.canvas.itemconfig(self.message_id, text="しゃしん を ほぞんちゅう...", fill='orange') # メッセージ変更
        if hasattr(self, 'root') and self.root:
            self.root.update_idletasks()

        timestamp = int(time.time())
        # 一時ファイルは不要になるか、あるいは生フレームを一度保存するなら残す
        # ここでは最終的な画像を直接作るため、temp_filenameは最終出力名に流用できる

        try:
            # --- ガイド枠内の画像を直接クロップ ---
            if not (self.guide_rect_id and self.canvas.winfo_exists() and \
                    self.canvas.type(self.guide_rect_id) == 'rectangle'):
                if hasattr(self, 'message_id') and self.message_id and \
                   hasattr(self, 'canvas') and self.canvas and self.canvas.winfo_exists():
                    self.canvas.itemconfig(self.message_id, text="エラー: ガイド枠が見つかりません", fill='red')
                return

            # キャンバス上のガイド枠の座標 (x1, y1, x2, y2)
            guide_canvas_coords = self.canvas.coords(self.guide_rect_id)
            gc_x1, gc_y1, gc_x2, gc_y2 = map(int, guide_canvas_coords)

            # カメラフィード表示領域のキャンバス上の中心座標とサイズ
            cam_display_center_x = self.cam_x
            cam_display_center_y = self.cam_y
            cam_display_width = self.cam_width
            cam_display_height = self.cam_height

            # カメラフィード表示領域のキャンバス上の左上座標
            cam_display_tl_x = cam_display_center_x - cam_display_width // 2
            cam_display_tl_y = cam_display_center_y - cam_display_height // 2

            # ガイド枠の、カメラフィード表示領域内での相対座標
            guide_relative_x1 = gc_x1 - cam_display_tl_x
            guide_relative_y1 = gc_y1 - cam_display_tl_y
            guide_relative_x2 = gc_x2 - cam_display_tl_x
            guide_relative_y2 = gc_y2 - cam_display_tl_y

            # 元のカメラフレームのサイズ
            original_frame_height, original_frame_width = self.last_frame.shape[:2]

            # スケーリング比率
            scale_x = original_frame_width / cam_display_width
            scale_y = original_frame_height / cam_display_height

            # 元のカメラフレームにおけるクロップ座標
            crop_x1 = int(guide_relative_x1 * scale_x)
            crop_y1 = int(guide_relative_y1 * scale_y)
            crop_x2 = int(guide_relative_x2 * scale_x)
            crop_y2 = int(guide_relative_y2 * scale_y)

            # 座標がフレーム範囲内にあることを確認・調整
            crop_x1 = max(0, crop_x1)
            crop_y1 = max(0, crop_y1)
            crop_x2 = min(original_frame_width, crop_x2)
            crop_y2 = min(original_frame_height, crop_y2)

            if crop_x1 >= crop_x2 or crop_y1 >= crop_y2:
                if hasattr(self, 'message_id') and self.message_id and \
                   hasattr(self, 'canvas') and self.canvas and self.canvas.winfo_exists():
                    self.canvas.itemconfig(self.message_id, text="エラー: クロップ範囲が無効です", fill='red')
                return

            # カメラフレーム(Numpy配列)をクロップ
            cropped_frame_np = self.last_frame[crop_y1:crop_y2, crop_x1:crop_x2]

            if cropped_frame_np.size == 0:
                if hasattr(self, 'message_id') and self.message_id and \
                   hasattr(self, 'canvas') and self.canvas and self.canvas.winfo_exists():
                    self.canvas.itemconfig(self.message_id, text="エラー: クロップ結果が空です", fill='red')
                return

            # Numpy配列からPIL Imageに変換
            # OpenCVはBGRなのでRGBに変換
            cropped_frame_rgb_np = cv2.cvtColor(cropped_frame_np, cv2.COLOR_BGR2RGB)
            processed_image_pil = Image.fromarray(cropped_frame_rgb_np)

            # --- YOLOとrembg、trim_transparent_areaの処理は削除またはコメントアウト ---
            # results = self.model(temp_filename, verbose=False) ... (以下YOLO関連削除)
            # img_byte_arr = io.BytesIO() ... (以下rembg関連削除)
            # if self.trim_transparent_area(...): ... (以下trim関連削除)

            base_output_filename = f"{expected_flag}_{timestamp}" # 拡張子なし
            # 最終的な保存パス (PNG形式で保存)
            final_image_path = os.path.join(self.output_dir, f"guide_cropped_{base_output_filename}.png")

            processed_image_pil.save(final_image_path, "PNG")
            print(f"ガイド枠内の画像を保存しました: {final_image_path}")

            self.captured_images[expected_flag] = final_image_path
            if hasattr(self, 'message_id') and self.message_id and \
               hasattr(self, 'canvas') and self.canvas and self.canvas.winfo_exists():
                self.canvas.itemconfig(self.message_id, text=f"{expected_flag} をほぞんしたよ！", fill='green') # メッセージ変更
            
            self.draw_result_screen() # 結果表示画面へ

        except Exception as e:
            print(f"ERROR during guide crop and save: {e}")
            import traceback
            traceback.print_exc()
            if hasattr(self, 'message_id') and self.message_id and \
               hasattr(self, 'canvas') and self.canvas and self.canvas.winfo_exists():
                self.canvas.itemconfig(self.message_id, text="エラー が はっせい しました", fill='red')
        # finally:
            # temp_filename を使わなくなったので、その削除処理も不要になる
            # if os.path.exists(temp_filename):
            #     try:
            #         os.remove(temp_filename)
            #         print(f"Deleted temporary file: {temp_filename}")
            #     except Exception as e_del:
            #         print(f"Warning: Error deleting temp file {temp_filename}: {e_del}")

    def trim_transparent_area(self, input_path, output_path):
        try:
            img = Image.open(input_path).convert("RGBA")
            bbox = img.getbbox()
            if bbox:
                img_cropped = img.crop(bbox)
                if img_cropped.width > 0 and img_cropped.height > 0:
                    img_cropped.save(output_path, "PNG")
                    return True
                else:
                    print(f"Trimming resulted in empty image for {input_path}. BBox: {bbox}")
                    shutil.copy(input_path, output_path)
                    return False 
            else: # 画像全体が透明だった場合など
                print(f"No content found to trim for {input_path} (getbbox returned None). Copying original.")
                shutil.copy(input_path, output_path)
                return True # ファイルはコピーされたのでTrueとするか、トリミングされなかったのでFalseとするかは要件次第
        except Exception as e:
            print(f"Error trimming transparent image '{input_path}': {e}")
            try: 
                shutil.copy(input_path, output_path)
                print(f"Fell back to copying original due to trim error for {input_path}")
            except Exception as e_copy:
                print(f"Error copying original file during trim fallback: {e_copy}")
            return False

    def update_frame(self):
        if not (hasattr(self, 'capture') and self.capture and self.capture.isOpened()):
             if self.current_screen == "next" and hasattr(self, 'message_id') and self.message_id and self.canvas.winfo_exists():
                 try:
                     self.canvas.itemconfig(self.message_id, text="カメラ接続エラー", fill="red")
                 except tk.TclError: pass 
             self.root.after(1000, self.update_frame) 
             return

        ret, frame = self.capture.read()
        if ret:
            self.frame_count += 1
            self.last_frame = frame # 常に最新フレームを保持

            if self.current_screen == "next" and self.canvas.winfo_exists():
                try:
                    frame_rgb = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2RGB)
                    frame_image_pil = Image.fromarray(frame_rgb)
                    frame_image_pil = frame_image_pil.resize((self.cam_width, self.cam_height), Image.Resampling.NEAREST)
                    self.image_tk = ImageTk.PhotoImage(image=frame_image_pil) 

                    if self.cam_feed_image_id and self.canvas.winfo_exists() and self.canvas.type(self.cam_feed_image_id):
                        self.canvas.itemconfig(self.cam_feed_image_id, image=self.image_tk)
                    elif self.canvas.winfo_exists(): 
                        self.cam_feed_image_id = self.canvas.create_image(self.cam_x, self.cam_y, anchor=tk.CENTER, image=self.image_tk)
                        if self.cam_feed_text_id and self.canvas.winfo_exists() and self.canvas.type(self.cam_feed_text_id):
                            self.canvas.delete(self.cam_feed_text_id)
                            self.cam_feed_text_id = None
                    
                    # --- ガイド線を最前面に表示 ---
                    if self.guide_rect_id and self.canvas.winfo_exists():
                        try:
                            if self.canvas.type(self.guide_rect_id): # アイテムが存在するか確認
                                self.canvas.tag_raise(self.guide_rect_id)
                        except tk.TclError: # アイテムが削除されている場合など
                            pass # 必要ならここで self.guide_rect_id = None など
                    # --- ガイド線処理ここまで ---

                except tk.TclError as e: 
                    print(f"TclError updating camera feed (item might be deleted): {e}")
                    self.cam_feed_image_id = None 
                except Exception as e:
                    print(f"Error updating camera feed display: {e}")
                    if self.cam_feed_text_id and self.canvas.winfo_exists() and self.canvas.type(self.cam_feed_text_id):
                         self.canvas.itemconfig(self.cam_feed_text_id, text="表示エラー")
        else:
            if self.current_screen == "next" and hasattr(self, 'message_id') and self.message_id and self.canvas.winfo_exists():
                try:
                     self.canvas.itemconfig(self.message_id, text="カメラから映像取得失敗", fill="red")
                except tk.TclError: pass

        self.root.after(33, self.update_frame)

    def on_close(self):
        print("Closing application...")
        if hasattr(self, 'capture') and self.capture and self.capture.isOpened():
            self.capture.release()
            print("Camera released.")

        print("Cleaning temporary files from output_dir...")
        if hasattr(self, 'output_dir') and os.path.isdir(self.output_dir):
            for item in os.listdir(self.output_dir):
                 if item.startswith("captured_image_temp_") and item.endswith(".jpg"):
                     temp_file_path = os.path.join(self.output_dir, item)
                     try:
                         os.remove(temp_file_path)
                         print(f"Deleted: {temp_file_path}")
                     except Exception as e:
                         print(f"Error deleting {temp_file_path}: {e}")
        self.root.destroy()

# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()

    # --- Fonts ---
    try:
        font_title = font.Font(family="Yu Gothic", size=30, weight="bold")
        font_title2 = font.Font(family="Yu Gothic", size=22)
        font_subject = font.Font(family="Yu Gothic", size=16)
    except tk.TclError:
        try:
            font_title = font.Font(family="Meiryo", size=30, weight="bold")
            font_title2 = font.Font(family="Meiryo", size=22)
            font_subject = font.Font(family="Meiryo", size=16)
        except tk.TclError:
            print("Japanese fonts (Yu Gothic/Meiryo) not found, using Tk default.")
            font_title = font.Font(size=30, weight="bold")
            font_title2 = font.Font(size=22)
            font_subject = font.Font(size=16)

    # --- Button Area Positions ---
    top_position1 = 150
    top_position2 = 300
    bottom_position1 = 320
    bottom_position2 = 470

    app = BlockGameApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()