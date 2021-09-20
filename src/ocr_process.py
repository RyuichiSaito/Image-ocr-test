import os
import sys

import pyocr
import pandas as pd
import numpy as np
import numpy
import cv2
from PIL import Image

from multiprocessing import Pool
import multiprocessing as mp
import multiprocessing.sharedctypes

from PyQt5.QtWidgets import QWidget, QToolTip, QApplication, QGridLayout
from PyQt5.QtGui import QColor, QFont, QImage, QPainter, QPixmap
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


filepath = "data.csv"
ocr_path = 'C:\\Program Files\\Tesseract-OCR'
OCR_NUM = 10
df = pd.read_csv(filepath)
OCR_BOX = None
df_data = pd.DataFrame(np.zeros((df.shape[0], OCR_NUM)))


# add path 
pyocr.tesseract.TESSERACT_CMD = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
if ocr_path not in os.environ["PATH"].split(os.pathsep):
    os.environ["PATH"] += os.pathsep + ocr_path

# ocr settings
tools = pyocr.get_available_tools()
tool = tools[0]


# setting GUI
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.df = pd.read_csv(filepath)
        self.scale_factor = 0.8
        self.N = OCR_NUM

        self.ocr_boxes = np.zeros((self.N,4), dtype=numpy.int64)
        self.box_index = 0
        self.rect = None
        self.data = None

        self.mouse_press_signal = pyqtSignal()

        self.resize(530, 350)
        self.initUI()
        self.func_convimg()
        self.setWindowTitle('Setup')
        self.move(100,100)
        self.show()

    def initUI(self):
        # Button settings
        self.btn1 = QPushButton('OK')
        self.btn2 = QPushButton('Run')
        self.btn3 = QPushButton('Save')
        self.btn1.clicked.connect(self.pushed_ok)
        self.btn2.clicked.connect(self.pushed_run)
        self.btn3.clicked.connect(self.pushed_save)

        # image label
        self.img_label = QLabel()
        self.img_label.setPixmap(self.func_convimg())
        # painter
        self.mouse_events()
        self.painter = QPainter()

        # layout
        grid = QGridLayout()
        grid.setSpacing(10)

        # set label location
        grid.addWidget(self.img_label, 0, 0, 4, 4)
        grid.addWidget(self.btn1, 5, 1)
        grid.addWidget(self.btn2, 5, 2)
        grid.addWidget(self.btn3, 5, 3)

        self.setLayout(grid) 

    def cvt_color(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.bitwise_not(img)
        return img

    def func_convimg(self):
        first_path = self.df.iloc[0,0]
        cv_img = cv2.imread(first_path)
        cv_img = self.cvt_color(cv_img)
        cv_img = cv2.resize(cv_img, 
                            dsize=None, 
                            fx = self.scale_factor, 
                            fy = self.scale_factor)

        height, width, bytesPerComponent = cv_img.shape
        bytesPerLine = bytesPerComponent * width

        qimg = QImage(cv_img.data,
                    width,
                    height,
                    bytesPerLine,
                    QImage.Format_RGB888)
        
        pixmap = QPixmap.fromImage(qimg)
        return pixmap


    def mouse_events(self):
        self.img_label.mousePressEvent = self.press_point
        self.img_label.mouseReleaseEvent = self.release_point

    def press_point(self, event):
        self.last_pos = event.pos()

    def release_point(self, event):
        cur_pos = event.pos()
        bx = [self.last_pos.x(), cur_pos.x()]
        by = [self.last_pos.y(), cur_pos.y()]
        
        bx.sort()
        by.sort()
        self.rect = [bx[0], by[0], bx[1]-bx[0], by[1]-by[0]]
        self.drow_box()

    def drow_box(self):
        pixmap = self.func_convimg()

        self.painter.begin(pixmap)
        self.painter.setPen(QColor(255, 0, 0))
        for i in range(self.box_index):
            self.painter.drawRect(*self.ocr_boxes[i,:]*self.scale_factor)
        self.painter.drawRect(*self.rect)
        self.painter.end()

        self.img_label.setPixmap(pixmap)
    
    def pushed_ok(self):
        rect = [np.round(r/self.scale_factor) for r in self.rect]
        if len(self.rect) == 0 or rect == list(self.ocr_boxes[self.box_index-1,:]):
            pass
        else:
            self.ocr_boxes[self.box_index, :] = rect[:]
            self.box_index += 1
            print(self.ocr_boxes)

    def pushed_run(self):
        self.data = run(self.ocr_boxes)

    def pushed_save(self):
        ### Save file Dialog ###        
        filter = 'csv(*.csv);;txt(*.txt)'
        name, _ = QFileDialog.getSaveFileName(self, 'Save File', filter= filter)
        self.data.to_csv(name, index=False)


# OCR section
def cv2pil(image):
    '''
     OpenCV -> PIL
     '''
    new_image = image.copy()
    if new_image.ndim == 2:
        pass
    elif new_image.shape[2] == 3:
        new_image = cv2.cvtColor(new_image, cv2.COLOR_BGR2RGB)
    elif new_image.shape[2] == 4:
        new_image = cv2.cvtColor(new_image, cv2.COLOR_BGRA2RGBA)
    new_image = Image.fromarray(new_image)
    return new_image


def run(ocr_boxes):
    ocr_box = ocr_boxes.tolist()

    # cpu count
    njobs = 1
    if os.cpu_count() != 1:
        njobs = os.cpu_count() - 1

    pool = Pool(njobs)
    print(pool)

    n = df.shape[0]
    
    data_ls = []
    for j in range(OCR_NUM):
        arg = [(i, j, ocr_box) for i in range(n)]
        res = pool.map(image_encode, arg)
    
        data_ls.append(res)

    ans = pd.DataFrame(data_ls).T    
    return ans


def image_encode(init):
    i = init[0]
    j = init[1]
    ocr_box = init[2]

    #print(i)
    img_path = df.iloc[i,0]
    cv_img = cv2.imread(img_path)
    
    rect = ocr_box[j]
    
    left = rect[0]
    right = left + rect[2]
    top = rect[1]
    bottom = top + rect[3]
    if left==0 or right==0 or top==0 or bottom==0:
        return 0

    cv_img = cv_img[top:bottom, left:right]
    cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    cv_img = cv2.bitwise_not(cv_img)
    pil_img = cv2pil(cv_img)

    builder = pyocr.builders.DigitBuilder(tesseract_layout=3)
    res = tool.image_to_string(pil_img, builder = builder)
    return res


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
