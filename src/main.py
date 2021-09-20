import sys
import os
import json

from PyQt5.QtWidgets import QWidget, QToolTip, QApplication, QGridLayout
from PyQt5.QtGui import QCloseEvent, QDoubleValidator, QFont, QIcon
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np
import pandas as pd

import concurrent.futures as confu

from grob_image import *
from setup_window import *

class Worker(QRunnable):
    '''
    Worker thread
    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.
    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function
    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        # Retrieve args/kwargs here; and fire processing using them
        self.fn()

class MainWindow(QWidget):
    def __init__(self, config_path = 'config.json') -> None:
        super().__init__()

        self.config_file = config_path
        self.N = 1
        self.column = ["file dir"]
        self.screen = None
        self.icon_path = './icon/'

        self.interval = 1
        self.current_row = 0
        self.ocr_data = []

        self.threadpool = QThreadPool()

        self.read_config()

        self.init_ui()
        self.show()


    def read_config(self):
        # try open and read config.json
        # WARNING jsonが壊れているとエラーになる
        try:
            with open(self.config_file, "r") as f:
                json_load = json.load(f)

            self.screen = json_load['SCREEN']
            

        except json.JSONDecodeError:
            print('Error') 
            # TODO 何か他の処理を書く　
            # セットアップを起動させる or エラーをポップアップさせる

        

    def init_ui(self):
        ### setup user interface ###

        self.resize(530, 350)
        self.setWindowTitle('Image Save')

        self.layout = QVBoxLayout(self)
        ### Initialize tab screen ###
        self.tabs = QTabWidget()
        self.tab1 = QWidget(self)
        self.tab2 = QWidget()
        self.tabs.resize(600,500)

        ### Add tabs ###
        self.tabs.addTab(self.tab1,"OCR")
        self.tabs.addTab(self.tab2,"Settings")

        self.tab1_init_ui()
        self.tab2_init_ui()

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)


    def tab1_init_ui(self):
        self.tab1.layout = QVBoxLayout(self)
    
        # ----------------
        # Create Widgets
        # ----------------
        txt1 = QLabel(' Run ')
        txt2 = QLabel(' Stop ')

        ### button setting ###
        btn1 = QPushButton(' Run')
        btn2 = QPushButton(' Stop')
        btn3 = QPushButton(' Save')
        btn4 = QPushButton(' Clear All')
        btn1.setIcon(QIcon(self.icon_path + 'start.png'))
        btn2.setIcon(QIcon(self.icon_path + 'stop.png'))
        btn3.setIcon(QIcon(self.icon_path + 'save.png'))      
        btn1.clicked.connect(self.run_ocr)
        btn2.clicked.connect(self.stop_ocr)
        btn3.clicked.connect(self.save_file)
        btn4.clicked.connect(self.clear_table)

        ### Table setting ###
        self.table = QTableWidget(1, self.N)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setHorizontalHeaderLabels(self.column)

        ### layout ###
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(self.table, 0, 0, 5, 5)
        grid.addWidget(btn1, 6, 2)
        grid.addWidget(btn2, 6, 3)
        grid.addWidget(btn3, 6, 4) 
        grid.addWidget(btn4, 6, 1)
        self.tab1.setLayout(grid)
    

    def tab2_init_ui(self):
        self.tab2.layout = QVBoxLayout(self)

        # ----------------
        # Create Widgets
        # ----------------
        txt1 = QLabel(' データ間隔 [sec] ')
        
        btn1 = QPushButton(' 初期設定 ')
        #btn2 = QPushButton(' 更新 ')
        btn1.clicked.connect(self.initial_setting)
        #btn2.clicked.connect(self.update_tab1)

        ### text ###
        self.interval_box = QLineEdit('1')
        self.interval_box.setValidator(QDoubleValidator(0.0, 100.0, 3))

        ### layout ###
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(txt1, 0, 0)
        grid.addWidget(self.interval_box, 0, 1)
        grid.addWidget(btn1, 1, 0)
        #grid.addWidget(btn2, 1, 1)
         
        self.tab2.setLayout(grid)


    def run_ocr(self):
        self.run = True
        self.grob_img_ = ImageSave(self.screen)
        self.interval = float(self.interval_box.text())*1000
        
        if self.current_row == 0:
            res = self.grob_img_.image_encode()
            
            cur = QTableWidgetItem('{}'.format(res))
            self.table.setItem(0, 0, cur)
            

        self.timer = QTimer()
        with confu.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            self.timer.setInterval(int(self.interval))
            executor.submit(self.timer.timeout.connect(self.work))
            self.timer.start()

    
    def work(self):
        #self.tab1.active_threads.append(self.tab1.threadpool.activeThreadCount() + 1)
        worker = Worker(self.add_row)
        # Execute
        self.threadpool.start(worker)


    def add_row(self):
        if self.run:
            """
            Single Thread
            """
            self.table.insertRow(self.current_row+1)
            self.current_row += 1

            res = self.grob_img_.image_encode()
            
            cur = QTableWidgetItem('{}'.format(res))
            self.table.setItem(self.current_row, 0, cur)
            


    def stop_ocr(self):
        self.run = False
        self.update()


    def save_file(self):
        ### get table items ###
        for i in range(self.current_row+1):
            row_data = [self.table.item(i, j).text() for j in range(self.N)]
            self.ocr_data.append(row_data)
        #print(self.ocr_data)

        ### Save file Dialog ###        
        filter = 'csv(*.csv);;txt(*.txt)'
        name, _ = QFileDialog.getSaveFileName(self, 'Save File', filter= filter)
        df = pd.DataFrame(self.ocr_data, columns=self.column)
        df.to_csv(name, index=False)


    def clear_table(self):
        self.table.clear()
        for _ in range(self.current_row):
            self.table.removeRow(1)
        self.current_row = 0
        self.table.setHorizontalHeaderLabels(self.column)


    def initial_setting(self):
        MainClass_subWindow = SubWindowClass(self)
        MainClass_subWindow.subclass_show_PROC()     
        self.read_config()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_()) 
