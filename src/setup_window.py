import json
import time
import sys

from PyQt5.QtWidgets import QWidget, QToolTip, QApplication, QGridLayout
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import pyautogui as gui
import ctypes



class CreateOCRplace():
    def __init__(self, ocr_points = 1, ocr_path = 'C:\\Program Files\\Tesseract-OCR') -> None:
        self.ocr_points = ocr_points
        self.path = ocr_path
        self.window_positions = None

    def GetWindowPosition(self):
        """
        ウインドウ上でクリックした場所の座標を取得する．
        return : list [(x1,y1),(x2,y2)]
        """
        try:
            while True:
                if ctypes.windll.user32.GetAsyncKeyState(0x01) == 0x8000:
                    #print('左クリック')
                    time.sleep(0.1)
                    return list(gui.position())
                
        except KeyboardInterrupt:
            print('終了')
            sys.exit()



class SubWindowClass:
    """
    OCRの位置を取得するクラス
    """
    def __init__(self, parent=None):
        self.position = [-1]*4

        self.SubClass_subwindow = QDialog(parent)
        self.SubClass_parent = parent
        self.SubClass_subwindow.setWindowTitle('setup') 
        self.ocr = CreateOCRplace(1)
        self.initUI()

    def initUI(self):
        label1 = QLabel('   カーソルを当て左クリックしてください   ')
        btn1 = QPushButton('      1点目      ')
        btn2 = QPushButton('      2点目      ')
        btn3 = QPushButton(' OK ')

        btn1.clicked.connect(self.subclass_getub)
        btn2.clicked.connect(self.subclass_getlb)
        btn3.clicked.connect(self.subClass_close)

        # layout widgets
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(label1, 1, 0, 1, -1)
        grid.addWidget(btn1, 2, 0)
        grid.addWidget(btn2, 2, 1)
        grid.addWidget(btn3, 3, 1)

        self.SubClass_subwindow.setLayout(grid)


    def subclass_show_PROC(self):
        self.SubClass_subwindow.exec_()


    def subClass_close(self):
        if self.position.count(-1) == 0:
            #  左右逆なら入れ替え 
            if self.position[0] > self.position[2]:
                self.position[:] = [self.position[i] for i in (2,3,0,1)]
            print(self.position)

            cfg = ConfigEdit(1, self.position)
            cfg.config_write()
            self.SubClass_subwindow.close()


    def subclass_getub(self):
        res = self.ocr.GetWindowPosition()
        #print(res)
        self.position[0] = int(res[0])
        self.position[1] = int(res[1])


    def subclass_getlb(self):
        res = self.ocr.GetWindowPosition()
        #print(res)
        self.position[2] = int(res[0])
        self.position[3] = int(res[1])
        

class ConfigEdit():
    def __init__(self, ocrnum, screen,config_path = 'config.json') -> None:
        self.config_file = config_path
        self.ocrnum = ocrnum
        self.screen = screen

    def config_write(self):
        config_data = {
            'OCR_NUM' : self.ocrnum,
            'SCREEN' : self.screen
        }
        
        #print(config_data)
        with open(self.config_file, "w") as f:
            json.dump(config_data, f, indent=4)
