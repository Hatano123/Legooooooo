import cv2

def find_available_cameras(max_devices=5):
    available_cameras = []
    for index in range(max_devices):
        cap = cv2.VideoCapture(index)
        if cap is not None and cap.isOpened():
            available_cameras.append(index)
            cap.release()
    return available_cameras

if __name__ == "__main__":
    cameras = find_available_cameras()
    if cameras:
        print("利用可能なカメラ：", cameras)
    else:
        print("利用可能なカメラは見つかりませんでした。")
