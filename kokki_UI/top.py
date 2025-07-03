import tkinter as tk
from tkinter import messagebox, font
from PIL import Image, ImageTk
import cv2
import numpy as np
import os
from ultralytics import YOLO
from rembg import remove
import time
import io
import shutil
from Audio import Audio
import random

class BlockGameApp:

    def __init__(self, root):
        self.root = root
        self.root.title("こっきでわくわく")
        self.audio = Audio()
        self.preview_paste_info = {'x': 0, 'y': 0, 'w': 0, 'h': 0} # プレビュー描画オフセットと実サイズ

        # --- Configuration ---
        self.flag_map = {
            0: "Japan", 1: "Sweden", 2: "Estonia",
            3: "Oranda", 4: "Germany", 5: "Denmark"
        }
        self.flag_names_jp = {
            "Japan": "日本", "Sweden": "スウェーデン", "Estonia": "エストニア",
            "Oranda": "オランダ", "Germany": "ドイツ", "Denmark": "デンマーク"
        }

        # Stores the PATH to the final processed image, or None
        self.captured_images = {flag: None for flag in self.flag_map.values()}

        # Initial setup
        self.current_screen = "main"
        self.blocknumber = None # Index (0-5) of the flag being processed
        self.last_frame = None
        self.frame_count = 0

        self.image_refs = []

        # Output directory for processed images
        self.output_dir = "output_images"
        os.makedirs(self.output_dir, exist_ok=True)

        # --- Camera Setup ---
        self.capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
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
            if self.capture and self.capture.isOpened(): #self.capture.release()
                pass
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

        # Store PhotoImage references for captured flags to prevent garbage collection
        self.flag_photo_references = {}

        # Explanation screen specific variables
        self.explanation_detection_count = 0
        self.last_detected_explanation_flag = None
        self.explanation_screen_message_id = None
        self.explanation_cam_feed_image_id = None # Separate ID for explanation screen camera feed

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

            self.canvas.lower(self.bg_canvas_id)

        except Exception as e:
            print(f"Error updating background image from {background_path}: {e}")
            self.canvas.config(bg="lightgrey")
            if self.bg_canvas_id and self.canvas.winfo_exists(): self.canvas.delete(self.bg_canvas_id)
            self.bg_tk = None

    def draw_main_screen(self):
        self.canvas.delete("all")
        self.current_screen = "main"
        # カメラ関連の表示オブジェクトをリセット
        self.cam_feed_image_id = None
        self.explanation_cam_feed_image_id = None
        self.image_tk = None # PhotoImage参照もクリア


        # --- Main screen specific background ---
        main_background_path = "image/background.jpg"
        try:
            if not os.path.exists(main_background_path):
                print(f"ERROR: Main background image file not found: {main_background_path}")
                self.canvas.config(bg="lightgrey") # Fallback color
                if self.bg_canvas_id and self.canvas.winfo_exists():
                    try:
                        self.canvas.delete(self.bg_canvas_id)
                    except tk.TclError:
                        pass
                self.bg_tk = None
                self.bg_canvas_id = None
            else:
                # Load and display the specific main background
                main_bg_image_pil = Image.open(main_background_path)
                main_bg_image_pil = main_bg_image_pil.resize((800, 600), Image.Resampling.LANCZOS)
                self.bg_tk = ImageTk.PhotoImage(main_bg_image_pil)

                if self.bg_canvas_id and self.canvas.winfo_exists():
                    try:
                        self.canvas.delete(self.bg_canvas_id)
                    except tk.TclError:
                        self.bg_canvas_id = None # Reset if ID was invalid

                self.bg_canvas_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_tk)
                self.canvas.lower(self.bg_canvas_id) # Send to back
        except Exception as e:
            print(f"Error setting main background image from {main_background_path}: {e}")
            self.canvas.config(bg="lightgrey")
            if self.bg_canvas_id and self.canvas.winfo_exists():
                try:
                    self.canvas.delete(self.bg_canvas_id)
                except tk.TclError:
                    pass
            self.bg_tk = None
            self.bg_canvas_id = None
        # --- End of Main screen specific background ---

        self.canvas.create_text(400, 30, text="こっきでわくわく", font=("Helvetica", 24, "bold"), fill="black")
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
        # Use self.flag_names_jp for consistency in displayed text
        button_texts = {name_en: self.flag_names_jp.get(name_en, name_en) for name_en in button_coords.keys()}

        text_y_offset_ratio = 0.4
        self.flag_photo_references.clear()

        for flag_name, coords in button_coords.items(): # flag_name here is the English key
            x1, y1, x2, y2 = coords
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            btn_width = x2 - x1
            btn_height = y2 - y1
            text_y = y1 + (btn_height * text_y_offset_ratio)

            # Get the Japanese display text using the English key
            display_text = button_texts[flag_name]

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
                    # Use display_text for fallback
                    self.canvas.create_text(center_x, text_y, text=f"{display_text}\n(表示エラー)", font=font_subject, fill="black", tags=(flag_name, "text_fallback"))
            else:
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="#ADD8E6", outline="black", stipple="gray50", tags=(flag_name, "button_default"))
                self.canvas.create_text(center_x, text_y, text=button_texts[flag_name], font=font_title2, fill="black", tags=(flag_name, "text_default"))

        if self.bg_canvas_id and self.canvas.winfo_exists():
            self.canvas.lower(self.bg_canvas_id)

        # --- 新しい「せつめい」ボタンの追加 ---
        explanation_btn_x1 = 600
        explanation_btn_y1 = 530
        explanation_btn_x2 = 750
        explanation_btn_y2 = 580
        self.canvas.create_rectangle(explanation_btn_x1, explanation_btn_y1, explanation_btn_x2, explanation_btn_y2,
                                     fill="purple", outline="black", tags="explanation_button")
        self.canvas.create_text((explanation_btn_x1 + explanation_btn_x2) // 2, (explanation_btn_y1 + explanation_btn_y2) // 2,
                                text="せつめい", font=font_subject, fill="white", tags="explanation_button")
        # --- ここまで ---
        
        reset_btn_x1 = 50
        reset_btn_y1 = 530
        reset_btn_x2 = 200
        reset_btn_y2 = 580
        self.canvas.create_rectangle(reset_btn_x1, reset_btn_y1, reset_btn_x2, reset_btn_y2,
                                     fill="orange", outline="black", tags="reset_button")
        self.canvas.create_text((reset_btn_x1 + reset_btn_x2) // 2, (reset_btn_y1 + reset_btn_y2) // 2,
                                text="リセット", font=font_subject, fill="white", tags="reset_button")
        

        # === BGM再生（即時） ===
        self.audio.stop_bgm()
        self.audio.play_bgm("audio/bgmset/lalalabread.mp3")
        #self.canvas.after(100, lambda: self.audio.play_voice("audio/voiceset/make/make_flags.wav"))


    def draw_next_screen(self):
        self.canvas.delete("all")
        self.current_screen = "next"
        # カメラ関連の表示オブジェクトをリセット
        self.cam_feed_image_id = None
        self.explanation_cam_feed_image_id = None
        self.image_tk = None # PhotoImage参照もクリア


        flag_name = self.flag_map.get(self.blocknumber)
        flag_name_en = self.flag_map[self.blocknumber]
        flag_name_jp = self.flag_names_jp.get(flag_name_en, flag_name_en)  # 日本語がなければ英語を使う
        if not flag_name:
            messagebox.showerror("Error", f"無効な選択です ({self.blocknumber})。")
            self.draw_main_screen()
            return

        # サンプル画像のパスと存在確認
        self.sample_image_path = f"image/{flag_name}.png"
        if not os.path.exists(self.sample_image_path):
            messagebox.showwarning("ファイル不足", f"サンプル画像が見つかりません:\n{self.sample_image_path}")
            # self.draw_main_screen() # サンプル画像がなくても続行する場合はコメントアウト
            # return

        # 背景画像の設定 (キャプチャ画面専用またはデフォルト)
        capture_bg_path = "image/background_capture.jpg"
        try:
            bg_image_path_to_load = capture_bg_path if os.path.exists(capture_bg_path) else "image/background.jpg"
            if not os.path.exists(bg_image_path_to_load):
                print(f"Critical: Fallback background {bg_image_path_to_load} not found.")
                self.canvas.config(bg="lightgrey")
            else:
                bg_image = Image.open(bg_image_path_to_load)
                bg_image = bg_image.resize((800, 600), Image.Resampling.LANCZOS)
                self.bg_next_screen_tk = ImageTk.PhotoImage(bg_image) # 参照を保持
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_next_screen_tk)
                self.canvas.lower(self.bg_next_screen_tk) # 背景なので一番下に
        except Exception as e:
            print(f"Error loading capture background: {e}")
            self.canvas.config(bg="lightgrey")

        self.canvas.create_text(400, 30, text=f"{flag_name_jp}: おてほん と おなじもの を つくってね", font=font_subject, fill="black")

        # サンプル画像の表示エリア設定と描画
        imageSizeX = 250 # サンプル画像の最大幅
        imageSizeY = 200 # サンプル画像の最大高さ
        sample_x = 180   # サンプル画像の中心 x 座標
        sample_y = 250   # サンプル画像の中心 y 座標
        try:
            if os.path.exists(self.sample_image_path): # 再度存在確認
                sample_image_pil = Image.open(self.sample_image_path)
                sample_image_pil.thumbnail((imageSizeX, imageSizeY), Image.Resampling.LANCZOS)
                self.sample_image_tk = ImageTk.PhotoImage(sample_image_pil) # 参照を保持
                self.canvas.create_image(sample_x, sample_y, anchor=tk.CENTER, image=self.sample_image_tk)
                sw, sh = sample_image_pil.size
                self.canvas.create_rectangle(sample_x - sw//2 - 5, sample_y - sh//2 - 5,
                                             sample_x + sw//2 + 5, sample_y + sh//2 + 5,
                                             outline="blue", width=2)
                self.canvas.create_text(sample_x, sample_y + sh//2 + 25, text="↑ おてほん ↑", font=font_subject, fill="black")
            else:
                # サンプル画像がない場合のプレースホルダー
                self.canvas.create_text(sample_x, sample_y, text="サンプル画像\nなし", font=font_subject, fill="grey", justify=tk.CENTER)
        except Exception as e:
            print(f"Sample image error for {self.sample_image_path}: {e}")
            self.canvas.create_text(sample_x, sample_y, text="サンプル画像\nエラー", font=font_subject, fill="red", justify=tk.CENTER)

        # カメラプレビューエリアの設定
        self.cam_x = 600   # プレビューエリアの中心 x
        self.cam_y = 250   # プレビューエリアの中心 y
        self.cam_width = 300 # プレビューエリア全体の幅 (この中にアスペクト比保持で表示)
        self.cam_height = 300 # プレビューエリア全体の高さ

        # プレビューエリアの背景 (黒い四角)
        self.canvas.create_rectangle(
            self.cam_x - self.cam_width // 2, self.cam_y - self.cam_height // 2,
            self.cam_x + self.cam_width // 2, self.cam_y + self.cam_height // 2,
            fill="black", outline="grey", tags="camera_bg_rect"
        )
        # カメラ準備中のテキスト (update_frameで画像表示時に削除される)
        self.cam_feed_text_id = self.canvas.create_text(self.cam_x, self.cam_y, text="カメラ準備中...", fill="white", font=font_subject)
        self.cam_feed_image_id = None # update_frameでカメラ画像アイテムIDを格納
        self.image_tk = None # update_frameでPhotoImage参照を保持

        # --- アスペクト比保持プレビューに合わせた7:12ガイド枠の描画 ---
        target_guide_aspect_ratio_wh = 12.0 / 7.0

        guide_w_if_h_is_max = int(self.cam_height * target_guide_aspect_ratio_wh)
        guide_h_if_w_is_max = int(self.cam_width / target_guide_aspect_ratio_wh)

        if guide_w_if_h_is_max <= self.cam_width:
            final_guide_height_on_preview = self.cam_height
            final_guide_width_on_preview = guide_w_if_h_is_max
        else:
            final_guide_width_on_preview = self.cam_width
            final_guide_height_on_preview = guide_h_if_w_is_max

        guide_x1 = self.cam_x - final_guide_width_on_preview // 2
        guide_y1 = self.cam_y - final_guide_height_on_preview // 2
        guide_x2 = self.cam_x + final_guide_width_on_preview // 2
        guide_y2 = self.cam_y + final_guide_height_on_preview // 2

        self.canvas.create_rectangle(
            guide_x1, guide_y1, guide_x2, guide_y2,
            outline="yellow", width=2, tags="crop_guide_rect"
        )
        self.preview_crop_guide_coords = (guide_x1, guide_y1, guide_x2, guide_y2)

        print(f"DEBUG (draw_next_screen): Preview Area (WxH): {self.cam_width}x{self.cam_height} at ({self.cam_x},{self.cam_y})")
        print(f"DEBUG (draw_next_screen): Final Guide Frame Size on Preview (WxH): {final_guide_width_on_preview}x{final_guide_height_on_preview}")
        print(f"DEBUG (draw_next_screen): Final Guide Frame Coords on Canvas (x1,y1,x2,y2): {self.preview_crop_guide_coords}")
        # --- ガイド枠描画ここまで ---

        # シャッターボタン
        self.canvas.create_rectangle(300, 450, 500, 500, fill="red", outline="black", tags="shutter")
        self.canvas.create_text(400, 475, text="シャッター！", font=font_subject, fill="white", tags="shutter")

        # 戻るボタン
        self.canvas.create_rectangle(50, 530, 250, 580, fill="lightblue", outline="black", tags="back_to_main")
        self.canvas.create_text(150, 555, text="← もどる", font=font_subject, fill="black", tags="back_to_main")

        # メッセージ表示用テキストオブジェクト (最初は空)
        self.message_id = self.canvas.create_text(400, 555, text="", font=("Helvetica", 16), fill="red")

        self.audio.play_voice("audio/voiceset/make/make_sample.wav")

    def draw_explanation_screen(self):
        self.canvas.delete("all")
        self.current_screen = "explanation"
        self.explanation_detection_count = 0  # カウントをリセット
        self.last_detected_explanation_flag = None # 最後に検出されたフラグをリセット
        # カメラ関連の表示オブジェクトをリセット
        self.cam_feed_image_id = None
        self.explanation_cam_feed_image_id = None
        self.image_tk = None # PhotoImage参照もクリア


        # 背景画像の設定
        explanation_bg_path = "image/background_explanation.jpg" # 説明画面専用の背景
        try:
            bg_image_path_to_load = explanation_bg_path if os.path.exists(explanation_bg_path) else "image/background.jpg"
            if not os.path.exists(bg_image_path_to_load):
                print(f"Critical: Fallback background {bg_image_path_to_load} not found for explanation screen.")
                self.canvas.config(bg="lightgrey")
            else:
                bg_image = Image.open(bg_image_path_to_load)
                bg_image = bg_image.resize((800, 600), Image.Resampling.LANCZOS)
                self.bg_next_screen_tk = ImageTk.PhotoImage(bg_image) # 参照を保持
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_next_screen_tk)
                self.canvas.lower(self.bg_next_screen_tk)
        except Exception as e:
            print(f"Error loading explanation background: {e}")
            self.canvas.config(bg="lightgrey")

        self.canvas.create_text(400, 50, text="しりたい こっき を かざしてね！", font=font_title, fill="black")

        # カメラプレビューエリアの設定 (サイズを調整)
        self.cam_x = 400
        self.cam_y = 250 # 少し上に移動
        self.cam_width = 400 # 幅を小さく
        self.cam_height = 300 # 高さを小さく

        self.canvas.create_rectangle(
            self.cam_x - self.cam_width // 2, self.cam_y - self.cam_height // 2,
            self.cam_x + self.cam_width // 2, self.cam_y + self.cam_height // 2,
            fill="black", outline="grey", tags="explanation_camera_bg_rect"
        )
        # テキストを画面の下中央に配置
        self.explanation_screen_message_id = self.canvas.create_text(
            400, 500, # 画面下中央に配置
            text="カメラ準備中...", fill="white", font=font_subject
        )
        self.explanation_cam_feed_image_id = None # Explanation screen's camera image ID
        self.image_tk = None # PhotoImage reference

        # 戻るボタンを左下に配置
        self.canvas.create_rectangle(50, 530, 250, 580, fill="lightblue", outline="black", tags="back_to_main_from_explanation")
        self.canvas.create_text(150, 555, text="← もどる", font=font_subject, fill="black", tags="back_to_main_from_explanation")

        #self.audio.play_voice("audio/voiceset/others/hold_flag.wav")


    def draw_result_screen(self):
        """検知成功後に表示する結果画面を描画する"""
        self.canvas.delete("all")
        self.current_screen = "result"
        # カメラ関連の表示オブジェクトをリセット
        self.cam_feed_image_id = None
        self.explanation_cam_feed_image_id = None
        self.image_tk = None # PhotoImage参照もクリア


        try:
            background_path = "image/background.jpg"
            if os.path.exists(background_path):
                bg_image = Image.open(background_path)
                bg_image = bg_image.resize((800, 600), Image.Resampling.LANCZOS)
                self.bg_result_screen_tk = ImageTk.PhotoImage(bg_image)
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_result_screen_tk)
                self.canvas.lower(self.bg_result_screen_tk)
            else:
                self.canvas.config(bg="lightyellow")
                print(f"Warning: Result screen background image not found: {background_path}")
        except Exception as e:
            print(f"Error loading background for result screen: {e}")
            self.canvas.config(bg="lightyellow")

        flag_name = self.flag_map.get(self.blocknumber, "不明な国")
        flag_name_en = self.flag_map[self.blocknumber]
        flag_name_jp = self.flag_names_jp.get(flag_name_en, flag_name_en)  # 日本語がなければ英語を使う
        self.canvas.create_text(400, 80,
                                 text=f"「{flag_name_jp}」をゲットしたよ！",
                                 font=font_title, fill="darkgreen")

        self.canvas.create_text(400, 150,
                                 text=f"国旗(こっき)の番号(ばんごう): {self.blocknumber}",
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

        self.canvas.after(300, lambda: self.audio.play_voice(f"audio/voiceset/get/get_{flag_name}.wav"))

    def detail_screen(self):
        # 国のデータ（画像ファイル・説明文）
        countries = {
            "Japan":[
                {
                    "name": "にほん",
                    "image": "image/sushi.jpg",
                    "text": "お寿司（すし）やおにぎりが大好きな、ごはんの国だよ。",
                    "voice": "audio/voiceset/introduction/intro_Japan/intro_Japan1.wav"
                },
                {
                    "name": "にほん（富士山）",
                    "image": "image/fuji.jpg",
                    "text": "富士山（ふじさん）という大きな山がぽっこりそびえているよ。",
                    "voice": "audio/voiceset/introduction/intro_Japan/intro_Japan2.wav"
                },
                {
                    "name": "にほん（春）",
                    "image": "image/Japan_town.jpg",
                    "text": "春には桜（さくら）がたくさん咲（さ）いて、\nピンクの景色（けしき）だよ。",
                    "voice": "audio/voiceset/introduction/intro_Japan/intro_Japan3.wav"
                },
            ],
        # 他の国を追加したければここに辞書を追加！
            "Sweden":[
                {
                    "name": "スウェーデン",
                    "image": "image/オーロラ.jpg",
                    "text": "オーロラが見（み）られる、星空（ほしぞら）がきれいな国だよ。",
                    "voice": "audio/voiceset/introduction/intro_Sweden/intro_Sweden1.wav"
                },
                {
                    "name": "スウェーデン（動物）",
                    "image": "image/鹿.jpg",
                    "text": "森（もり）でクマやトナカイに会（あ）えるかもしれないよ。",
                    "voice": "audio/voiceset/introduction/intro_Sweden/intro_Sweden2.wav"
                },
                {
                    "name": "スウェーデン（イケア）",
                    "image": "image/IKEA.jpg",
                    "text": "イケア（IKEA）の家具（かぐ）をつくる、デザインの国だよ。",
                    "voice": "audio/voiceset/introduction/intro_Sweden/intro_Sweden3.wav"
                },
            ],
            "Estonia":[
                {
                    "name": "エストニア",
                    "image": "image/森.jpg",
                    "text": "森（もり）と湖（みずうみ）がたくさんある、\n自然（しぜん）あふれる国だよ。",
                    "voice": "audio/voiceset/introduction/intro_Estonia/intro_Estonia1.wav"
                },
                {
                    "name": "エストニア（お菓子）",
                    "image": "image/カレフ.jpg",
                    "text": "かわいいお菓子（おかし）「カレフ」を楽しめるよ。",
                    "voice": "audio/voiceset/introduction/intro_Estonia/intro_Estonia2.wav"
                },
                {
                    "name": "エストニア（教育）",
                    "image": "image/図書館.jpg",
                    "text": "デジタル大国（たいこく）で、\n学校の宿題（しゅくだい）もインターネットでできるよ。",
                    "voice": "audio/voiceset/introduction/intro_Estonia/intro_Estonia3.wav"
                },
            ],
            "Oranda":[
                {
                    "name": "オランダ",
                    "image": "image/チューリップ.jpg",
                    "text": "風車とチューリップがいっぱいの、カラフルなお花の国だよ。",
                    "voice": "audio/voiceset/introduction/intro_Oranda/intro_Oranda1.wav"
                } ,
                {
                    "name": "オランダ（自転車）",
                    "image": "image/自転車.jpg",
                    "text": "自転車に乗る人が多くて、どこへでもペダルでおさんぽできるよ。",
                    "voice": "audio/voiceset/introduction/intro_Oranda/intro_Oranda2.wav"
                },
                {
                    "name": "オランダ（運河）",
                    "image": "image/街並み.jpg",
                    "text": "運河（うんが）に小舟（こぶね）を浮かべて、水の上をわたれるよ。",
                    "voice": "audio/voiceset/introduction/intro_Oranda/intro_Oranda3.wav"
                },
            ],
            "Germany":[
                {
                    "name": "ドイツ",
                    "image": "image/城.jpg",
                    "text": "お城（しろ）が山（やま）や川（かわ）のそばにたくさんあるよ。",
                    "voice": "audio/voiceset/introduction/intro_Germany/intro_Germany1.wav"
                },
                {
                    "name": "ドイツ（食べ物）",
                    "image": "image/ソーセージ.jpg",
                    "text": "ソーセージやプレッツェルをもぐもぐおいしく食（た）べられるよ。",
                    "voice": "audio/voiceset/introduction/intro_Germany/intro_Germany2.wav"
                },
                {
                    "name": "ドイツ（街）",
                    "image": "image/ド街並み.jpg",
                    "text": "森の中を走る汽車（きしゃ）や、\n大きなクリスマスマーケットがあるよ。",
                    "voice": "audio/voiceset/introduction/intro_Germany/intro_Germany3.wav"
                },
            ],
            "Denmark":[
                {
                    "name": "デンマーク",
                    "image": "image/人魚.jpg",
                    "text": "おとぎ話（ばなし）の人魚姫（ひめ）や\nお城（しろ）がある、メルヘンの国だよ。",
                    "voice": "audio/voiceset/introduction/intro_Denmark/intro_Denmark1.wav"
                },
                {
                    "name": "デンマーク（自転車）",
                    "image": "image/お城.jpg",
                    "text": "自転車（じてんしゃ）で町（まち）を走（はし）るのが\nとっても上手（じょうず）だよ。",
                    "voice": "audio/voiceset/introduction/intro_Denmark/intro_Denmark2.wav"
                },
                {
                    "name": "デンマーク（レゴ）",
                    "image": "image/レゴ.jpg",
                    "text": "レゴの本社（ほんしゃ）があって、\nブロックで遊（あそ）ぶのが大好きだよ。",
                    "voice": "audio/voiceset/introduction/intro_Denmark/intro_Denmark3.wav"
                },
            ]
        }
        self.current_screen = "detail"
        self.canvas.delete("all")
        self.image_refs.clear()
        # カメラ関連の表示オブジェクトをリセット
        self.cam_feed_image_id = None
        self.explanation_cam_feed_image_id = None
        self.image_tk = None # PhotoImage参照もクリア


        flag_name = self.flag_map.get(self.blocknumber, "Unknown")
        # 2. 国旗画像を薄く加工して背景として表示

        flag_bg_path = f"image/{flag_name}.png"  # 国旗画像パスの例。ファイル構成に合わせて変えてください。

        try:
            flag_bg_img = Image.open(flag_bg_path).resize((800,600)).convert("RGBA")

        # 透明度を下げる（アルファ値を40%に）
            alpha = flag_bg_img.split()[3].point(lambda p: p * 0.4)  # 0.4は透明度調整。0=透明,1=不透明
            flag_bg_img.putalpha(alpha)

            flag_bg_tk = ImageTk.PhotoImage(flag_bg_img)
            self.image_refs.append(flag_bg_tk)
            # 白枠の中（中央）に国旗を表示
            self.canvas.create_image(400, 300, image=flag_bg_tk, anchor=tk.CENTER)
        except Exception as e:
            print(f"国旗画像の読み込み失敗: {e}")


        flag_name_en = self.flag_map[self.blocknumber]
        flag_name_jp = self.flag_names_jp.get(flag_name_en, flag_name_en)  # 日本語がなければ英語を使う

        # メインタイトルを黒で表示
        self.canvas.create_text(400, 50, text=f"{flag_name_jp} について", font=font_title, fill="black")

        selected_info = random.choice(countries[flag_name])

        img = Image.open(selected_info["image"]).resize((300,300))
        img_tk = ImageTk.PhotoImage(img)
        self.image_refs.append(img_tk)

        self.canvas.create_image(400, 250, image=img_tk, anchor=tk.CENTER)
        self.canvas.create_text(430, 430, text=selected_info["text"], font=font_subject, fill="black")

        self.canvas.create_rectangle(300, 500, 500, 550, fill="lightblue", outline="black", tags="back_to_main")
        self.canvas.create_text(400, 525, text="メインにもどる", font=font_subject, fill="black", tags="back_to_main")

        self.audio.stop_bgm()
        self.audio.play_bgm(f"audio/bgmset/{flag_name}.mp3")
        self.audio.play_voice(selected_info["voice"])


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
            if tag == "explanation_button":
                print("Explanation button clicked. Navigating to explanation screen.")
                self.draw_explanation_screen()
                return
            
            if tag == "reset_button":
                print("Reset button clicked.")
                self.reset_all()
                return

            for num, name in self.flag_map.items():
                if tag == name:
                    self.blocknumber = num
                    print(f"Selected flag: {name} (Block number: {self.blocknumber})")

                    # ここで分岐：画像がキャプチャ済みなら詳細画面、それ以外は撮影画面
                    if self.captured_images.get(name):
                        self.detail_screen()
                    else:
                        self.draw_next_screen()
                    return  # 必須：1つ見つかったら終了

            print(f"Unhandled click on main screen with tag: {tag}")

        elif self.current_screen == "next":
            if tag == "shutter":
                print("Shutter button clicked")
                self.capture_shutter()
            elif tag == "back_to_main":
                print("Back to main clicked from next screen")
                self.draw_main_screen()

        elif self.current_screen == "result":
            if tag == "back_to_main_from_result":
                print("Back to main from result screen clicked")
                self.draw_main_screen()

        elif self.current_screen == "detail":
            if tag == "back_to_main":
                print("Back to main from detail clicked")
                self.draw_main_screen()

        elif self.current_screen == "explanation":
            if tag == "back_to_main_from_explanation":
                print("Back to main from explanation screen clicked")
                self.draw_main_screen()


    def capture_shutter(self):
        if self.last_frame is None:
            if self.message_id and self.canvas.winfo_exists(): self.canvas.itemconfig(self.message_id, text="カメラの じゅんびができてないよ")
            return
        if self.blocknumber is None:
            if self.message_id and self.canvas.winfo_exists(): self.canvas.itemconfig(self.message_id, text="エラー: フラッグが選択されていません")
            return

        expected_flag = self.flag_map.get(self.blocknumber)
        flag_name_en = self.flag_map[self.blocknumber]
        flag_name_jp = self.flag_names_jp.get(flag_name_en, flag_name_en)  # 日本語がなければ英語を使う
        if not expected_flag:
            if self.message_id and self.canvas.winfo_exists(): self.canvas.itemconfig(self.message_id, text=f"エラー: 不明なブロック番号 {self.blocknumber}")
            return

        if self.message_id and self.canvas.winfo_exists():
            self.canvas.itemconfig(self.message_id, text="しゃしん を しらべてるよ...", fill='orange')
            self.audio.play_voice("audio/voiceset/others/check_picture.wav")
        
        self.root.update_idletasks()

        

        timestamp = int(time.time())
        temp_filename = f"captured_image_temp_{self.blocknumber}_{timestamp}.jpg"

        try:
            cv2.imwrite(temp_filename, self.last_frame)

            results = self.model(temp_filename, verbose=False)
            confidence_threshold = 0.4
            detected_correct_flag = False
            best_confidence = 0
            best_box = None

            if results and len(results[0].boxes) > 0:
                boxes = results[0].boxes
                for i in range(len(boxes)):
                    confidence = boxes.conf[i].item()
                    label_index = int(boxes.cls[i].item())
                    object_type = self.model.names.get(label_index, "Unknown")
                    if object_type == expected_flag and confidence >= confidence_threshold:
                        if confidence > best_confidence:
                            best_confidence = confidence
                            detected_correct_flag = True
                            best_box = boxes.xyxy[i].tolist()


            # `capture_shutter` 関数の中のこの部分を修正
            if detected_correct_flag and best_box: # Ensure best_box is not None
                if self.message_id and self.canvas.winfo_exists(): self.canvas.itemconfig(self.message_id, text=f"{flag_name_jp} をみつけた！ しょりちゅう...", fill='blue')
                self.root.update_idletasks()
                try:
                    # ★★★ 修正点: with構文を使ってファイルを自動で閉じる ★★★
                    with Image.open(temp_filename) as img_pil_original_capture:
                        original_capture_width, original_capture_height = img_pil_original_capture.size

                        if self.preview_crop_guide_coords is None:
                            raise ValueError("Crop guide coords not set.")
                        if self.preview_paste_info['w'] == 0 or self.preview_paste_info['h'] == 0:
                            raise ValueError("Preview paste info not set or invalid (w or h is 0).")

                        preview_area_abs_x1 = self.cam_x - self.cam_width // 2
                        preview_area_abs_y1 = self.cam_y - self.cam_height // 2

                        guide_abs_x1, guide_abs_y1, guide_abs_x2, guide_abs_y2 = self.preview_crop_guide_coords

                        guide_rel_area_x1 = guide_abs_x1 - preview_area_abs_x1
                        guide_rel_area_y1 = guide_abs_y1 - preview_area_abs_y1
                        guide_rel_area_x2 = guide_abs_x2 - preview_area_abs_x1
                        guide_rel_area_y2 = guide_abs_y2 - preview_area_abs_y1

                        guide_rel_image_x1 = guide_rel_area_x1 - self.preview_paste_info['x']
                        guide_rel_image_y1 = guide_rel_area_y1 - self.preview_paste_info['y']
                        guide_rel_image_x2 = guide_rel_area_x2 - self.preview_paste_info['x']
                        guide_rel_image_y2 = guide_rel_area_y2 - self.preview_paste_info['y']

                        display_w_on_preview = self.preview_paste_info['w']
                        display_h_on_preview = self.preview_paste_info['h']

                        if display_w_on_preview <= 0 or display_h_on_preview <=0: # ゼロ除算を避ける
                            raise ValueError(f"Preview display size is zero or negative: {display_w_on_preview}x{display_h_on_preview}")

                        scale_x = original_capture_width / float(display_w_on_preview)
                        scale_y = original_capture_height / float(display_h_on_preview)

                        crop_orig_x1 = int(guide_rel_image_x1 * scale_x)
                        crop_orig_y1 = int(guide_rel_image_y1 * scale_y)
                        crop_orig_x2 = int(guide_rel_image_x2 * scale_x)
                        crop_orig_y2 = int(guide_rel_image_y2 * scale_y)

                        crop_orig_x1 = max(0, crop_orig_x1)
                        crop_orig_y1 = max(0, crop_orig_y1)
                        crop_orig_x2 = min(original_capture_width, crop_orig_x2)
                        crop_orig_y2 = min(original_capture_height, crop_orig_y2)

                        # (デバッグプリントは省略)

                        if crop_orig_x1 >= crop_orig_x2 or crop_orig_y1 >= crop_orig_y2:
                            error_msg = (f"Invalid crop dimensions after scaling. "
                                         f"CropBox:({crop_orig_x1},{crop_orig_y1},{crop_orig_x2},{crop_orig_y2}).")
                            print(f"ERROR: {error_msg}")
                            raise ValueError(error_msg)

                        cropped_img = img_pil_original_capture.crop((crop_orig_x1, crop_orig_y1, crop_orig_x2, crop_orig_y2))
                    
                    # 'with'ブロックの外に移動
                    permanent_filename_base = f"{expected_flag}_{timestamp}"
                    final_image_path = os.path.join(self.output_dir, f"guide_cropped_{permanent_filename_base}.jpg")
                    cropped_img.save(final_image_path, "JPEG", quality=90)
                    print(f"Saved guide-cropped image to: {final_image_path}")

                    self.captured_images[expected_flag] = final_image_path
                    print(f"成功！ {flag_name_jp} を追加しました。ファイル: {final_image_path}")
                    self.draw_result_screen()
                    return
                except Exception as e_process_save:
                    # (以下は変更なし)
                    print(f"ERROR during image processing/saving for {expected_flag}: {e_process_save}")
                    if self.message_id and self.canvas.winfo_exists():
                        self.canvas.itemconfig(self.message_id, text=f"エラー: {expected_flag} の 加工・保存に しっぱい...", fill='red')
            
            else:
                if self.message_id and self.canvas.winfo_exists(): self.canvas.itemconfig(self.message_id, text=f"{flag_name_jp} が みつからない or はっきりしない...", fill='red')
            


        except Exception as e:
            print(f"ERROR during capture/YOLO processing: {e}")
            if self.message_id and self.canvas.winfo_exists():
                self.canvas.itemconfig(self.message_id, text="エラー が はっせい しました", fill='red')
        finally:
            if os.path.exists(temp_filename):
                try:
                    os.remove(temp_filename)
                except Exception as e_del:
                    print(f"Warning: Error deleting temp file {temp_filename}: {e_del}")


    def _resize_with_aspect_ratio(self, pil_image, target_width, target_height, background_color="black"):
        """
        PILイメージをアスペクト比を保持してリサイズし、指定された背景色の中央に配置する。
        戻り値: PIL.Image.Image オブジェクトと、貼り付け情報。
        """
        original_w, original_h = pil_image.size
        target_aspect_ratio = float(target_width) / target_height # ターゲットエリアのアスペクト比
        original_aspect_ratio = float(original_w) / original_h

        if original_aspect_ratio > target_aspect_ratio:
            # 元画像がターゲットエリアより横長の場合 (レターボックス)
            # -> ターゲット幅いっぱいにリサイズ
            display_w = target_width
            display_h = int(target_width / original_aspect_ratio)
        else:
            # 元画像がターゲットエリアより縦長または同じアスペクト比の場合 (ピラーボックス)
            # -> ターゲット高さいっぱいにリサイズ
            display_h = target_height
            display_w = int(target_height * original_aspect_ratio)

        # アスペクト比を保持してリサイズ
        resized_image = pil_image.resize((display_w, display_h), Image.Resampling.LANCZOS)

        # 背景イメージを作成し、中央にリサイズ画像を貼り付け
        final_image = Image.new("RGB", (target_width, target_height), background_color)
        paste_x = (target_width - display_w) // 2
        paste_y = (target_height - display_h) // 2
        final_image.paste(resized_image, (paste_x, paste_y))
        
        # ★★★ 修正点: 計算した情報を返す ★★★
        return final_image, paste_x, paste_y, display_w, display_h
    
    def reset_all(self):
        """
        全てのキャプチャ画像と状態をリセットして初期状態に戻します。
        """
        # 確認ダイアログを表示
        if not messagebox.askyesno("かくにん", "ほんとうに すべてのデータをけして リセットしますか？"):
            return # 「いいえ」が押されたら何もしない

        print("--- Resetting Application State ---")
        
        # 1. キャプチャ画像の記録をリセット
        self.captured_images = {flag: None for flag in self.flag_map.values()}
        print("Captured image records have been reset.")

        # 2. `output_images` ディレクトリの中身を削除
        if os.path.isdir(self.output_dir):
            try:
                # 一度フォルダごと削除して、作り直すのが確実
                shutil.rmtree(self.output_dir)
                print(f"Directory '{self.output_dir}' and its contents have been deleted.")
                os.makedirs(self.output_dir, exist_ok=True)
                print(f"Directory '{self.output_dir}' has been recreated.")
            except Exception as e:
                print(f"Error while resetting output directory: {e}")
                messagebox.showerror("リセットエラー", f"画像の保存フォルダのリセット中にエラーがおきました。\n{e}")
        
        # 3. メイン画面を再描画して見た目を更新
        self.draw_main_screen()
        print("--- Reset Complete ---")

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
                    # If trimming fails to produce a valid image, copy original as fallback
                    shutil.copy(input_path, output_path)
                    return False # Indicate trimming itself might have an issue but we have a file
            else:
                shutil.copy(input_path, output_path)
                return True
        except Exception as e:
            print(f"Error trimming transparent image '{input_path}': {e}")
            try: # Fallback: copy original to output if trimming errors out
                shutil.copy(input_path, output_path)
                print(f"Fell back to copying original due to trim error for {input_path}")
            except Exception as e_copy:
                print(f"Error copying original file during trim fallback: {e_copy}")
            return False

    
    def update_frame(self):
        # print(f"Current time: {time.time():.2f} JST, Frame: {self.frame_count}, Screen: {self.current_screen}")

        # 遷移中の状態の場合は、UI更新をスキップして次のafterを待つ
        if self.current_screen == "transitioning":
            self.root.after(33, self.update_frame)
            return

        if not (hasattr(self, 'capture') and self.capture and self.capture.isOpened()):
            print("Camera not open, retrying in 1 second.")
            self.root.after(1000, self.update_frame)
            return

        ret, frame = self.capture.read()
        if not ret: # フレーム取得失敗の場合
            if self.current_screen in ["next", "explanation"] and self.canvas.winfo_exists():
                try:
                    target_message_id = None
                    if self.current_screen == "next":
                        target_message_id = self.message_id
                    elif self.current_screen == "explanation":
                        target_message_id = self.explanation_screen_message_id

                    if target_message_id and self.canvas.winfo_exists():
                        self.canvas.itemconfig(target_message_id, text="カメラから映像取得失敗", fill="red")
                except tk.TclError:
                    pass
            self.root.after(33, self.update_frame) # 引き続きフレーム更新を試みる
            return

        # フレームが正常に取得できた場合のみ処理を続行
        self.frame_count += 1
        self.last_frame = frame # 元解像度のフレームを保持

        if self.current_screen in ["next", "explanation"] and self.canvas.winfo_exists():
            try:
                frame_rgb = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2RGB)
                frame_image_pil = Image.fromarray(frame_rgb)

                # プレビューサイズを画面に応じて切り替え
                target_cam_width = 0
                target_cam_height = 0
                cam_feed_image_id_ref = None
                cam_feed_text_id_ref = None
                cam_x_offset = 0
                cam_y_offset = 0

                if self.current_screen == "next":
                    target_cam_width = self.cam_width
                    target_cam_height = self.cam_height
                    cam_feed_image_id_ref = "cam_feed_image_id"
                    cam_feed_text_id_ref = "cam_feed_text_id"
                    cam_x_offset = self.cam_x
                    cam_y_offset = self.cam_y
                elif self.current_screen == "explanation":
                    target_cam_width = self.cam_width # `draw_explanation_screen`で更新された値
                    target_cam_height = self.cam_height # `draw_explanation_screen`で更新された値
                    cam_feed_image_id_ref = "explanation_cam_feed_image_id"
                    cam_feed_text_id_ref = "explanation_screen_message_id"
                    cam_x_offset = self.cam_x
                    cam_y_offset = self.cam_y

                processed_preview_pil, paste_x, paste_y, display_w, display_h = self._resize_with_aspect_ratio(
                    frame_image_pil,
                    target_cam_width,
                    target_cam_height
                )
                self.preview_paste_info = {'x': paste_x, 'y': paste_y, 'w': display_w, 'h': display_h}
                self.image_tk = ImageTk.PhotoImage(image=processed_preview_pil) # 参照を保持 (重要: GC防止)

                current_cam_feed_image_id = getattr(self, cam_feed_image_id_ref)
                current_cam_feed_text_id = getattr(self, cam_feed_text_id_ref)

                # カメラフィード画像の更新または作成
                if current_cam_feed_image_id and self.canvas.winfo_exists() and self.canvas.type(current_cam_feed_image_id):
                    self.canvas.itemconfig(current_cam_feed_image_id, image=self.image_tk)
                elif self.canvas.winfo_exists():
                    setattr(self, cam_feed_image_id_ref, self.canvas.create_image(cam_x_offset, cam_y_offset, anchor=tk.CENTER, image=self.image_tk))
                    # カメラフィードのテキストがあれば削除
                    if current_cam_feed_text_id and self.canvas.winfo_exists() and self.canvas.type(current_cam_feed_text_id):
                        self.canvas.delete(current_cam_feed_text_id)
                        setattr(self, cam_feed_text_id_ref, None) # 削除したらIDをNoneにする

                if self.current_screen == "next":
                    if self.canvas.winfo_exists() and self.canvas.find_withtag("crop_guide_rect"):
                        self.canvas.tag_raise("crop_guide_rect")
                elif self.current_screen == "explanation":
                    # Explanation screen specific logic
                    # 10フレームごとにYOLO検出を実行
                    if self.frame_count % 10 == 0:
                        results = self.model(self.last_frame, verbose=False)
                        detected_flag_name = None
                        best_confidence = 0.4 # Confidence threshold for detection
                        
                        print(f"--- DEBUG (Frame {self.frame_count}): YOLO Detection Results ---")
                        if results and len(results[0].boxes) > 0:
                            current_frame_detections = []
                            for i, box in enumerate(results[0].boxes):
                                confidence = box.conf[0].item()
                                label_index = int(box.cls[0].item())
                                object_type = self.model.names.get(label_index, "Unknown")
                                current_frame_detections.append(f"   検出 {i+1}: タイプ='{object_type}', 信頼度={confidence:.2f}")

                                # 最も信頼度の高い有効なフラグを特定
                                if object_type in self.flag_map.values() and confidence > best_confidence:
                                    best_confidence = confidence
                                    detected_flag_name = object_type
                            
                            for detection_str in current_frame_detections:
                                print(detection_str)
                        else:
                            print("   検出なし")
                        
                        # 検出結果に基づいて連続カウントを更新
                        if detected_flag_name and detected_flag_name == self.last_detected_explanation_flag:
                            self.explanation_detection_count += 1
                        elif detected_flag_name: # 新しいフラグが検出された場合
                            self.last_detected_explanation_flag = detected_flag_name
                            self.explanation_detection_count = 1
                        else: # 何も検出されなかった場合、または有効なフラグが検出されなかった場合
                            self.last_detected_explanation_flag = None
                            self.explanation_detection_count = 0
                        
                        print(f"   現在の連続検出フレーム数: {self.explanation_detection_count}")
                        print("------------------------------------------")

                        # テキスト表示の更新
                        display_text = "こっき を かざしてね！"
                        fill_color = "white"
                        if self.last_detected_explanation_flag:
                            display_jp_name = self.flag_names_jp.get(self.last_detected_explanation_flag, self.last_detected_explanation_flag)
                            display_text = f"「{display_jp_name}」が検知されたよ！（連続　{self.explanation_detection_count}フレーム）"
                            fill_color = "green"
                        self.canvas.itemconfig(self.explanation_screen_message_id, text=display_text, fill=fill_color)
                        self.root.update_idletasks() # 画面表示を即時更新

                        # 9フレーム連続検出で詳細画面へ遷移
                         # 9フレーム連続検出で詳細画面へ遷移
                        if self.explanation_detection_count >= 5:
                            found_block_num = None
                            for num, name in self.flag_map.items():
                                if name == self.last_detected_explanation_flag:
                                    found_block_num = num
                                    break
                            
                            if found_block_num is not None:
                                self.blocknumber = found_block_num
                                print(f"Auto-navigating to detail screen for {self.last_detected_explanation_flag}")
                                # 中間状態やメイン画面描画を挟まず、直接詳細画面を呼び出す
                                self.detail_screen()
                                # ★★★ 修正点: returnを削除し、ループが継続するようにする ★★★
                                # return
                            else:
                                print(f"ERROR: Detected flag '{self.last_detected_explanation_flag}' not found in flag_map for transition.")
                                # マップにない国旗が検出されたが遷移できない場合、カウントをリセットして継続
                                self.last_detected_explanation_flag = None
                                self.explanation_detection_count = 0
                                if self.canvas.winfo_exists(): # ウィジェットが存在するか確認
                                    try:
                                        self.canvas.itemconfig(self.explanation_screen_message_id, text="不明な国旗です。こっき を かざしてね！", fill="red")
                                    except tk.TclError:
                                        print("Could not update explanation message; canvas item may be gone.")

            except tk.TclError as e:
                print(f"TclError updating camera feed or canvas item (item might be deleted): {e}")
                # Tkinterオブジェクトがすでに破棄されている場合に発生。画面遷移中によく起こる。
                # 参照をNoneにリセットし、次回描画時に再作成を試みる。
                self.cam_feed_image_id = None
                self.explanation_cam_feed_image_id = None
                self.image_tk = None # PhotoImage参照もクリア
            except Exception as e:
                print(f"Error in update_frame (current_screen: {self.current_screen}) : {e}")
                import traceback
                traceback.print_exc() # より詳細なエラー情報を出力

        # 継続してupdate_frameを呼び出す
        self.root.after(33, self.update_frame) # Aim for ~30 FPS

    def on_close(self):
        print("Closing application...")
        if hasattr(self, 'capture') and self.capture and self.capture.isOpened():
           #self.capture.release()
            print("Camera released.")

        print("Cleaning temporary files...")
        for item in os.listdir('.'):
            if item.startswith("captured_image_temp_") and item.endswith(".jpg"):
                try:
                    os.remove(item)
                    print(f"Deleted: {item}")
                except Exception as e:
                    print(f"Error deleting {item}: {e}")
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