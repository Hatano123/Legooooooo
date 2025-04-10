import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtGui import QPixmap
import pyqtgraph.opengl as gl
import numpy as np
from stl import mesh  # numpy-stlを使用
import cv2

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("PyQt with 3D Model")
        self.setGeometry(100, 100, 800, 600)

        self.widget = gl.GLViewWidget(self)
        self.widget.setCameraPosition(distance=500)  # カメラの距離を調整
        self.widget.setGeometry(0, 0, 800, 600)
        self.widget.show()

        self.model = self.createModel("output.stl")
        self.widget.addItem(self.model)

    def createModel(self,model_path):
        # STLファイルの読み込みと3Dモデルの作成
        your_mesh = mesh.Mesh.from_file(model_path)  # STLファイルパス
        vertices = np.array(your_mesh.vectors, dtype=np.float32)
        faces = np.arange(vertices.shape[0] * 3, dtype=np.uint32).reshape(vertices.shape[0], 3)
        model = gl.GLMeshItem(vertexes=vertices.reshape(-1, 3), faces=faces, smooth=False, color=(1, 1, 1, 1), shader="shaded")
    
        return model

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

