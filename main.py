import sys
import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
# from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QLabel,
#         QMainWindow, QMenu, QMessageBox, QScrollArea, QSizePolicy, QWidget)
from PyQt5.QtWidgets import *
import numpy as np
import skimage.morphology, skimage.color, skimage.transform, skimage.io, skimage.filters
import cv2


class ImageViewer(QMainWindow):
    def __init__(self):
        super(ImageViewer, self).__init__()
        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.imageLabel.setMouseTracking(True)
        self.setMouseTracking(True)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setMouseTracking(True)
        self.setCentralWidget(self.scrollArea)
        self.createActions()
        self.createMenus()
        self.setWindowTitle("Image Viewer")
        self.menuBarRect = [self.menuBar().rect().x(),self.menuBar().rect().y(),\
                            self.menuBar().rect().width(),self.menuBar().rect().height()]
        # self.resize(2000, 1000+self.menuBarRect[3]) # default size
        self.fixed_image_size = [1500/2, 2000/2] # resize all of images
        self.scaleFactor = 1.0 # default scale factor
        self.isRunning = False # state of program
        self.bytesPerComponent = 3 # RGB

        self.nFile = 0 # number of files
        self.cur_fidx = 0 # selected file index
        self.cur_dir_idx = 0 # current subdirectory index
        self.cols = 4 # default columns of canvas
        self.rows = -1 # declare rows of canvas
        self.idx_label = None # declare index image
        self.need2DrawCanvas = True # for drawing canvas
        self.curMousePt = [0, 0] # declare current cursor point
        self.pressCtrl = False # (do no operating) state for pressing control key

        self.fundus = [] # (to do)
        self.FAG = [] # (to do)

        # list dock for subdirectory
        self.widget1 = QDockWidget("sub directory", self)
        self.listWidget = QListWidget()
        self.listWidget.clear()
        self.widget1.setWidget(self.listWidget)
        self.widget1.setFloating(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.widget1)
        self.listWidget.itemDoubleClicked.connect(self.item_double_click)

        # show full screen
        self.showFullScreen()
        # open directory browser
        self.openDirectory()

    # add item into list viewer
    def addSubDirIntoListViewer(self):
        self.listWidget.clear()
        for i, cur_dir in enumerate(self.sub_dir_list['name']):
            if self.cur_dir_idx == i:
                self.listWidget.addItem(cur_dir+'<---')
            else:
                self.listWidget.addItem(cur_dir)

    # list item double click event
    def item_double_click(self, item):
        self.cur_dir_idx = self.listWidget.currentRow()
        self.openChangedDirectory()

    # mouse button press event
    def mousePressEvent(self, QMouseEvent):
        if self.nFile == 0:
            return

        # get mouse position
        cursor = [int(np.round((QMouseEvent.pos().y() - self.menuBarRect[3]))), \
                  int(np.round(QMouseEvent.pos().x()))]

        # prevent Null(None)
        if self.idx_label[int(cursor[0]/self.scaleFactor), int(cursor[1]/self.scaleFactor)] != -1:
            # get selected image index
            self.cur_fidx = self.idx_label[int(cursor[0]/self.scaleFactor),
                                           int(cursor[1]/self.scaleFactor)]
            self.paint() # draw selected image

    # mouse button release event
    def mouseReleaseEvent(self, QMouseEvent):
        if self.nFile ==0:
            return

    # mouse move event
    def mouseMoveEvent(self, QMouseEvent):
        if self.nFile ==0:
            return

        # get mouse position
        cursor = [int(np.round((QMouseEvent.pos().y() - self.menuBarRect[3]))), \
                  int(np.round(QMouseEvent.pos().x()))]
        self.curMousePt = cursor # record current mouse position
        self.paint() # draw current mouse position

    # key press event
    def keyPressEvent(self, event):
        # get key
        key = event.key()

        # pressed control key
        if key == Qt.Key_Control:
            self.pressCtrl = True
        # pressed [ key
        elif key == Qt.Key_BracketLeft:
            self.zoomOut()
        # pressed ] key
        elif key ==Qt.Key_BracketRight:
            self.zoomIn()
        # pressed W key(move up)
        elif key == Qt.Key_W:
            tmp_cur_fidx = self.cur_fidx - self.cols
            if tmp_cur_fidx >= 0:
                self.cur_fidx = tmp_cur_fidx
            self.paint()
        # pressed S key(move down)
        elif key == Qt.Key_S:
            tmp_cur_fidx = self.cur_fidx + self.cols
            if tmp_cur_fidx < self.nFile:
                self.cur_fidx = tmp_cur_fidx
            self.paint()
        # pressed A key(move left)
        elif key == Qt.Key_A:
            tmp_cur_fidx = self.cur_fidx - 1
            if tmp_cur_fidx >= 0:
                self.cur_fidx = tmp_cur_fidx
            self.paint()
        # pressed D key(move right)
        elif key == Qt.Key_D:
            tmp_cur_fidx = self.cur_fidx + 1
            if tmp_cur_fidx < self.nFile:
                self.cur_fidx = tmp_cur_fidx
            self.paint()

    # key release event
    def keyReleaseEvent(self, event):
        # get key
        key = event.key()
        if key == Qt.Key_Control:
            self.pressCtrl = False

    ## wheel event
    # def wheelEvent(self, event):
    #     if self.pressCtrl:
    #         dgree = event.angleDelta()
    #         print(dgree)

    # zoom in
    def zoomIn(self):
        self.scaleImage(1.25)

    # zoom out
    def zoomOut(self):
        self.scaleImage(0.8)

    # restore scale to original image
    def normalSize(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    # fit to window frame size
    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked()
        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()

        self.updateActions()

    # resize event
    def resizeEvent(self, event):
        if self.isRunning == True:
            self.paint()

    # draw
    def paint(self):
        # get rows of current subdirectory image set
        if self.rows == -1:
            self.rows = int(np.ceil((len(self.img_list)-1)/float(self.cols)))

        # draw all of image into canvas
        if self.need2DrawCanvas:
            self.need2DrawCanvas = False
            # declare canvas
            self.canvas = np.ones([self.fixed_image_size[0]*self.rows, self.fixed_image_size[1]*self.cols, 3], dtype=np.ubyte)*255

            # declare index image for record and initialize to -1
            self.idx_label = np.zeros([self.fixed_image_size[0]*self.rows, self.fixed_image_size[1]*self.cols], dtype=np.int16)
            self.idx_label[:, :] = -1

            # record to all of image position at canvas
            self.drawPosition = []
            for i in range(len(self.img_list)):
                appear_boundary = self.img_list[i]
                appear_boundary = skimage.transform.resize(appear_boundary, self.fixed_image_size)*255
                appear_boundary = appear_boundary.astype(np.ubyte)
                appear_boundary[0:2, :] = [255, 255, 255]
                appear_boundary[-2:, :] = [255, 255, 255]
                appear_boundary[:, 0:2] = [255, 255, 255]
                appear_boundary[:, -2:] = [255, 255, 255]

                self.drawPosition.append([self.fixed_image_size[0]*int(i/self.cols),self.fixed_image_size[0]*(int(i/self.cols)+1),
                    self.fixed_image_size[1]*int(i%self.cols),self.fixed_image_size[1]*(int(i%self.cols)+1)])

                self.canvas[self.drawPosition[-1][0]:self.drawPosition[-1][1],
                self.drawPosition[-1][2]:self.drawPosition[-1][3]] = appear_boundary
                self.idx_label[self.drawPosition[-1][0]:self.drawPosition[-1][1],
                self.drawPosition[-1][2]:self.drawPosition[-1][3]] = i

        ## draw additional information like selected image, current cursor
        # copy canvas
        cur_canvas = self.canvas.copy()
        # draw selected image differently
        cur_canvas[self.drawPosition[self.cur_fidx][0]:self.drawPosition[self.cur_fidx][1],
        self.drawPosition[self.cur_fidx][2]:self.drawPosition[self.cur_fidx][3], 2] = 128

        # draw current curcor point
        cv2.circle(cur_canvas, (int((self.curMousePt[1]-4)/self.scaleFactor), int((self.curMousePt[0]-4)/self.scaleFactor)), 2, (255,0,0), -1)

        # update viewing layer(similar to update device context in MFC)
        self.bytesPerLine = self.bytesPerComponent * cur_canvas.shape[1]
        image_q = QImage(cur_canvas.data, cur_canvas.shape[1], cur_canvas.shape[0], self.bytesPerLine, QImage.Format_RGB888)
        self.imageLabel.setPixmap(QPixmap.fromImage(image_q))
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())
        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), 1)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), 1)
        self.updateActions()

    # open directory from selected path
    def openDirectory(self):
        self.need2DrawCanvas = True
        self.sub_dir_list = {}
        self.file_path_list = []
        self.img_list = []
        self.sub_dir_list['name'] = []
        self.sub_dir_list['path'] = []

        root_dir_path = QFileDialog.getExistingDirectory(self, "Open Directory",QDir.currentPath())
        if root_dir_path == "":
            return False

        root_dir_path = root_dir_path+'/'
        for sub_dir_name in sorted(os.listdir(root_dir_path)):
            path = root_dir_path + sub_dir_name + '/'
            if os.path.isdir(path):
                self.sub_dir_list['path'].append(root_dir_path + sub_dir_name + '/')
                self.sub_dir_list['name'].append(sub_dir_name)

        self.addSubDirIntoListViewer()

        for fname in sorted(os.listdir(self.sub_dir_list['path'][self.cur_dir_idx])):
            is_dcm = fname.find('.dcm') != -1
            if is_dcm is False:
                self.file_path_list.append([self.sub_dir_list['path'][self.cur_dir_idx] + fname, fname])

        # read all images
        for fpath, fname in self.file_path_list:
            img = skimage.io.imread(fpath)
            if len(img.shape)==2:
                img = skimage.color.gray2rgb(img)
            self.img_list.append(img)

        self.nFile = len(self.file_path_list)
        if self.nFile != 0:
            self.isRunning = True
            self.menuBarRect = [self.menuBar().rect().x(), self.menuBar().rect().y(), \
                                self.menuBar().rect().width(), self.menuBar().rect().height()]
            self.paint()

    # when Debugging or update code, open directory from prefixed path.
    # if you do not edit, must annotation!
    def openFixedDirectory(self):
        self.need2DrawCanvas = True
        self.sub_dir_list = {}
        self.file_path_list = []
        self.img_list = []

        # search directory
        root_dir_path = './data/'
        self.sub_dir_list['name'] = []
        self.sub_dir_list['path'] = []
        for sub_dir_name in sorted(os.listdir(root_dir_path)):
            path = root_dir_path + sub_dir_name + '/'
            if os.path.isdir(path):
                self.sub_dir_list['path'].append(root_dir_path + sub_dir_name + '/')
                self.sub_dir_list['name'].append(sub_dir_name)

        # add subdirectory into list viewer
        self.addSubDirIntoListViewer()

        for fname in sorted(os.listdir(self.sub_dir_list['path'][self.cur_dir_idx])):
            is_dcm = fname.find('.dcm') != -1
            if is_dcm is False:
                self.file_path_list.append([self.sub_dir_list['path'][self.cur_dir_idx] + fname, fname])

        # read all images
        for fpath, fname in self.file_path_list:
            img = skimage.io.imread(fpath)
            if len(img.shape)==2:
                img = skimage.color.gray2rgb(img)
            self.img_list.append(img)

        self.nFile = len(self.file_path_list)
        if self.nFile != 0:
            self.isRunning = True
            self.menuBarRect = [self.menuBar().rect().x(), self.menuBar().rect().y(), \
                                self.menuBar().rect().width(), self.menuBar().rect().height()]
            self.paint()

    # if changing subdirectory, reload image or path, etc
    def openChangedDirectory(self):
        self.need2DrawCanvas = True
        self.cur_fidx = 0
        self.file_path_list = []
        self.img_list = []

        # add subdirectory into list viewer
        self.addSubDirIntoListViewer()

        # reload image path
        for fname in sorted(os.listdir(self.sub_dir_list['path'][self.cur_dir_idx])):
            is_dcm = fname.find('.dcm') != -1
            if is_dcm is False:
                self.file_path_list.append([self.sub_dir_list['path'][self.cur_dir_idx] + fname, fname])

        # read all images
        for fpath, fname in self.file_path_list:
            img = skimage.io.imread(fpath)
            if len(img.shape) == 2:
                img = skimage.color.gray2rgb(img)
            self.img_list.append(img)

        self.nFile = len(self.file_path_list)
        if self.nFile != 0:
            self.isRunning = True
            self.menuBarRect = [self.menuBar().rect().x(), self.menuBar().rect().y(), \
                                self.menuBar().rect().width(), self.menuBar().rect().height()]
            self.paint()

    def createActions(self):
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q",
                triggered=self.close)

        self.zoomInAct = QAction("Zoom &In (25%)", self, shortcut="Ctrl++ or ]",
                enabled=False, triggered=self.zoomIn)

        self.zoomOutAct = QAction("Zoom &Out (25%)", self, shortcut="Ctrl+- or [",
                enabled=False, triggered=self.zoomOut)

        self.normalSizeAct = QAction("&Normal Size", self, shortcut="Ctrl+S",
                enabled=False, triggered=self.normalSize)

        # self.fitToWindowAct = QAction("&Fit to Window", self, enabled=False,
        #         checkable=True, shortcut="Ctrl+F", triggered=self.fitToWindow)

        self.aboutQtAct = QAction("About &Qt", self,
                triggered=QApplication.instance().aboutQt)

        self.openDirectoyAct = QAction("&Open Directory...", self, triggered=self.openDirectory) # added by kjNoh 170714

        self.openFixedDirectoyAct = QAction("&Open Fixed Directory...", self,
                                       triggered=self.openFixedDirectory)  # added by kjNoh 171027

    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openDirectoyAct)  # added by kjNoh 170714
        self.fileMenu.addAction(self.openFixedDirectoyAct)  # added by kjNoh 171027
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addSeparator()
        # self.viewMenu.addAction(self.fitToWindowAct)

        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.helpMenu)

    def updateActions(self):
        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())

    # image scaling
    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                                + ((factor - 1) * scrollBar.pageStep()/2)))

## main call ##
if __name__ == '__main__':
    app = QApplication(sys.argv)
    imageViewer = ImageViewer()
    imageViewer.show()
sys.exit(app.exec_())

