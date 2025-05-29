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

        # --- Camera Setup with timing ---
        print("カメラを起動しています...")
        camera_start_time = time.time()
        
        self.capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.capture.isOpened():
            messagebox.showerror("Error", "Cannot access the camera")
            root.destroy()
            return
        
        camera_end_time = time.time()
        camera_init_time = camera_end_time - camera_start_time
        print(f"カメラの起動完了！ 所要時間: {camera_init_time:.2f}秒")

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
            if self.capture.isOpened(): self.capture.release()
            root.destroy()
            return

        # --- UI Setup ---
        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack()

        self.bg_tk = None # Placeholder for background PhotoImage
        self.bg_canvas_id = None # ID of the background image on the canvas

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

        # Check if any specific flag is captured to show its background
        # Simple logic: show the background of the *last* captured flag type if available
        last_captured_flag = None
        for flag_name in self.flag_map.values():
             if self.captured_images.get(flag_name):
                 last_captured_flag = flag_name # Keep track of the latest found

        if last_captured_flag:
            potential_path = f"image/{last_captured_flag}.jpg"
            if os.path.exists(potential_path):
                background_path = potential_path
            else:
                print(f"Warning: Background image not found for {last_captured_flag} at {potential_path}")

        # Optional: Check if ALL flags are captured for a special background
        # all_captured = all(self.captured_images.values())
        # if all_captured and os.path.exists("image/all_flags_complete.jpg"):
        #     background_path = "image/all_flags_complete.jpg"

        try:
            if not os.path.exists(background_path):
                print(f"ERROR: Background image file not found: {background_path}")
                # Fallback to a solid color if the default is missing
                self.canvas.config(bg="lightgrey")
                if self.bg_canvas_id: self.canvas.delete(self.bg_canvas_id) # Remove old image if bg fails
                self.bg_tk = None
                return

            new_bg_image = Image.open(background_path)
            new_bg_image = new_bg_image.resize((800, 600), Image.Resampling.LANCZOS)
            self.bg_tk = ImageTk.PhotoImage(new_bg_image)

            if self.bg_canvas_id and self.canvas.winfo_exists(): # Check if canvas item exists
                 # Check if the canvas item ID is still valid before configuring
                 try:
                    self.canvas.itemconfig(self.bg_canvas_id, image=self.bg_tk)
                 except tk.TclError: # Handle case where canvas item might have been deleted unexpectedly
                    print("Warning: Background canvas item not found, creating new one.")
                    self.bg_canvas_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_tk)
            else: # Create it if it doesn't exist or canvas was cleared
                 self.bg_canvas_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_tk)

            self.canvas.lower(self.bg_canvas_id) # Ensure background is behind other elements

        except Exception as e:
            print(f"Error updating background image from {background_path}: {e}")
            # Fallback in case of PIL errors etc.
            self.canvas.config(bg="lightgrey")
            if self.bg_canvas_id: self.canvas.delete(self.bg_canvas_id)
            self.bg_tk = None

    def draw_main_screen(self):
        self.canvas.delete("all") # Clear previous screen elements
        self.current_screen = "main"
        self.update_background_image() # Draw the background first

        # --- Static Text ---
        self.canvas.create_text(400, 30, text="Legoooooo Flags!", font=("Helvetica", 24, "bold"), fill="black")
        self.canvas.create_text(400, 70, text="こっきをつくろう！", font=font_subject, fill="black")
        self.canvas.create_text(400, 110, text="つくりたい くに をクリックしてね！", font=font_subject, fill="black")

        # --- Dynamic Flag Buttons/Images ---
        button_coords = {
            "Japan":   (10, top_position1, 250, top_position2),   # Top Left
            "Sweden":  (260, top_position1, 510, top_position2),  # Top Middle
            "Estonia": (520, top_position1, 770, top_position2),  # Top Right
            "Oranda": (10, bottom_position1, 250, bottom_position2), # Bottom Left
            "Germany": (260, bottom_position1, 510, bottom_position2), # Bottom Middle
            "Denmark": (520, bottom_position1, 770, bottom_position2)  # Bottom Right
        }
        button_texts = { # Japanese labels
            "Japan": "にほん", "Sweden": "ｽｳｪｰﾃﾞﾝ", "Estonia": "ｴｽﾄﾆｱ",
            "Oranda": "オランダ", "Germany": "ドイツ", "Denmark": "ﾃﾞﾝﾏｰｸ"
        }
        text_y_offset_ratio = 0.4 # Place text roughly 40% down from the top of the button height

        # Clear previous photo references
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
                # --- Display Captured Image ---
                try:
                    img = Image.open(captured_image_path)

                    # Resize to fit button area while maintaining aspect ratio
                    img.thumbnail((btn_width - 10, btn_height - 10), Image.Resampling.LANCZOS) # Use thumbnail with padding

                    img_tk = ImageTk.PhotoImage(img)
                    # Store reference dynamically using the dictionary
                    self.flag_photo_references[flag_name] = img_tk

                    # Draw the image centered in the button area
                    self.canvas.create_image(center_x, center_y, anchor=tk.CENTER, image=img_tk, tags=(flag_name, "flag_display"))

                    # Optional: Add a border around the captured image
                    self.canvas.create_rectangle(x1, y1, x2, y2, outline="green", width=2, tags=(flag_name, "flag_border")) # Green border for captured

                except Exception as e:
                    print(f"Error displaying captured image {flag_name} from {captured_image_path}: {e}")
                    # Fallback to drawing the default button if image fails to load/display
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="#FFCCCC", outline="black", stipple="gray25", tags=(flag_name, "button_fallback")) # Reddish fallback
                    self.canvas.create_text(center_x, text_y, text=f"{button_texts[flag_name]}\n(表示エラー)", font=font_subject, fill="black", tags=(flag_name, "text_fallback"))
            else:
                # --- Draw Default Button ---
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="#ADD8E6", outline="black", stipple="gray50", tags=(flag_name, "button_default")) # Light blue default
                self.canvas.create_text(center_x, text_y, text=button_texts[flag_name], font=font_title2, fill="black", tags=(flag_name, "text_default"))

        # Ensure background is lowest layer AFTER drawing everything else
        if self.bg_canvas_id:
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

        # --- Background ---
        # You can use a specific capture background or the default one
        capture_bg_path = "image/background_capture.jpg" # Or "image/background.jpg"
        try:
            bg_image = Image.open(capture_bg_path if os.path.exists(capture_bg_path) else "image/background.jpg")
            bg_image = bg_image.resize((800, 600), Image.Resampling.LANCZOS)
            self.bg_next_screen_tk = ImageTk.PhotoImage(bg_image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_next_screen_tk)
            self.canvas.lower(self.bg_next_screen_tk)
        except Exception as e:
            print(f"Error loading capture background: {e}")
            self.canvas.config(bg="lightgrey")

        # --- Instructions ---
        self.canvas.create_text(400, 30, text=f"{flag_name}: おてほん と おなじもの を つくってね", font=font_subject, fill="black")

        # --- Sample Image Display (Left) ---
        imageSizeX = 250
        imageSizeY = 200
        sample_x = 180
        sample_y = 250
        try:
            sample_image = Image.open(self.sample_image_path)
            sample_image.thumbnail((imageSizeX, imageSizeY), Image.Resampling.LANCZOS)
            sample_tk = ImageTk.PhotoImage(sample_image)
            self.sample_image_tk = sample_tk # Keep reference
            self.canvas.create_image(sample_x, sample_y, anchor=tk.CENTER, image=sample_tk)
            # Optional frame
            sw, sh = sample_image.size
            self.canvas.create_rectangle(sample_x - sw//2 - 5, sample_y - sh//2 - 5,
                                         sample_x + sw//2 + 5, sample_y + sh//2 + 5,
                                         outline="blue", width=2)
            self.canvas.create_text(sample_x, sample_y + sh//2 + 25, text="↑ おてほん ↑", font=font_subject, fill="black")
        except Exception as e:
            print(f"Sample image error for {self.sample_image_path}: {e}")
            self.canvas.create_text(sample_x, sample_y, text="サンプル画像\nエラー", font=font_subject, fill="red", justify=tk.CENTER)

        # --- Camera Feed Display (Right) ---
        self.cam_x = 600
        self.cam_y = 250
        self.cam_width = 300
        self.cam_height = 300
        self.cam_feed_rect = self.canvas.create_rectangle(self.cam_x - self.cam_width//2, self.cam_y - self.cam_height//2,
                                                           self.cam_x + self.cam_width//2, self.cam_y + self.cam_height//2,
                                                           fill="black", outline="grey")
        self.cam_feed_text_id = self.canvas.create_text(self.cam_x, self.cam_y, text="カメラ準備中...", fill="white", font=font_subject)
        self.cam_feed_image_id = None # Will hold the ID of the camera image item
        self.image_tk = None # Holds the PhotoImage for the camera feed

        # --- Buttons ---
        self.canvas.create_rectangle(300, 450, 500, 500, fill="red", outline="black", tags="shutter")
        self.canvas.create_text(400, 475, text="シャッター！", font=font_subject, fill="white", tags="shutter")

        self.canvas.create_rectangle(50, 530, 250, 580, fill="lightblue", outline="black", tags="back_to_main")
        self.canvas.create_text(150, 555, text="← もどる", font=font_subject, fill="black", tags="back_to_main")

        # --- Message area ---
        self.message_id = self.canvas.create_text(400, 555, text="", font=("Helvetica", 16), fill="red")

    def detail_screen(self):
        # This function is currently not used as capture_shutter goes back to main.
        # If you want a detail screen, call this from capture_shutter instead of draw_main_screen.
        self.current_screen = "detail"
        self.canvas.delete("all")
        flag_name = self.flag_map.get(self.blocknumber, "Unknown")
        self.canvas.create_text(400, 50, text=f"{flag_name} - 詳細", font=font_title, fill="black")
        # ... (add content like displaying the captured image larger, info etc.) ...
        # Add a back button
        self.canvas.create_rectangle(300, 500, 500, 550, fill="lightblue", outline="black", tags="back_to_main")
        self.canvas.create_text(400, 525, text="メインにもどる", font=font_subject, fill="black", tags="back_to_main")


    def mouse_event(self, event):
        x, y = event.x, event.y
        # Find the topmost item under the cursor with a tag
        items = self.canvas.find_overlapping(x, y, x, y)
        if not items: return # Clicked on empty space or background

        # Process tags of the topmost item found
        tags = self.canvas.gettags(items[-1]) # Get tags of the last (topmost) item
        if not tags: return # Item has no tags

        tag = tags[0] # Use the first tag for primary identification

        print(f"Clicked on item with tags: {tags}, primary tag: {tag}") # Debugging click

        if self.current_screen == "main":
            # Check if the clicked tag is one of the flag names
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
                print("Back to main clicked")
                self.draw_main_screen()

        elif self.current_screen == "detail": # If you implement detail screen
             if tag == "back_to_main":
                 print("Back to main from detail clicked")
                 self.draw_main_screen()

    def capture_shutter(self):
        if self.last_frame is None:
            self.canvas.itemconfig(self.message_id, text="カメラの じゅんびができてないよ")
            return
        if self.blocknumber is None:
            self.canvas.itemconfig(self.message_id, text="エラー: フラッグが選択されていません")
            return

        expected_flag = self.flag_map.get(self.blocknumber)
        if not expected_flag:
            self.canvas.itemconfig(self.message_id, text=f"エラー: 不明なブロック番号 {self.blocknumber}")
            return

        self.canvas.itemconfig(self.message_id, text="しゃしん を しらべてるよ...", fill='orange')
        self.root.update_idletasks()

        # Use a unique temp filename to avoid potential conflicts if processing is slow
        timestamp = int(time.time())
        temp_filename = f"captured_image_temp_{self.blocknumber}_{timestamp}.jpg"

        try:
            cv2.imwrite(temp_filename, self.last_frame)
            print(f"Temporary image saved: {temp_filename}")

            # --- YOLO Inference ---
            results = self.model(temp_filename, verbose=False)
            confidence_threshold = 0.4 # Increased threshold slightly
            detected_correct_flag = False
            best_confidence = 0 # Track the best confidence for the correct flag

            if results and len(results[0].boxes) > 0:
                boxes = results[0].boxes
                for i in range(len(boxes)):
                    confidence = boxes.conf[i].item()
                    label_index = int(boxes.cls[i].item())
                    object_type = self.model.names.get(label_index, "Unknown")

                    print(f"Detected: {object_type} (Confidence: {confidence:.2f})")

                    if object_type == expected_flag and confidence >= confidence_threshold:
                        if confidence > best_confidence: # Found the correct flag with high enough confidence
                            best_confidence = confidence # Update best confidence for this flag type
                            detected_correct_flag = True
                            print(f"Processing best candidate for {expected_flag} (Conf: {confidence:.2f})")

                            # Store detection details for processing *after* the loop
                            best_box = boxes.xyxy[i].tolist()
                            # Break or continue? For now, let's process the first high-confidence match.
                            # If you want the absolute highest confidence one, remove the break and store details.
                            break # Process this one

            # --- Process the best detection if found ---
            if detected_correct_flag:
                self.canvas.itemconfig(self.message_id, text=f"{expected_flag} をみつけた！ しょりちゅう...", fill='blue')
                self.root.update_idletasks()
                x1, y1, x2, y2 = map(int, best_box)

                try:
                    # 1. Crop
                    img_pil = Image.open(temp_filename)
                    if x1 >= x2 or y1 >= y2: raise ValueError("Invalid BBox")
                    cropped = img_pil.crop((x1, y1, x2, y2))
                    if cropped.width == 0 or cropped.height == 0: raise ValueError("Empty crop")

                    # 2. Remove Background
                    img_byte_arr = io.BytesIO()
                    cropped.save(img_byte_arr, format='PNG')
                    input_image_bytes = img_byte_arr.getvalue()
                    output_data = remove(input_image_bytes) # Simpler call might work

                    if not output_data: raise ValueError("rembg returned empty data.")
                    try:
                        removed_bg_img = Image.open(io.BytesIO(output_data))
                    except Exception as e_open_rembg:
                        print(f"Error opening image data from rembg: {e_open_rembg}. Falling back.")
                        removed_bg_img = cropped.convert("RGBA") # Fallback

                    # 3. Define Paths
                    # Use flag name for more descriptive output file names
                    base_output_filename = f"{expected_flag}_{timestamp}" # Add timestamp
                    raw_output_path = os.path.join(self.output_dir, f"result_{base_output_filename}.png")
                    trimmed_output_path = os.path.join(self.output_dir, f"trimmed_{base_output_filename}.png")

                    # 4. Save the non-trimmed version first
                    removed_bg_img.save(raw_output_path, "PNG")
                    print(f"Saved background-removed image: {raw_output_path}")

                    # 5. Trim Transparency
                    final_image_path = None
                    if self.trim_transparent_area(raw_output_path, trimmed_output_path):
                        final_image_path = trimmed_output_path
                        print(f"Successfully trimmed: {trimmed_output_path}")
                    else:
                        print(f"Trimming failed or not needed for {raw_output_path}, using non-trimmed.")
                        final_image_path = raw_output_path # Use the non-trimmed if trim failed

                    # *** SUCCESS ***
                    self.captured_images[expected_flag] = final_image_path # Update state
                    self.canvas.itemconfig(self.message_id, text=f"やった！ {expected_flag} をついかしたよ！", fill='green')
                    self.root.update_idletasks()
                    time.sleep(1.5) # Show success message
                    self.draw_main_screen() # Go back and refresh main screen
                    return # Exit function on success

                except (ValueError, IOError, Exception) as process_err:
                    print(f"ERROR during image processing for {expected_flag}: {process_err}")
                    self.canvas.itemconfig(self.message_id, text=f"エラー: {expected_flag} の しょりに しっぱい...", fill='red')
                    # Stay on capture screen to allow retry

            else: # Correct flag not detected with high enough confidence
                self.canvas.itemconfig(self.message_id, text=f"{expected_flag} が みつからない or はっきりしない...", fill='red')

        except Exception as e:
            print(f"ERROR during capture/YOLO: {e}")
            self.canvas.itemconfig(self.message_id, text="エラー が はっせい しました", fill='red')

        finally:
            # Clean up the temporary file
            if os.path.exists(temp_filename):
                try:
                    os.remove(temp_filename)
                    print(f"Deleted temporary file: {temp_filename}")
                except Exception as e_del:
                    print(f"Warning: Error deleting temp file {temp_filename}: {e_del}")


    def trim_transparent_area(self, input_path, output_path):
        """Trims transparent pixels around the object in a PNG image."""
        try:
            img = Image.open(input_path).convert("RGBA")
            bbox = img.getbbox()
            if bbox:
                img_cropped = img.crop(bbox)
                if img_cropped.width > 0 and img_cropped.height > 0:
                    img_cropped.save(output_path, "PNG")
                    # print(f"Trimmed image saved: {output_path}") # Less verbose
                    return True
                else:
                    print(f"Trimming resulted in empty image for {input_path}. BBox: {bbox}")
                    return False
            else:
                # print(f"No non-transparent pixels found in {input_path}. Cannot trim.") # Less verbose
                # If no transparent pixels, copy original to output path as "trimmed"
                import shutil
                shutil.copy(input_path, output_path)
                return True # Treat as success (nothing needed trimming)
        except Exception as e:
            print(f"Error trimming transparent image '{input_path}': {e}")
            return False

    def update_frame(self):
        """Reads a frame from the camera and updates the display if on the next_screen."""
        if not (self.capture and self.capture.isOpened()):
             # Handle case where camera might close unexpectedly
             if self.current_screen == "next" and self.message_id:
                 self.canvas.itemconfig(self.message_id, text="カメラ接続エラー", fill="red")
             return # Stop trying to update

        ret, frame = self.capture.read()
        if ret:
            self.frame_count += 1
            if self.frame_count % 2 == 0: # Update slightly more often for smoother feed
                self.last_frame = frame

                if self.current_screen == "next":
                    try:
                        frame_rgb = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2RGB)
                        frame_image = Image.fromarray(frame_rgb)
                        # Use dimensions defined in draw_next_screen
                        frame_image = frame_image.resize((self.cam_width, self.cam_height), Image.Resampling.NEAREST) # Nearest neighbor is faster for preview
                        frame_tk = ImageTk.PhotoImage(image=frame_image)
                        self.image_tk = frame_tk # Store reference!

                        if self.cam_feed_image_id:
                            # Update existing image item
                            self.canvas.itemconfig(self.cam_feed_image_id, image=self.image_tk)
                        else:
                            # Create image item if it doesn't exist
                            self.cam_feed_image_id = self.canvas.create_image(self.cam_x, self.cam_y, anchor=tk.CENTER, image=self.image_tk)
                            # Remove "Loading..." text only once after the first frame is shown
                            if self.cam_feed_text_id:
                                self.canvas.delete(self.cam_feed_text_id)
                                self.cam_feed_text_id = None # Prevent trying to delete again

                    except Exception as e:
                        print(f"Error updating camera feed display: {e}")
                        # Optionally display an error on the canvas itself
                        if self.cam_feed_text_id:
                             self.canvas.itemconfig(self.cam_feed_text_id, text="表示エラー")

        # Schedule the next update
        self.root.after(33, self.update_frame) # Aim for ~30 FPS

    def on_close(self):
        """Release resources and clean up on window close."""
        print("Closing application...")
        if hasattr(self, 'capture') and self.capture and self.capture.isOpened():
            self.capture.release()
            print("Camera released.")

        # Clean up any remaining temp files (more robustly)
        print("Cleaning temporary files...")
        for item in os.listdir('.'): # Check current directory
             if item.startswith("captured_image_temp_") and item.endswith(".jpg"):
                 try:
                     os.remove(item)
                     print(f"Deleted: {item}")
                 except Exception as e:
                     print(f"Error deleting {item}: {e}")

        # # Optional: Clean output directory (use carefully!)
        # if os.path.exists(self.output_dir):
        #     print(f"Cleaning output directory: {self.output_dir}")
        #     # ... (add code to remove files in self.output_dir if desired) ...

        self.root.destroy()

# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()

    # --- Fonts (using common system fonts as fallback) ---
    try:
        # Try common Japanese fonts first
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
    top_position1 = 150 # Y start for top row
    top_position2 = 300 # Y end for top row
    bottom_position1 = 320 # Y start for bottom row
    bottom_position2 = 470 # Y end for bottom row

    # --- Create and Run App ---
    app = BlockGameApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close) # Handle window close properly
    root.mainloop()