import tkinter as tk
from tkinter import messagebox, font
from PIL import Image, ImageTk, ImageFont
import cv2
import numpy as np
import os
from ultralytics import YOLO
from rembg import remove

class BlockGameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Block Game")

        # Initial setup
        self.current_screen = "main"
        self.blocknumber = None # 0 for house, 1 for cars
        self.sample_image_path = None
        self.last_frame = None
        self.frame_count = 0
        # Store paths to the processed (background removed, trimmed) captured images
        self.captured_images = {"house": None, "cars": None}
        # Try camera index 1 first, then 0 if needed (common setup)
        self.capture = cv2.VideoCapture(1)
        if not self.capture.isOpened():
            print("Warning: Camera index 1 failed, trying index 0.")
            self.capture = cv2.VideoCapture(0)
            if not self.capture.isOpened():
                messagebox.showerror("Error", "Cannot access the camera")
                root.destroy()
                return # Stop initialization if camera fails

        # Load YOLO model (make sure 'bestbest.pt' is in the correct path)
        try:
            self.model = YOLO('bestbest.pt')
        except Exception as e:
             messagebox.showerror("Error", f"Failed to load YOLO model 'bestbest.pt': {e}")
             root.destroy()
             return

        # Output directory for processed images
        self.output_dir = "output_images"
        os.makedirs(self.output_dir, exist_ok=True)

        # Main canvas
        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack()

        # Load initial background image (Keep reference)
        self.bg_tk = None
        self.update_background_image() # Load initial background

        # --- Keep references to images to prevent garbage collection ---
        self.house_image_tk = None
        self.cars_image_tk = None
        self.bg_next_screen_tk = None
        self.image_tk = None
        self.sample_image_tk = None
        # --- ---

        # Draw the initial screen
        self.draw_main_screen()

        # Mouse click event
        self.canvas.bind("<Button-1>", self.mouse_event)

        # Start frame update loop
        self.update_frame()

    def update_background_image(self):
        """Dynamically selects and loads the main background image based on captured items."""
        if self.captured_images["house"] and self.captured_images["cars"]:
            background_path = "image/house_car_less.jpg"
        elif self.captured_images["house"]:
            background_path = "image/house_less.jpg"
        elif self.captured_images["cars"]:
            background_path = "image/car_less.jpg"
        else:
            background_path = "image/town.jpg"  # Initial background

        try:
            new_bg_image = Image.open(background_path)
            new_bg_image = new_bg_image.resize((800, 600))
            self.bg_tk = ImageTk.PhotoImage(new_bg_image) # Update reference
        except FileNotFoundError:
             print(f"Error: Background image not found at {background_path}. Using default white.")
             # Create a fallback white image if needed
             new_bg_image = Image.new('RGB', (800, 600), color = 'white')
             self.bg_tk = ImageTk.PhotoImage(new_bg_image)
        except Exception as e:
            print(f"Error loading background image '{background_path}': {e}")
            # Fallback
            new_bg_image = Image.new('RGB', (800, 600), color = 'white')
            self.bg_tk = ImageTk.PhotoImage(new_bg_image)

    def draw_main_screen(self):
        """Draws the main screen with dynamic background and buttons/images."""
        self.update_background_image() # Ensure background is up-to-date
        self.canvas.delete("all")
        self.current_screen = "main"

        # Draw background image
        if self.bg_tk:
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_tk)
        else:
             # Draw fallback background if image failed to load
             self.canvas.create_rectangle(0, 0, 800, 600, fill="white", outline="")


        # Text
        self.canvas.create_text(400, 30, text="Legoooooo", font=("Helvetica", 24), fill="black")
        self.canvas.create_text(420, 70, text="まちをかんせいさせよう！", font=font_subject, fill="black")

        # Buttons and images
        house_button_coords = (270, 90, 570, 440) # x1, y1, x2, y2
        cars_button_coords = (240, 440, 500, 560) # x1, y1, x2, y2

        # House button/image
        if self.captured_images["house"]:
            try:
                # Display captured house image, fitting within button area
                house_image = Image.open(self.captured_images["house"])
                # Calculate aspect ratio to fit
                img_w, img_h = house_image.size
                box_w = house_button_coords[2] - house_button_coords[0]
                box_h = house_button_coords[3] - house_button_coords[1]
                scale = min(box_w / img_w, box_h / img_h)
                new_w, new_h = int(img_w * scale * 0.9), int(img_h * scale * 0.9) # Add some padding
                house_image = house_image.resize((new_w, new_h))

                self.house_image_tk = ImageTk.PhotoImage(house_image) # Keep reference
                # Center the image in the button area
                center_x = (house_button_coords[0] + house_button_coords[2]) / 2
                center_y = (house_button_coords[1] + house_button_coords[3]) / 2
                self.canvas.create_image(center_x, center_y, anchor=tk.CENTER, image=self.house_image_tk)
                # Transparent button overlay for clicking
                self.canvas.create_rectangle(*house_button_coords, fill="", outline="", tags="house_area") # Use different tag if needed
            except Exception as e:
                print(f"Error displaying captured house image: {e}")
                # Draw placeholder button if image fails
                self.draw_placeholder_button("house", house_button_coords)
        else:
            # Draw house placeholder button
            self.draw_placeholder_button("house", house_button_coords)


        # Car button/image
        if self.captured_images["cars"]:
            try:
                 # Display captured cars image
                cars_image = Image.open(self.captured_images["cars"])
                # Calculate aspect ratio to fit
                img_w, img_h = cars_image.size
                box_w = cars_button_coords[2] - cars_button_coords[0]
                box_h = cars_button_coords[3] - cars_button_coords[1]
                scale = min(box_w / img_w, box_h / img_h)
                new_w, new_h = int(img_w * scale * 0.9), int(img_h * scale * 0.9) # Add some padding
                cars_image = cars_image.resize((new_w, new_h))

                self.cars_image_tk = ImageTk.PhotoImage(cars_image) # Keep reference
                 # Center the image in the button area
                center_x = (cars_button_coords[0] + cars_button_coords[2]) / 2
                center_y = (cars_button_coords[1] + cars_button_coords[3]) / 2
                self.canvas.create_image(center_x, center_y, anchor=tk.CENTER, image=self.cars_image_tk)
                 # Transparent button overlay for clicking
                self.canvas.create_rectangle(*cars_button_coords, fill="", outline="", tags="cars_area") # Use different tag if needed
            except Exception as e:
                print(f"Error displaying captured cars image: {e}")
                # Draw placeholder button if image fails
                self.draw_placeholder_button("cars", cars_button_coords)
        else:
            # Draw car placeholder button
            self.draw_placeholder_button("cars", cars_button_coords)

    def draw_placeholder_button(self, item_type, coords):
        """Helper function to draw the placeholder buttons"""
        x1, y1, x2, y2 = coords
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        if item_type == "house":
            color = "#ADD8E6" # Light blue
            text = "🏠️おうち"
            stipple_pattern = tome_home # Use global variable for stipple
            tag = "house"
        elif item_type == "cars":
            color = "#90EE90" # Light green
            text = "🚗くるま"
            stipple_pattern = tome_car # Use global variable for stipple
            tag = "cars"
        else:
            return # Unknown type

        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black", stipple=stipple_pattern, tags=tag)
        self.canvas.create_text(center_x, center_y, text=text, font=font_title2, fill="black", tags=tag) # Add tag to text too


    def draw_next_screen(self):
        """Draws the screen for capturing a specific block."""
        self.canvas.delete("all")
        self.current_screen = "next"

        # Background image for the capture screen (sample.jpg)
        try:
            bg_image = Image.open("sample.jpg") # Use a neutral/instructional background
            bg_image = bg_image.resize((800, 600))
            self.bg_next_screen_tk = ImageTk.PhotoImage(bg_image) # Keep reference
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_next_screen_tk)
        except Exception as e:
            print(f"Error loading sample.jpg background: {e}. Using light green.")
            self.canvas.create_rectangle(0, 0, 800, 600, fill="lightgreen", outline="")

        # Instructions
        self.canvas.create_text(400, 30, text="ひだりのおてほんとおなじものをつくってね", font=font_subject, fill="black")
        instruction_y = 80
        if self.blocknumber == 0: # House
            self.canvas.create_text(240, instruction_y, text="まえからとってね！", font=font_subject, fill="black")
            self.sample_image_path = "image/house.png"
            imageSizeX, imageSizeY = 300, 300
        elif self.blocknumber == 1: # Cars
            self.canvas.create_text(240, instruction_y, text="よこむきにとってね！", font=font_subject, fill="black")
            self.sample_image_path = "image/car.png"
            imageSizeX, imageSizeY = 400, 400 # Car sample might be wider

        # Display camera feed on the right (placeholder initially)
        cam_x, cam_y, cam_w, cam_h = 550, 200, 300, 300 # Center coords and size
        self.canvas.create_rectangle(cam_x - cam_w//2, cam_y - cam_h//2,
                                     cam_x + cam_w//2, cam_y + cam_h//2,
                                     fill="gray", outline="black")
        self.canvas.create_text(cam_x, cam_y, text="Camera Feed", font=("Helvetica", 14), fill="white")
        # The actual feed will be drawn by update_frame

        # Display Sample image on the left
        sample_frame_coords = (100, 100, 400, 400) # x1, y1, x2, y2 for the frame
        sx1, sy1, sx2, sy2 = sample_frame_coords
        self.canvas.create_rectangle(sx1, sy1, sx2, sy2, fill="white", outline="black", width=4)

        if self.sample_image_path:
            try:
                sample_image = Image.open(self.sample_image_path)
                # Resize sample image to fit within the defined frame, preserving aspect ratio
                sample_image.thumbnail((sx2 - sx1 - 10, sy2 - sy1 - 10)) # Add padding

                self.sample_image_tk = ImageTk.PhotoImage(sample_image) # Keep reference
                # Place the sample image in the center of the frame
                self.canvas.create_image((sx1 + sx2) // 2, (sy1 + sy2) // 2, anchor=tk.CENTER, image=self.sample_image_tk)

            except FileNotFoundError:
                 print(f"Sample image error: File not found at {self.sample_image_path}")
                 self.canvas.create_text((sx1 + sx2) // 2, (sy1 + sy2) // 2, text="Sample Missing", font=("Helvetica", 12), fill="red")
            except Exception as e:
                print(f"Sample image error: {e}")
                self.canvas.create_text((sx1 + sx2) // 2, (sy1 + sy2) // 2, text="Image Error", font=("Helvetica", 12), fill="red")
        else:
             self.canvas.create_text((sx1 + sx2) // 2, (sy1 + sy2) // 2, text="No Sample", font=("Helvetica", 12), fill="black")


        # Shutter button
        shutter_coords = (300, 450, 500, 500) # x1, y1, x2, y2
        self.canvas.create_rectangle(*shutter_coords, fill="red", outline="black", tags="shutter")
        self.canvas.create_text((shutter_coords[0]+shutter_coords[2])//2, (shutter_coords[1]+shutter_coords[3])//2,
                                text="📷 しゃしんをとる", font=font_subject, fill="white", tags="shutter") # Add tag to text

        # Back to main button (left bottom)
        back_coords = (50, 500, 250, 550) # x1, y1, x2, y2
        self.canvas.create_rectangle(*back_coords, fill="blue", outline="black", tags="back_to_main")
        self.canvas.create_text((back_coords[0]+back_coords[2])//2, (back_coords[1]+back_coords[3])//2,
                                text="🏠 さいしょにもどる", font=font_subject, fill="white", tags="back_to_main") # Add tag to text

        # Message area (initially empty) - create text item to update later
        self.message_id = self.canvas.create_text(400, 570, text="", font=("Helvetica", 16), fill="red", anchor=tk.CENTER)


    def mouse_event(self, event):
        """Handles mouse clicks based on the current screen."""
        x, y = event.x, event.y
        clicked_tags = self.canvas.gettags(tk.CURRENT) # Get tags of item under cursor

        if self.current_screen == "main":
            # Check tags instead of raw coordinates for flexibility
            if "house" in clicked_tags:
                if not self.captured_images["house"]: # Only allow capture if not already done
                    self.blocknumber = 0 # House
                    self.draw_next_screen()
            elif "cars" in clicked_tags:
                 if not self.captured_images["cars"]: # Only allow capture if not already done
                    self.blocknumber = 1 # Cars
                    self.draw_next_screen()
            # Add clicks for already captured image areas if needed (e.g., re-capture?)
            elif "house_area" in clicked_tags:
                 print("House already captured. Click button again to re-capture?")
                 # Optional: Add logic to allow re-capturing
                 # self.blocknumber = 0
                 # self.captured_images["house"] = None # Reset
                 # self.draw_next_screen()
            elif "cars_area" in clicked_tags:
                 print("Cars already captured. Click button again to re-capture?")
                 # Optional: Add logic to allow re-capturing
                 # self.blocknumber = 1
                 # self.captured_images["cars"] = None # Reset
                 # self.draw_next_screen()


        elif self.current_screen == "next":
            if "shutter" in clicked_tags:
                self.capture_shutter()
            elif "back_to_main" in clicked_tags:
                self.draw_main_screen() # Go back to main screen

    def capture_shutter(self):
        """
        Captures an image from the camera, performs object detection using YOLO,
        removes the background of the detected object, trims transparency,
        and saves the result. Updates the main screen if successful.
        """
        if self.last_frame is not None:
            # 1. Save the raw captured frame temporarily
            raw_filename = f"temp_capture_{self.blocknumber}.jpg"
            raw_capture_path = os.path.join(self.output_dir, raw_filename)
            cv2.imwrite(raw_capture_path, self.last_frame)
            print(f"Temporary image saved: {raw_capture_path}")

            # Update message to indicate processing
            self.canvas.itemconfig(self.message_id, text="しゃしんをしらべてるよ...")
            self.root.update_idletasks() # Force UI update

            # 2. Run YOLO detection on the saved image
            try:
                results = self.model(raw_capture_path)
            except Exception as e:
                 print(f"Error during YOLO detection: {e}")
                 self.canvas.itemconfig(self.message_id, text="エラー！うまくしらべられなかった...")
                 return

            # 3. Process detection results
            confidence_threshold = 0.3 # Adjusted confidence threshold
            detected = False
            best_match_found = False # Flag to ensure only the best match is processed

            if results and results[0].boxes and len(results[0].boxes) > 0:

                # Sort detections by confidence score (descending)
                sorted_indices = np.argsort(results[0].boxes.conf.cpu().numpy())[::-1]

                for i in sorted_indices:
                    if best_match_found: break # Stop after finding the first valid match

                    box = results[0].boxes.xyxy[i]
                    confidence = results[0].boxes.conf[i]
                    label_index = int(results[0].boxes.cls[i])
                    object_type = self.model.names.get(label_index, "unknown") # Safely get name

                    print(f"Detected: {object_type} (Conf: {confidence:.2f})")

                    # Check if confidence is high enough
                    if confidence < confidence_threshold:
                        print(f"  Skipping low confidence detection.")
                        continue

                    # Check if the detected object matches the expected type
                    expected_type = "house" if self.blocknumber == 0 else "cars"
                    if object_type != expected_type:
                        print(f"  Skipping - Expected '{expected_type}', got '{object_type}'.")
                        continue

                    # --- Match Found! Process this one ---
                    best_match_found = True
                    detected = True
                    print(f"  Processing best match: {object_type}")

                    # 4. Crop the detected object from the *original Pillow image* for better quality
                    try:
                        original_image_pil = Image.open(raw_capture_path)
                        x1, y1, x2, y2 = map(int, box.tolist())
                        # Add some padding to the crop box if desired (optional)
                        padding = 10
                        x1 = max(0, x1 - padding)
                        y1 = max(0, y1 - padding)
                        x2 = min(original_image_pil.width, x2 + padding)
                        y2 = min(original_image_pil.height, y2 + padding)

                        cropped_pil = original_image_pil.crop((x1, y1, x2, y2))
                    except Exception as e:
                        print(f"Error cropping image: {e}")
                        self.canvas.itemconfig(self.message_id, text="エラー！ しゃしんのきりぬきにしっぱい...")
                        continue # Try next detection if available (though unlikely now)


                    # 5. Remove background using rembg
                    try:
                        output_data = remove(cropped_pil.tobytes(), alpha_matting=True) # Use alpha matting for potentially better edges
                        removed_bg_pil = Image.frombytes("RGBA", cropped_pil.size, output_data)
                    except Exception as e:
                        print(f"Error removing background: {e}")
                        self.canvas.itemconfig(self.message_id, text="エラー！ はいけいをけせなかった...")
                        continue

                    # 6. Trim transparent area
                    # Define paths for saving intermediate and final results
                    bg_removed_path = os.path.join(self.output_dir, f"result_{object_type}.png")
                    trimmed_output_path = os.path.join(self.output_dir, f"trimmed_{object_type}.png")
                    removed_bg_pil.save(bg_removed_path, "PNG") # Save intermediate step

                    if self.trim_transparent_area(bg_removed_path, trimmed_output_path):
                        # 7. Save the final trimmed image path
                        self.captured_images[object_type] = trimmed_output_path
                        print(f"Successfully processed and saved: {trimmed_output_path}")
                        # Go back to main screen AFTER successful processing
                        self.draw_main_screen()
                    else:
                        print(f"Trimming failed for {bg_removed_path}. Using untrimmed version.")
                        # Fallback: Use the background-removed but untrimmed image
                        self.captured_images[object_type] = bg_removed_path
                        self.draw_main_screen() # Still go back, but with untrimmed

            # --- After checking all detections ---
            if not detected: # No valid detection passed checks
                if results and results[0].boxes and len(results[0].boxes) > 0:
                    # Objects were detected, but not the right type or confidence
                    self.canvas.itemconfig(self.message_id, text="うーん、ちがうものみたい？ もういちど！")
                else:
                    # No objects detected at all
                    self.canvas.itemconfig(self.message_id, text="なにもみつけられなかったよ...")
            
            # Clean up the temporary raw capture file
            if os.path.exists(raw_capture_path):
                try:
                    os.remove(raw_capture_path)
                    print(f"Deleted temporary file: {raw_capture_path}")
                except Exception as e:
                    print(f"Error deleting temporary file {raw_capture_path}: {e}")

        else:
            self.canvas.itemconfig(self.message_id, text="カメラがうごいてないみたい...")


    def trim_transparent_area(self, input_path, output_path):
        """
        Trims the transparent border from a PNG image.

        Args:
            input_path (str): Path to the input PNG image.
            output_path (str): Path to save the trimmed PNG image.

        Returns:
            bool: True if trimming was successful, False otherwise.
        """
        try:
            img = Image.open(input_path).convert("RGBA")

            # Get the bounding box of the non-transparent area
            bbox = img.getbbox()

            if bbox:
                # Crop the image to the bounding box
                trimmed_img = img.crop(bbox)
                trimmed_img.save(output_path, "PNG")
                print(f"Trimmed image saved: {output_path}")
                return True
            else:
                # Image might be entirely transparent
                print(f"No non-transparent pixels found in {input_path}. Cannot trim.")
                # Copy the original if it's all transparent? Or just return False?
                # Let's return False, indicating trimming didn't happen.
                return False

        except FileNotFoundError:
             print(f"Error trimming: Input file not found at {input_path}")
             return False
        except Exception as e:
            print(f"Error trimming transparent image: {e}")
            return False


    def update_frame(self):
        """Reads a frame from the camera and updates the display if on the 'next' screen."""
        if self.capture and self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                self.frame_count += 1
                 # Update less frequently to save resources, adjust as needed
                if self.frame_count % 3 == 0:
                    self.last_frame = frame # Store the latest frame for capture

                    # Only update the canvas if we are on the screen showing the camera feed
                    if self.current_screen == "next":
                        try:
                            frame_rgb = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2RGB)
                            frame_image = Image.fromarray(frame_rgb)
                            # Define target size for camera feed display
                            cam_w, cam_h = 300, 300
                            frame_image = frame_image.resize((cam_w, cam_h))
                            self.image_tk = ImageTk.PhotoImage(image=frame_image) # Keep reference

                            # Define center coordinates for the camera feed image
                            cam_x, cam_y = 550, 200
                            # Draw the new frame OVER the placeholder/previous frame
                            # Ensure we use a specific tag to easily delete/update later if needed
                            self.canvas.create_image(cam_x, cam_y, anchor=tk.CENTER, image=self.image_tk, tags="camera_feed")

                        except Exception as e:
                            print(f"Error updating camera feed display: {e}")
                            # Optionally display an error message on the canvas

        # Schedule the next frame update
        self.root.after(30, self.update_frame) # Update roughly 30 times per second (adjust interval)

    def on_close(self):
        """Releases resources and cleans up files when the window is closed."""
        print("Closing application...")
        # Release camera
        if self.capture and self.capture.isOpened():
            self.capture.release()
            print("Camera released.")

        # Delete temporary capture files and potentially processed images
        # It's safer to delete specific temp files than everything in output_dir
        for i in range(2): # Assuming block numbers 0 and 1
            temp_filename = f"temp_capture_{i}.jpg"
            temp_path = os.path.join(self.output_dir, temp_filename)
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    print(f"Deleted: {temp_path}")
                except Exception as e:
                    print(f"Error deleting {temp_path}: {e}")
            
            # Optional: Clean up processed images if desired upon closing
            # result_filename = f"result_house.png" # Example for house
            # result_path = os.path.join(self.output_dir, result_filename)
            # if os.path.exists(result_path):
            #    # os.remove(result_path) ... and so on for car, trimmed versions

        # Destroy the Tkinter window
        self.root.destroy()

# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()

    # Define fonts (Consider using more universally available fonts or checking OS)
    try:
        font_title = font.Font(family="MS Gothic", size=50) # Might not exist on non-Windows
        font_title2 = font.Font(family="MS Gothic", size=30)
        font_subject = font.Font(family="MS Gothic", size=20)
    except tk.TclError:
        print("Warning: MS Gothic font not found. Using default fonts.")
        font_title = font.Font(size=50) # Fallback
        font_title2 = font.Font(size=30)
        font_subject = font.Font(size=20)


    # Global variables for initial button stipple (placeholder appearance)
    tome_home ="gray75" # Stipple pattern for house button when not captured
    tome_car ="gray75"  # Stipple pattern for car button when not captured

    # Create and run the application
    app = BlockGameApp(root)
    # Set the close window protocol
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    # Start the Tkinter main loop
    root.mainloop()