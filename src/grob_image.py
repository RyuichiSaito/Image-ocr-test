import datetime
import os

from PIL import Image, ImageGrab

class ImageSave():
    def __init__(self, screen, dirpath = './output/'):
        self.screen = screen
        self.dirpath = dirpath

        self.chk_dir()

    def chk_dir(self):
        if not os.path.isdir(self.dirpath):
            os.makedirs(self.dirpath)

    def image_encode(self):
        img = ImageGrab.grab(bbox=self.screen)

        now = datetime.datetime.now()
        filename = self.dirpath + 'img_' + now.strftime('%Y%m%d_%H%M%S_%f') + '.png'
        
        img.save(filename)

        return filename