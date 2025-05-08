
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
        self.capture = cv2.VideoCapture(-1) # Try default camera
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

            self.canvas.lower(self.bg_canvas_id)

        except Exception as e:
            print(f"Error updating background image from {background_path}: {e}")
            self.canvas.config(bg="lightgrey")
            if self.bg_canvas_id and self.canvas.winfo_exists(): self.canvas.delete(self.bg_canvas_id)
            self.bg_tk = None

    def draw_main_screen(self):
        self.canvas.delete("all")
        self.current_screen = "main"
        self.update_background_image()

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

        if self.bg_canvas_id and self.canvas.winfo_exists():
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
            if not os.path.exists(bg_image_path_to_load): # Double check fallback
                print(f"Critical: Fallback background {bg_image_path_to_load} not found.")
                self.canvas.config(bg="lightgrey") # Simple fallback
            else:
                bg_image = Image.open(bg_image_path_to_load)
                bg_image = bg_image.resize((800, 600), Image.Resampling.LANCZOS)
                self.bg_next_screen_tk = ImageTk.PhotoImage(bg_image)
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_next_screen_tk)
                self.canvas.lower(self.bg_next_screen_tk)
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
            self.sample_image_tk = ImageTk.PhotoImage(sample_image_pil) # Keep reference
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

        self.canvas.create_rectangle(300, 450, 500, 500, fill="red", outline="black", tags="shutter")
        self.canvas.create_text(400, 475, text="シャッター！", font=font_subject, fill="white", tags="shutter")

        self.canvas.create_rectangle(50, 530, 250, 580, fill="lightblue", outline="black", tags="back_to_main")
        self.canvas.create_text(150, 555, text="← もどる", font=font_subject, fill="black", tags="back_to_main")

        self.message_id = self.canvas.create_text(400, 555, text="", font=("Helvetica", 16), fill="red")


    def draw_result_screen(self):
        """検知成功後に表示する結果画面を描画する"""
        self.canvas.delete("all")
        self.current_screen = "result"

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

    def detail_screen(self): # Currently unused
        self.current_screen = "detail"
        self.canvas.delete("all")
        flag_name = self.flag_map.get(self.blocknumber, "Unknown")
        self.canvas.create_text(400, 50, text=f"{flag_name} - 詳細", font=font_title, fill="black")
        self.canvas.create_rectangle(300, 500, 500, 550, fill="lightblue", outline="black", tags="back_to_main")
        self.canvas.create_text(400, 525, text="メインにもどる", font=font_subject, fill="black", tags="back_to_main")


    def mouse_event(self, event):
        x, y = event.x, event.y
        items = self.canvas.find_overlapping(x, y, x, y)
        if not items: return

        tags = self.canvas.gettags(items[-1])
        if not tags: return

        tag = tags[0]
        print(f"Clicked on item with tags: {tags}, primary tag: {tag} on screen: {self.current_screen}")

        if self.current_screen == "main":
            found_flag = False
            for num, name in self.flag_map.items():
                if tag == name:
                    self.blocknumber = num
                    print(f"Selected flag: {name} (Block number: {self.blocknumber})")
                    self.draw_next_screen()
                    found_flag = True
                    break
            if not found_flag:
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

    def capture_shutter(self):
        if self.last_frame is None:
            if self.message_id and self.canvas.winfo_exists(): self.canvas.itemconfig(self.message_id, text="カメラの じゅんびができてないよ")
            return
        if self.blocknumber is None:
            if self.message_id and self.canvas.winfo_exists(): self.canvas.itemconfig(self.message_id, text="エラー: フラッグが選択されていません")
            return

        expected_flag = self.flag_map.get(self.blocknumber)
        if not expected_flag:
            if self.message_id and self.canvas.winfo_exists(): self.canvas.itemconfig(self.message_id, text=f"エラー: 不明なブロック番号 {self.blocknumber}")
            return

        if self.message_id and self.canvas.winfo_exists(): self.canvas.itemconfig(self.message_id, text="しゃしん を しらべてるよ...", fill='orange')
        self.root.update_idletasks()

        timestamp = int(time.time())
        temp_filename = f"captured_image_temp_{self.blocknumber}_{timestamp}.jpg"

        try:
            cv2.imwrite(temp_filename, self.last_frame)
            print(f"Temporary image saved: {temp_filename}")

            results = self.model(temp_filename, verbose=False)
            confidence_threshold = 0.4
            detected_correct_flag = False
            best_confidence = 0
            best_box = None # Initialize best_box

            if results and len(results[0].boxes) > 0:
                boxes = results[0].boxes
                for i in range(len(boxes)):
                    confidence = boxes.conf[i].item()
                    label_index = int(boxes.cls[i].item())
                    object_type = self.model.names.get(label_index, "Unknown")
                    print(f"Detected: {object_type} (Confidence: {confidence:.2f})")

                    if object_type == expected_flag and confidence >= confidence_threshold:
                        if confidence > best_confidence:
                            best_confidence = confidence
                            detected_correct_flag = True
                            best_box = boxes.xyxy[i].tolist() # Store the box coordinates
                            # Don't break here if you want the absolute best confidence among multiple detections
                            # For now, let's assume the first good one is fine or update as we go.
                            # If multiple high-confidence are found, this will pick the last one iterated.
                            # To pick the absolute best, remove the break and do processing after loop.
                            # For simplicity, we'll process if detected_correct_flag is True after the loop.


            if detected_correct_flag and best_box: # Ensure best_box is not None
                if self.message_id and self.canvas.winfo_exists(): self.canvas.itemconfig(self.message_id, text=f"{expected_flag} をみつけた！ しょりちゅう...", fill='blue')
                self.root.update_idletasks()
                x1, y1, x2, y2 = map(int, best_box)

                try:
                    img_pil = Image.open(temp_filename)
                    if x1 >= x2 or y1 >= y2: raise ValueError("Invalid BBox")
                    cropped = img_pil.crop((x1, y1, x2, y2))
                    if cropped.width == 0 or cropped.height == 0: raise ValueError("Empty crop")

                    img_byte_arr = io.BytesIO()
                    cropped.save(img_byte_arr, format='PNG')
                    input_image_bytes = img_byte_arr.getvalue()
                    output_data = remove(input_image_bytes)

                    if not output_data: raise ValueError("rembg returned empty data.")
                    try:
                        removed_bg_img = Image.open(io.BytesIO(output_data))
                    except Exception as e_open_rembg:
                        print(f"Error opening image data from rembg: {e_open_rembg}. Falling back.")
                        removed_bg_img = cropped.convert("RGBA")

                    base_output_filename = f"{expected_flag}"
                    raw_output_path = os.path.join(self.output_dir, f"result_{base_output_filename}.png")
                    trimmed_output_path = os.path.join(self.output_dir, f"trimmed_{base_output_filename}.png")

                    removed_bg_img.save(raw_output_path, "PNG")
                    print(f"Saved background-removed image: {raw_output_path}")

                    final_image_path = None
                    if self.trim_transparent_area(raw_output_path, trimmed_output_path):
                        final_image_path = trimmed_output_path
                        print(f"Successfully trimmed: {trimmed_output_path}")
                    else:
                        print(f"Trimming failed or not needed for {raw_output_path}, using non-trimmed.")
                        final_image_path = raw_output_path

                    self.captured_images[expected_flag] = final_image_path
                    print(f"成功！ {expected_flag} を追加しました。ファイル: {final_image_path}")
                    self.draw_result_screen()
                    return

                except (ValueError, IOError, Exception) as process_err:
                    print(f"ERROR during image processing for {expected_flag}: {process_err}")
                    if self.message_id and self.canvas.winfo_exists(): self.canvas.itemconfig(self.message_id, text=f"エラー: {expected_flag} の しょりに しっぱい...", fill='red')

            else:
                if self.message_id and self.canvas.winfo_exists(): self.canvas.itemconfig(self.message_id, text=f"{expected_flag} が みつからない or はっきりしない...", fill='red')

        except Exception as e:
            print(f"ERROR during capture/YOLO: {e}")
            if self.message_id and self.canvas.winfo_exists(): self.canvas.itemconfig(self.message_id, text="エラー が はっせい しました", fill='red')

        finally:
            if os.path.exists(temp_filename):
                try:
                    os.remove(temp_filename)
                    print(f"Deleted temporary file: {temp_filename}")
                except Exception as e_del:
                    print(f"Warning: Error deleting temp file {temp_filename}: {e_del}")


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
        if not (hasattr(self, 'capture') and self.capture and self.capture.isOpened()):
             if self.current_screen == "next" and hasattr(self, 'message_id') and self.message_id and self.canvas.winfo_exists():
                 try:
                     self.canvas.itemconfig(self.message_id, text="カメラ接続エラー", fill="red")
                 except tk.TclError: pass # Canvas item might be gone
             self.root.after(1000, self.update_frame) # Try reconnecting/checking less often
             return

        ret, frame = self.capture.read()
        if ret:
            self.frame_count += 1
            # Process every frame or every Nth frame
            # if self.frame_count % 2 == 0: # Example: process every other frame
            self.last_frame = frame

            if self.current_screen == "next" and self.canvas.winfo_exists(): # Ensure canvas is still there
                try:
                    frame_rgb = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2RGB)
                    frame_image_pil = Image.fromarray(frame_rgb)
                    frame_image_pil = frame_image_pil.resize((self.cam_width, self.cam_height), Image.Resampling.NEAREST)
                    self.image_tk = ImageTk.PhotoImage(image=frame_image_pil) # Keep reference

                    if self.cam_feed_image_id and self.canvas.winfo_exists() and self.canvas.type(self.cam_feed_image_id):
                        self.canvas.itemconfig(self.cam_feed_image_id, image=self.image_tk)
                    elif self.canvas.winfo_exists(): # Create if not exists or was deleted
                        self.cam_feed_image_id = self.canvas.create_image(self.cam_x, self.cam_y, anchor=tk.CENTER, image=self.image_tk)
                        if self.cam_feed_text_id and self.canvas.winfo_exists() and self.canvas.type(self.cam_feed_text_id):
                            self.canvas.delete(self.cam_feed_text_id)
                            self.cam_feed_text_id = None
                except tk.TclError as e: # Handle cases where canvas items might be deleted
                    print(f"TclError updating camera feed (item might be deleted): {e}")
                    self.cam_feed_image_id = None # Reset so it gets recreated
                except Exception as e:
                    print(f"Error updating camera feed display: {e}")
                    if self.cam_feed_text_id and self.canvas.winfo_exists() and self.canvas.type(self.cam_feed_text_id):
                         self.canvas.itemconfig(self.cam_feed_text_id, text="表示エラー")
        else:
            # print("Failed to retrieve frame from camera.") # Can be noisy
            if self.current_screen == "next" and hasattr(self, 'message_id') and self.message_id and self.canvas.winfo_exists():
                try:
                     self.canvas.itemconfig(self.message_id, text="カメラから映像取得失敗", fill="red")
                except tk.TclError: pass


        self.root.after(33, self.update_frame) # Aim for ~30 FPS

    def on_close(self):
        print("Closing application...")
        if hasattr(self, 'capture') and self.capture and self.capture.isOpened():
            self.capture.release()
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
